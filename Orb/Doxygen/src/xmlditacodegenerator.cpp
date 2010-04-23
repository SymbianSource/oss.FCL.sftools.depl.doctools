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
#include "xmlditacodegenerator.h"

XMLDITACodeGenerator::XMLDITACodeGenerator(XmlStream &t) : m_xs(t),
															m_xes(t),
															m_lineNumber(-1),
															m_insideCodeLine(FALSE),
															m_normalHLNeedStartTag(TRUE),
															m_insideSpecialHL(FALSE)
{
#if DITA_CODE_GENERATE
#endif
}

XMLDITACodeGenerator::~XMLDITACodeGenerator()
{
#if DITA_CODE_GENERATE
#endif
}

void XMLDITACodeGenerator::codify(const char *text)
{
#if DITA_CODE_GENERATE
	if (m_insideCodeLine && !m_insideSpecialHL && m_normalHLNeedStartTag) {
		m_xes.push("highlight", "class", "normal");
		m_normalHLNeedStartTag=FALSE;
	}
	writeXMLDITACodeString(m_xs, text, col);
#endif
}

void XMLDITACodeGenerator::writeCodeLink(const char *ref,const char *file,
                   const char *anchor,const char *name,
                   const char *tooltip) 
{
#if DITA_CODE_GENERATE
	if (m_insideCodeLine && !m_insideSpecialHL && m_normalHLNeedStartTag) {
		m_xes.push("highlight", "class", "normal");
		m_normalHLNeedStartTag=FALSE;
	}
	writeXMLDITALink(m_xs, ref, file, anchor, name, tooltip);
	col += strlen(name);
#endif
}

void XMLDITACodeGenerator::startCodeLine()
{
#if DITA_CODE_GENERATE
	AttributeMap codeAttrs;
	if (m_lineNumber!=-1) {
		QString lineNum;
		lineNum.setNum(m_lineNumber);
		codeAttrs["lineno"] = lineNum;
		if (!m_refId.isEmpty()) {
			codeAttrs["refid"] = m_refId;
			if (m_isMemberRef) {
				codeAttrs["refkind"] = "member";
			} else {
				codeAttrs["refkind"] = "compound";
			}
		}
		if (!m_external.isEmpty()) {
			codeAttrs["external"] = m_external;
		}
	}
	m_xes.push("codeline", codeAttrs);
	m_insideCodeLine = TRUE;
	col = 0;
#endif
}

void XMLDITACodeGenerator::endCodeLine() {
#if DITA_CODE_GENERATE
	if (!m_insideSpecialHL && !m_normalHLNeedStartTag) {
		m_xes.pop("highlight");
		m_normalHLNeedStartTag = TRUE;
	}
	m_xes.pop("codeline");
	m_lineNumber = -1;
	m_refId.resize(0);
	m_external.resize(0);
	m_insideCodeLine = FALSE;
#endif
}

void XMLDITACodeGenerator::startCodeAnchor(const char *id)
{
#if DITA_CODE_GENERATE
	if (m_insideCodeLine && !m_insideSpecialHL && m_normalHLNeedStartTag) {
		m_xes.push("highlight", "class", "normal");
		m_normalHLNeedStartTag = FALSE;
	}
	m_xes.push("anchor", "id", id);
#endif
}

void XMLDITACodeGenerator::endCodeAnchor()
{
#if DITA_CODE_GENERATE
	m_xes.pop("anchor");
#endif
}

void XMLDITACodeGenerator::startFontClass(const char *colorClass)
{
#if DITA_CODE_GENERATE
	if (m_insideCodeLine && !m_insideSpecialHL && !m_normalHLNeedStartTag) {
		m_xes.pop("highlight");
		m_normalHLNeedStartTag=TRUE;
	}
	m_xes.push("highlight", "class", colorClass );
	m_insideSpecialHL = TRUE;
#endif
}

void XMLDITACodeGenerator::endFontClass()
{
#if DITA_CODE_GENERATE
	m_xes.pop("highlight");
	m_insideSpecialHL = FALSE;
#endif
}

void XMLDITACodeGenerator::writeLineNumber(const char *extRef,const char *compId,
                     const char *anchorId,int l)
{
#if DITA_CODE_GENERATE
	// we remember the information provided here to use it 
	// at the <codeline> start tag.
	m_lineNumber = l;
	if (compId) {
		m_refId=compId;
		if (anchorId) {
			m_refId += (QCString)"_1"+anchorId;
		}
		m_isMemberRef = anchorId!=0;
		if (extRef) {
			m_external=extRef;
		}
	}
#endif
}

void XMLDITACodeGenerator::finish()
{
#if DITA_CODE_GENERATE
	if (m_insideCodeLine) {
		endCodeLine();
	}
#endif
}

void XMLDITACodeGenerator::writeXMLDITACodeString(XmlStream &xt, const char *s, int &col)
{
#if DITA_CODE_GENERATE
	char c;
	while ((c=*s++)) {
		switch(c) {
			case '\t':  { 
				int spacesToNextTabStop = Config_getInt("TAB_SIZE") - (col % Config_getInt("TAB_SIZE")); 
				col += spacesToNextTabStop;
				while (spacesToNextTabStop--) {
					XmlElement(xt, "sp");
				}
				break;
			}
			case ' ':
				XmlElement(xt, "sp");
				col++; 
				break;
			default:
				xt << c;
				col++;
				break;
		}
	} 
#endif
}

void XMLDITACodeGenerator::linkableSymbol(int, const char *,Definition *,Definition *)
{
#if DITA_CODE_GENERATE
#endif
}

void XMLDITACodeGenerator::writeCodeAnchor(const char *)
{
#if DITA_CODE_GENERATE
#endif
}

