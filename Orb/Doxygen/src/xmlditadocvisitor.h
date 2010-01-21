
#ifndef _XMLDITADOCVISITOR_H
#define _XMLDITADOCVISITOR_H

#include "docvisitor.h"
#include "xmlwriter.h"
#include "xmlditatrace.h"
#include <qstack.h>
#include <qcstring.h>
#include <qmap.h>
#include <qdict.h>


class QTextStream;
class CodeOutputInterface;
class QString;

/*! @brief Concrete visitor implementation for XML output. */
class XmlDitaDocVisitor : public DocVisitor
{
  public:
    XmlDitaDocVisitor(XmlStream &s,CodeOutputInterface &ci);
    
    //--------------------------------------
    // visitor functions for leaf nodes
    //--------------------------------------
    
    void visit(DocWord *);
    void visit(DocLinkedWord *);
    void visit(DocWhiteSpace *);
    void visit(DocSymbol *);
    void visit(DocURL *);
    void visit(DocLineBreak *);
    void visit(DocHorRuler *);
    void visit(DocStyleChange *);
    void visit(DocVerbatim *);
    void visit(DocAnchor *);
    void visit(DocInclude *);
    void visit(DocIncOperator *);
    void visit(DocFormula *);
    void visit(DocIndexEntry *);
    void visit(DocSimpleSectSep *);

    //--------------------------------------
    // visitor functions for compound nodes
    //--------------------------------------
    
    void visitPre(DocAutoList *);
    void visitPost(DocAutoList *);
    void visitPre(DocAutoListItem *);
    void visitPost(DocAutoListItem *);
    void visitPre(DocPara *) ;
    void visitPost(DocPara *);
    void visitPre(DocRoot *);
    void visitPost(DocRoot *);
    void visitPre(DocSimpleSect *);
    void visitPost(DocSimpleSect *);
    void visitPre(DocTitle *);
    void visitPost(DocTitle *);
    void visitPre(DocSimpleList *);
    void visitPost(DocSimpleList *);
    void visitPre(DocSimpleListItem *);
    void visitPost(DocSimpleListItem *);
    void visitPre(DocSection *);
    void visitPost(DocSection *);
    void visitPre(DocHtmlList *);
    void visitPost(DocHtmlList *) ;
    void visitPre(DocHtmlListItem *);
    void visitPost(DocHtmlListItem *);
    //void visitPre(DocHtmlPre *);
    //void visitPost(DocHtmlPre *);
    void visitPre(DocHtmlDescList *);
    void visitPost(DocHtmlDescList *);
    void visitPre(DocHtmlDescTitle *);
    void visitPost(DocHtmlDescTitle *);
    void visitPre(DocHtmlDescData *);
    void visitPost(DocHtmlDescData *);
    void visitPre(DocHtmlTable *);
    void visitPost(DocHtmlTable *);
    void visitPre(DocHtmlRow *);
    void visitPost(DocHtmlRow *) ;
    void visitPre(DocHtmlCell *);
    void visitPost(DocHtmlCell *);
    void visitPre(DocHtmlCaption *);
    void visitPost(DocHtmlCaption *);
    void visitPre(DocInternal *);
    void visitPost(DocInternal *);
    void visitPre(DocHRef *);
    void visitPost(DocHRef *);
    void visitPre(DocHtmlHeader *);
    void visitPost(DocHtmlHeader *);
    void visitPre(DocImage *);
    void visitPost(DocImage *);
    void visitPre(DocDotFile *);
    void visitPost(DocDotFile *);
    void visitPre(DocLink *);
    void visitPost(DocLink *);
    void visitPre(DocRef *);
    void visitPost(DocRef *);
    void visitPre(DocSecRefItem *);
    void visitPost(DocSecRefItem *);
    void visitPre(DocSecRefList *);
    void visitPost(DocSecRefList *);
    //void visitPre(DocLanguage *);
    //void visitPost(DocLanguage *);
    void visitPre(DocParamSect *);
    void visitPost(DocParamSect *);
    void visitPre(DocParamList *);
    void visitPost(DocParamList *);
    void visitPre(DocXRefItem *);
    void visitPost(DocXRefItem *);
    void visitPre(DocInternalRef *);
    void visitPost(DocInternalRef *);
    void visitPre(DocCopy *);
    void visitPost(DocCopy *);
    void visitPre(DocText *);
    void visitPost(DocText *);

	virtual ~XmlDitaDocVisitor() {}

	const QString query(const QString &paramName) const;
	QDictIterator<QString> queryIterator()
	{
		return QDictIterator<QString>(paramDict);
	}
  private:

    //--------------------------------------
    // helper functions 
    //--------------------------------------
    
    void filter(const char *str);
    void startLink(const QString &ref,const QString &file,
                   const QString &anchor);
    void endLink();

	void write(const QString &string);
	void push(const QString &tagName);
	void push(const QString &tagName, const QString &key, const QString &value);
	void push(const QString &tagName, AttributeMap &map);
	void pop(const QString &tagName);
	void pushpop(const QString &tagName);
	void pushpop(const QString &tagName, const QString &text);	

    void pushEnabled();
    void popEnabled();
	// Default pop of a single element
	void visitPreDefault(const QString &elem);
	// Default pop of a single element
	void visitPostDefault(const QString &elem);

	void startXref(const QString &href,const QString &text);
	void endXref();
    //--------------------------------------
    // state variables
    //--------------------------------------
	XmlStream& xmlStream;
	XmlElementStack xmlElemStack;
    CodeOutputInterface &m_ci;
    bool m_insidePre;
    bool m_hide;
    QStack<bool> m_enabled;
    QCString m_langExt;
	bool m_insideParamlist;
	QMap<int, QString> paramMap;
	QDict<QString> paramDict;
	QString currParam;
};

#endif //_XMLDITADOCVISITOR_H
