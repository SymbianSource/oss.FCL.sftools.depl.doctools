
#include "xmlditadocvisitor.h"
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


XmlDitaDocVisitor::XmlDitaDocVisitor(XmlStream &s,CodeOutputInterface &ci) 
  : DocVisitor(DocVisitor_XML), xmlStream(s), xmlElemStack(s), m_ci(ci), m_insidePre(FALSE), m_hide(FALSE), 
    m_insideParamlist(FALSE), paramMap(), paramDict(), currParam()
{}

 
  //--------------------------------------
  // visitor functions for leaf nodes
  //--------------------------------------

void XmlDitaDocVisitor::visit(DocWord *w)
{
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
	if (m_hide) {
		return;
	}
	if (w->getDefinition() != 0) {
		startLink("", w->getDefinition()->qualifiedName(), "");
	} else {
		startLink(w->ref(), w->file(), w->anchor());
	}
	write(w->word());
	endLink();
}

void XmlDitaDocVisitor::visit(DocWhiteSpace *w)
{
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
	if (m_hide) {
	  return;
	}
	if (u->isEmail()) {
		startXref(QString("mailto:")+QString(u->url()), u->url());
	} else {
		startXref(u->url(), u->url());
	}
	endXref();
}

void XmlDitaDocVisitor::visit(DocLineBreak *lb)
{
	if (m_hide){
	  return;
	}
	//pushpop("linebreak");
	//if (lb->parent()->kind() == lb->Kind_Verbatim) {
	if (m_insidePre) {
		write("\n");
	}
}

void XmlDitaDocVisitor::visit(DocHorRuler *)
{
	if (m_hide) {
	  return;
	}
	//pushpop("hruler");
	xmlStream.comment("hruler not supported by DITA 1.1");
}

void XmlDitaDocVisitor::visit(DocStyleChange *s)
{
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
			xmlStream.comment("center not supported by DITA 1.1");
			//push("center");
		} else {
			//pop("center");
		}
		break;
	case DocStyleChange::Small:
		if (s->enable()) {
			xmlStream.comment("small not supported by DITA 1.1");
			//push("small");
		} else {
			//pop("small");
		}
		break;
	case DocStyleChange::Preformatted:
		if (s->enable()) 
		{
			push("pre");  
			m_insidePre = TRUE;
		} else {
			pop("pre");
			m_insidePre = FALSE;
		}
		break;
	case DocStyleChange::Div:  /* HTML only */ break;
	case DocStyleChange::Span: /* HTML only */ break;
	}
}

void XmlDitaDocVisitor::visit(DocVerbatim *s)
{
	if (m_hide) {
	  return;
	}
	switch(s->type())
	{
		case DocVerbatim::Code:
			push("codeblock");
			write(s->text());
			pop("codeblock");
			break;
		case DocVerbatim::Verbatim:
			pushpop("pre", s->text());
			break;
		case DocVerbatim::HtmlOnly: 
			//pushpop("htmlonly", s->text());
			break;
		case DocVerbatim::ManOnly: 
			//pushpop("manonly", s->text());
			break;
		case DocVerbatim::LatexOnly: 
			//pushpop("latexonly", s->text());
			break;
		case DocVerbatim::XmlOnly: 
			write(s->text());
			break;
		case DocVerbatim::Dot: 
			//pushpop("dot", s->text());
			break;
		case DocVerbatim::Msc: 
			//pushpop("msc", s->text());
			break;
	}
}

void XmlDitaDocVisitor::visit(DocAnchor *anc)
{
	if (m_hide) {
	  return;
	}
	xmlElemStack.addAttribute("id", anc->file()+"_1"+anc->anchor());
	//push("anchor", "id", anc->file()+"_1"+anc->anchor());
	//pop("anchor");
}

