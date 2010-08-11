
#include "xmldita.h"
#include "xmlditadocvisitor.h"
#include "xmlditatrace.h"
#include "docparser.h"
#include "language.h"
#include "doxygen.h"
#include "outputgen.h"
#include "xmlgen.h"
#include "dot.h"
#include "message.h"
#include "util.h"
#include <qfileinfo.h> 
#include "parserintf.h"

// <simpletable> support
static const char* ELEM_SIMPLETABLE = "simpletable";
static const char* ELEM_SIMPLETABLEROW = "strow";

//XmlDitaDocVisitor(XmlStream &s,CodeOutputInterface &ci, DocBlockContents *docBlockMaps);
XmlDitaDocVisitor::XmlDitaDocVisitor(XmlStream &s,CodeOutputInterface &ci, DocBlockContents *docBlockMaps) 
  : DocVisitor(DocVisitor_XML),
  xmlStream(s),
  xmlElemStack(s),
  m_ci(ci),
  m_insidePre(false),
  m_hide(false), 
  m_insideParamlist(false),
  m_paramIsTemplate(false),
  m_docBlockMaps(docBlockMaps),
  m_writingDl(false),
  m_mustInsertStrow(false),
  m_strowOrStheadIsPending(false),
  m_addTextToReturnDoc(false),
  m_paraRefCount(0)
{
	//paramDict.setAutoDelete(true);
}

 
  //--------------------------------------
  // visitor functions for leaf nodes
  //--------------------------------------

void XmlDitaDocVisitor::visit(DocWord *w)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocWord*)", w)
	if (m_hide) {
		return;
	}
	// Catches normal text (text outside of a tag or command)
	// and puts it in a "p"
	if (xmlElemStack.isEmpty()) {
		visitPreDefault("p");
	}	
	write(w->word());
}

void XmlDitaDocVisitor::visit(DocLinkedWord *w)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocLinkedWord*)", w)
	if (m_hide) {
		return;
	}
	//printf("XmlDitaDocVisitor calling startLink() DocLinkedWord=`%s'\n", w->word().data());
	Definition *d = w->getDefinition();
	if (0) {
		QString myName;
		myName = d->qualifiedName();
		//printf("XmlDitaDocVisitor calling startLink() DocLinkedWord [name]=`%s'\n", myName.data());
		startLink("", myName, "");
	} else {
		//printf("XmlDitaDocVisitor calling startLink() DocLinkedWord [file]=`%s'\n", w->file().data());
#if DITA_SUPRESS_NAMESPACE_LINKS
		if (w->file().find("namespace") != 0) {
			startLink(w->ref(), w->file(), w->anchor());
		}
#else
		startLink(w->ref(), w->file(), w->anchor());
#endif
	}
	write(w->word());
#if DITA_SUPRESS_NAMESPACE_LINKS
	if (w->file().find("namespace") != 0) {
		endLink();
	}
#else
	endLink();
#endif
}

void XmlDitaDocVisitor::visit(DocWhiteSpace *w)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocWhiteSpace*)", w)
	if (m_hide) {
		return;
	}
	if (m_insidePre) {
		write(w->chars());
	} else {
		write(" ");
	}
}

void XmlDitaDocVisitor::visit(DocSymbol *s)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocSymbol*)", s)
  if (m_hide) {
	return;
  }

  switch(s->symbol())
  {
    case DocSymbol::BSlash:  write("\\"); break;
    case DocSymbol::At:      write("@"); break;
	// NOTE: The XMl stream will translate entities i.e. "&" to "&amp;"
    case DocSymbol::Less:    write("<"); break;
    case DocSymbol::Greater: write(">"); break;
    case DocSymbol::Amp:     write("&"); break;
    case DocSymbol::Dollar:  write("$"); break;
    case DocSymbol::Hash:    write("#"); break;
    case DocSymbol::Percent: write("%"); break;
	case DocSymbol::Apos:    write("'"); break;
    case DocSymbol::Quot:    write("\""); break;
	case DocSymbol::Copy:    xmlStream.writeUnicode("copy");	break;
    case DocSymbol::Tm:      xmlStream.writeUnicode("trade");	break;
    case DocSymbol::Reg:     xmlStream.writeUnicode("reg");		break;
    case DocSymbol::Lsquo:   xmlStream.writeUnicode("lsquo");		break;
    case DocSymbol::Rsquo:	 xmlStream.writeUnicode("rsquo");		break;
    case DocSymbol::Ldquo:	 xmlStream.writeUnicode("ldquo");		break;
    case DocSymbol::Rdquo:	 xmlStream.writeUnicode("rdquo");		break;
    case DocSymbol::Ndash:	 xmlStream.writeUnicode("ndash");		break;
    case DocSymbol::Mdash:	 xmlStream.writeUnicode("mdash");		break;
	case DocSymbol::Uml:	 xmlStream.writeUnicode((const char*)(QString(QChar(s->letter()))+"uml")); break;
	case DocSymbol::Acute:	 xmlStream.writeUnicode((const char*)(QString(QChar(s->letter()))+"acute")); break;
	case DocSymbol::Grave:	 xmlStream.writeUnicode((const char*)(QString(QChar(s->letter()))+"grave")); break;
	case DocSymbol::Circ:	 xmlStream.writeUnicode((const char*)(QString(QChar(s->letter()))+"circ")); break;
	case DocSymbol::Tilde:	 xmlStream.writeUnicode((const char*)(QString(QChar(s->letter()))+"tilde")); break;
	case DocSymbol::Cedil:	 xmlStream.writeUnicode((const char*)(QString(QChar(s->letter()))+"cedil")); break;
	case DocSymbol::Ring:	 xmlStream.writeUnicode((const char*)(QString(QChar(s->letter()))+"ring")); break;
	case DocSymbol::Slash:	 xmlStream.writeUnicode((const char*)(QString(QChar(s->letter()))+"slash")); break;
    case DocSymbol::Szlig:	 xmlStream.writeUnicode("szlig");					   break;
    case DocSymbol::Nbsp:    xmlStream.writeUnicode("nbsp");					   break;
    case DocSymbol::Aelig:	 xmlStream.writeUnicode("aelig");					   break;
    case DocSymbol::AElig:   xmlStream.writeUnicode("AElig");					   break;
    default:
		err("Error: unknown symbol found\n");
  }
}

