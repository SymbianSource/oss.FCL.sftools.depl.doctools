/******************************************************************************
 *
 * Copyright (c) 2009 Nokia Corporation and/or its subsidiary(-ies).
 *
 * Permission to use, copy, modify, and distribute this software and its
 * documentation under the terms of the GNU General Public License is hereby 
 * granted. No representations are made about the suitability of this software 
 * for any purpose. It is provided "as is" without express or implied warranty.
 * See the GNU General Public License for more details.
 *
 */

#include <stdlib.h>

#include "qtbc.h"
#include "doxygen.h"
#include "message.h"
#include "config.h"
#include "classlist.h"
#include "util.h"
#include "defargs.h"
#include "outputgen.h"
#include "dot.h"
#include "pagedef.h"
#include "filename.h"
#include "version.h"
#include "xmlditadocvisitor.h"
#include "docparser.h"
#include "language.h"
#include "parserintf.h"
// DITA Specific includes
#include "xmldita.h"
#include "xmlwriter.h"
#include "xmlditagen.h"
#include "xmlditaelementprefix.h"
#include "xmlditacodegenerator.h"

#include <qdir.h>
#include <qfile.h>
#include <qtextstream.h>
#include <qmap.h>
// Only for linkifyTextDITA
#include <qregexp.h>

// Macros that control DITA output
/* File location such as:
<declarationFile name="filePath" value="C:/wip/sysdoc/tools/Doxygen/branches/DITA/test/PaulRo/func_inherit/src/func_inherit.h"/>
<declarationFileLine name="lineNumber" value="12"/>
<definitionFile name="filePath" value="C:/wip/sysdoc/tools/Doxygen/branches/DITA/test/PaulRo/func_inherit/src/func_inherit.h"/>
<definitionFileLineStart name="lineNumber" value="11"/>
<definitionFileLineEnd name="lineNumber" value="18"/>
*/
#define DITA_FILE_LOCATION					1
//#define DITA_GEN_MEMBERDEF_DEFINE			0
// For Doxygen do we emit elements that could be emitted for languages
// that we do not yet support
#define DITA_EMIT_FOR_UNSUPPORTED_LANGS		0

#define DITA_FILE_MEMBERS_IN_OWN_TOPICS		0

// If set this emits keyref attributes, otherwise they are href attributes
#define DITA_KEYREF_SUPPORT					0
// If set this emits <shortdesc> element
#define DITA_SHORTDESC_SUPPORT				0

// Global instance of the DITAElementPrefix class for use within this code
static DITAElementPrefix g_elemPrefix;

class TextGeneratorXMLDITALinker
{
public:
	TextGeneratorXMLDITALinker(XmlStream &xt): m_xt(xt) {}
	void writeString(const char *s, bool /*keepSpaces*/) const { m_xt << s; }
	void writeBreak() const {}
	void writeLink(const ClassDef *cd, const char *text) const;
	void writeLink(const MemberDef *md, const char *text) const;
private:
	XmlStream &m_xt;
};

// NOTE: There is a strong similarity here with DITAGenertorBase::id()
void TextGeneratorXMLDITALinker::writeLink(const ClassDef *cd, const char *text) const
{
#if DITA_KEYREF_SUPPORT
	XmlElement elem(m_xt, "apiRelation", "keyref", cd->getOutputFileBase());
#else
	QString mdId = cd->getOutputFileBase();
	mdId.append(Config_getString("XML_DITA_EXTENSION"));
	mdId.append("#");
	mdId.append(cd->getOutputFileBase());
	XmlElement elem(m_xt, "apiRelation", "href", mdId);
#endif
	m_xt.characters(text);
}

// NOTE: There is a strong similarity here with DITAGenertorBase::id()
void TextGeneratorXMLDITALinker::writeLink(const MemberDef *md, const char *text) const
{
#if DITA_KEYREF_SUPPORT
	QString mdId = md->getOutputFileBase();
	mdId.append("_1" + md->anchor());
	XmlElement elem(m_xt, "apiRelation", "keyref", mdId);
#else
	QString mdId = md->getOutputFileBase();
	mdId.append(Config_getString("XML_DITA_EXTENSION"));
	mdId.append("#");
	mdId.append(md->getOutputFileBase());
	mdId.append("_1" + md->anchor());
	XmlElement elem(m_xt, "apiRelation", "href", mdId);
#endif
	m_xt.characters(text);
}

// NOTE Similar to code in util.h and util.cpp
void linkifyTextDITA(const TextGeneratorXMLDITALinker &ol,
                 Definition *scope,
                 FileDef *fileScope,
                 const char *text
                );


/* It looks like what is happening here is that we are seraching
a string like "const Pod const &" for _identifier_(s) that we can
link to.
*/
void linkifyTextDITA(const TextGeneratorXMLDITALinker &out,
					Definition *scope,
					FileDef *fileScope,
					const char *text)
{
	//printf("`%s'\n",text);
	static QRegExp regExp("[a-z_A-Z\\x80-\\xFF][~!a-z_A-Z0-9.:\\x80-\\xFF]*");
	//static QRegExp regExpSplit("(?!:),");
	QCString txtStr = text;
	int strLen = txtStr.length();
	/*
	printf("linkifyTextDITA scope=\"%s\" fileScope=\"%s\" strtxt=\"%s\" strlen=%d\n",
	    scope ? scope->name().data() : "<none>",
	    fileScope ? fileScope->name().data() : "<none>",
	    txtStr.data(),
		strLen);
	*/
	int matchLen;
	int index = 0;
	int newIndex;
	int skipIndex = 0;
	int floatingIndex = 0;
	if (strLen == 0) {
		return;
	}
	// read a word from the text string
	while ((newIndex = regExp.match(txtStr, index, &matchLen)) != -1 && (newIndex == 0 || !(txtStr.at(newIndex-1) >= '0' && txtStr.at(newIndex-1) <= '9'))) {
		// avoid matching part of hex numbers
		// add non-word part to the result
		floatingIndex += newIndex - skipIndex+matchLen;
		bool insideString=FALSE; 
		int i;
		for (i = index; i < newIndex; i++) { 
			if (txtStr.at(i)=='"') {
				insideString = !insideString; 
			}
		}
		out.writeString(txtStr.mid(skipIndex,newIndex-skipIndex), FALSE); 
		// get word from string
		QCString word = txtStr.mid(newIndex, matchLen);
		QCString matchWord = substitute(word,".","::");
		//printf("linkifyTextDITA word=\"%s\" matchWord=\"%s\" scope=\"%s\"\n",
		//    word.data(),matchWord.data(),scope?scope->name().data():"<none>");
		bool found=FALSE;
		if (!insideString) {
			ClassDef     *cd = 0;
			FileDef      *fd = 0;
			MemberDef    *md = 0;
			NamespaceDef *nd = 0;
			GroupDef     *gd = 0;
			//printf("** Match word '%s'\n", matchWord.data());
			MemberDef *typeDef=0;
			if ((cd = getResolvedClass(scope, fileScope, matchWord, &typeDef))) {
				//printf("Found class \"%s\"\n", cd->name().data());
				// add link to the result
				if (cd->isLinkable()) {
					out.writeLink(cd, word);
					found = TRUE;
				}
			} else if (typeDef) {
				//printf("Found typedef %s\n",typeDef->name().data());
				if (typeDef->isLinkable()) {
					out.writeLink(typeDef, word);
					found=TRUE;
				}
			} else if ((cd=getClass(matchWord+"-p"))) {
				// search for Obj-C protocols as well
				// add link to the result
				if (cd->isLinkable()) {
					out.writeLink(cd, word);
					found = TRUE;
				}
			} else {
				//printf("   -> nothing\n");
			}
			QCString scopeName;
			if (scope && (scope->definitionType() == Definition::TypeClass || scope->definitionType() == Definition::TypeNamespace)) {
				scopeName = scope->name();
			}
			//printf("ScopeName=%s\n",scopeName.data());
			//if (!found) {
			//	printf("Trying to link %s in %s\n",word.data(),scopeName.data()); 
			//}
			if (!found && getDefs(scopeName, matchWord, 0, md, cd, fd, nd, gd) && (md->isTypedef() || md->isEnumerate() || md->isReference() || md->isVariable()) && md->isLinkable()) {
				//printf("Found ref scope=%s\n",d?d->name().data():"<global>");
				//ol.writeObjectLink(d->getReference(),d->getOutputFileBase(),
				//                       md->anchor(),word);
				out.writeLink(md, word);
				found=TRUE;
			}
		}
		if (!found) {
			// add word to the result
			out.writeString(word, FALSE);
		}
		// set next start point in the string
		//printf("index=%d/%d\n",index,txtStr.length());
		skipIndex=index=newIndex+matchLen;
	}
	// add last part of the string to the result.
	out.writeString(txtStr.right(txtStr.length()-skipIndex), FALSE);
}

#if USE_DOXYGEN_ID_AS_XML_ID == 0
// This is a tempory hack to give Doxygen Definition objects a different ID
// that can be used by the visitor class when writing xref's
#include "xmlditaxrefmap.h"

void DITAGeneratorBase::remapXrefs(DocNode *root) const
{
	XmlDitaXrefERemapDocVisitor v;
	// visit all nodes
	root->accept(&v);
    XrefMapT::Iterator it;
	for( it = v.m_XrefRemap.begin(); it != v.m_XrefRemap.end(); ++it ) {
		//QString myNewStr = id(it.key());
		Definition *d = it.key();
		if (d->definitionType() == Definition::TypeMember) {
			v.m_XrefRemap[it.key()] = id((MemberDef*)it.key());
		} else {
			v.m_XrefRemap[it.key()] = id(it.key());
		}
	}
	for( it = v.m_XrefRemap.begin(); it != v.m_XrefRemap.end(); ++it ) {
		printf("Horrible remap hack: %x -> %s\n", it.key(), it.data().data());
    }
}

#endif


/****************************************************
 * Section: DITAGeneratorBase - Common functionality.
 ****************************************************/
