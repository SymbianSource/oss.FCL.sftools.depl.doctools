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

#ifndef XMLDITAXREFMAP_H
#define XMLDITAXREFMAP_H

#if USE_DOXYGEN_ID_AS_XML_ID ==0
#include <qmap.h>

typedef QMap<Definition *, QString> XrefMapT;

class XmlDitaXrefERemapDocVisitor : public DocVisitor
{
public:
	XmlDitaXrefERemapDocVisitor() : DocVisitor(DocVisitor_XML) {};
    //--------------------------------------
    // visitor functions for leaf nodes
    //--------------------------------------
    void visit(DocWord *) {}
    void visit(DocLinkedWord *w)
	{
		Definition *d = w->getDefinition();
		if (d) {
			m_XrefRemap.insert(d, QString(""));
		}
	}
    void visit(DocWhiteSpace *) {}
    void visit(DocSymbol *) {}
    void visit(DocURL *) {}
    void visit(DocLineBreak *) {}
    void visit(DocHorRuler *) {}
    void visit(DocStyleChange *) {}
    void visit(DocVerbatim *) {}
    void visit(DocAnchor *) {}
    void visit(DocInclude *) {}
    void visit(DocIncOperator *) {}
    void visit(DocFormula *) {}
    void visit(DocIndexEntry *) {}
    void visit(DocSimpleSectSep *) {}
    //--------------------------------------
    // visitor functions for compound nodes
    //--------------------------------------
    void visitPre(DocAutoList *) {}
    void visitPost(DocAutoList *) {}
    void visitPre(DocAutoListItem *) {}
    void visitPost(DocAutoListItem *) {}
	void visitPre(DocPara *) {}
    void visitPost(DocPara *) {}
    void visitPre(DocRoot *) {}
    void visitPost(DocRoot *) {}
    void visitPre(DocSimpleSect *) {}
    void visitPost(DocSimpleSect *) {}
    void visitPre(DocTitle *) {}
    void visitPost(DocTitle *) {}
    void visitPre(DocSimpleList *) {}
    void visitPost(DocSimpleList *) {}
    void visitPre(DocSimpleListItem *) {}
    void visitPost(DocSimpleListItem *) {}
    void visitPre(DocSection *) {}
    void visitPost(DocSection *) {}
    void visitPre(DocHtmlList *) {}
	void visitPost(DocHtmlList *) {}
    void visitPre(DocHtmlListItem *) {}
    void visitPost(DocHtmlListItem *) {}
    //void visitPre(DocHtmlPre *) {}
    //void visitPost(DocHtmlPre *) {}
    void visitPre(DocHtmlDescList *) {}
    void visitPost(DocHtmlDescList *) {}
    void visitPre(DocHtmlDescTitle *) {}
    void visitPost(DocHtmlDescTitle *) {}
    void visitPre(DocHtmlDescData *) {}
    void visitPost(DocHtmlDescData *) {}
    void visitPre(DocHtmlTable *) {}
    void visitPost(DocHtmlTable *) {}
    void visitPre(DocHtmlRow *) {}
	void visitPost(DocHtmlRow *) {}
    void visitPre(DocHtmlCell *) {}
    void visitPost(DocHtmlCell *) {}
    void visitPre(DocHtmlCaption *) {}
    void visitPost(DocHtmlCaption *) {}
    void visitPre(DocInternal *) {}
    void visitPost(DocInternal *) {}
    void visitPre(DocHRef *) {}
    void visitPost(DocHRef *) {}
    void visitPre(DocHtmlHeader *) {}
    void visitPost(DocHtmlHeader *) {}
    void visitPre(DocImage *) {}
    void visitPost(DocImage *) {}
    void visitPre(DocDotFile *) {}
    void visitPost(DocDotFile *) {}
    void visitPre(DocLink *w)
	{
		Definition *d = w->getDefinition();
		if (d) {
			m_XrefRemap.insert(d, QString(""));
		}
	}
    void visitPost(DocLink *) {}
    void visitPre(DocRef *w)
	{
		Definition *d = w->getDefinition();
		if (d) {
			m_XrefRemap.insert(d, QString(""));
		}
	}
    void visitPost(DocRef *) {}
    void visitPre(DocSecRefItem *) {}
    void visitPost(DocSecRefItem *) {}
    void visitPre(DocSecRefList *) {}
    void visitPost(DocSecRefList *) {}
    //void visitPre(DocLanguage *) {}
    //void visitPost(DocLanguage *) {}
    void visitPre(DocParamSect *) {}
    void visitPost(DocParamSect *) {}
    void visitPre(DocParamList *) {}
    void visitPost(DocParamList *) {}
    void visitPre(DocXRefItem *) {}
    void visitPost(DocXRefItem *) {}
    void visitPre(DocInternalRef *w)
	{
		Definition *d = w->getDefinition();
		if (d) {
			m_XrefRemap.insert(d, QString(""));
		}
	}
    void visitPost(DocInternalRef *) {}
    void visitPre(DocCopy *) {}
    void visitPost(DocCopy *) {}
    void visitPre(DocText *) {}
    void visitPost(DocText *) {}

	virtual ~XmlDitaXrefERemapDocVisitor() {}
//  private:
	XrefMapT m_XrefRemap;
 };

#endif //USE_DOXYGEN_ID_AS_XML_ID ==0

#endif // XMLDITAXREFMAP_H