void XmlDitaDocVisitor::visit(DocInclude *inc)
{
	if (m_hide) {
	  return;
	}
  switch(inc->type())
  {
    case DocInclude::IncWithLines:
      { 
         push("codeblock");
         QFileInfo cfi( inc->file() );
         FileDef fd( cfi.dirPath(), cfi.fileName() );
         Doxygen::parserManager->getParser(inc->extension())
                               ->parseCode(m_ci,inc->context(),
                                           inc->text().latin1(),
                                           inc->isExample(),
                                           inc->exampleFile(), &fd);
         pop("codeblock"); 
      }
      break;    
    case DocInclude::Include: 
      push("codeblock");
      Doxygen::parserManager->getParser(inc->extension())
                            ->parseCode(m_ci,inc->context(),
                                        inc->text().latin1(),
                                        inc->isExample(),
                                        inc->exampleFile());
      pop("codeblock"); 
      break;
    case DocInclude::DontInclude: 
      break;
    case DocInclude::HtmlInclude: 
	  //pushpop("htmlonly", inc->text());
      break;
    case DocInclude::VerbInclude: 
	  pushpop("pre", inc->text());
      break;
  }
}

void XmlDitaDocVisitor::visit(DocIncOperator *op)
{
  DITA_DOC_VISITOR_TRACE("visit(DocIncOperator*)",op);
  if (op->isFirst()) 
  {
    if (!m_hide) {
		push("codeblock");
    }
    pushEnabled();
    m_hide = TRUE;
  }
  if (op->type()!=DocIncOperator::Skip) 
  {
    popEnabled();
    if (!m_hide) {
      Doxygen::parserManager->getParser(m_langExt)
                            ->parseCode(m_ci,op->context(),
                                        op->text().latin1(),op->isExample(),
                                        op->exampleFile());
    }
    pushEnabled();
    m_hide=TRUE;
  }
  if (op->isLast())  
  {
    popEnabled();
	if (!m_hide) {
		pop("codeblock"); 
	}
  }
}

void XmlDitaDocVisitor::visit(DocFormula *f)
{
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
	if (m_hide) {
	  return;
	}

	push("indexterm");
	write(ie->entry());
	pop("indexterm");
#if 0
	push("indexentry");
	push("primaryie");
	write(ie->entry());
	pop("primaryie");
	pushpop("secondaryie");
	pop("indexentry");
#endif
}

void XmlDitaDocVisitor::visit(DocSimpleSectSep *)
{
  //pushpop("simplesectsep");
}

//--------------------------------------
// visitor functions for compound nodes
//--------------------------------------

void XmlDitaDocVisitor::visitPre(DocAutoList *l)
{
	if (m_hide) {
	  return;
	}
	if (l->isEnumList()) {
		push("ol");
	} else {
		push("ul");
	}
}

void XmlDitaDocVisitor::visitPost(DocAutoList *l)
{
	if (l->isEnumList()) {
		visitPostDefault("ol");
	} else {
		visitPostDefault("ul");
	}
}

void XmlDitaDocVisitor::visitPre(DocAutoListItem *)
{
	visitPreDefault("li");
}

void XmlDitaDocVisitor::visitPost(DocAutoListItem *) 
{
	visitPostDefault("li");
}

void XmlDitaDocVisitor::visitPre(DocPara *p) 
{
	if (xmlElemStack.isEmpty() || xmlElemStack.peek().getElemName() != "p") {
		visitPreDefault("p");
	}
}

void XmlDitaDocVisitor::visitPost(DocPara *)
{
	if (!xmlElemStack.isEmpty() && xmlElemStack.peek().getElemName() == "p") {
		visitPostDefault("p");
	}
}

void XmlDitaDocVisitor::visitPre(DocRoot *)
{}

void XmlDitaDocVisitor::visitPost(DocRoot *)
{}