void DITAGeneratorBase::writeXMLDocBlock(XmlStream &t,
					  const QCString &fileName,
					  int lineNr,
					  Definition *scope,
					  MemberDef * md,
					  const QCString &text,
					  ParamDescriptionMap *pMap) const
{
	QCString stext = text.stripWhiteSpace();
	if (stext.isEmpty()) {
		return;
	}
	if (pMap) {
		t.outputSuspend();
	}
	// convert the documentation string into an abstract syntax tree
	DocNode *root = validatingParseDoc(fileName, lineNr, scope, md, text+"\n", FALSE, FALSE);
#if USE_DOXYGEN_ID_AS_XML_ID == 0
	remapXrefs(root);
#endif
	// create a code generator
	XMLDITACodeGenerator *xmlCodeGen = new XMLDITACodeGenerator(t);
	// create a parse tree visitor for XML
	XmlDitaDocVisitor *visitor = new XmlDitaDocVisitor(t, *xmlCodeGen);
	// visit all nodes
	root->accept(visitor);
	if (pMap) {
		// Load map with result
		pMap->clear();
		QDictIterator<QString> it = visitor->queryIterator();
		while (it.current()) {
			/*printf("writeXMLDocBlock() loading param \"%s\" with \"%s\"\n",
					it.currentKey(),
					(visitor->query(it.currentKey())).data()
					);
			*/
			pMap->insert(it.currentKey(), visitor->query(it.currentKey()));
			++it;
		}
		// Resume output on the stream
		t.outputResume();
	}
	// clean up
	delete visitor;
	delete xmlCodeGen;
	delete root;
}

/** Opens an element, writes some text and closes the element.
@param t The XML stream to write to.
@param e The XML element name.
@param a The XML element attributes.
@param text The Text to write in the element.
*/
void DITAGeneratorBase::writeXMLElementAndText(XmlStream& t, QString e, AttributeMap& a, QString text) const
{
	XmlElement elem(t, e, a);
	t.characters(text);
}

/** Opens an element, writes some text and closes the element.
@param t The XML stream to write to.
@param e The XML element name.
@param text The Text to write in the element.
*/
void DITAGeneratorBase::writeXMLElementAndText(XmlStream& t, QString e, QString text) const
{
	XmlElement elem(t, e, AttributeMap());
	t.characters(text);
}

QString DITAGeneratorBase::accessSpecifier(Protection p, bool assertOnPackage) const
{
	QString s;
	switch (p) {
		case Public:
			s = "public";
			break;
		case Protected:
			s = "protected";
			break;
		case Private:
			s = "private";
			break;
		case Package:
			if (assertOnPackage) {
				ASSERT(0);
			}
			s = "package";
			break;
	}
	return s;
}

/** Write out the class access e.g. <cxxClassAccessSpecifier value="public"/> */
void DITAGeneratorBase::writeAccessSpecifierElement(XmlStream &xs,
													ClassDef *cd,
													Protection p) const
{
	XmlElement(xs,
		g_elemPrefix.elemPrefix(cd, true)+"AccessSpecifier",
		"value",
		accessSpecifier(p, false));
}

/** Write out the member access e.g. <cxxFunctionAccessSpecifier value="public"/> */
void DITAGeneratorBase::writeAccessSpecifierElement(XmlStream &xs,
													MemberDef *md,
													Protection p) const
{
	XmlElement(xs,
		g_elemPrefix.elemPrefix(md, true)+"AccessSpecifier",
		"value",
		accessSpecifier(p, false));
}

/** Write out an element with a prefix such as <cxxFunctionPureVirtual/> */
void DITAGeneratorBase::writeVirtualElement(XmlStream &xs, QString p, Specifier v) const
{
	switch (v) {
		case Normal:
			// Nothing
			break;
		case Virtual:
			XmlElement(xs, p+"Virtual");
			break;
		case Pure:
			XmlElement(xs, p+"PureVirtual");
			break;
	}
}

/** Write out an element such as <cxxFunctionPureVirtual/> */
void DITAGeneratorBase::writeVirtualElement(XmlStream &xs, MemberDef *md)
{
	writeVirtualElement(xs, g_elemPrefix.elemPrefix(md, true), md->virtualness());
}

/** Write out an element that specifically describes inheritence
such as <cxxClassPureVirtual/> */
void DITAGeneratorBase::writeVirtualElement(XmlStream &xs, ClassDef *cd, Specifier v)
{
	writeVirtualElement(xs, g_elemPrefix.elemPrefix(cd, true), v);
}

/** Writes a reference to a record (class, struct, union).
For example is suffix is "BaseClass":
<cxxClassBaseClass keyref="xvz">xzy</cxxClassBaseClass>
*/
void DITAGeneratorBase::writeReferenceTo(XmlStream &xs, const ClassDef *cd, const QString &suffix)
{
#if DITA_KEYREF_SUPPORT
	XmlElement e(xs, g_elemPrefix.elemReference(cd)+suffix, "keyref", id(cd));
#else
	QString mdId = cd->getOutputFileBase();
	mdId.append(Config_getString("XML_DITA_EXTENSION"));
	mdId.append("#");
	mdId.append(id(cd));
	XmlElement e(xs, g_elemPrefix.elemReference(cd)+suffix, "href", mdId);
#endif
	xs.characters(cd->qualifiedName());
}

/** Writes a reference to a member.
For example <cxxFunction+suffix keyref="xvz">xzy</cxxFunction+suffix>
*/
void DITAGeneratorBase::writeReferenceTo(XmlStream &xs, const MemberDef *md, const QString &suffix)
{
#if DITA_KEYREF_SUPPORT
	XmlElement e(xs, g_elemPrefix.elemReference(md)+suffix, "keyref", id(md));
#else
	QString mdId = md->getOutputFileBase();
	mdId.append(Config_getString("XML_DITA_EXTENSION"));
	mdId.append("#");
	mdId.append(id(md));
	XmlElement e(xs, g_elemPrefix.elemReference(md)+suffix, "href", mdId);
#endif
	xs.characters(nameLookup(md));
}

/** Writes a reference to a member from a class/struct/union.
For example <cxxClassFunction+suffix keyref="xvz">xzy</cxxClassFunction+suffix>
*/
void DITAGeneratorBase::writeReferenceTo(XmlStream &xs, const ClassDef *cd, const MemberDef *md, const QString &suffix)
{
#if DITA_KEYREF_SUPPORT
	XmlElement e(xs,
		g_elemPrefix.elemReference(cd)+g_elemPrefix.memberKind(md)+suffix,
		"keyref",
		id(md));
#else
	QString mdId = cd->getOutputFileBase();
	mdId.append(Config_getString("XML_DITA_EXTENSION"));
	mdId.append("#");
	mdId.append(id(md));
	XmlElement e(xs,
		g_elemPrefix.elemReference(cd)+g_elemPrefix.memberKind(md)+suffix,
		"href",
		mdId);
#endif
	xs.characters(nameLookup(md));
}

void DITAGeneratorBase::writeInnerClasses(const ClassDef *pc, const ClassSDict *cl, XmlStream &t)
{
	bool mustWrite = false;
	if (cl) {
		ClassSDict::Iterator cli(*cl);
		ClassDef *cd;
		for (cli.toFirst(); (cd = cli.current()); ++cli) {
			// skip anonymous scopes
			if (cd && !cd->isHidden() && cd->name().find('@')==-1) {
				mustWrite = true;
				break;
			}
		}
	}
	if (cl && mustWrite) {
		ClassSDict::Iterator cli(*cl);
		XmlElement el0(t, g_elemPrefix.elemPrefix(pc, true)+"Nested");
		XmlElement el1(t, g_elemPrefix.elemPrefix(pc, true)+"NestedDetail");
		ClassDef *cd;
		for (cli.toFirst(); (cd = cli.current()); ++cli) {
			// skip anonymous scopes
			if (!cd->isHidden() && cd->name().find('@')==-1) {
				//writeXMLElementAndText(t, "apiName", cd->name());
				// "Nested*" is chosen because of ISO/IEC 14882:1998(E) 9.7 Nested class declarations [class.nest]
				//writeReferenceTo(t, pc, "Nested" + g_elemPrefix.memberKind(cd));
				//void DITAGeneratorBase::writeReferenceTo(XmlStream &xs, const ClassDef *cd, const MemberDef *md, const QString &suffix)
				// Note quirky way of composeing this
				QString mdId = cd->getOutputFileBase();
				mdId.append(Config_getString("XML_DITA_EXTENSION"));
				mdId.append("#");
				mdId.append(id(cd));
				XmlElement e(t,
					g_elemPrefix.elemReference(pc)+"Nested" + g_elemPrefix.memberKind(cd),
					"href",
					mdId);
				t.characters(cd->name());
			}
		}
	}
}

/*
void DITAGeneratorBase::writeInnerClasses(const NamespaceDef *npc, const ClassSDict *cl, XmlStream &t)
{
	if (cl) {
		ClassSDict::Iterator cli(*cl);
		ClassDef *cd;
		for (cli.toFirst(); (cd = cli.current()); ++cli) {
			// skip anonymous scopes
			if (!cd->isHidden() && cd->name().find('@')==-1) {
				// "NestedClass" is chosen because of ISO/IEC 14882:1998(E) 9.7 Nested class declarations [class.nest] 
				writeReferenceTo(t, npc, g_elemPrefix.elemPrefix(cd, true) + "Nested");
			}
		}
	}
}
*/

void DITAGeneratorBase::writeTemplateArgumentList(ClassDef *cd,
												ArgumentList *al,
												XmlStream &xt,
												Definition *scope,
												FileDef *fileScope)
{
	if (al) {
		XmlElement tplElem(xt, g_elemPrefix.elemPrefix(cd, true) + "TemplateParamList");
		ArgumentListIterator ali(*al);
		Argument *a;
		for (ali.toFirst();(a=ali.current());++ali) {
			XmlElement tplElem(xt, g_elemPrefix.elemPrefix(cd, true) + "TemplateParameter");
			// In an ArgumentList the type always seems to be empty
			if (!a->type.isEmpty()) {
				//XmlElement(xt, "type");
				linkifyTextDITA(TextGeneratorXMLDITALinker(xt), scope, fileScope, a->type);
			}
			// TODO: Fix this element
			/*
			if (!a->name.isEmpty()) {
				writeXMLElementAndText(xt, "declname", a->name);
				//writeXMLElementAndText(xt, "defname", a->name);
			}
			*/
			// TODO: Fix this element
			/*
			if (!a->defval.isEmpty()) {
				XmlElement(xt, "defval");
				xt << a->defval;
				//linkifyTextDITA(TextGeneratorXMLDITALinker(xt), scope, fileScope, a->defval);
			}
			*/
		}
	}
}

