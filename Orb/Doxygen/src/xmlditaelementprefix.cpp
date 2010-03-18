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
#include "xmlditaelementprefix.h"

// Version to use in the DOCTYPE declaration
// Should match regex: v(\d+)\.(\d+)\.(\d+)(\S*)
const char *DOCTYPE_VERSION = "v0.5.0";

DITAElementPrefix::DITAElementPrefix()
{
	//QDict<char> m_extToLang;
	//QDict<char> m_langToPrefix;
	// NOTE: Keys must be in lowercase as the extension will be
	// coerced to lowercase before matching
	// NOTE: Value is case sensitive and must match the key of m_langToPrefix
	// C/C++ languages - our primary concern - we treat C as C++ for the moment
	// NOTE: This is very similar to initDefaultExtensionMapping() in util.h/util.cpp
	// TODO: Respect extension/language mapping in config file
	// TODO: Have list of supported languages in DITA e.g. isSupported(Definition*);
	// so that callers can decide to supress output for unsupported languages
	m_extToLang.insert(".h",     "C++");
	m_extToLang.insert(".c",     "C++");
	m_extToLang.insert(".cpp",   "C++");
	m_extToLang.insert(".cc",    "C++");
	m_extToLang.insert(".cp",    "C++");
	m_extToLang.insert(".cxx",   "C++");
	m_extToLang.insert(".inl",   "C++");
	m_extToLang.insert(".cia",   "C++");
	m_extToLang.insert(".hrh",   "C++");
	m_extToLang.insert(".s",     "C++");
	// Other languages
	m_extToLang.insert(".idl",   "IDL"); 
	m_extToLang.insert(".ddl",   "IDL"); 
	m_extToLang.insert(".odl",   "IDL"); 
	m_extToLang.insert(".java",  "Java");
	m_extToLang.insert(".as",    "JavaScript"); 
	m_extToLang.insert(".js",    "JavaScript");
	m_extToLang.insert(".cs",    "C Sharp");
	m_extToLang.insert(".d",     "D");
	m_extToLang.insert(".php",   "PHP"); 
	m_extToLang.insert(".php4",  "PHP");
	m_extToLang.insert(".php5",  "PHP");
	m_extToLang.insert(".inc",   "PHP");
	m_extToLang.insert(".phtml", "PHP");
	m_extToLang.insert(".m",     "Objective C");
	m_extToLang.insert(".M",     "Objective C");
	m_extToLang.insert(".mm",    "Objective C");
	m_extToLang.insert(".py",    "Python");
	m_extToLang.insert(".f",     "Fortran");
	m_extToLang.insert(".f90",   "Fortran");
	m_extToLang.insert(".vhd",   "VHDL");
	m_extToLang.insert(".vhdl",  "VHDL");
	// Default Language
	m_defaultLanguage = "C++";
	//
	// Now load the language to element prefix, case sensitve all round.
	// However the class behavior is that if there is no entry then the prefix is the
	// language in lower case with spaces removed i.e. implicitly "C Sharp" -> "csharp"
	//
	m_langToPrefix.insert("C++", "cxx");
	// Map of language to the owner of the DOCTYPE
	m_langToDoctypeOwner.insert("C++", "NOKIA");
	m_langToDoctypeOwner.insert("Java", "IBM");
}

QString DITAElementPrefix::srcLang(const QString &fileName)
{
	QString retStr;
	int i = fileName.findRev('.');
	QFileInfo fInfo(fileName);
	//QString ext = fileName.right(fileName.length() - i).lower();
	QString ext = fInfo.extension();
	if (ext.length() > 0 && m_extToLang.find(ext)) {
		retStr = QString(m_extToLang[ext]);
	} else {
		// WTF?
		//retStr = "_" + ext + "_";
		retStr = m_defaultLanguage;
	}
	//printf("DITAElementPrefix::srcLang file \"%s\" extension \"%s\" gets \"%s\"\n", fileName.data(), ext.data(), retStr.data());
	return retStr;
}

QString DITAElementPrefix::elemPrefix(const QString &srcLang)
{
	char *p = m_langToPrefix[srcLang];
	if (p) {
		return QString(p);
	}
	// Fall back to returning the suppied argument but in lower case and
	// with spaces removed
	QString retStr;
	for (uint i = 0; i < srcLang.length(); ++i) {
		if (srcLang[i] != " ") {
			retStr.append(srcLang[i]);
		}
	}
	return retStr.lower();
}

QString DITAElementPrefix::srcLang(const Definition *d)
{
	QCString myFileName = d->getDefFileName();
	return srcLang(myFileName);
}

QString DITAElementPrefix::memberKind(const MemberDef *md)
{
	// Get the kind, make lower case and capitalise the first letter
	// Special case turn "enumvalue" to "Enumerator"
	// [ISO/IEC 9899:1999 (E) 6.7.2.2 Enumeration specifiers]
	if (md->memberTypeName() == "enumvalue") {
		return QString("Enumerator");
	}
	return capFirstLetter(md->memberTypeName());
}