void XmlDitaDocVisitor::visit(DocURL *u)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocURL*)", u)
	if (m_hide) {
	  return;
	}
	if (u->isEmail()) {
		startXref(QString("mailto:")+QString(u->url()), u->url());
	} else {
		// Need format attribute for external URLs to prevent DITA proccessing persuing
		// external links
		AttributeMap myMap;
		myMap["href"] = u->url();
		myMap["format"] = "html";
		push("xref", myMap);
		write(u->url());	
	}
	endXref();
}

void XmlDitaDocVisitor::visit(DocLineBreak *lb)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocLineBreak*)", lb)
	if (m_hide){
	  return;
	}
	if (m_insidePre) {
		write("\n");
	}
}

void XmlDitaDocVisitor::visit(DocHorRuler *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocHorRuler*)")
	if (m_hide) {
	  return;
	}
	xmlStream.comment(" hruler not supported by DITA 1.1 ");
}

void XmlDitaDocVisitor::visit(DocStyleChange *s)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocStyleChange*)", s)
	if (m_hide) {
	  return;
	}
	switch (s->style())
	{
	case DocStyleChange::Bold:
		if (s->enable()) {
			push("b");
		} else { 
			pop("b");
		}
		break;
	case DocStyleChange::Italic:
		if (s->enable()) {
			push("i");
		} else {
			pop("i");
		}
		break;
	case DocStyleChange::Code:
		if (s->enable()) {
			push("tt");
		} else {
			pop("tt");
		}
		break;
	case DocStyleChange::Subscript:
		if (s->enable()) {
			push("sub");
		} else {
			pop("sub");
		}
		break;
	case DocStyleChange::Superscript:
		if (s->enable()) {
			push("sup");
		} else {
			pop("sup");
		}
		break;
	case DocStyleChange::Center:
		if (s->enable()) {
			xmlStream.comment(" center not supported by DITA 1.1 ");
		}
		break;
	case DocStyleChange::Small:
		if (s->enable()) {
			xmlStream.comment(" small not supported by DITA 1.1 ");
		}
		break;
	case DocStyleChange::Preformatted:
		if (s->enable()) 
		{
			push("pre");  
			m_insidePre = true;
		} else {
			pop("pre");
			m_insidePre = false;
		}
		break;
	case DocStyleChange::Div:
		if (s->enable()) {
			xmlStream.comment(" div not supported by DITA 1.1 ");
		}
		break;
	case DocStyleChange::Span:
		if (s->enable()) {
			xmlStream.comment(" span not supported by DITA 1.1 ");
		}
		break;
	}
}

void XmlDitaDocVisitor::visit(DocVerbatim *s)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocVerbatim*)", s)
	if (m_hide) {
	  return;
	}
	switch(s->type())
	{
		// Note fall through
		case DocVerbatim::Code:
		case DocVerbatim::Verbatim:
		case DocVerbatim::XmlOnly: 
			pushpop("codeblock", s->text());
			break;
		// Note fall through
		case DocVerbatim::HtmlOnly: 
		case DocVerbatim::ManOnly: 
		case DocVerbatim::LatexOnly: 
		case DocVerbatim::Dot: 
		case DocVerbatim::Msc: 
			break;
	}
}

void XmlDitaDocVisitor::visit(DocAnchor *anc)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocAnchor*)", anc)
	if (m_hide) {
	  return;
	}
	xmlElemStack.addAttribute("id", anc->file()+"_1"+anc->anchor());
}

void XmlDitaDocVisitor::visit(DocInclude *inc)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocInclude*)", inc)
	if (m_hide) {
	  return;
	}
	switch(inc->type()) {
		case DocInclude::IncWithLines:
		{ 
			push("codeblock");
			QFileInfo cfi(inc->file());
			FileDef fd(cfi.dirPath(), cfi.fileName());
			Doxygen::parserManager->getParser(inc->extension())->parseCode(
					m_ci,inc->context(),
					inc->text().latin1(),
					inc->isExample(),
					inc->exampleFile(),
					&fd
				);
			pop("codeblock"); 
		}
		break;    
    case DocInclude::Include: 
		push("codeblock");
		Doxygen::parserManager->getParser(inc->extension())->parseCode(
				m_ci,inc->context(),
				inc->text().latin1(),
				inc->isExample(),
				inc->exampleFile()
				);
			pop("codeblock"); 
		break;
    case DocInclude::DontInclude: 
      break;
    case DocInclude::HtmlInclude: 
      break;
    case DocInclude::VerbInclude: 
	  pushpop("pre", inc->text());
      break;
	}
}

void XmlDitaDocVisitor::visit(DocIncOperator *op)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocIncOperator*)", op)
	if (op->isFirst()) {
		if (!m_hide) {
			push("codeblock");
		}
		pushEnabled();
		m_hide = true;
	}
	if (op->type()!=DocIncOperator::Skip) {
		popEnabled();
		if (!m_hide) {
			Doxygen::parserManager->getParser(m_langExt)->parseCode(
					m_ci,op->context(),
					op->text().latin1(),
					op->isExample(),
					op->exampleFile()
				);
		}
		pushEnabled();
		m_hide=true;
	}
	if (op->isLast()) {
		popEnabled();
		if (!m_hide) {
			pop("codeblock"); 
		}
	}
}