void DITAGeneratorBase::writeTemplateArgumentList(MemberDef *md,
												ArgumentList *al,
												XmlStream &xt,
												Definition *scope,
												FileDef *fileScope)
{
	if (al) {
		XmlElement tplElem(xt, g_elemPrefix.elemPrefix(md, true) + "TemplateParamList");
		ArgumentListIterator ali(*al);
		Argument *a;
		for (ali.toFirst(); (a = ali.current()); ++ali) {
			XmlElement tplElem(xt, g_elemPrefix.elemPrefix(md, true) + "TemplateParameter");
			// In an ArgumentList the type always seems to be empty
			if (!a->type.isEmpty()) {
				//XmlElement(xt, "type");
				linkifyTextDITA(TextGeneratorXMLDITALinker(xt), scope, fileScope, a->type);
			}
			// TODO: Fix this element
			/*
			if (!a->name.isEmpty()) {
				writeXMLElementAndText(xt, "declname", a->name);
				//writeXMLElementAndText(xt, "defname", a->name);
			}
			*/
			// TODO: Fix this element
			/*
			if (!a->defval.isEmpty()) {
				XmlElement(xt, "defval");
				xt << a->defval;
				//linkifyTextDITA(TextGeneratorXMLDITALinker(xt), scope, fileScope, a->defval);
			}
			*/
		}
	}
}

void DITAGeneratorBase::generateXMLForBriefDescription(Definition *d, MemberDef *md, XmlStream &xs) const
{
#if DITA_SHORTDESC_SUPPORT
	XmlElement e(xs, "shortdesc");
	// TODO: Remove once we work out what to do here (shortdesc cannot have p etc.)
	ParamDescriptionMap *pMap = new ParamDescriptionMap();
	if (md == 0) {
		//writeXMLDocBlock(xs, d->briefFile(), d->briefLine(), d, 0, d->briefDescription(), 0);
		writeXMLDocBlock(xs, d->briefFile(), d->briefLine(), d, 0, d->briefDescription(), pMap);
	} else {
		//writeXMLDocBlock(xs, md->briefFile(), md->briefLine(), d, md, md->briefDescription(), 0);
		writeXMLDocBlock(xs, md->briefFile(), md->briefLine(), d, md, md->briefDescription(), pMap);
	}
	delete pMap;
#endif
}

void DITAGeneratorBase::generateXMLForDetailedDescription(Definition *d, MemberDef *md, XmlStream &xs) const
{
	XmlElement e(xs, "apiDesc");
	if (md == 0) {
		writeXMLDocBlock(xs, d->docFile(), d->docLine(), d, 0, d->documentation(), 0);
	} else {
		writeXMLDocBlock(xs, md->docFile(), md->docLine(), d, md, md->documentation(), 0);
	}
}

void DITAGeneratorBase::writeFileLocation(Definition *d, XmlStream &xt, const QString &prefix, bool incDef) const
{
#if DITA_FILE_LOCATION
	QString lineNum;
	AttributeMap attrs;
	XmlElement elemLocation(xt, prefix+"APIItemLocation");
	// <declarationFile name="path" value="include/foo.h”/ >
	// <declarationFile name="line" value="172"/>
	attrs["name"] = "filePath";
	attrs["value"] = d->getDefFileName();
	XmlElement(xt, prefix+"DeclarationFile", attrs);
	// For line numbers ignore things like namespaces, groups, file, package etc.
	// in fact everything except classes and members
	if (d->definitionType() == Definition::TypeClass || d->definitionType()==Definition::TypeMember) {
		attrs["name"] = "lineNumber";
		attrs["value"] = lineNum.setNum(d->getDefLine());
		XmlElement(xt, prefix+"DeclarationFileLine", attrs);
	}
	if (incDef && d->getStartBodyLine() != -1 && d->getEndBodyLine() != -1) {
		QString defFileName;
		FileDef *fDef = d->getBodyDef();
		if (fDef && d->definitionType() == Definition::TypeMember) {
			// Functions etc.
			defFileName = fDef->absFilePath();
		} else {
			defFileName = d->getDefFileName();
		}
		// <definitionFile name="path" value="src/foo.cpp”/ >
		// <definitionFileLineStart name="line" value="754"/>
		// <definitionFileLineEnd name="line" value="778"/>
		attrs["name"] = "filePath";
		attrs["value"] = defFileName;
		XmlElement(xt, prefix+"DefinitionFile", attrs);
		attrs["name"] = "lineNumber";
		attrs["value"] = lineNum.setNum(d->getStartBodyLine());
		XmlElement(xt, prefix+"DefinitionFileLineStart", attrs);
		attrs["value"] = lineNum.setNum(d->getEndBodyLine());
		XmlElement(xt, prefix+"DefinitionFileLineEnd", attrs);
	}
#endif
}

void DITAGeneratorBase::stripQualifiers(QCString &typeStr)
{
	bool done = FALSE;
	while (!done) {
		if (typeStr.stripPrefix("static ")) {
		} else if (typeStr.stripPrefix("virtual ")) {
		} else if (typeStr.stripPrefix("volatile ")) {
		} else if (typeStr=="virtual") {
			typeStr="";
		} else {
			done = TRUE;
		}
	}
}

void DITAGeneratorBase::writeMemberTemplateLists(MemberDef *md, XmlStream &xt)
{
	LockingPtr<ArgumentList> templMd = md->templateArguments();
	if (templMd!=0) {
		// TODO Fix once DTDs supports templates.
		//writeTemplateArgumentList(md, templMd.pointer(), xt, md->getClassDef(), md->getFileDef());
	}
}

QCString DITAGeneratorBase::outputFileNameFromDefinition(Definition *d) const
{
	QCString outputDirectory = Config_getString("XML_DITA_OUTPUT");
	QCString fileName = outputDirectory + "/" + d->getOutputFileBase() + Config_getString("XML_DITA_EXTENSION");
	return fileName;
}

/** Write DITA for storage class specifiers 
i.e. extern | static | auto | register | mutable
*/
void DITAGeneratorBase::writeMemberScs(const MemberDef *md, XmlStream &xt) const
{
	// Storage class specifiers: extern | static | auto | register | mutable
	// Note C has typedef (but not mutable) See:
	// ISO/IEC 9899:1999 (E) 6.7.1 Storage-class specifiers
	// Note: auto and register not supported by Doxygen
	QString scsString = "StorageClassSpecifier";
	if (md->isExternal()) {
		XmlElement(xt, g_elemPrefix.elemPrefix(md, true) + scsString + "Extern");
	}
	if (md->isStatic()) {
		XmlElement(xt, g_elemPrefix.elemPrefix(md, true) + scsString + "Static");
	}
	if (md->isMutable()) {
		XmlElement(xt, g_elemPrefix.elemPrefix(md, true) + scsString + "Mutable");
	}
}

/** Writes out function specific properties such
as inline, is Constructor etc.
*/
void DITAGeneratorBase::writeFunctionProperties(const MemberDef *md, XmlStream &xt) const
{
	LockingPtr<ArgumentList> al = md->argumentList();
	if(al != 0) {
		if(al->constSpecifier) {
			XmlElement(xt, g_elemPrefix.elemPrefix(md, true)+"Const");
		}
		if (md->isExplicit()) {
			XmlElement(xt, g_elemPrefix.elemPrefix(md, true)+"Explicit");
		}
		if (md->isInline()) {
			XmlElement(xt, g_elemPrefix.elemPrefix(md, true)+"Inline");
		}
		if (md->isFinal()) {
			XmlElement(xt, g_elemPrefix.elemPrefix(md, true)+"Final");
		}
		if (md->isSealed()) {
			XmlElement(xt, g_elemPrefix.elemPrefix(md, true)+"Sealed");
		}
		if (md->isNew()) {
			XmlElement(xt, g_elemPrefix.elemPrefix(md, true)+"New");
		}
		// Virtual
		writeVirtualElement(xt, g_elemPrefix.elemPrefix(md, true), md->virtualness());
		// Identifying Constructors and destructors
		if (md->isConstructor()) {
			XmlElement(xt, g_elemPrefix.elemPrefix(md, true) + "Constructor");
		}
		if (md->isDestructor()) {
			XmlElement(xt, g_elemPrefix.elemPrefix(md, true) + "Destructor");
		}
	}
}

/** Writes out parameters for functions and function-like macros. */
void DITAGeneratorBase::writeMacroAndFunctionParameters(MemberDef *md, Definition *def, XmlStream &xt) const
{
	QString pName = "Parameter";
	QString dName = "DeclarationName";
	XmlElement paramElement(xt, g_elemPrefix.elemPrefix(md, true)+pName+"s");
	// Grab function parameter descriptions
	ParamDescriptionMap paramMap;
	writeXMLDocBlock(xt, md->docFile(), md->docLine(), def, md, md->documentation(), &paramMap);
	if (md->memberType() == MemberDef::Define && md->argsString()) {
		// Function-like macros
		if (md->argumentList()->count() == 0) {
			// special case for "foo()" to disguish it from "foo".
			XmlElement(xt, g_elemPrefix.elemPrefix(md, true)+pName);
		} else {
			ArgumentListIterator ali(*md->argumentList());
			Argument *a;
			for (ali.toFirst();(a = ali.current());++ali) {
				XmlElement paramElement(xt, g_elemPrefix.elemPrefix(md, true)+pName);
				writeXMLElementAndText(xt, g_elemPrefix.elemPrefix(md, true)+pName+dName, a->type);
				// Write out the apiDefNote from the paramMap
				// declaration name is: a->name
				// definition name is: defArg->name
				QString paramDescription;
				if (paramMap.contains(a->type)) {
					paramDescription = paramMap[a->type];
				} else {
					// NOP as paramDescription is empty
				}
				writeXMLElementAndText(xt, "apiDefNote", paramDescription);
			}
		}
	} else {
		// Functions
		LockingPtr<ArgumentList> declAl = md->declArgumentList();
		LockingPtr<ArgumentList> defAl = md->argumentList();
		if (declAl != 0 && declAl->count()>0) {
			ArgumentListIterator declAli(*declAl);
			ArgumentListIterator defAli(*defAl);
			Argument *a;
			for (declAli.toFirst();(a = declAli.current());++declAli) {
				Argument *defArg = defAli.current();
				XmlElement paramElement(xt, g_elemPrefix.elemPrefix(md, true)+pName);
#if DITA_EMIT_FOR_UNSUPPORTED_LANGS
				// 'attributes' - IDL only
				if (!a->attrib.isEmpty()) {
					writeXMLElementAndText(xt, "attributes", a->attrib);
				}
#endif
				if (!a->type.isEmpty()) {
					XmlElement typeElem(xt, g_elemPrefix.elemPrefix(md, true)+pName+"DeclaredType");
					linkifyTextDITA(TextGeneratorXMLDITALinker(xt), def, md->getBodyDef(), a->type);
				}
				// TODO: Type decomposition to fundemental type, classes arrays etc?
				// Declaration name
				if (!a->name.isEmpty()) {
					writeXMLElementAndText(xt, g_elemPrefix.elemPrefix(md, true)+pName+dName, a->name);
				}
				if (defArg && !defArg->name.isEmpty() && defArg->name!=a->name) {
					writeXMLElementAndText(xt, g_elemPrefix.elemPrefix(md, true)+pName+"DefinitionName", defArg->name);
				}
				// 'array specifier' - Fortran only?
				// No, C: void fvla(int m, int C[m][m]);
				// Has a->array() == "[m][m]"
				if (!a->array.isEmpty()) {
					// TODO fix once DTDs support cxxFunctionParameterArray
					//writeXMLElementAndText(xt, g_elemPrefix.elemPrefix(md, true)+pName+"Array", a->array);
				}
				if (!a->defval.isEmpty()) {
					XmlElement defvalElem(xt, g_elemPrefix.elemPrefix(md, true)+pName+"DefaultValue");
					linkifyTextDITA(TextGeneratorXMLDITALinker(xt), def, md->getBodyDef(), a->defval);
				}
				if (defArg && defArg->hasDocumentation()) {
					generateXMLForBriefDescription(md->getOuterScope(), md, xt);
				}
				if (defArg) {
					++defAli;
				}
				// Write out the apiDefNote from the paramMap
				// declaration name is: a->name
				// definition name is: defArg->name
				QString paramDescription;
				if (paramMap.contains(a->name)) {
					paramDescription = paramMap[a->name];
				} else if (defArg && paramMap.contains(defArg->name)) {
					paramDescription = paramMap[defArg->name];
				} else {
					// NOP as paramDescription is empty
				}
				writeXMLElementAndText(xt, "apiDefNote", paramDescription);
			}
		}
	}
}