void XmlDitaDocVisitor::visitPre(DocSimpleSect *s)
{
	if (m_hide) {
	  return;
	}
	switch(s->type())
	{
		// Fall through
		case DocSimpleSect::See:		
		case DocSimpleSect::Return:		
		case DocSimpleSect::Author:		
		case DocSimpleSect::Authors:	
		case DocSimpleSect::Version:	
		case DocSimpleSect::Since:		
		case DocSimpleSect::Date:		
		case DocSimpleSect::Pre:		
		case DocSimpleSect::Post:		
		case DocSimpleSect::Invar:		
		case DocSimpleSect::User:		
		case DocSimpleSect::Rcs:		
			if (xmlElemStack.isEmpty() || xmlElemStack.peek().getElemName() != "p") {
				push("p"); 
			}
			break;
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
		default:
			ASSERT(0);
#if 0
		case DocSimpleSect::See:		push("simplesect", "kind", "see"); break;
		case DocSimpleSect::Return:		push("simplesect", "kind", "return"); break;
		case DocSimpleSect::Author:		push("simplesect", "kind", "author"); break;
		case DocSimpleSect::Authors:	push("simplesect", "kind", "authors"); break;
		case DocSimpleSect::Version:	push("simplesect", "kind", "version"); break;
		case DocSimpleSect::Since:		push("simplesect", "kind", "since"); break;
		case DocSimpleSect::Date:		push("simplesect", "kind", "date"); break;
		case DocSimpleSect::Note:		push("simplesect", "kind", "note"); break;
		case DocSimpleSect::Warning:	push("simplesect", "kind", "warning"); break;
		case DocSimpleSect::Pre:		push("simplesect", "kind", "pre"); break;
		case DocSimpleSect::Post:		push("simplesect", "kind", "post"); break;
		case DocSimpleSect::Invar:		push("simplesect", "kind", "invariant"); break;
		case DocSimpleSect::Remark:		push("simplesect", "kind", "remark"); break;
		case DocSimpleSect::Attention:	push("simplesect", "kind", "attention"); break;
		case DocSimpleSect::User:		push("simplesect", "kind", "par"); break;
		case DocSimpleSect::Rcs:		push("simplesect", "kind", "rcs"); break;
		case DocSimpleSect::Unknown:	break;
#endif
	}
}

void XmlDitaDocVisitor::visitPost(DocSimpleSect *s)
{
	if (m_hide) {
	  return;
	}	
	switch(s->type())
	{
		// Fall through
		case DocSimpleSect::Note:		
		case DocSimpleSect::Warning:	
		case DocSimpleSect::Remark:		
		case DocSimpleSect::Attention:	
			pop("note"); 
			break;
		case DocSimpleSect::Unknown:	
			break;
		default:
			if (!xmlElemStack.isEmpty() && xmlElemStack.peek().getElemName() == "p") {
				pop("p"); 
			}
			break;
	}
  //visitPostDefault("simplesect");
}

void XmlDitaDocVisitor::visitPre(DocTitle *)
{	
	if (!xmlElemStack.isEmpty() && xmlElemStack.peek().getElemName() == "concept") {
		visitPreDefault("title");
	} else {
		if (xmlElemStack.isEmpty() || xmlElemStack.peek().getElemName() != "p") {
			visitPreDefault("p");
		}
		visitPreDefault("b");
	}

}

void XmlDitaDocVisitor::visitPost(DocTitle *)
{
	if (xmlElemStack.peek().getElemName() == "title") {
		visitPostDefault("title");
	} else {
		visitPostDefault("b");
		if (!xmlElemStack.isEmpty() && xmlElemStack.peek().getElemName() == "p") {
			visitPostDefault("p");
		}
	}
}

void XmlDitaDocVisitor::visitPre(DocSimpleList *)
{
  visitPreDefault("ul");
}

void XmlDitaDocVisitor::visitPost(DocSimpleList *)
{
  visitPostDefault("ul");
}

void XmlDitaDocVisitor::visitPre(DocSimpleListItem *)
{
  visitPreDefault("li");
}

void XmlDitaDocVisitor::visitPost(DocSimpleListItem *) 
{
  visitPostDefault("li");
}

void XmlDitaDocVisitor::visitPre(DocSection *s)
{
	// Currently unsupported
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
	if (s->type()==DocHtmlList::Ordered) {
		visitPostDefault("ol"); 
	} else {
		visitPostDefault("ul");
	}
}

void XmlDitaDocVisitor::visitPre(DocHtmlListItem *)
{
  visitPreDefault("li");
}

void XmlDitaDocVisitor::visitPost(DocHtmlListItem *) 
{
  visitPostDefault("li");
}