void XmlDitaDocVisitor::visit(DocFormula *f)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocFormula*)", f)
	write(f->text());
#if 0
	if (m_hide) {
	  return;
	}
  QString s;
  s.setNum(f->id());
  push("formula", "id", s);
  write(f->text());
  pop("formula");
#endif
}

void XmlDitaDocVisitor::visit(DocIndexEntry *ie)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocIndexEntry*)", ie)
	if (m_hide) {
	  return;
	}
	pushpop("indexterm", ie->entry());
}

void XmlDitaDocVisitor::visit(DocSimpleSectSep *ss)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visit(DocSimpleSectSep*)", ss)
}

//--------------------------------------
// visitor functions for compound nodes
//--------------------------------------
void XmlDitaDocVisitor::visitPre(DocAutoList *l)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocAutoList*)", l)
	if (l->isEnumList()) {
		visitPreDefault("ol");
	} else {
		visitPreDefault("ul");
	}
}

void XmlDitaDocVisitor::visitPost(DocAutoList *l)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPost(DocAutoList*)", l)
	if (l->isEnumList()) {
		visitPostDefault("ol");
	} else {
		visitPostDefault("ul");
	}
}

void XmlDitaDocVisitor::visitPre(DocAutoListItem *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocAutoListItem*)")
	visitPreDefault("li");
}

void XmlDitaDocVisitor::visitPost(DocAutoListItem *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocAutoListItem*)")
	visitPostDefault("li");
}

void XmlDitaDocVisitor::visitPre(DocPara *p) 
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocPara*)", p)
	if (m_writingDl) {
		// Do an asymetric pop/push for dt/dd
		// Can not guarentee that we have a "dt" at the top of the stack so can not pop("dt")
		pop();
		push("dd");
	} else if (canPushPara()) {
		visitPreDefault("p");
	} else if (!canPushPara()) {
		m_paraRefCount += 1;
	}
}

void XmlDitaDocVisitor::visitPost(DocPara *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocPara*)")
	if (!m_writingDl && m_paraRefCount == 0 && canPopPara()) {
		visitPostDefault("p");
	} else if (m_paraRefCount > 0){
		m_paraRefCount -= 1;
	}
	ASSERT(m_paraRefCount >= 0);
}

void XmlDitaDocVisitor::visitPre(DocRoot *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocRoot*)")
}

void XmlDitaDocVisitor::visitPost(DocRoot *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocRoot*)")
}

void XmlDitaDocVisitor::visitPre(DocSimpleSect *s)
{
#ifdef DITA_TRACE
	// Trace stuff
	switch(s->type()) {
		case DocSimpleSect::See:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::See: ")
			break;
		case DocSimpleSect::Author:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Author: ")
			break;
		case DocSimpleSect::Authors:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Authors: ")
			break;
		case DocSimpleSect::Version:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Version: ")
			break;
		case DocSimpleSect::Since:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Since: ")
			break;
		case DocSimpleSect::Date:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Date: ")
			break;
		case DocSimpleSect::Invar:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Invar: ")
			break;
		case DocSimpleSect::Rcs:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Rcs: ")
			break;
		case DocSimpleSect::Pre:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Pre: ")
			break;
		case DocSimpleSect::Post:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Post: ")
			break;
		case DocSimpleSect::User:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::User: ")
			break;
		case DocSimpleSect::Note:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Note: ")
			break;
		case DocSimpleSect::Warning:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Warning: ")
			break;
		case DocSimpleSect::Remark:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Remark: ")
			break;
		case DocSimpleSect::Attention:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Attention: ")
			break;
		case DocSimpleSect::Unknown:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Unknown: ")
			break;
		case DocSimpleSect::Return:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPre(DocSimpleSect*): case DocSimpleSect::Return: ")
			break;
		default:
			ASSERT(0);
			break;
	}
#endif // DITA_TRACE
	if (m_hide) {
	  return;
	}
	switch(s->type())
	{
		// Note Fall through, render as simple paragraph
		case DocSimpleSect::See:
		case DocSimpleSect::Invar:
		case DocSimpleSect::Rcs:		
			if (canPushPara()) {
				push("p"); 
			}
			break;
		//
		// Types that make a definition list
		//
		case DocSimpleSect::Author:
			pushDl("author");
			write("Author");
			break;
		case DocSimpleSect::Authors:
			pushDl("authors");
			write("Authors");
			break;
		case DocSimpleSect::Version:
			pushDl("version");
			write("Version");
			break;
		case DocSimpleSect::Since:
			pushDl("since");
			write("Since");
			break;
		case DocSimpleSect::Date:
			pushDl("date");
			write("Date");
			break;
		case DocSimpleSect::Pre:
			pushDl("precondition");
			write("Pre-condition");
			break;
		case DocSimpleSect::Post:
			pushDl("postcondition");
			write("Post-condition");
			break;
		case DocSimpleSect::User:
			// ALIAS tags are rendered as definition lists
			pushDl("user");
			break;
		//
		// Make a note element
		//
		case DocSimpleSect::Note:		
			push("note", "type", "note"); 
			break;
		case DocSimpleSect::Warning:	
			push("note", "type", "caution"); 
			break;
		case DocSimpleSect::Remark:		
			push("note", "type", "other"); 
			break;
		case DocSimpleSect::Attention:	
			push("note", "type", "attention"); 
			break;
		case DocSimpleSect::Unknown:	
			break;
		case DocSimpleSect::Return:
			// Set flag to gather text into m_docBlockMaps->returnDoc rather than writing it out
			//printf("Setting m_addTextToReturnDoc true\n");
			m_addTextToReturnDoc = true;
			break;
		default:
			ASSERT(0);
			break;
	}
}

