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

#ifndef XMLDITAGEN_H
#define XMLDITAGEN_H
#include "xmldita.h"
#include "xmlditaparammap.h"

void generateXMLDITA();

/// Used for sorting members by declaration source code line.
/// Implemented by DITAClassGenerator and DITAFileGenerator
typedef QMap<int, MemberDef*> SrcDeclMemberMap;
/// Used for sorting members by nameLookup().
/// Implemented by DITAClassGenerator and DITAFileGenerator
typedef QMap<QString, MemberDef*> MemberNameLookupMap;
/// Used for removing duplicate member IDs, actually we treat this map as a set
typedef QMap<QString, bool> MemberIdMap;

class DITAGeneratorBase
{
public:
	DITAGeneratorBase(XmlStream &x): ix(x) {}
	void writeXMLDocBlock(XmlStream &t,
						  const QCString &fileName,
						  int lineNr,
						  Definition *scope,
						  MemberDef * md,
						  const QCString &text,
						  DocBlockContentsType *docBlockMaps) const;
						  //ParamDescriptionMap *pMap) const;
	void writeXMLElementAndText(XmlStream& t, QString e, AttributeMap& a, QString text) const;
	void writeXMLElementAndText(XmlStream& t, QString e, QString text) const;
	QString accessSpecifier(Protection p, bool assertOnPackage=false) const;
	void writeInnerGroups(const GroupList *gl, XmlStream & xt);
	void writeInnerClasses(const ClassDef *pc, const ClassSDict *cl, XmlStream &t);
	void writeInnerClasses(const NamespaceDef *npc, const ClassSDict *cl, XmlStream &t);
	void generateXMLSection(Definition *d,
							XmlStream &ix,
							XmlStream &t,
							MemberList *ml,
							const char *kind,
							const char *header=0,
							const char *documentation=0);
	void writeTemplateArgumentList(QString &elemPrefix,
									ArgumentList *al,
									XmlStream &xt,
									Definition *scope,
									FileDef *fileScope,
									const DocBlockContentsType& paramMaps) const;
	void writeTemplateArgumentList(ClassDef *cd,
									ArgumentList *al,
									XmlStream &xt,
									Definition *scope,
									FileDef *fileScope,
									const DocBlockContentsType& paramMaps) const;
	void writeTemplateArgumentList(MemberDef *md,
									ArgumentList *al,
									XmlStream &xt,
									Definition *scope,
									FileDef *fileScope,
									const DocBlockContentsType& paramMaps) const;
	void generateXMLForBriefDescription(Definition *d, MemberDef *md, XmlStream &xs) const;
	void generateXMLForDetailedDescription(Definition *d, MemberDef *md, XmlStream &xs) const;
	void generateXMLForDefFileName(const Definition *d, XmlStream &xt, bool incLine=true);
	void writeFileLocation(Definition *d, XmlStream &xt, const QString &prefix, bool incDef) const;
	QCString outputFileNameFromDefinition(Definition *d) const;
#if USE_DOXYGEN_ID_AS_XML_ID == 0
	void remapXrefs(DocNode *root) const;
#endif
protected:
	/** This is the index XML stream */
	XmlStream &ix;
private:
	QString m_SourceLang;
	QString m_srcElemPrefix;
private:
	void stripQualifiers(QCString &typeStr);
	//AttributeMap getMapAttributes(const QString &id) const;

protected:
	// id(...) functions
	QString id(const Definition *d) const;
	QString id(const MemberDef *d) const;
	QString id(const PageDef *d) const;
	// This returns the ID that is used for duplicate member detection
	QString idForDuplicateMember(const MemberDef *md) const;
	
	AttributeMap getMapAttributes(const Definition *d) const;
	//AttributeMap getMapAttributes(const MemberDef *d) const;
	//AttributeMap getMapAttributes(const PageDef *d) const;

	void writeAccessSpecifierElement(XmlStream &xs,
										ClassDef *cd,
										Protection p) const;
	void writeAccessSpecifierElement(XmlStream &xs,
										MemberDef *cd,
										Protection p) const;
	void writeReferenceTo(XmlStream &xs, const ClassDef *cd, const QString &suffix);
	void writeReferenceTo(XmlStream &xs, const MemberDef *md, const QString &suffix);
	void writeReferenceTo(XmlStream &xs, const ClassDef *cd, const MemberDef *md, const QString &suffix);
	void writeVirtualElement(XmlStream &xs, ClassDef *cd, Specifier v);
	void writeVirtualElement(XmlStream &xs, MemberDef *d);
// Generating output from MemberDef objects
protected:
	void generateXMLForMember(MemberDef *md, XmlStream &xt, Definition *def);
	QString nameLookup(const MemberDef *md) const;
	QString visualPrototype(const MemberDef *md) const;
private:
	void writeMemberScs(const MemberDef *md, XmlStream &xt) const;
	void writeFunctionProperties(const MemberDef *md, XmlStream &xt) const;
	void writeMacroParameters(MemberDef *md, Definition *def, XmlStream &xt) const;
	void writeFunctionTemplateAndParameters(MemberDef *md, Definition *def, XmlStream &xt) const;
	void writeMemberBitField(const MemberDef *md, XmlStream &xt) const;
	void writeMemberEnumerator(const MemberDef *md, XmlStream &xt);
	void writeMemberTemplateLists(MemberDef *md, XmlStream &xt, const DocBlockContentsType& paramMaps) const;
protected:
	void writeVirtualElement(XmlStream &xs, QString p, Specifier v) const;
private:
	DITAGeneratorBase (const DITAGeneratorBase &rhs);
	DITAGeneratorBase& operator=(const DITAGeneratorBase &rhs);
protected:
	// Used to eliminate duplicate IDs in a class
	MemberIdMap m_memberIdMap;
};