void XmlDitaDocVisitor::visitPre(DocHtmlDescList *)
{
  visitPreDefault("dl");
}

void XmlDitaDocVisitor::visitPost(DocHtmlDescList *) 
{
  visitPostDefault("dl");
}

void XmlDitaDocVisitor::visitPre(DocHtmlDescTitle *)
{
	if (m_hide) {
	  return;
	}
	push("dlentry");
	push("dt");
	//push("varlistentry");
	//push("term");
}

void XmlDitaDocVisitor::visitPost(DocHtmlDescTitle *) 
{
	if (m_hide) {
	  return;
	}
	pop("dt");
	//pop("dlentry");
	// pop("term");
	// pop("varlistentry");
}

void XmlDitaDocVisitor::visitPre(DocHtmlDescData *)
{
  push("dd");
  //visitPreDefault("li");
}

void XmlDitaDocVisitor::visitPost(DocHtmlDescData *) 
{
  pop("dd");
  pop("dlentry");
  //visitPostDefault("li");  
}

void XmlDitaDocVisitor::visitPre(DocHtmlTable *t)
{
	if (m_hide) {
	  return;
	}
	push("simpletable");
#if 0
	AttributeMap attrs;
	QString vR, vC;
	vR.setNum(t->numRows());
	attrs["rows"] = vR;
	vC.setNum(t->numCols());
	attrs["cols"] = vC;
	push("table", attrs);
#endif
}

void XmlDitaDocVisitor::visitPost(DocHtmlTable *) 
{
	visitPostDefault("simpletable");
}

void XmlDitaDocVisitor::visitPre(DocHtmlRow *)
{
	// FIXME look ahead to first cell
	// if isHeading is true do
	// visitPreDefault("sthead");
	// else
	visitPreDefault("strow");
}

void XmlDitaDocVisitor::visitPost(DocHtmlRow *) 
{
  visitPostDefault("strow");
}

void XmlDitaDocVisitor::visitPre(DocHtmlCell *c)
{
	visitPreDefault("stentry");
#if 0
	if (m_hide) {
	  return;
	}
	if (c->isHeading()) {
	  push("entry", "thead", "yes");
	} else {
	  push("entry", "thead", "no");
	}
#endif
}

void XmlDitaDocVisitor::visitPost(DocHtmlCell *c) 
{
  visitPostDefault("stentry");
}

void XmlDitaDocVisitor::visitPre(DocHtmlCaption *)
{
  // Caption is unsupported
}

void XmlDitaDocVisitor::visitPost(DocHtmlCaption *) 
{
  // Caption is unsupported
}

void XmlDitaDocVisitor::visitPre(DocInternal *)
{
  //visitPreDefault("internal");
}

void XmlDitaDocVisitor::visitPost(DocInternal *) 
{
  //visitPostDefault("internal");
}

void XmlDitaDocVisitor::visitPre(DocHRef *href)
{
  push("xref", "href", href->url());
}

void XmlDitaDocVisitor::visitPost(DocHRef *) 
{
  visitPostDefault("xref");
}

void XmlDitaDocVisitor::visitPre(DocHtmlHeader *header)
{
	visitPreDefault("b");
#if 0
  QString hdgLevel;
  hdgLevel.setNum(header->level());
  push("heading", "level", hdgLevel);
#endif
}

void XmlDitaDocVisitor::visitPost(DocHtmlHeader *) 
{
  visitPostDefault("b");
}

void XmlDitaDocVisitor::visitPre(DocImage *img)
{
	// Currently unsupported
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
  //visitPostDefault("image");
}

void XmlDitaDocVisitor::visitPre(DocDotFile *df)
{
	// Currently unsupported
#if 0
	if (m_hide) {
	  return;
	}
	push("dotfile", "name", df->file());
#endif
}

void XmlDitaDocVisitor::visitPost(DocDotFile *) 
{
//  visitPostDefault("dotfile");
}

void XmlDitaDocVisitor::visitPre(DocLink *lnk)
{
	if (m_hide) {
	  return;
	}
	if (lnk->getDefinition() != 0) {
		startLink("", lnk->getDefinition()->qualifiedName(), "");
	} else {
		startLink(lnk->ref(),lnk->file(),lnk->anchor());
	}	
}