void XmlDitaDocVisitor::visitPost(DocSimpleSect *s)
{
#ifdef DITA_TRACE
	// Trace stuff
	switch(s->type()) {
		case DocSimpleSect::See:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::See: ")
			break;
		case DocSimpleSect::Author:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Author: ")
			break;
		case DocSimpleSect::Authors:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Authors: ")
			break;
		case DocSimpleSect::Version:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Version: ")
			break;
		case DocSimpleSect::Since:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Since: ")
			break;
		case DocSimpleSect::Date:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Date: ")
			break;
		case DocSimpleSect::Invar:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Invar: ")
			break;
		case DocSimpleSect::Rcs:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Rcs: ")
			break;
		case DocSimpleSect::Pre:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Pre: ")
			break;
		case DocSimpleSect::Post:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Post: ")
			break;
		case DocSimpleSect::User:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::User: ")
			break;
		case DocSimpleSect::Note:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Note: ")
			break;
		case DocSimpleSect::Warning:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Warning: ")
			break;
		case DocSimpleSect::Remark:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Remark: ")
			break;
		case DocSimpleSect::Attention:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Attention: ")
			break;
		case DocSimpleSect::Unknown:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Unknown: ")
			break;
		case DocSimpleSect::Return:
			DITA_DOC_VISITOR_TRACE_STRING(" XmlDitaDocVisitor::visitPost(DocSimpleSect*): case DocSimpleSect::Return: ")
			break;
		default:
			ASSERT(0);
			break;
	}
#endif // DITA_TRACE
	if (m_hide) {
	  return;
	}	
	switch(s->type())
	{
		case DocSimpleSect::See:
			break;
		// Note fall through
		case DocSimpleSect::Invar:		
		case DocSimpleSect::Rcs:		
			if (m_paraRefCount == 0 && canPopPara()) {
				pop("p"); 
			}
			break;
		// Note fall through for definiton lists
		case DocSimpleSect::Author:
		case DocSimpleSect::Authors:	
		case DocSimpleSect::Version:	
		case DocSimpleSect::Since:		
		case DocSimpleSect::Date:		
		case DocSimpleSect::Pre:
		case DocSimpleSect::Post:
		case DocSimpleSect::User:
			popDl();
			break;
		// Note fall through for note element
		case DocSimpleSect::Note:		
		case DocSimpleSect::Warning:	
		case DocSimpleSect::Remark:		
		case DocSimpleSect::Attention:	
			pop("note"); 
			break;
		case DocSimpleSect::Unknown:	
			break;
		case DocSimpleSect::Return:
			// Unset flag to gather text into m_docBlockMaps->returnDoc
			//printf("Setting m_addTextToReturnDoc false\n");
			m_addTextToReturnDoc = false;
			break;
		default:
			ASSERT(0);
			break;
	}
  //visitPostDefault("simplesect");
}

void XmlDitaDocVisitor::visitPre(DocTitle *)
{	
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocTitle*)")
	if (!xmlElemStack.isEmpty() && xmlElemStack.peek().getElemName() == "concept") {
		visitPreDefault("title");
	} else {
		if (canPushPara()) {
			visitPreDefault("p");
		}
		visitPreDefault("b");
	}
}

void XmlDitaDocVisitor::visitPost(DocTitle *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocTitle*)")
	if (!xmlElemStack.isEmpty() && xmlElemStack.peek().getElemName() == "title") {
		visitPostDefault("title");
	} else {
		visitPostDefault("b");
		if (canPopPara()) {
			visitPostDefault("p");
		}
	}
}

void XmlDitaDocVisitor::visitPre(DocSimpleList *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocSimpleList*)")
	visitPreDefault("ul");
}

void XmlDitaDocVisitor::visitPost(DocSimpleList *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocSimpleList*)")
	visitPostDefault("ul");
}

void XmlDitaDocVisitor::visitPre(DocSimpleListItem *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocSimpleListItem*)")
	visitPreDefault("li");
}

void XmlDitaDocVisitor::visitPost(DocSimpleListItem *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocSimpleListItem*)")
	visitPostDefault("li");
}

void XmlDitaDocVisitor::visitPre(DocSection *s)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocSection*)", s)
	// Currently unsupported
	xmlStream.comment(" XmlDitaDocVisitor::visitPre(DocSection*) not currently supported by DITA 1.1 ");
#if 0
	if (m_hide) {
	  return;
	}
	QString sectNum;
	sectNum.setNum(s->level());
	QString sectAnchor(s->file());
	if (!s->anchor().isEmpty()) {
		sectAnchor.append("_1");
		sectAnchor.append(s->anchor());
	}
	push("sect"+sectNum, "id", sectAnchor);
	pushpop("title", s->title());
#endif
}

void XmlDitaDocVisitor::visitPost(DocSection *s) 
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPost(DocSection*)", s)
	xmlStream.comment(" XmlDitaDocVisitor::visitPre(DocSection*) not currently supported by DITA 1.1 ");
#if 0
	// The original did not have the if(m_hide) test.
	// I assume that is an error so visitPostDefault() uses it.
	QString level;
	level.setNum(s->level());
	visitPostDefault("sect" + level);
#endif
}