/** Write DITA for member variables that are bit-fields */
void DITAGeneratorBase::writeMemberBitField(const MemberDef *md, XmlStream &xt) const
{
	ASSERT(md->memberType() == MemberDef::Variable && md->bitfieldString());
	QCString bitfield = md->bitfieldString();
	if (bitfield.at(0)==':') {
		bitfield = bitfield.mid(1);
	}
	// Write out element if it is a pad bit, this is when the declarator is absent
	QString typeStr(md->typeString());
	if (typeStr.simplifyWhiteSpace().length() == 0) {
		// Padded bit-field
		XmlElement(xt, g_elemPrefix.elemPrefix(md, true)+"BitFieldPad", "value", bitfield.simplifyWhiteSpace());
	} else {
		// Normal bit-field
		XmlElement(xt, g_elemPrefix.elemPrefix(md, true)+"BitField", "value", bitfield.simplifyWhiteSpace());
	}
}

/** Write DITA for member that has enumerator values */
void DITAGeneratorBase::writeMemberEnumerator(const MemberDef *md, XmlStream &xt)
{
	ASSERT(md->memberType() == MemberDef::Enumeration);
	LockingPtr<MemberList> enumFields = md->enumFieldList();
	if (enumFields != 0) {
		MemberListIterator emli(*enumFields);
		MemberDef *emd;
		// Locals to eliminate duplicate IDs
		bool eliminateDupeIds = Config_getBool("XML_DITA_OMIT_DUPLICATE_MEMBERS");
		// Element is cxxEnumerators not cxxEnumerations
		XmlElement enumeratorListElem(xt, g_elemPrefix.elemPrefix(md, false)+"Enumerators");
		for (emli.toFirst(); (emd = emli.current()); ++emli) {
			if (!eliminateDupeIds || m_memberIdMap.find(id(emd)) == m_memberIdMap.end()) {
				XmlElement enemElem(
					xt,
					g_elemPrefix.elemPrefix(emd, true),
					"id",
					id(emd));
				// Access qualifier
				//writeXMLElementAndText(xt, g_elemPrefix.elemPrefix(emd, true)+"Name", emd->name());
				writeXMLElementAndText(xt, "apiName", emd->name());
				generateXMLForBriefDescription(emd->getOuterScope(), emd, xt);
				// <cxxEnumeratorDetail>
				//XmlElement enumeratorDetail(xt, g_elemPrefix.elemPrefix(emd, true)+"Detail");
				{
					// <cxxEnumeratorDefinition>
					//XmlElement enumeratorDetail(xt, g_elemPrefix.elemPrefix(emd, true)+"Definition");
					//writeAccessSpecifierElement(xt, emd, emd->protection());
					// Name, prototype and name lookup
					QCString scopeName;
					if (md->getClassDef()) { 
						scopeName=md->getClassDef()->name();
					} else if (md->getNamespaceDef()) {
						scopeName=md->getNamespaceDef()->name();
					}
					// Scope of this member
					writeXMLElementAndText(xt, g_elemPrefix.elemPrefix(emd, true)+"ScopedName", scopeName);
					// 'Visual' prototype
					writeXMLElementAndText(xt, g_elemPrefix.elemPrefix(emd, true)+"Prototype", visualPrototype(emd));
					// A string that represents the lookup
					writeXMLElementAndText(xt, g_elemPrefix.elemPrefix(emd, true)+"NameLookup", nameLookup(emd));

					if (!emd->initializer().isEmpty()) {
						XmlElement(xt, g_elemPrefix.elemPrefix(emd, true)+"Initialiser", "value", emd->initializer().simplifyWhiteSpace());
						//writeXMLElementAndText(xt, g_elemPrefix.elemPrefix(md, true)+"Initializer", emd->initializer().simplifyWhiteSpace());
					}
					writeFileLocation(emd, xt, g_elemPrefix.elemPrefix(emd, true), false);
				} // </cxxEnumeratorDefinition>
				generateXMLForDetailedDescription(emd->getOuterScope(), emd, xt);
				// </cxxEnumeratorDetail>
			}
			if (eliminateDupeIds) {
				m_memberIdMap.insert(id(emd), true);
			}
		}
	}
}

void DITAGeneratorBase::generateXMLForMember(MemberDef *md, XmlStream &xt, Definition *def)
{
	// enum values are written as part of the enum
	if (md->memberType() == MemberDef::EnumValue) {
		return;
	}
	if (md->isHidden()) {
		return;
	}
	// TODO: Add Friend to DTD
	if(md->memberType() == MemberDef::Friend) {
		return;
	}
	// Locals to eliminate duplicate IDs
	bool eliminateDupeIds = Config_getBool("XML_DITA_OMIT_DUPLICATE_MEMBERS");
	if (eliminateDupeIds && m_memberIdMap.find(id(md)) != m_memberIdMap.end()) {
		return;
	}
	bool isFunc=FALSE;
	switch (md->memberType()) {
		case MemberDef::EnumValue:
			ASSERT(0);
			break;
		// Note fall through
		case MemberDef::Function:
		case MemberDef::Signal:
		case MemberDef::Friend:
		case MemberDef::DCOP:
		case MemberDef::Slot:
			isFunc = TRUE;
			break;
		default:
			isFunc=FALSE;
	}
	// Index is written by the caller as they know if we are a global or not
	XmlElement memberdefElem(xt, g_elemPrefix.elemPrefix(md, true), "id", id(md));
	writeXMLElementAndText(xt, "apiName", md->name());
	// <shortdesc>
	generateXMLForBriefDescription(md, 0, xt);
	{
		// <cxx...Detail>
		// Write out the class details
		XmlElement elemClassDetail(xt, g_elemPrefix.elemPrefix(md, true)+"Detail");
		{
			// <cxx...Definition>
			// Class defintion
			XmlElement elemDef(xt, g_elemPrefix.elemPrefix(md, true)+"Definition");
			writeAccessSpecifierElement(xt, md, md->protection());
			// Storage class specifiers: extern | static | auto | register | mutable
			writeMemberScs(md, xt);
			if (isFunc) {
				// Write out function specific properties such as inline, is Constructor etc.
				writeFunctionProperties(md, xt);
			}
			// Type information
			if (md->memberType() != MemberDef::Define && md->memberType() != MemberDef::Enumeration) {
				if (md->memberType() != MemberDef::Typedef) {
					writeMemberTemplateLists(md, xt);
				}
				QCString typeStr = md->typeString();
				stripQualifiers(typeStr);
				{
					XmlElement typeElem(xt, g_elemPrefix.elemPrefix(md, true)+"DeclaredType");
					linkifyTextDITA(TextGeneratorXMLDITALinker(xt), def, md->getBodyDef(), typeStr);
				}
				// TODO: Type decomposition to fundemental type, classes arrays etc?
			}
			
			// TODO when defined in DTD
			// BitFields, if appropriate
			//if (md->memberType() == MemberDef::Variable && md->bitfieldString()) {
			//	writeMemberBitField(md, xt);
			//}

			// Name, prototype and name lookup
			QCString scopeName;
			if (md->getClassDef()) { 
				scopeName=md->getClassDef()->name();
			} else if (md->getNamespaceDef()) {
				scopeName=md->getNamespaceDef()->name();
			}
			// Scope of this member, except for #defines
			if (md->memberType() != MemberDef::Define) {
				writeXMLElementAndText(xt, g_elemPrefix.elemPrefix(md, true)+"ScopedName", scopeName);
			}
			// 'Visual' prototype
			writeXMLElementAndText(xt, g_elemPrefix.elemPrefix(md, true)+"Prototype", visualPrototype(md));
			// Lookup string
			writeXMLElementAndText(xt, g_elemPrefix.elemPrefix(md, true)+"NameLookup", nameLookup(md));
#if DITA_EMIT_FOR_UNSUPPORTED_LANGS
			if (md->memberType() == MemberDef::Property) {
				if (md->isReadable()) {
					writeXMLElementAndText(xt, "read", md->getReadAccessor());
				}
				if (md->isWritable()) {
					writeXMLElementAndText(xt, "write", md->getWriteAccessor());
				}
			}
#endif
			// Re-implements
			{
				MemberDef *rmd = md->reimplements();
				// NOTE: Do not re-implement different types
				if (rmd && rmd->memberType() == md->memberType()) {
					//XmlElement reimplementsElem(xt, g_elemPrefix.elemPrefix(md, true)+"Reimplements");
					writeReferenceTo(xt, rmd, "Reimplemented");
				}
			}
			// Function and macro parameters
			if (isFunc || (md->memberType() == MemberDef::Define)) {
				writeMacroAndFunctionParameters(md, def, xt);
			}
			// Enumerators
			if (md->memberType() == MemberDef::Enumeration) {
				writeMemberEnumerator(md, xt);
			}
			// File location information
			if (md->getDefLine() != -1) {
				if (isFunc || md->memberType() == MemberDef::Enumeration) {
					writeFileLocation(md, xt, g_elemPrefix.elemPrefix(md, true), true);
				} else {
					// Do not include definition file, start block, end block
					writeFileLocation(md, xt, g_elemPrefix.elemPrefix(md, true), false);
				}
			}
		} // End cxx...Def
		generateXMLForDetailedDescription(md->getOuterScope(), md, xt);
	} // End <cxx...Detail>
	// TODO: Related links?

	// TODO: Move this to its proper place
	// avoid that extremely large tables are written to the output. 
	// todo: it's better to adhere to MAX_INITIALIZER_LINES.
	//if (!md->initializer().isEmpty() && md->initializer().length() < 2000) {
	//	XmlElement initializerElem(xt, "initializer");
	//	linkifyTextDITA(TextGeneratorXMLDITALinker(xt), def, md->getBodyDef(), md->initializer());
	//}
	if (md->excpString()) {
		XmlElement exceptionsElem(xt, "exceptions");
		linkifyTextDITA(TextGeneratorXMLDITALinker(xt), def, md->getBodyDef(), md->excpString());
	}
	// Record that we have written this ID
	if (eliminateDupeIds) {
		m_memberIdMap.insert(id(md), true);
	}
}