void XmlDitaDocVisitor::visitPost(DocLink *) 
{
	if (m_hide) {
	  return;
	}
	endLink();
}

void XmlDitaDocVisitor::visitPre(DocRef *ref)
{
	if (m_hide) {
	  return;
	}
	if (!ref->file().isEmpty()) {
		if (ref->getDefinition() != 0) {
			startLink("", ref->getDefinition()->qualifiedName(), "");
		} else {
			startLink(ref->ref(), ref->file(), ref->anchor());
		}	
	}
	if (!ref->hasLinkText()) {
	  write(ref->targetTitle());
	}
}

void XmlDitaDocVisitor::visitPost(DocRef *ref) 
{
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
	if (m_hide) {
	  return;
	}
	push("li", "id", ref->file()+"_1"+ref->anchor());
}

void XmlDitaDocVisitor::visitPost(DocSecRefItem *) 
{
  visitPostDefault("li");
}

void XmlDitaDocVisitor::visitPre(DocSecRefList *)
{
  visitPreDefault("ul");
}

void XmlDitaDocVisitor::visitPost(DocSecRefList *) 
{
  visitPostDefault("ul");
}

void XmlDitaDocVisitor::visitPre(DocParamSect *s)
{
	m_insideParamlist = TRUE;
	if (m_hide) {
	  return;
	}
	switch(s->type()) {
		case DocParamSect::Param: 
			push("paraml", "class", "param"); 
			break;
		case DocParamSect::RetVal: 
			push("paraml", "class", "retval"); 
			break;
		case DocParamSect::Exception: 
			push("paraml", "class", "exception"); 
			break;
		case DocParamSect::TemplateParam: 
			push("paraml", "class", "templateparam"); 
			break;
		default:
		  ASSERT(0);
	}
}

void XmlDitaDocVisitor::visitPost(DocParamSect *)
{
	visitPostDefault("paraml");
	m_insideParamlist = FALSE;
}

void XmlDitaDocVisitor::visitPre(DocParamList *pl)
{
	if (m_hide) {
	  return;
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
		paramDict.insert(currParam, new QString(""));
	}

#if 0
	push("parameteritem");
	push("parameternamelist");
	QListIterator<DocNode> li(pl->parameters());
	DocNode *param;
	for (li.toFirst();(param=li.current());++li) {
		AttributeMap attrs;
		if (pl->direction() != DocParamSect::Unspecified) {
			if (pl->direction() == DocParamSect::In) {
				attrs["direction"] = "in";
			} else if (pl->direction() == DocParamSect::Out) {
				attrs["direction"] = "out";
			} else if (pl->direction() == DocParamSect::InOut) {
				attrs["direction"] = "inout";
			} else{
				ASSERT(0);
			}
		}
		push("parametername", attrs);
		if (param->kind() == DocNode::Kind_Word)
		{
		  visit((DocWord*)param); 		
		}
		else if (param->kind() == DocNode::Kind_LinkedWord)
		{
		  visit((DocLinkedWord*)param); 
		}
		pop("parametername");
	}
	pop("parameternamelist");
	push("parameterdescription");
#endif
}

void XmlDitaDocVisitor::visitPost(DocParamList *)
{
	if (m_hide) {
	  return;
	}
	pop("parameterdescription");
	pop("parameteritem");
}

void XmlDitaDocVisitor::visitPre(DocXRefItem *x)
{
	if (m_hide) {
	  return;
	}
	// \deprecated commands result in DocXRefItem
	// with "deprecated" as the filename
	if (x->file() == "deprecated"){
		// Fall through to start new paragraph for deprecated description
	}else
		{
		push("xref", "id", x->file()+"_1"+x->anchor());
		write(x->title());
	}
#if 0
	push("xrefsect", "id", x->file()+"_1"+x->anchor());
	pushpop("xreftitle", x->title());
	push("xrefdescription");
#endif
}