void XmlDitaDocVisitor::visitPre(DocHtmlList *s)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocHtmlList*)", s)
	if (m_hide) {
	  return;
	}
	if (s->type()==DocHtmlList::Ordered) {
		push("ol"); 
	} else {
		push("ul"); 
	}
}

void XmlDitaDocVisitor::visitPost(DocHtmlList *s) 
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPost(DocHtmlList*)", s)
	if (s->type()==DocHtmlList::Ordered) {
		visitPostDefault("ol"); 
	} else {
		visitPostDefault("ul");
	}
}

void XmlDitaDocVisitor::visitPre(DocHtmlListItem *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocHtmlListItem*)")
	visitPreDefault("li");
}

void XmlDitaDocVisitor::visitPost(DocHtmlListItem *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocHtmlListItem*)")
	visitPostDefault("li");
}

void XmlDitaDocVisitor::visitPre(DocHtmlDescList *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocHtmlDescList*)")
	visitPreDefault("dl");
}

void XmlDitaDocVisitor::visitPost(DocHtmlDescList *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocHtmlDescList*)")
	visitPostDefault("dl");
}

void XmlDitaDocVisitor::visitPre(DocHtmlDescTitle *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocHtmlDescTitle*)")
	if (m_hide) {
	  return;
	}
	push("dlentry");
	push("dt");
}

void XmlDitaDocVisitor::visitPost(DocHtmlDescTitle *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocHtmlDescTitle*)")
	if (m_hide) {
	  return;
	}
	//printf("XmlDitaDocVisitor::visitPost(DocHtmlDescTitle *)\n");
	pop("dt");
	// Note: We have to wait until XmlDitaDocVisitor::visitPost(DocHtmlDescData *) to pop("dlentry");
}

void XmlDitaDocVisitor::visitPre(DocHtmlDescData *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocHtmlDescData*)")
	push("dd");
}

void XmlDitaDocVisitor::visitPost(DocHtmlDescData *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocHtmlDescData*)")
	pop("dd");
	pop("dlentry");
}

void XmlDitaDocVisitor::visitPre(DocHtmlTable *t)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocHtmlTable*)", t)
	if (m_hide) {
	  return;
	}
	push(ELEM_SIMPLETABLE);
}

void XmlDitaDocVisitor::visitPost(DocHtmlTable *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocHtmlTable*)")
	visitPostDefault(ELEM_SIMPLETABLE);
}

void XmlDitaDocVisitor::visitPre(DocHtmlRow *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocHtmlRow*)")
	// Set lazy flag
	m_strowOrStheadIsPending = true;
	// We have look ahead to first cell before deciding whether to use a "sthead" or not
	// this is done in XmlDitaDocVisitor::visitPre(DocHtmlCell *c)
}

void XmlDitaDocVisitor::visitPost(DocHtmlRow *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocHtmlRow*)")
	// Note: No testing as we could be either poping a sthead or an strow but pop we must
	// (well only if we have pushed).
	if (!m_strowOrStheadIsPending) {
		pop();
	}
	m_strowOrStheadIsPending = false;
}

void XmlDitaDocVisitor::visitPre(DocHtmlCell *c)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocHtmlCell*)", c)
	if (m_strowOrStheadIsPending) {
		// Write sthead or strow for the first cell only
		if (c->isHeading()) {
			visitPreDefault("sthead");
		} else {
			visitPreDefault(ELEM_SIMPLETABLEROW);
		}
		m_strowOrStheadIsPending = false;
	}
	visitPreDefault("stentry");
}

void XmlDitaDocVisitor::visitPost(DocHtmlCell *c) 
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPost(DocHtmlCell*)", c)
	visitPostDefault("stentry");
}

void XmlDitaDocVisitor::visitPre(DocHtmlCaption *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocHtmlCaption*)")
	// Caption is unsupported
	xmlStream.comment(" XmlDitaDocVisitor::visitPre(DocHtmlCaption*) not currently supported by DITA 1.1 ");
}

void XmlDitaDocVisitor::visitPost(DocHtmlCaption *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocHtmlCaption*)")
	// Caption is unsupported
	xmlStream.comment(" XmlDitaDocVisitor::visitPost(DocHtmlCaption*) not currently supported by DITA 1.1 ");
}

void XmlDitaDocVisitor::visitPre(DocInternal *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocInternal*)")
	xmlStream.comment(" XmlDitaDocVisitor::visitPre(DocInternal*) not currently supported by DITA 1.1 ");
}

void XmlDitaDocVisitor::visitPost(DocInternal *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocInternal*)")
	xmlStream.comment(" XmlDitaDocVisitor::visitPost(DocInternal*) not currently supported by DITA 1.1 ");
}

void XmlDitaDocVisitor::visitPre(DocHRef *href)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocHRef*)", href)
	push("xref", "href", href->url());
}

void XmlDitaDocVisitor::visitPost(DocHRef *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocHRef*)")
	visitPostDefault("xref");
}

void XmlDitaDocVisitor::visitPre(DocHtmlHeader *header)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocHtmlHeader*)", header)
	visitPreDefault("b");
#if 0
  QString hdgLevel;
  hdgLevel.setNum(header->level());
  push("heading", "level", hdgLevel);
#endif
}

void XmlDitaDocVisitor::visitPost(DocHtmlHeader *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocHtmlHeader*)")
	visitPostDefault("b");
}

void XmlDitaDocVisitor::visitPre(DocImage *img)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocImage*)", img)
	// Currently unsupported
	xmlStream.comment(" XmlDitaDocVisitor::visitPre(DocImage*) not currently supported by DITA 1.1 ");