/** Returns the formal, fully qualified declaration of the member.
This follows: ISO/IEC 14882:1998(E) Section 3.4 Name Lookup
For example given:
class Class {
inline const char* StrFunction(const char* buffer=NULL, int index=0) volatile const;
};

This would return:
"Class::StrFunction(const char*, int) const volatile"

Note: Reordering of const/volatile
*/
QString DITAGeneratorBase::nameLookup(const MemberDef *md) const
{
	QCString formalDecl;
	if (md->getClassDef()) { 
		formalDecl = md->getClassDef()->name();
	} else if (md->getNamespaceDef()) {
		formalDecl = md->getNamespaceDef()->name();
	}
	QCString retVal;
	if (md->memberType() == MemberDef::Enumeration) {
		// Enums are different, we use the ':' prefix
		if (formalDecl.length() > 0){
			retVal = formalDecl + ":" + md->name();
		} else {
			retVal = ":";
			retVal.append(md->name());
		}
	} else {
		if (formalDecl.length() > 0){
			retVal = formalDecl + "::" + md->name();
		} else {
			retVal = md->name();
		}
	}
	if (md->memberType() == MemberDef::Function) {
		// Functions
		retVal.append("(");
		LockingPtr<ArgumentList> declAl = md->declArgumentList();
		if (declAl != 0 && declAl->count() > 0) {
			ArgumentListIterator declAli(*declAl);
			Argument *a;
			int argNum = 0;
			for (declAli.toFirst();(a = declAli.current()); ++declAli) {
				if (!a->type.isEmpty()) {
					if (argNum > 0) {
						retVal.append(",");
					}
					retVal.append(a->type);
				}
				argNum++;
			}
		}
		retVal.append(")");
		if (declAl != 0) {
			// Add cv qualifiers in order
			if (declAl->constSpecifier) {
				retVal.append("const");
			}
			if (declAl->volatileSpecifier) {
				if (declAl->constSpecifier) {
					retVal.append(" ");
				}
				retVal.append("volatile");
			}
		}
	}
	return retVal;
}

/** Returns the 'visual' prototype of the member. 
For example given:
class Class {
inline const char* StrFunction(const char* buffer=NULL, int index=0) volatile const;
};

This would return:
"inline const char* StrFunction(const char* buffer=NULL, int index=0) volatile const;"

Note: Reordering of const/volatile
*/
QString DITAGeneratorBase::visualPrototype(const MemberDef *md) const
{
	QString retStr;
	if (md->memberType() == MemberDef::Function) {
		if (md->isInline()) {
			retStr.append("inline ");
		}
	}
	if (md->memberType() == MemberDef::EnumValue) {
		// Enumerators are a special case
		retStr = md->name();
		if (!md->initializer().isEmpty()) {
			retStr += " = ";
			retStr += md->initializer().simplifyWhiteSpace();
		}
	} else {
		retStr.append(md->declaration());
	}
	return retStr;
}

/** Returns the id as a string. If USE_DOXYGEN_ID_AS_XML_ID is non-zero
then this follows the near-identical convention
of Doxygen XML id attibutes.
Otherwise it may do something different.
*/
QString DITAGeneratorBase::id(const Definition *d) const
{
#if USE_DOXYGEN_ID_AS_XML_ID
	QString retId = d->getOutputFileBase();
	return retId;
#else
	return d->qualifiedName();
#endif
}

QString DITAGeneratorBase::id(const MemberDef *md) const
{
#if USE_DOXYGEN_ID_AS_XML_ID
	QString retId = md->getOutputFileBase();
	retId.append("_1" + md->anchor());
	return retId;
#else
	return nameLookup(md);
#endif
}

QString DITAGeneratorBase::id(const PageDef *pd) const
{
#if USE_DOXYGEN_ID_AS_XML_ID
	QString retId = pd->getOutputFileBase();
	retId.append("_1" + pd->name());
	if (retId == "index") {
		retId = "indexpage";
	}
	return retId;
#else
	return pd->qualifiedName();
#endif
}

AttributeMap DITAGeneratorBase::getMapAttributes(const Definition *d) const
//(const QString &id) const
{
	// TODO: DITA does not allow a href to refer to an ID within a topic
	// so the #... shoudl be removed. It is only here temporarily
	// so that the map creator can pick up the fully qualified name from
	// the part after the '#'
	AttributeMap mapAttrs;
	//mapAttrs.insert("href", id + Config_getString("XML_DITA_EXTENSION") + #" + id);
	QString myHref = d->getOutputFileBase() + Config_getString("XML_DITA_EXTENSION") + "#";
	myHref += id(d);
	mapAttrs.insert("href", myHref);
	mapAttrs.insert("navtitle", d->qualifiedName());
	return mapAttrs;
}

/*AttributeMap DITAGeneratorBase::getMapAttributes(const Definition *d) const
{
	return getMapAttributes(id(d));
}

AttributeMap DITAGeneratorBase::getMapAttributes(const MemberDef *d) const
{
	return getMapAttributes(id(d));	
}

AttributeMap DITAGeneratorBase::getMapAttributes(const PageDef *d) const
{
	return getMapAttributes(id(d));
}*/

/************************************************
 * End: DITAGeneratorBase - Common functionality.
 ************************************************/

/*****************************
 * Section: class/struct/union
 *****************************/
void DITAClassGenerator::generateXMLForClasses()
{
	// Write classes
	ClassSDict::Iterator cli(*Doxygen::classSDict);
	ClassDef *cd;
	// TODO: Define order of this iterator
	for (cli.toFirst(); (cd = cli.current()); ++cli) {
		//msg("Generating XML DITA output for class %s\n",cd->name().data());
		//printf("Class in language \"%s\" has element prefix \"%s\"\n", g_elemPrefix.srcLang(cd).data(), g_elemPrefix.elemPrefix(cd).data());
		// We only want to make this call for a class that is not a nested class
		// because this call will create the appropriate DITA map for nested classes
		if (cd->getOuterScope()->definitionType() == Definition::TypeNamespace) {
			writeDITAMapEntryForClass(cd);
		}
		generateXMLForClass(cd);
	}
}

/** Recursively generate DITA map entries. */
void DITAClassGenerator::writeDITAMapEntryForClass(ClassDef *cd)
{
	if (skipThisClass(cd)) {
		return;
	}
	if (!isCompletelyDefined(cd)) {
		return;
	}
	/*
	Definition *d = cd->getOuterScope();
	Definition::DefType dt = d->definitionType();
	QCString n = d->name();
	bool b = (d->definitionType() == Definition::TypeNamespace);
	*/
	// Make an index entry for me
	XmlElement idxElem(ix, g_elemPrefix.ditaMapRef(cd), getMapAttributes(cd));
	// TODO: Define order of this iterator
	ClassSDict *cl = cd->getInnerClasses();
	if (cl) {
		ClassSDict::Iterator cli(*cl);
		ClassDef *ncd;
		for (cli.toFirst(); (ncd = cli.current()); ++cli) {
			// skip anonymous scopes
			if (!ncd->isHidden() && ncd->name().find('@') == -1) {
				// Recursive call
				writeDITAMapEntryForClass(ncd);
			}
		}
	}
}

bool DITAClassGenerator::skipThisClass(ClassDef *cd) const
{
	if (cd->isReference()) {
		return true; // skip external references.
	}
	if (cd->isHidden()) {
		return true; // skip hidden classes.
	}
	if (cd->name().find('@') != -1) {
		return true; // skip anonymous compounds.
	}
	if (cd->templateMaster() != 0) {
		return true; // skip generated template instances.
	}
	// Check type of class, only class/struct/union supported
	bool retVal = true;
	switch (cd->compoundType()) {
		// Note fall through
		case ClassDef::Class:
		case ClassDef::Struct:
		case ClassDef::Union:
			retVal = false;
			break;
		default:
			retVal = true;
			break;
	}
	return retVal;
}

/** Returns true if all members functions are defined */
bool DITAClassGenerator::isCompletelyDefined(ClassDef *cd) const
{
	if (Config_getBool("XML_DITA_OMIT_UNLINKABLE")) {
		if (cd->memberNameInfoSDict()) {
			MemberNameInfoSDict::Iterator mnii(*cd->memberNameInfoSDict());
			MemberNameInfo *mni;
			for (mnii.toFirst(); (mni=mnii.current()); ++mnii) {
				MemberNameInfoIterator mii(*mni);
				MemberInfo *mi;
				for (mii.toFirst(); (mi=mii.current()); ++mii) {
					MemberDef *md = mi->memberDef;
					if (md->memberType() == MemberDef::Function) {
						if (md->getBodyDef() == 0
							|| md->getStartBodyLine() == -1
							|| md->getEndBodyLine() == -1) {
								return false;
						}
					}
				}
			}
		}
	}
	return true;
}