void XmlDitaDocVisitor::visitPost(DocXRefItem *)
{
	if (m_hide) {
	  return;
	}
	// An xref will be top of stack unless the current 
	// DocXRefItem was caused by a \deprecated command
	if (!xmlElemStack.isEmpty() && xmlElemStack.peek().getElemName() == "xref") {
		pop("xref");
	}
	
#if 0
	pop("xrefdescription");
	pop("xrefsect");
#endif
}

void XmlDitaDocVisitor::visitPre(DocInternalRef *ref)
{
	if (m_hide) {
	  return;
	}
	startLink(0, ref->file(), ref->anchor());
}

void XmlDitaDocVisitor::visitPost(DocInternalRef *) 
{
	if (m_hide) {
	  return;
	}
	endLink();
	write(" ");
}

void XmlDitaDocVisitor::visitPre(DocCopy *c)
{
	// Currently unsupported
#if 0
	if (m_hide) {
	  return;
	}
	push("copydoc", "link", c->link());
#endif
}

void XmlDitaDocVisitor::visitPost(DocCopy *)
{
//	visitPostDefault("copydoc");
}

void XmlDitaDocVisitor::visitPre(DocText *)
{}

void XmlDitaDocVisitor::visitPost(DocText *)
{}

void XmlDitaDocVisitor::startXref(const QString &href,const QString &text)
{
	push("xref", "href", href);
	write(text);	
}

void XmlDitaDocVisitor::endXref()
{
	pop("xref");
}

void XmlDitaDocVisitor::startLink(const QString &ref,const QString &file,const QString &anchor)
{
  AttributeMap refAttrs;
  if (!anchor.isEmpty()) {
	  refAttrs["href"] = file+"_1"+anchor;
  } else {
	  refAttrs["href"] = file;
  }
  push("xref", refAttrs);
#if 0
  AttributeMap refAttrs;
  if (!anchor.isEmpty()) {
	  refAttrs["refid"] = file+"_1"+anchor;
	  refAttrs["kindref"] = "member";
  } else {
	  refAttrs["refid"] = file;
	  refAttrs["kindref"] = "compound";
  }
  if (!ref.isEmpty()) {
	  refAttrs["external"] = ref;
  }
  push("ref", refAttrs);
#endif
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


void XmlDitaDocVisitor::write(const QString &string)
{
	if (m_insideParamlist) {
		// TODO: Review the use of paramDict as I think that there is a
		// memory leak here [PaulRo 2010-01-20]
		QString *pStr = paramDict.find(currParam);
		if (pStr) {
			paramDict.replace(currParam, new QString(*pStr + string));
		} else {
			paramDict.replace(currParam, new QString(string));
		}
	} else {
		xmlStream << string;
	}
}

void XmlDitaDocVisitor::push(const QString &tagName)
{
	if (m_insideParamlist) {
		// TODO
	} else {
		xmlElemStack.push(tagName);
	}
}

void XmlDitaDocVisitor::push(const QString &tagName, const QString &key, const QString &value)
{
	if (m_insideParamlist) {
		// TODO
	} else {
		xmlElemStack.push(tagName, key, value);
	}
}

void XmlDitaDocVisitor::push(const QString &tagName, AttributeMap &map)
{
	if (m_insideParamlist) {
		// TODO
	} else {
		xmlElemStack.push(tagName, map);
	}
}

void XmlDitaDocVisitor::pop(const QString &tagName)
{
	if (m_insideParamlist) {
		// TODO
	} else {
		xmlElemStack.pop(tagName);
	}
}

void XmlDitaDocVisitor::pushpop(const QString &tagName)
{
	if (m_insideParamlist) {
		// TODO
	} else {
		xmlElemStack.pushpop(tagName);
	}
}

void XmlDitaDocVisitor::pushpop(const QString &tagName, const QString &text)
{
	if (m_insideParamlist) {
		paramDict.replace(currParam, new QString(*paramDict[currParam] + text));
	} else {
		xmlElemStack.pushpop(tagName, text);
	}
}

const QString XmlDitaDocVisitor::query(const QString &paramName) const
{
	if (paramDict.find(paramName)) {
		return *paramDict[paramName];
	} else {
		// TODO positional option
		return "";
	}
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

