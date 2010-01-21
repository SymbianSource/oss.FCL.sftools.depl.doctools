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

#ifndef XMLDITACODEGENERATOR_H
#define XMLDITACODEGENERATOR_H

#include "outputgen.h"
//#include "definition.h"
#include "config.h"
//#include "xmlditalink.h"
#include "xmlwriter.h"

/* TODO: Decide how to implement this in DITA.
Do we use the elements in:
Chapter 14 Programming Elements
of the DITA Version 1.1 Language Specification?
e.g. <sep> <kwd> etc.?
*/
/** Macro to remove implementaiton code from the XMLDITACodeGenerator
If defined as 0 then all the implementation 
*/
#define DITA_CODE_GENERATE 0
class XMLDITACodeGenerator : public CodeOutputInterface
{
public:
	XMLDITACodeGenerator(XmlStream &t);
	virtual ~XMLDITACodeGenerator();
	void codify(const char *text);
    void writeCodeLink(const char *ref,const char *file,
                       const char *anchor,const char *name,
                       const char *tooltip);
	void startCodeLine();
	void endCodeLine();
	void startCodeAnchor(const char *id);
	void endCodeAnchor();
	void startFontClass(const char *colorClass);
	void endFontClass();
	void writeCodeAnchor(const char *);
    void writeLineNumber(const char *extRef,const char *compId,
                         const char *anchorId,int l);
	void linkableSymbol(int, const char *,Definition *,Definition *);
    void finish();
  private:
    XmlStream &m_xs;
	XmlElementStack m_xes;
    QCString m_refId;
    QCString m_external;
    int m_lineNumber;
    bool m_isMemberRef;
    int col;
    bool m_insideCodeLine;
    bool m_normalHLNeedStartTag;
    bool m_insideSpecialHL;
	void writeXMLDITACodeString(XmlStream &xt, const char *s, int &col);
};

#endif // XMLDITACODEGENERATOR_H