void DITAClassGenerator::generateXMLForClass(ClassDef *cd)
{
	// Clear the duplicate ID map regardless of what we write
	m_memberIdMap.clear();
	if (skipThisClass(cd)) {
		return;
	}
	msg("Generating XML DITA output for class %s i.e. %s\n", cd->name().data(), cd->className().data());
	//msg("Generating XML DITA output for class %s type=%d\n", cd->name().data(), cd->compoundType());
	if (!isCompletelyDefined(cd)) {
		msg("Rejecting XML DITA output for class not completely defined: %s\n", cd->name().data());
		return;
	}
	// Initialise DITA file stream for this class
	XmlStream xt(outputFileNameFromDefinition(cd), "UTF-8", "no", g_elemPrefix.doctypeStr(cd));
	if (!xt.isOpen()) {
		err("Cannot open file %s for writing!\n", outputFileNameFromDefinition(cd).data());
		return;
	}
	// Open root node
#if USE_DOXYGEN_ID_AS_XML_ID
	XmlElement elemRoot(xt, g_elemPrefix.elemPrefix(cd, true), "id", cd->getOutputFileBase());
#else
	XmlElement elemRoot(xt, g_elemPrefix.elemPrefix(cd, true), "id", id(cd));
#endif
	// Now: <!ELEMENT cxxClass   ((%apiName;), (%shortdesc;), (%prolog;)?, (%cxxClassDetail;), (%related-links;)?, (%cxxClass-info-types;)*)>
	// <apiName>
	{
		XmlElement elemRoot(xt, "apiName");
		xt.characters(cd->name());
	}
	// <shortdesc>
	generateXMLForBriefDescription(cd, 0, xt);
	{
		// <cxxClassDetail>
		// Write out the class details
		XmlElement elemClassDetail(xt, g_elemPrefix.elemPrefix(cd, true)+"Detail");
		{
			// <cxxClassDefinition>
			// Class defintion
			XmlElement elemDef(xt, g_elemPrefix.elemPrefix(cd, true)+"Definition");
			writeAccessSpecifierElement(xt, cd, cd->protection());
			if (cd->isAbstract()) {
				XmlElement(xt, g_elemPrefix.elemPrefix(cd, true)+"Abstract");
			}
			// Inheritance
			if (cd->baseClasses()) {
				XmlElement elemDef(xt, g_elemPrefix.elemPrefix(cd, true)+"Derivations");
				BaseClassListIterator bcli(*cd->baseClasses());
				generateXMLForBaseDerivedClasses(xt, bcli);
			}
			// Class template information
			// TODO: Fix template parameter lists
			//writeTemplateList(cd, xt);
			// File location
			writeFileLocation(cd, xt, g_elemPrefix.elemPrefix(cd, true), true);
		}
		generateXMLForDetailedDescription(cd, 0, xt);
	}
	// Write out links to nested classes
	writeInnerClasses(cd, cd->getInnerClasses(), xt);
	// Get list of members in declaration order - direct members only
	SrcDeclMemberMap memberMap = membersInDeclOrder(cd, false);
	SrcDeclMemberMap::Iterator iter;
	for (iter = memberMap.begin(); iter != memberMap.end(); ++iter) {
		//printf("membersInDeclOrder()line: %d member: \"%s\"\n", iter.key(), iter.data()->qualifiedName().data());
		generateXMLForMember(iter.data(), xt, cd);
	}
	{
		// List of references to inherited members
		// Get list of all members in formal declaration order
		MemberNameLookupMap memberMap = membersInFormalDeclOrder(cd, true);
		// First look ahead to see if there are relevant members
		bool hasRelevantMembers = false;
		{
			MemberNameLookupMap::Iterator iter;
			for (iter = memberMap.begin(); iter != memberMap.end(); ++iter) {
				MemberDef *tempMd = iter.data();
				if (tempMd->getClassDef() != cd) {
					hasRelevantMembers = true;
					break;
				}
			}
		}
		// Optional element
		if (memberMap.count() > 0 && hasRelevantMembers) {
			XmlElement elemInherits(xt, g_elemPrefix.elemPrefix(cd, true)+"Inherits");
			XmlElement elemInheritsDetail(xt, g_elemPrefix.elemPrefix(cd, true)+"InheritsDetail");
			MemberNameLookupMap::Iterator iter;
			for (iter = memberMap.begin(); iter != memberMap.end(); ++iter) {
				MemberDef *tempMd = iter.data();
				if (tempMd->getClassDef() && tempMd->getClassDef() != cd) {
					//printf("Inherited members, accepting formal name: \"%s\"\n", iter.key().data());
					// TODO: Fix once cxxClassTypedefInherited and cxxClassFriendInherited are supported by the dtds
					if ((iter.data()->memberType() != MemberDef::Typedef) && (g_elemPrefix.memberKind(iter.data()) != "Friend")) {
						writeReferenceTo(xt, tempMd->getClassDef(), iter.data(), "Inherited");
					}
				} else {
					//printf("Inherited members, rejecting formal name: \"%s\"\n", iter.key().data());
				}
			}
		}
	}
}

void DITAClassGenerator::generateXMLForBaseDerivedClasses(XmlStream& t, BaseClassListIterator& bcli)
{
	BaseClassDef *bcd;
	QString myPrefix("Derivation");
	for (bcli.toFirst();(bcd=bcli.current());++bcli) {
		XmlElement derivatonClass(t, g_elemPrefix.elemPrefix(bcd->classDef, true)+myPrefix);
		//writeAccessSpecifierElement(t, bcd->classDef, bcd->prot);
		XmlElement(t,
					g_elemPrefix.elemPrefix(bcd->classDef, true)+myPrefix+"AccessSpecifier",
					"value",
					accessSpecifier(bcd->prot, false));
		writeVirtualElement(t, g_elemPrefix.elemPrefix(bcd->classDef, true)+myPrefix, bcd->virt);
		writeReferenceTo(t, bcd->classDef, "BaseClass");
	}
}

/** Returns a map of class/struct/union members in source code declaration line order. 
If incAllMembers is true then all members (including inherited members) is added
otherwise only direct members are included. The test is: md->getClassDef() == cd */
SrcDeclMemberMap DITAClassGenerator::membersInDeclOrder(ClassDef *cd,
														bool incAllMembers)
{
	SrcDeclMemberMap retMap;
	//printf("membersInDeclOrder() class is \"%s\"\n", cd->qualifiedName().data());
	if (cd->memberNameInfoSDict()) {
		MemberNameInfoSDict::Iterator mnii(*cd->memberNameInfoSDict());
		MemberNameInfo *mni;
		for (mnii.toFirst(); (mni=mnii.current()); ++mnii) {
			MemberNameInfoIterator mii(*mni);
			MemberInfo *mi;
			for (mii.toFirst(); (mi=mii.current()); ++mii) {
				MemberDef *md = mi->memberDef;
				//int lineNo = md->getDefLine();
				//printf("membersInDeclOrder() \"%s\" on line %d\n", md->qualifiedName().data(), lineNo);
				//printf("Member of: \"%s\"\n", md->getClassDef()->qualifiedName().data());
				if (incAllMembers || md->getClassDef() == cd) {
					// TODO: Check if the line number is already there
					// TODO: Check declaration file name missmatch
					retMap.insert(md->getDefLine(), md);
				}
			}
		}
	}
	//printf("\n");
	return retMap;
}

/** Returns a map of class/struct/union members in formal declaration  order.
If incAllMembers is true then all members (including inherited members) is added
otherwise only direct members are included. The test is: md->getClassDef() == cd
*/
MemberNameLookupMap DITAClassGenerator::membersInFormalDeclOrder(ClassDef *cd,
														bool incAllMembers)
{
	MemberNameLookupMap retMap;
	//printf("membersInDeclOrder() class is \"%s\"\n", cd->qualifiedName().data());
	if (cd->memberNameInfoSDict()) {
		MemberNameInfoSDict::Iterator mnii(*cd->memberNameInfoSDict());
		MemberNameInfo *mni;
		for (mnii.toFirst(); (mni=mnii.current()); ++mnii) {
			MemberNameInfoIterator mii(*mni);
			MemberInfo *mi;
			for (mii.toFirst(); (mi=mii.current()); ++mii) {
				MemberDef *md = mi->memberDef;
				//int lineNo = md->getDefLine();
				//printf("membersInDeclOrder() \"%s\" on line %d\n", md->qualifiedName().data(), lineNo);
				//printf("Member of: \"%s\"\n", md->getClassDef()->qualifiedName().data());
				if (incAllMembers || md->getClassDef() == cd) {
					// TODO: Check formal declaration is already there
					retMap.insert(nameLookup(md), md);
				}
			}
		}
	}
	//printf("\n");
	return retMap;
}

void DITAClassGenerator::writeTemplateList(ClassDef *cd, XmlStream &xt)
{
	// TODO: Fix once templates are working DTD
	//writeTemplateArgumentList(cd, cd->templateArguments(), xt, cd, 0);
}
/**************************
 * End: class/struct/union
 *************************/

/**********************
 * Section: Namespaces
 *********************/
void DITANamespaceGenerator::generateXMLForNamespaces()
{
	NamespaceSDict::Iterator nli(*Doxygen::namespaceSDict);
	NamespaceDef *nd;
	for (nli.toFirst();(nd = nli.current()); ++nli) {
		msg("Generating XML DITA output for namespace %s\n",nd->name().data());
		// TODO: Add back in namespaces once the DTD is done
		//generateXMLForNamespace(nd);
	}
}

void DITANamespaceGenerator::generateXMLForNamespace(NamespaceDef *nd)
{
	m_memberIdMap.clear();
	if (nd->isReference() || nd->isHidden()) {
		return; // skip external references
	}
	msg("Generating XML DITA output for namespace %s\n", nd->name().data());
	// Index entry
	XmlElement elemIndex(ix, g_elemPrefix.ditaMapRef(nd), getMapAttributes(nd));
	// Initialise DITA file stream for this namespace
	XmlStream xt(outputFileNameFromDefinition(nd), "UTF-8", "no", g_elemPrefix.doctypeStr(nd));
	if (!xt.isOpen()) {
		err("Cannot open file %s for writing!\n", outputFileNameFromDefinition(nd).data());
		return;
	}
	// Open root node
#if USE_DOXYGEN_ID_AS_XML_ID
	XmlElement elemRoot(xt, g_elemPrefix.elemPrefix(nd, true), "id", nd->getOutputFileBase());
#else
	XmlElement elemRoot(xt, g_elemPrefix.elemPrefix(nd, true), "id", id(nd));
#endif
	//writeInnerClasses(nd, nd->getClassSDict(), xt);
	writeInnerNamespaces(nd->getNamespaceSDict(), xt);
	generateXMLForBriefDescription(nd, 0, xt);
	generateXMLForDetailedDescription(nd, 0, xt);
	{
		// List of references to members
		// Get list of all members in formal declaration order
		MemberNameLookupMap memberMap = membersInFormalDeclOrder(nd, false);
		MemberNameLookupMap::Iterator iter;
		for (iter = memberMap.begin(); iter != memberMap.end(); ++iter) {
			//printf("formal name: \"%s\"\n", iter.key().data());
			// Index entry
			XmlElement(ix, g_elemPrefix.ditaMapRef(iter.data()), getMapAttributes(iter.data()));
			// Write referece to Namespace XML file
			writeReferenceTo(xt, iter.data(), "NamespaceMember");
		}
	}
}