#if 0
  AttributeMap imgAttrs;
  // First the image type
  switch(img->type())
  {
    case DocImage::Html:
		imgAttrs["type"] = "html";
		break;
    case DocImage::Latex:
		imgAttrs["type"] = "latex";
		break;
	case DocImage::Rtf:
		imgAttrs["type"] = "rtf";
		break;
	default:
		ASSERT(0);
		break;
  }
  // Now the image name
  QString baseName=img->name();
  int i;
  if ((i=baseName.findRev('/'))!=-1 || (i=baseName.findRev('\\'))!=-1)
  {
    baseName=baseName.right(baseName.length()-i-1);
  }
  imgAttrs["name"] = baseName;
  // Image width
  if (!img->width().isEmpty())
  {
    imgAttrs["width"] = img->width();
  }
  // Image height
  // NOTE: In the original this was an else if. I assume that this is an error
  if (!img->height().isEmpty())
  {
    imgAttrs["height"] = img->height();
  }
  push("image", imgAttrs);

  // copy the image to the output dir
  QFile inImage(img->name());
  QFile outImage(Config_getString("XML_DITA_OUTPUT")+"/"+baseName.ascii());
  if (inImage.open(IO_ReadOnly))
  {
    if (outImage.open(IO_WriteOnly))
    {
      char *buffer = new char[inImage.size()];
      inImage.readBlock(buffer,inImage.size());
      outImage.writeBlock(buffer,inImage.size());
      outImage.flush();
      delete[] buffer;
    }
  }
#endif
}

void XmlDitaDocVisitor::visitPost(DocImage *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocImage*)")
	xmlStream.comment(" XmlDitaDocVisitor::visitPost(DocImage*) not currently supported by DITA 1.1 ");
}

void XmlDitaDocVisitor::visitPre(DocDotFile *df)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocDotFile*)", df)
	// Currently unsupported
	xmlStream.comment(" XmlDitaDocVisitor::visitPre(DocDotFile*) not currently supported by DITA 1.1 ");
}

void XmlDitaDocVisitor::visitPost(DocDotFile *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocDotFile*)")
	xmlStream.comment(" XmlDitaDocVisitor::visitPost(DocDotFile*) not currently supported by DITA 1.1 ");
}

void XmlDitaDocVisitor::visitPre(DocLink *lnk)
{
	// The result of a \link...\endlink command
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocLink*)", lnk)
	if (m_hide) {
	  return;
	}
	startLink(lnk->ref(), lnk->file(), lnk->anchor());
}

void XmlDitaDocVisitor::visitPost(DocLink *) 
{
	// The result of a \link...\endlink command
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocLink*)")
	if (m_hide) {
	  return;
	}
	endLink();
}

void XmlDitaDocVisitor::visitPre(DocRef *ref)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocRef*)", ref)
	if (m_hide) {
	  return;
	}
	if (!ref->file().isEmpty()) {
		if (ref->getDefinition() != 0) {
			//printf("XmlDitaDocVisitor calling startLink() DocRef [name]=`%s'\n", ref->getDefinition()->qualifiedName().data());
			startLink("", ref->getDefinition()->qualifiedName(), "");
		} else {
			//printf("XmlDitaDocVisitor calling startLink() DocRef [file]=`%s'\n", ref->file().data());
			startLink(ref->ref(), ref->file(), ref->anchor());
		}	
	}
	if (!ref->hasLinkText()) {
	  write(ref->targetTitle());
	}
}

void XmlDitaDocVisitor::visitPost(DocRef *ref) 
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPost(DocRef*)", ref)
	if (m_hide) {
	  return;
	}
	if (!ref->file().isEmpty()) {
	  endLink();
	}
	write(" ");
}

void XmlDitaDocVisitor::visitPre(DocSecRefItem *ref)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocSecRefItem*)", ref)
	if (m_hide) {
	  return;
	}
	push("li", "id", ref->file()+"_1"+ref->anchor());
}

void XmlDitaDocVisitor::visitPost(DocSecRefItem *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocSecRefItem*)")
	visitPostDefault("li");
}

void XmlDitaDocVisitor::visitPre(DocSecRefList *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocSecRefList*)")
	visitPreDefault("ul");
}

void XmlDitaDocVisitor::visitPost(DocSecRefList *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocSecRefList*)")
	visitPostDefault("ul");
}

void XmlDitaDocVisitor::visitPre(DocParamSect *s)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocParamSect*)", s)
	if (m_hide) {
	  return;
	}
	switch(s->type()) {
		case DocParamSect::Param:
			m_insideParamlist = true;
			m_paramIsTemplate = false;
			push("paraml", "class", "param"); 
			break;
		case DocParamSect::RetVal:
			// NOTE: This code never seems to get exercised
			m_insideParamlist = false;
			push("paraml", "class", "retval"); 
			break;
		case DocParamSect::Exception:
			//printf("void XmlDitaDocVisitor::visitPre(DocParamSect *s) Exception\n");
			m_insideParamlist = false;
			push("dl", "outputclass", "exception");
			push("dlentry");
			pushpop("dt", "Exceptions");
			push("dd");
			push(ELEM_SIMPLETABLE);
			break;
		case DocParamSect::TemplateParam: 
			m_insideParamlist = true;
			m_paramIsTemplate = true;
			push("paraml", "class", "templateparam");
			break;
		default:
		  ASSERT(0);
	}
}

void XmlDitaDocVisitor::visitPost(DocParamSect *s)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocParamSect*)")
	if (m_hide) {
	  return;
	}
	switch(s->type()) {
		case DocParamSect::Exception:
			pop(ELEM_SIMPLETABLE); 
			pop("dd"); 
			pop("dlentry"); 
			pop("dl"); 
			break;
		default:
			visitPostDefault("paraml");
			break;
	}
	m_insideParamlist = false;
}