class DITAClassGenerator : public DITAGeneratorBase
{
public:
	DITAClassGenerator(XmlStream &x): DITAGeneratorBase(x) {}
	void generateXMLForClasses();
private:
	void generateXMLForBaseDerivedClasses(XmlStream& t, BaseClassListIterator& bcli);
	SrcDeclMemberMap membersInDeclOrder(ClassDef *cd, bool incAllMembers);
	MemberNameLookupMap membersInFormalDeclOrder(ClassDef *cd, bool incAllMembers);
	void writeTemplateList(ClassDef *cd, XmlStream &xt);
	void writeDITAMapEntryForClass(ClassDef *cd);
	void generateXMLForClass(ClassDef *cd);
	bool skipThisClass(ClassDef *cd) const;
	bool isCompletelyDefined(ClassDef *cd) const;
private:
	DITAClassGenerator (const DITAClassGenerator &rhs);
	DITAClassGenerator& operator=(const DITAClassGenerator &rhs);
};

class DITANamespaceGenerator : public DITAGeneratorBase
{
public:
	DITANamespaceGenerator(XmlStream &x): DITAGeneratorBase(x) {}
	void generateXMLForNamespaces();
	void writeInnerNamespaces(const NamespaceSDict *nl, XmlStream &xt);
private:
	void generateXMLForNamespace(NamespaceDef *nd);
	MemberNameLookupMap membersInFormalDeclOrder(NamespaceDef *nd, bool incAllMembers);
private:
	DITANamespaceGenerator (const DITANamespaceGenerator &rhs);
	DITANamespaceGenerator& operator=(const DITANamespaceGenerator &rhs);
};

class DITAFileGenerator : public DITAGeneratorBase
{
public:
	DITAFileGenerator(XmlStream &x): DITAGeneratorBase(x) {}
	void generateXMLForFiles();
private:
	void writeXMLDITACodeBlock(XmlStream &t,FileDef *fd);
	void generateXMLForFile(FileDef *fd);
	bool fileHasMembers(FileDef *fd, bool incAllMembers);
	SrcDeclMemberMap membersInDeclOrder(FileDef *cd, bool incAllMembers);
	MemberNameLookupMap membersInFormalDeclOrder(FileDef *cd, bool incAllMembers);
private:
	DITAFileGenerator (const DITAFileGenerator &rhs);
	DITAFileGenerator& operator=(const DITAFileGenerator &rhs);
};

class DITAGroupGenerator : public DITAGeneratorBase
{
public:
	DITAGroupGenerator(XmlStream &x): DITAGeneratorBase(x) {}
	void generateXMLForGroups();
private:
	void generateXMLForGroup(GroupDef *gd);
private:
	DITAGroupGenerator (const DITAGroupGenerator &rhs);
	DITAGroupGenerator& operator=(const DITAGroupGenerator &rhs);
};

class DITADirGenerator : public DITAGeneratorBase
{
public:
	DITADirGenerator(XmlStream &x): DITAGeneratorBase(x) {}
	void generateXMLForDirectories();
private:
	void writeInnerDirs(const DirList *dl, XmlStream & xt);
	void generateXMLForDir(DirDef *dd);
	DITADirGenerator (const DITADirGenerator &rhs);
	DITADirGenerator& operator=(const DITADirGenerator &rhs);
};

class DITAPageGenerator : public DITAGeneratorBase
{
public:
	DITAPageGenerator(XmlStream &x): DITAGeneratorBase(x) {}
	void generateXMLForPages();
	void generateXMLForExamples();
	void generateXMLForMainPage();
private:
	QCString getPageName(PageDef *pd);
	void generateXMLForPage(PageDef *pd, bool isExample);
private:
	DITAPageGenerator (const DITAPageGenerator &rhs);
	DITAPageGenerator& operator=(const DITAPageGenerator &rhs);
};

#endif // XMLDITAGEN_H