void DITANamespaceGenerator::writeInnerNamespaces(const NamespaceSDict *nl,XmlStream &xt)
{
	if (nl) {
		NamespaceSDict::Iterator nli(*nl);
		NamespaceDef *nd;
		for (nli.toFirst();(nd=nli.current());++nli) {
			// skip anonymous scopes
			if (!nd->isHidden() && nd->name().find('@')==-1) {
				XmlElement e(xt, "innernamespace", "refid", nd->getOutputFileBase());
				xt << nd->name();
			}
		}
	}
}

MemberNameLookupMap DITANamespaceGenerator::membersInFormalDeclOrder(NamespaceDef *nd, bool incAllMembers)
{
	MemberNameLookupMap retMap;
	//printf("membersInFormalDeclOrder() namespace is \"%s\"\n", nd->name().data());
	QListIterator<MemberList> mli(nd->getMemberLists());
	MemberList *ml;
	for (mli.toFirst();(ml=mli.current());++mli) {
		if ((ml->listType()&MemberList::declarationLists) != 0) {
			MemberListIterator mli(*ml);
			MemberDef *md;
			for (mli.toFirst(); (md = mli.current()); ++mli) {
				if (incAllMembers || (md->getNamespaceDef() == nd)) {
					// TODO: Check if already there
					//printf("membersInFormalDeclOrder() adding member \"%s\": \"%s\"\n", md->name().data(), nameLookup(md).data());
					retMap.insert(nameLookup(md), md);
				} else {
					//printf("membersInFormalDeclOrder() rejecting member \"%s\": \"%s\"\n", md->name().data(), nameLookup(md).data());
				}
			}
		}
	}
	//printf("\n");
	return retMap;
}
/******************
 * End: Namespaces
 *****************/

/******************************
 * Section: Pages and examples
 *****************************/
void DITAPageGenerator::generateXMLForPages()
{
	PageSDict::Iterator pdi(*Doxygen::pageSDict);
	PageDef *pd=0;
	for (pdi.toFirst();(pd=pdi.current());++pdi) {
		msg("Generating XML DITA output for page %s\n",pd->name().data());
		generateXMLForPage(pd, FALSE);
	}
}

void DITAPageGenerator::generateXMLForExamples()
{
	PageSDict::Iterator pdi(*Doxygen::exampleSDict);
	PageDef *pd=0;
	for (pdi.toFirst();(pd=pdi.current());++pdi) {
		msg("Generating XML DITA output for example %s\n",pd->name().data());
		generateXMLForPage(pd, TRUE);
	}
}

void DITAPageGenerator::generateXMLForMainPage()
{
	generateXMLForPage(Doxygen::mainPage, FALSE);
}

void DITAPageGenerator::generateXMLForPage(PageDef *pd, bool isExample)
{
	m_memberIdMap.clear();
	if (pd->isReference()) {
		return;
	}
	//const char *kindName = isExample ? "example" : "page";
	// Index entry
	XmlElement(ix, "topicref", getMapAttributes(pd));
	// Note: Non-standard way of creating filename
	QCString pageName = pd->getOutputFileBase();//id(pd);
	QCString outputDirectory = Config_getString("XML_DITA_OUTPUT");
	XmlStream xt(outputDirectory+"/"+pageName+Config_getString("XML_DITA_EXTENSION"),
		"UTF-8",
		"no",
		"topic PUBLIC \"-//OASIS//DTD DITA Topic//EN\" \"../../dtd/topic.dtd\"");
	XmlElement elemTopic(xt, "topic", "id", pageName);
	SectionInfo *si = Doxygen::sectionDict.find(pd->name());
	if (si) {
		writeXMLElementAndText(xt, "title", si->title);
	}else{
		writeXMLElementAndText(xt, "title", pd->name());
	}
	XmlElement elemBody(xt, "body");
	if (isExample) {
		writeXMLDocBlock(xt, pd->docFile(), pd->docLine(), pd, 0, pd->documentation()+"\n\\include "+pd->name(), 0);
	} else {
		writeXMLDocBlock(xt, pd->docFile(), pd->docLine(), pd, 0, pd->documentation(), 0);
	}
}
/**************************
 * End: Pages and examples
 *************************/

/********************************************************
 * Section: Files - supported in that we extract globals
 *******************************************************/
void DITAFileGenerator::generateXMLForFiles()
{
	FileNameListIterator fnli(*Doxygen::inputNameList);
	FileName *fn;
	for (;(fn=fnli.current());++fnli) {
		FileNameIterator fni(*fn);
		FileDef *fd;
		for (;(fd=fni.current());++fni) {
			//printf("Generting DITA for File: %s\n", fd->absFilePath().data());
			generateXMLForFile(fd);
		}
	}
}

void DITAFileGenerator::writeXMLDITACodeBlock(XmlStream &t,FileDef *fd)
{
	// Note this is effetively a NOP as the XMLDITACodeGenerator has no effective functionaliity
	ParserInterface *pIntf=Doxygen::parserManager->getParser(fd->getDefFileExtension());
	pIntf->resetCodeParserState();
	XMLDITACodeGenerator *xmlGen = new XMLDITACodeGenerator(t);
	pIntf->parseCode(*xmlGen,
						0,
						fileToString(fd->absFilePath(),Config_getBool("FILTER_SOURCE_FILES")),
						FALSE,
						0,
						fd);
	xmlGen->finish();
	delete xmlGen;
}

void DITAFileGenerator::generateXMLForFile(FileDef *fd)
{
	m_memberIdMap.clear();
	if (fd->isReference()) {
		return; // skip external references
	}
	// Look ahead to see if there are any members if not don't write anything
	// and don't make an index entry
	if (!fileHasMembers(fd, false)) {
		msg("Generating XML DITA output for file %s - no members\n", fd->name().data());
		return;
	}
	// Index entry
	XmlElement idxElem(ix, g_elemPrefix.ditaMapRef(fd), getMapAttributes(fd));
	// Create output stream
	QCString outputDirectory = Config_getString("XML_DITA_OUTPUT");
	// Initialise DITA file stream for this file
	XmlStream xt(outputFileNameFromDefinition(fd), "UTF-8", "no", g_elemPrefix.doctypeStr(fd));
	msg("Generating XML DITA output for file %s -> %s\n", fd->name().data(), outputFileNameFromDefinition(fd).data());
	if (!xt.isOpen()) {
		err("Cannot open file %s for writing!\n", outputFileNameFromDefinition(fd).data());
		return;
	}
	// Open root node
#if USE_DOXYGEN_ID_AS_XML_ID
	XmlElement elemRoot(xt, g_elemPrefix.elemPrefix(fd, true), "id", fd->getOutputFileBase());
#else
	XmlElement elemRoot(xt, g_elemPrefix.elemPrefix(fd, true), "id", id(fd));
#endif
	//writeXMLElementAndText(xt, g_elemPrefix.elemPrefix(fd, true)+"Name", AttributeMap(), fd->name());
	writeXMLElementAndText(xt, "apiName", fd->name());

	// This section is the include graph. We do not support that in DITA yet.
	// Perhaps this needs a specialisation for source files?
#if 0
	IncludeInfo *inc;
	if (fd->includeFileList()) {
		QListIterator<IncludeInfo> ili1(*fd->includeFileList());
		for (ili1.toFirst();(inc=ili1.current());++ili1) {
			AttributeMap incAttrs;
			if (inc->fileDef && !inc->fileDef->isReference()) {// TODO: support external references
				incAttrs["refid"] = id(inc->fileDef);
			}
			incAttrs["local"] = inc->local ? "yes" : "no";
			writeXMLElementAndText(xt, "includes", incAttrs, inc->includeName);
		}
	}
	if (fd->includedByFileList()) {
		QListIterator<IncludeInfo> ili2(*fd->includedByFileList());
		for (ili2.toFirst();(inc=ili2.current());++ili2) {
			AttributeMap incAttrs;
			if (inc->fileDef && !inc->fileDef->isReference()) {// TODO: support external references
				incAttrs["refid"] = id(inc->fileDef);
			}
			incAttrs["local"] = inc->local ? "yes" : "no";
			writeXMLElementAndText(xt, "includedby", incAttrs, inc->includeName);
		}
	}

	DotInclDepGraph incDepGraph(fd,FALSE);
	if (!incDepGraph.isTrivial()) {
		XmlElement e(xt, "incdepgraph");
		incDepGraph.writeXML(xt);
	}

	DotInclDepGraph invIncDepGraph(fd,TRUE);
	if (!invIncDepGraph.isTrivial()) {
		XmlElement e(xt, "invincdepgraph");
		invIncDepGraph.writeXML(xt);
	}
#endif // File include graph stuff
	// File members i.e. globals
	// Get list of all members (in declaration order,
	// not that his matters as we write them each in their own topic)
	SrcDeclMemberMap memberMap = membersInDeclOrder(fd, false);
	SrcDeclMemberMap::Iterator iter;
#if DITA_FILE_MEMBERS_IN_OWN_TOPICS
	// This section needs to write out globals each in their own topics
	// (class/struct/union are written elswhere)
	{
		for (iter = memberMap.begin(); iter != memberMap.end(); ++iter) {
			// Index entry
			XmlElement(ix, g_elemPrefix.ditaMapRef(iter.data()), "href", id(iter.data()));
			//printf("line: %d member: \"%s\"\n", iter.key(), iter.data()->qualifiedName().data());
			//generateXMLForMember(iter.data(), ix, xt, fd);
			QCString memberFileName = outputDirectory + "/";
			memberFileName.append(id(iter.data()));
			memberFileName.append(Config_getString("XML_DITA_EXTENSION"));
			XmlStream xm(memberFileName, "UTF-8", "no", g_elemPrefix.doctypeStr(iter.data()));
			generateXMLForMember(iter.data(), xm, fd);
		}
	}
#endif
	// This is file description stuff, make it a cxxHeader???
	//generateXMLForBriefDescription(fd, 0, xt);
	/*
	// <cxxFileDetail>
	{
		XmlElement elemClassDetail(xt, g_elemPrefix.elemPrefix(fd, true)+"Detail");
		generateXMLForDetailedDescription(fd, 0, xt);
	}
	*/
#if DITA_FILE_MEMBERS_IN_OWN_TOPICS
	{
		XmlElement elemRoot(xt, g_elemPrefix.elemPrefix(fd, true)+"Members");
		// List of references to members
		// Get list of all members in formal declaration order
		MemberNameLookupMap memberMap = membersInFormalDeclOrder(fd, false);
		MemberNameLookupMap::Iterator iter;
		for (iter = memberMap.begin(); iter != memberMap.end(); ++iter) {
			//printf("formal name: \"%s\"\n", iter.key().data());
			writeReferenceTo(xt, iter.data(), "FileMember");
		}
	}
#else
	{
		for (iter = memberMap.begin(); iter != memberMap.end(); ++iter) {
			generateXMLForMember(iter.data(), xt, fd);
		}
	}
#endif
	// Program listing not supported in DITA yet
	//printf("File getDefLine(): %d\n", fd->getDefLine());
	writeFileLocation(fd, xt, g_elemPrefix.elemPrefix(fd, true), true);
}

