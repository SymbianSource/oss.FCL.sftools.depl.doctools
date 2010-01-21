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

#ifndef XMLDITAELEMENTPREFIX_H
#define XMLDITAELEMENTPREFIX_H

#include "definition.h"
#include "classdef.h"
#include "memberdef.h"
#include "namespacedef.h"
#include "filedef.h"
#include <qstring.h>
#include <qdict.h>

/** Class that handles mappings between file name extensions and the
source code language. This also handles mappings from source code language
to DITA element prefix e.g. <cxxClassDef> and references to DITA elements
such as <cxxclass>
*/
class DITAElementPrefix
{
public:
	DITAElementPrefix();
	QString srcLang(const QString& fileName);
	QString srcLang(const Definition *d);
	QString memberKind(const MemberDef *md);
	QString memberKind(const ClassDef *cd);
	QString elemPrefix(const QString& fileName);
	QString elemPrefix(const Definition *d);
	QString elemPrefix(const MemberDef *md, bool includeKind);
	QString elemPrefix(const ClassDef *cd, bool includeKind);
	QString elemPrefix(const NamespaceDef *nd, bool includeKind);
	QString elemPrefix(const FileDef *nd, bool includeKind);
	QString elemReference(const MemberDef *md);
	QString elemReference(const ClassDef *cd);
	// DITA Map references to the 'big four'
	QString ditaMapRef(const MemberDef *md);
	QString ditaMapRef(const ClassDef *cd);
	QString ditaMapRef(const NamespaceDef *nd);
	QString ditaMapRef(const FileDef *fd);
	// DOCTYPE stuff
	QString doctypeOwner(const QString &srcLang);
	// DOCTYPE for the 'big four'
	QString doctypeStr(const MemberDef *md);
	QString doctypeStr(const ClassDef *cd);
	QString doctypeStr(const NamespaceDef *nd);
	QString doctypeStr(const FileDef *fd);
	QString doctypeStr(const QString &srcLang, const QString &ePref, const QString &sInsert);
private:
	QDict<char> m_extToLang;
	QDict<char> m_langToPrefix;
	QDict<char> m_langToDoctypeOwner;
private:
	QString capFirstLetter(const QString& in) const;
	QString doctypeStr(const Definition *d, const QString &ePref, const QString& sInsert);
private:
	// Private cctor and op=
	DITAElementPrefix (const DITAElementPrefix &rhs);
	DITAElementPrefix& operator=(const DITAElementPrefix &rhs);
};

#endif // XMLDITAELEMENTPREFIX_H