void XmlDitaDocVisitor::visitPre(DocParamList *pl)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocParamList*)", pl)
	if (m_hide) {
	  return;
	}
	if (!m_insideParamlist) {
		push("strow");
		push("stentry");
	}
	QListIterator<DocNode> li(pl->parameters());
	DocNode *param;
	for (li.toFirst();(param=li.current());++li) {
		if (param->kind() == DocNode::Kind_Word) {			
			currParam = ((DocWord*)param)->word();
		} else if (param->kind() == DocNode::Kind_LinkedWord) {
			currParam = ((DocLinkedWord*)param)->word();
		} else {
			// FIXME, what should we use here
			currParam = "";
		}
		if (canLoadParameterMap()) {
			if (m_paramIsTemplate) {
				m_docBlockMaps->tparamMap.insert(currParam, "");
			} else {
				m_docBlockMaps->paramMap.insert(currParam, "");
			}
		} else {
			if (param->kind() == DocNode::Kind_Word)
			{
			  visit((DocWord*)param); 		
			}
			else if (param->kind() == DocNode::Kind_LinkedWord)
			{
			  visit((DocLinkedWord*)param); 
			}
		}
	}
	if (!m_insideParamlist) {
		pop("stentry");
		push("stentry");
	}
}

void XmlDitaDocVisitor::visitPost(DocParamList *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocParamList*)")
	if (m_hide) {
	  return;
	}
	if (!m_insideParamlist) {
		pop("stentry");
		pop("strow");
	}
}

void XmlDitaDocVisitor::visitPre(DocXRefItem *x)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocXRefItem*)", x)
	if (m_hide) {
	  return;
	}
	// \deprecated commands result in DocXRefItem
	// with "deprecated" as the filename
	if (x->file() == "deprecated"){
		// Fall through to start new paragraph for deprecated description
	} else {
		QString hrefStr = x->file();
		hrefStr.append(Config_getString("XML_DITA_EXTENSION"));
		hrefStr.append("#");
		hrefStr.append(x->file());
		hrefStr.append("_1");
		hrefStr.append(x->anchor());
		push("xref", "href", hrefStr);
		write(x->title());
	}
}

void XmlDitaDocVisitor::visitPost(DocXRefItem *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocXRefItem*)")
	if (m_hide) {
	  return;
	}
	// An xref will be top of stack unless the current 
	// DocXRefItem was caused by a \deprecated command
	if (!xmlElemStack.isEmpty() && xmlElemStack.peek().getElemName() == "xref") {
		pop("xref");
	}
}

void XmlDitaDocVisitor::visitPre(DocInternalRef *ref)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocInternalRef*)", ref)
	if (m_hide) {
	  return;
	}
	startLink(0, ref->file(), ref->anchor());
}

void XmlDitaDocVisitor::visitPost(DocInternalRef *) 
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocXRefItem*)")
	if (m_hide) {
	  return;
	}
	endLink();
	write(" ");
}

void XmlDitaDocVisitor::visitPre(DocCopy *c)
{
	DITA_DOC_VISITOR_TRACE("XmlDitaDocVisitor::visitPre(DocCopy*)", c)
	// Currently unsupported
	xmlStream.comment(" XmlDitaDocVisitor::visitPre(DocCopy*) not currently supported by DITA 1.1 ");
}

void XmlDitaDocVisitor::visitPost(DocCopy *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocCopy*)")
	xmlStream.comment(" XmlDitaDocVisitor::visitPost(DocCopy*) not currently supported by DITA 1.1 ");
}

void XmlDitaDocVisitor::visitPre(DocText *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPre(DocText*)")
}

void XmlDitaDocVisitor::visitPost(DocText *)
{
	DITA_DOC_VISITOR_TRACE_NOARG("XmlDitaDocVisitor::visitPost(DocText*)")
}

void XmlDitaDocVisitor::startXref(const QString &href,const QString &text)
{
	push("xref", "href", href);
}

void XmlDitaDocVisitor::endXref()
{
	pop("xref");
}

void XmlDitaDocVisitor::startLink(const QString &ref,const QString &file,const QString &anchor)
{
  AttributeMap refAttrs;
  /*
  printf("XmlDitaDocVisitor::startLink(): ref: \"%s\", file: \"%s\", anchor: \"%s\"\n",
	  ref.data(),
	  file.data(),
	  anchor.data());
  */
  if (!anchor.isEmpty()) {
	  refAttrs["href"] = file+".xml#"+file+"_1"+anchor;
  } else {
	  refAttrs["href"] = file+".xml#"+file;
  }
  push("xref", refAttrs);
}

void XmlDitaDocVisitor::endLink()
{
  visitPostDefault("xref");
}

void XmlDitaDocVisitor::pushEnabled()
{
  m_enabled.push(new bool(m_hide));
}

void XmlDitaDocVisitor::popEnabled()
{
  bool *v = m_enabled.pop();
  ASSERT(v!=0);
  m_hide = *v;
  delete v;
}

bool XmlDitaDocVisitor::canWriteToXmlStream() const
{
	if (m_insideParamlist || m_addTextToReturnDoc || m_docBlockMaps != 0) {
		return false;
	} else {
		return true;
	}
}

/// Returns true if I gather text into m_docBlockMaps->returnDoc?
bool XmlDitaDocVisitor::shouldAddTextToReturnDoc() const
{
	return (m_addTextToReturnDoc && m_docBlockMaps != 0);
}