/** Returns true/false if this file has members */
bool DITAFileGenerator::fileHasMembers(FileDef *fd, bool incAllMembers)
{
	QListIterator<MemberList> mli(fd->getMemberLists());
	MemberList *ml;
	for (mli.toFirst();(ml = mli.current()); ++mli) {
		if ((ml->listType()&MemberList::declarationLists) != 0) {
			MemberListIterator mli(*ml);
			MemberDef *md;
			for (mli.toFirst(); (md = mli.current()); ++mli) {
				if (incAllMembers || (md->getDefFileName() == fd->getDefFileName())) {//md->getFileDef() == fd) {
					return true;
				}
			}
		}
	}
	//printf("\n");
	return false;
}

/** Returns a map of members in source code declaration line order. 
Unless incAllMembers is true this only returns members whose declaration file
is the supplied file - this test is done with a file name string match */
SrcDeclMemberMap DITAFileGenerator::membersInDeclOrder(FileDef *fd, bool incAllMembers)
{
	SrcDeclMemberMap retMap;
	//printf("membersInDeclOrder() file is \"%s\"\n", fd->absFilePath().data());
	QListIterator<MemberList> mli(fd->getMemberLists());
	MemberList *ml;
	for (mli.toFirst();(ml=mli.current());++mli) {
		if ((ml->listType()&MemberList::declarationLists) != 0) {
			MemberListIterator mli(*ml);
			MemberDef *md;
			for (mli.toFirst(); (md = mli.current()); ++mli) {
				if (incAllMembers || (md->getDefFileName() == fd->getDefFileName())) {//md->getFileDef() == fd) {
					// TODO: Check if the line number is already there
					//printf("membersInDeclOrder() adding member \"%s\" getFileDefName(): \"%s\"\n", md->name().data(), md->getDefFileName().data());
					retMap.insert(md->getDefLine(), md);
				} else {
					//printf("membersInDeclOrder() rejecting member \"%s\" getFileDefName(): \"%s\"\n", md->name().data(), md->getDefFileName().data());
				}
			}
		}
	}
	//printf("\n");
	return retMap;
}

/** Returns a map Returns a map of members in formal declaration  order.
Unless incAllMembers is true this only returns members whose declaration file
is the supplied file - this test is done with a file name string match
*/
MemberNameLookupMap DITAFileGenerator::membersInFormalDeclOrder(FileDef *fd,
													bool incAllMembers)
{
	MemberNameLookupMap retMap;
	//printf("membersInFormalDeclOrder() file is \"%s\"\n", fd->absFilePath().data());
	QListIterator<MemberList> mli(fd->getMemberLists());
	MemberList *ml;
	for (mli.toFirst();(ml=mli.current());++mli) {
		if ((ml->listType()&MemberList::declarationLists) != 0) {
			MemberListIterator mli(*ml);
			MemberDef *md;
			for (mli.toFirst(); (md = mli.current()); ++mli) {
				if (incAllMembers || (md->getDefFileName() == fd->getDefFileName())) {//md->getFileDef() == fd) {
					// TODO: Check if the line number is already there
					//printf("membersInFormalDeclOrder() adding member \"%s\" getFileDefName(): \"%s\"\n", md->name().data(), md->getDefFileName().data());
					retMap.insert(nameLookup(md), md);
				} else {
					//printf("membersInFormalDeclOrder() rejecting member \"%s\" getFileDefName(): \"%s\"\n", md->name().data(), md->getDefFileName().data());
				}
			}
		}
	}
	//printf("\n");
	return retMap;
}
/*************
 * End: Files
 ************/

/////////////////////////////////////////////////
// NOTE: There is no DITA support from here on
// apart from the main calling funcitons...
/////////////////////////////////////////////////

/**************************************************************
 * Section: Directories - not supported at the moment
 *************************************************************/
void DITADirGenerator::generateXMLForDirectories()
{
	DirDef *dir;
	DirSDict::Iterator sdi(*Doxygen::directories);
	for (sdi.toFirst();(dir=sdi.current());++sdi) {
		msg("Generate XML DITA output for dir %s\n", dir->name().data());
		generateXMLForDir(dir);
	}
}

void DITADirGenerator::writeInnerDirs(const DirList *dl, XmlStream & xt)
{
}

void DITADirGenerator::generateXMLForDir(DirDef *dd)
{
	m_memberIdMap.clear();
	if (dd->isReference()) {
		return; // skip external references
	}
	// Directory documenation not generated for DITA yet, if ever.
	return;
}
/*****************************
 * End: Files and directories
 ****************************/

/***********************************************
 * Section: Groups - not supported at the moment
 ***********************************************/
void DITAGroupGenerator::generateXMLForGroups()
{
	GroupSDict::Iterator gli(*Doxygen::groupSDict);
	GroupDef *gd;
	for (;(gd=gli.current());++gli) {
		msg("Generating XML DITA output for group %s\n",gd->name().data());
		generateXMLForGroup(gd);
	}
}

void DITAGroupGenerator::generateXMLForGroup(GroupDef *gd)
{
	m_memberIdMap.clear();
	if (gd->isReference()) {
		return; // skip external references
	}
	return;
}
/**************
 * End: Groups
 **************/

/**********************************
 * Section: main calling functions
 *********************************/
void generateXSD(const QString &outDir)
{
}

void writeCombineScript()
{
}

void generateXML(QCString outputDirectory)
{
	// + classes
	// + namespaces
	// + files
	// + groups
	// + related pages
	// - examples
	generateXSD(outputDirectory);
	QCString mapTitle = Config_getString("PROJECT_NAME");
	if (mapTitle == "") {
		mapTitle = "root";
	}
	msg("DITA output for project \"%s\" - started.\n", mapTitle.data());
	XmlStream ix(
		outputDirectory+"/"+mapTitle+Config_getString("XML_DITA_EXTENSION_DITAMAP"),
		"UTF-8",
		"no",
		g_elemPrefix.doctypeStr("C++", "cxxAPIMap", "Map")
		);
	// TODO: <!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "../dtd/map.dtd">
	if (!ix.isOpen()) {
		err("Cannot open index file %s for writing!\n", ix.getFileName());
		return;
	}
	// TODO: This cxxAPIMAp is hard coded
	AttributeMap mapAttrs;
	mapAttrs.insert("title", mapTitle);
	mapAttrs.insert("id", mapTitle);
	XmlElement elemRoot(ix, "cxxAPIMap", mapAttrs);

	DITAClassGenerator dcg(ix);
	dcg.generateXMLForClasses();

	DITANamespaceGenerator dng(ix);
	dng.generateXMLForNamespaces();

	DITAFileGenerator dfg(ix);
	dfg.generateXMLForFiles();

	DITAGroupGenerator dgg(ix);
	dgg.generateXMLForGroups();
	
	DITAPageGenerator pageGenerator(ix);	
	pageGenerator.generateXMLForPages();

	DITADirGenerator dirGenerator(ix);
	dirGenerator.generateXMLForDirectories();
	
	pageGenerator.generateXMLForExamples();

	if (Doxygen::mainPage) {
		msg("Generating XML DITA output for the main page\n");
		pageGenerator.generateXMLForMainPage();
	}
	writeCombineScript();
	// Dump traceability comment
	QString traceComment;
	traceComment.append("\n");
	traceComment.append("Doxygen version: ");
	traceComment.append(versionString);
	traceComment.append("\n");
	ix.comment(traceComment);
	msg("DITA output for project \"%s\" - finished.\n", mapTitle.data());
}

bool createOutputDirectory(QCString &outputDirectory) 
{
	if (outputDirectory.isEmpty()) {
		outputDirectory = QDir::currentDirPath();
	} else {
		QDir dir(outputDirectory);
		if (!dir.exists()) {
			dir.setPath(QDir::currentDirPath());
			if (!dir.mkdir(outputDirectory)) {
				err("Error: tag XML_DITA_OUTPUT: Output directory `%s' does not exist and cannot be created\n", outputDirectory.data());
				exit(1);
			} else if (!Config_getBool("QUIET")) {
				err("Notice: Output directory `%s' does not exist. I have created it for you.\n", outputDirectory.data());
			}
			dir.cd(outputDirectory);
		}
		outputDirectory = dir.absPath();
	}
	QDir dir(outputDirectory);
	if (!dir.exists()) {
		dir.setPath(QDir::currentDirPath());
		if (!dir.mkdir(outputDirectory)) {
			return FALSE;
		}
	}
	return TRUE;
}

void generateXMLDITA()
{
	QCString outputDirectory = Config_getString("XML_DITA_OUTPUT");
	if (!createOutputDirectory(outputDirectory)) {
		err("Cannot create directory %s\n", outputDirectory.data());
		return;
	}
	//DITAXMLGenerator xmlGen;
	generateXML(outputDirectory);
}

/******************************
 * End: main calling functions
 *****************************/