QString DITAElementPrefix::memberKind(const ClassDef *cd)
{
	return capFirstLetter(cd->compoundTypeString());
}

/** Return a string that is the input lowercased then first letter capitalised */
QString DITAElementPrefix::capFirstLetter(const QString& in) const
{
	if (in.length() == 0) {
		return in.upper();
	}
	QString myStr(in.lower());
	QString myPref(myStr.left(1).upper());
	QString mySuff(myStr.remove(0, 1));
	return myPref + mySuff;
}

QString DITAElementPrefix::elemPrefix(const Definition *d)
{
	QCString myFileName = d->getDefFileName();
	return elemPrefix(srcLang(myFileName));
}

QString DITAElementPrefix::elemPrefix(const MemberDef *md, bool includeKind)
{
	QCString myFileName = md->getDefFileName();
	if (includeKind) {
		return elemPrefix(srcLang(myFileName)) + memberKind(md);
	}
	return elemPrefix(srcLang(myFileName));
}

QString DITAElementPrefix::elemPrefix(const ClassDef *cd, bool includeKind)
{
	QCString myFileName = cd->getDefFileName();
	if (includeKind) {
		// Get the kind and capitalise the first letter
		return elemPrefix(srcLang(myFileName)) + capFirstLetter(cd->compoundTypeString());
	}
	return elemPrefix(srcLang(myFileName));
}

QString DITAElementPrefix::elemPrefix(const NamespaceDef *nd, bool includeKind)
{
	QCString myFileName = nd->getDefFileName();
	if (includeKind) {
		return elemPrefix(srcLang(myFileName)) + "Namespace";
	}
	return elemPrefix(srcLang(myFileName));
}

QString DITAElementPrefix::elemPrefix(const FileDef *fd, bool includeKind)
{
	QCString myFileName = fd->getDefFileName();
	if (includeKind) {
		return elemPrefix(srcLang(myFileName)) + "File";
	}
	return elemPrefix(srcLang(myFileName));
}

/** Return a string that can be use as a element name that refers to the MemberDef */
QString DITAElementPrefix::elemReference(const MemberDef *md)
{
	return elemPrefix(md, true);
}

/** Return a string that can be use as a element name that refers to the ClassDef */
QString DITAElementPrefix::elemReference(const ClassDef *cd)
{
	return elemPrefix(cd, true);
}

// DITA Map references to the 'big four'
QString DITAElementPrefix::ditaMapRef(const MemberDef *md)
{
	return elemPrefix(md, true)+"Ref";
}

QString DITAElementPrefix::ditaMapRef(const ClassDef *cd)
{
	return elemPrefix(cd, true)+"Ref";
}

QString DITAElementPrefix::ditaMapRef(const NamespaceDef *nd)
{
	return elemPrefix(nd, true)+"Ref";
}

QString DITAElementPrefix::ditaMapRef(const FileDef *fd)
{
	return elemPrefix(fd, true)+"Ref";
}


/* Returns the DOCTYPE owner from the source code language or "???" */
QString DITAElementPrefix::doctypeOwner(const QString &srcLang)
{
	char *p = m_langToDoctypeOwner[srcLang];
	if (p) {
		return QString(p);
	}
	return QString("???");
}

QString DITAElementPrefix::doctypeStr(const QString &srcLang, const QString &ePref, const QString &sInsert)
{
	QString retVal = ePref;
	retVal += " PUBLIC \"-//";
	retVal += doctypeOwner(srcLang);
	retVal += "//DTD DITA ";
	retVal += srcLang;
	retVal += " API ";
	retVal += sInsert;
	retVal += " Reference Type ";
	retVal += DOCTYPE_VERSION;
	retVal += "//EN\" \"dtd/";
	retVal += ePref;
	retVal += ".dtd\" ";
	return retVal;
}

QString DITAElementPrefix::doctypeStr(const Definition *d, const QString &ePref, const QString &sInsert)
{
	return doctypeStr(srcLang(d), ePref, sInsert);
}
/** Return a string that can be use as a DOCTYPE for the XML for the ClassDef */
QString DITAElementPrefix::doctypeStr(const MemberDef *md)
{
	return doctypeStr(md, elemPrefix(md, true), capFirstLetter(md->memberTypeName()));
}

/** Return a string that can be use as a DOCTYPE for the XML for the MemberDef */
QString DITAElementPrefix::doctypeStr(const ClassDef *cd)
{
	return doctypeStr(cd, elemPrefix(cd, true), capFirstLetter(cd->compoundTypeString()));
}

/** Return a string that can be use as a DOCTYPE for the XML for the Namespace */
QString DITAElementPrefix::doctypeStr(const NamespaceDef *nd)
{
	return doctypeStr(nd, elemPrefix(nd, true), "Namespace");
}

/** Return a string that can be use as a DOCTYPE for the XML for the File */
QString DITAElementPrefix::doctypeStr(const FileDef *fd)
{
	return doctypeStr(fd, elemPrefix(fd, true), "File");
}