bool XmlDitaDocVisitor::canLoadParameterMap() const
{
	return m_insideParamlist && m_docBlockMaps != 0;
}

/** Keeps track of state so that a simpletable has a strow. */
void XmlDitaDocVisitor::checkSimpleTable(const QString &tagName)
{
	if (tagName == ELEM_SIMPLETABLE) {
		m_mustInsertStrow = true;
	} else if (m_mustInsertStrow && tagName == "strow") {
		m_mustInsertStrow = false;
	}
}

void XmlDitaDocVisitor::addStrowToSimpleTableOnPop(const QString &tagName)
{
	if (tagName == ELEM_SIMPLETABLE && m_mustInsertStrow) {
		pushpop(ELEM_SIMPLETABLEROW);
		m_mustInsertStrow = false;
	}
}

void XmlDitaDocVisitor::write(const QString &string)
{
	if (canWriteToXmlStream()) {
		xmlStream << string;
	} else if (canLoadParameterMap()) {
		if (m_paramIsTemplate) {
			if (m_docBlockMaps->tparamMap.contains(currParam)) {
				m_docBlockMaps->tparamMap[currParam].append(string);
			} else {
				m_docBlockMaps->tparamMap[currParam] = string;
			}
		} else {
			if (m_docBlockMaps->paramMap.contains(currParam)) {
				m_docBlockMaps->paramMap[currParam].append(string);
			} else {
				m_docBlockMaps->paramMap[currParam] = string;
			}
		}
	} else if (shouldAddTextToReturnDoc()) {
		//printf("Adding \"%s\" to returnDoc\n", string.data());
		m_docBlockMaps->returnDoc.append(string);
	}
}

void XmlDitaDocVisitor::push(const QString &tagName)
{
	if (canWriteToXmlStream()) {
		checkSimpleTable(tagName);
		xmlElemStack.push(tagName);
	}
}

void XmlDitaDocVisitor::push(const QString &tagName, const QString &key, const QString &value)
{
	if (canWriteToXmlStream()) {
		checkSimpleTable(tagName);
		xmlElemStack.push(tagName, key, value);
	}
}

void XmlDitaDocVisitor::push(const QString &tagName, AttributeMap &map)
{
	if (canWriteToXmlStream()) {
		checkSimpleTable(tagName);
		xmlElemStack.push(tagName, map);
	}
}

/** pop without checking element matches.
This can be useful when making asymetric push/pops
*/
void XmlDitaDocVisitor::pop()
{
	if (canWriteToXmlStream()) {
		// Note: No use of addStrowToSimpleTableOnPop()
		xmlElemStack.pop();
	}
}

void XmlDitaDocVisitor::pop(const QString &tagName)
{
	if (canWriteToXmlStream()) {
		addStrowToSimpleTableOnPop(tagName);
		xmlElemStack.pop(tagName);
	}
}

void XmlDitaDocVisitor::pushpop(const QString &tagName)
{
	if (canWriteToXmlStream() && tagName != ELEM_SIMPLETABLE) {
		xmlElemStack.pushpop(tagName);
	}
}

void XmlDitaDocVisitor::pushpop(const QString &tagName, const QString &text)
{
	if (canWriteToXmlStream() && tagName != ELEM_SIMPLETABLE) {
		xmlElemStack.pushpop(tagName, text);
	} else if (canLoadParameterMap()) {
		if (m_paramIsTemplate) {
			if (m_docBlockMaps->tparamMap.contains(currParam)) {
				m_docBlockMaps->tparamMap[currParam].append(text);
			} else {
				m_docBlockMaps->tparamMap[currParam] = text;
			}
		} else {
			if (m_docBlockMaps->paramMap.contains(currParam)) {
				m_docBlockMaps->paramMap[currParam].append(text);
			} else {
				m_docBlockMaps->paramMap[currParam] = text;
			}
		}
	}
}

/** Pushes a definition list onto the stack
@param outputClass The value of the outputclass attribute in the dl element
*/
void XmlDitaDocVisitor::pushDl(const QString &outputClass)
{

	// ALIAS tags are rendered as definition lists
	push("dl", "outputclass", outputClass);
	push("dlentry");
	push("dt");
	// This state allows us to do an asymetric push/pop when writing a DocPara
	m_writingDl = true;
}

/** Pops a definition list onto the stack
*/
void XmlDitaDocVisitor::popDl()
{
	// ALIAS tags are rendered as definition lists
	// Note that this is asymetric as pre pushed dt and we pop dd
	// We don't use pop("dd"); as the swap might not have happened
	// and we risk an assertion failure at that point.
	pop();
	pop("dlentry");
	pop("dl");
	// Unset the state variable that allows us to do an
	// asymetric push/pop when writing a DocPara
	m_writingDl = false;
}

/// Returns true if it is OK to write a para element
bool XmlDitaDocVisitor::canPushPara() const
{
	if (!xmlElemStack.isEmpty()) {
		QString e = xmlElemStack.peek().getElemName();
		if (e == "xref" || e == "p" || e == "dt") {
			return false;
		}
	}
	return true;
}

bool XmlDitaDocVisitor::canPopPara() const
{
	if (!xmlElemStack.isEmpty() && xmlElemStack.peek().getElemName() == "p") {
			return true;
	}
	return false;
}

/** Default treatment of a post traversal visit, this just
pushes a single element with no attributes. */
void XmlDitaDocVisitor::visitPreDefault(const QString& elem)
{
	if (m_hide) {
	  return;
	}
	push(elem);
}

/** Default treatment of a post traversal visit, this just
pops a single element. */
void XmlDitaDocVisitor::visitPostDefault(const QString& elem)
{
	if (m_hide) {
	  return;
	}
	pop(elem);
}

