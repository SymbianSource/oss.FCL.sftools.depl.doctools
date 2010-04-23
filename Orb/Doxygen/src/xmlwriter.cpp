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



#include "xmlwriter.h"
#include "message.h"
#include "xmldita.h"

char ILLEGAL_UNICODE_REPLACEMENT = ' ';
/******************** XmlStream ********************/
XmlStream::XmlStream(const QString &fileName, const QString &aEncoding, const QString &aStandalone, const QString &doctypeStr) : mFile(fileName), \
											mStreamP(0), \
											mElemStack(), \
											mInElement(false)
{
	mCanIndentList.setAutoDelete(true);
	mIsOpen = mFile.open(IO_WriteOnly);
	if (mIsOpen) {
		mStreamP = new QTextStream(&mFile);
		if (aEncoding == "UTF-8") {
			mStreamP->setEncoding(QTextStream::UnicodeUTF8);
		} else if(aEncoding == "Latin1") {
			mStreamP->setEncoding(QTextStream::Latin1);
		} else if(aEncoding == "ISO-8859-1") {
			mStreamP->setEncoding(QTextStream::Latin1);
		} else {
			// No specific encoding set
		}
		*mStreamP << "<?xml version='1.0' encoding='" << aEncoding << "' standalone='" << aStandalone << "'?>";
		if (doctypeStr.length() > 0) {
			*mStreamP << "\n<!DOCTYPE " << doctypeStr << ">";
		}
	} else {
		mStreamP = 0;
		err("Cannot open file %s for writing!\n", fileName.data());
	}
	// Allow output
	outputResume();
	/// Build text -> unicode map
	unicodeCharTable.insert("copy", "A9");
	unicodeCharTable.insert("trade", "2122");
	unicodeCharTable.insert("reg", "AE");
	unicodeCharTable.insert("lsquo", "60");
	unicodeCharTable.insert("rsquo", "B4");
	unicodeCharTable.insert("ldquo", "201C");
	unicodeCharTable.insert("rdquo", "201D");
	unicodeCharTable.insert("ndash", "2013");
	unicodeCharTable.insert("mdash", "2014");
	unicodeCharTable.insert("Auml", "C4");
	unicodeCharTable.insert("Euml", "CB");
	unicodeCharTable.insert("Iuml", "CF");
	unicodeCharTable.insert("Ouml", "F6");
	unicodeCharTable.insert("Uuml", "FC");
	unicodeCharTable.insert("Yuml", "178");
	unicodeCharTable.insert("auml", "E4");
	unicodeCharTable.insert("euml", "EB");
	unicodeCharTable.insert("iuml", "EF");
	unicodeCharTable.insert("ouml", "F6");
	unicodeCharTable.insert("uuml", "FC");
	unicodeCharTable.insert("yuml", "FF");
	unicodeCharTable.insert("Aacute", "C1");
	unicodeCharTable.insert("Eacute", "C9");
	unicodeCharTable.insert("Iacute", "CD");
	unicodeCharTable.insert("Oacute", "D3");
	unicodeCharTable.insert("Uacute", "DA");
	unicodeCharTable.insert("Yacute", "DD");
	unicodeCharTable.insert("aacute", "E1");
	unicodeCharTable.insert("eacute", "E9");
	unicodeCharTable.insert("iacute", "ED");
	unicodeCharTable.insert("oacute", "F3");
	unicodeCharTable.insert("uacute", "FA");
	unicodeCharTable.insert("yacute", "FD");
	unicodeCharTable.insert("Agrave", "C0");
	unicodeCharTable.insert("Egrave", "C8");
	unicodeCharTable.insert("Igrave", "CC");
	unicodeCharTable.insert("Ograve", "D2");
	unicodeCharTable.insert("Ugrave", "F9");
	unicodeCharTable.insert("agrave", "E0");
	unicodeCharTable.insert("egrave", "E8");
	unicodeCharTable.insert("igrave", "EC");
	unicodeCharTable.insert("ograve", "F2");
	unicodeCharTable.insert("ugrave", "F9");
	//unicodeCharTable.insert("ygrave", ""); In doxygen documentation but code unknown or doesn't exist
	unicodeCharTable.insert("Acirc", "C2");
	unicodeCharTable.insert("Ecirc", "CA");
	unicodeCharTable.insert("Icirc", "CE");
	unicodeCharTable.insert("Ocirc", "D4");
	unicodeCharTable.insert("Ucirc", "DB");
	unicodeCharTable.insert("acirc", "E2");
	unicodeCharTable.insert("ecirc", "EA");
	unicodeCharTable.insert("icirc", "EE");
	unicodeCharTable.insert("ocirc", "F4");
	unicodeCharTable.insert("ucirc", "FB");
	//unicodeCharTable.insert("ycirc", ""); In doxygen documentation but code unknown or doesn't exist
	unicodeCharTable.insert("Atilde", "C3");
	unicodeCharTable.insert("Ntilde", "D1");
	unicodeCharTable.insert("Otilde", "D5");
	unicodeCharTable.insert("atilde", "E3");
	unicodeCharTable.insert("ntilde", "F1");
	unicodeCharTable.insert("otilde", "F5");
	unicodeCharTable.insert("szlig", "DF");
	unicodeCharTable.insert("Ccedil", "C7");
	unicodeCharTable.insert("ccedil", "E7");
	unicodeCharTable.insert("Aring", "C5");
	unicodeCharTable.insert("aring", "E5");
	unicodeCharTable.insert("Oslash", "D8");
	unicodeCharTable.insert("oslash", "F8");
	unicodeCharTable.insert("nbsp", "A0");
	unicodeCharTable.insert("AElig", "C6");
	unicodeCharTable.insert("aelig", "E6");
	
}

void XmlStream::startElement(const QString& aElemName, const AttributeMap& aAttrs)
{
	if (mStreamP && mIsOpen && mCanWrite) {
		if (mInElement) {
			// Close existing element
			*mStreamP << ">";
		} else {
			mInElement = true;
		}
		indent();
		// Write element name
		*mStreamP << "<" << aElemName;
		// Attributes in sorted order
		AttributeMapIter it = aAttrs.begin();
		while (it != aAttrs.end()){
			QString attrVal = encodeText(it.data());
#ifdef DITA_OT_BUG_ATTRIBUTE_VALUE_HACK
			// DITA Open Toolkit error, it fails to re-encode files properly
			// Replace "&lt;" with "&amp;lt;"
			// Replace "&gt;" with "&amp;gt;"
			int fIdx = 0;
			QString toFind;
			QString toReplace;
			toFind = "&lt;";
			toReplace = "&amp;lt;";
			fIdx = attrVal.find(toFind, 0);
			while (fIdx != -1) {
				attrVal.replace(fIdx, toFind.length(), toReplace);
				fIdx = attrVal.find(toFind, 0);
			}
			toFind = "&gt;";
			toReplace = "&amp;gt;";
			fIdx = attrVal.find(toFind, 0);
			while (fIdx != -1) {
				attrVal.replace(fIdx, toFind.length(), toReplace);
				fIdx = attrVal.find(toFind, 0);
			}
#endif
			*mStreamP << " " << it.key() << "=\"" << attrVal << "\"";
			++it;
		}
		// Update internals
		mInElement = true;
		//mCanIndent = true;
		mElemStack.push(&aElemName);
		mCanIndentList.append(new bool(true));
	}
}

void XmlStream::characters(const QString& aText)
{
	// If this test was not here then if passed an empty string the stream
	// will end up writing <Element></Element> rather than <Element/>
	if (aText.length() > 0) {
		if (mStreamP && mIsOpen && mCanWrite) {
			closeElementDeclIfOpen();
			*mStreamP << encodeText(aText);
		}
		// Don't indent mixed content
		//mCanIndent = false;
		setLastIndent(false);
	}
#ifdef DITA_TRACE
#ifdef DITA_TRACE_TO_XML
	// Useful for assertion crashes where otherwise the buffer would be lost
	flush(*mStreamP);
#endif
#endif
}

void XmlStream::characters(char c)
{
	if (mStreamP && mIsOpen && mCanWrite) {
		closeElementDeclIfOpen();
		if (isLegalXmlChar(c)) {
			if (mustEncodeChar(c)) {
				*mStreamP << encodeChar(c);
			} else {
				*mStreamP << c;
			}
		} else {
			*mStreamP << ILLEGAL_UNICODE_REPLACEMENT;
		}
	}
	// Don't indent mixed content
	//mCanIndent = false;
	setLastIndent(false);
#ifdef DITA_TRACE
#ifdef DITA_TRACE_TO_XML
	// Useful for assertion crashes where otherwise the buffer would be lost
	flush(*mStreamP);
#endif
#endif
}

XmlStream& XmlStream::operator<<(const QCString& s)
{
    characters(s);
	return *this;
}

XmlStream& XmlStream::operator<<(const char* s)
{
    characters(s);
	return *this;
}

XmlStream& XmlStream::operator<<(char c)
{
    characters(c);
	return *this;
}

XmlStream& XmlStream::writeUnicode(const QCString& s)
{
	if (mStreamP && mIsOpen && mCanWrite) {
		closeElementDeclIfOpen();
		if (unicodeCharTable.find(s)) {
			*mStreamP << "&#x";
			*mStreamP << unicodeCharTable[s];
			*mStreamP << ";";
		} else {
			// Write a warning as a comment
			QString cmtTxt = "Can not write Unicode for Doxygen interpreted symbol: \"";
			cmtTxt += s;
			cmtTxt += "\"";
			comment(cmtTxt);
		}
	}
	// Don't indent mixed content
	//mCanIndent = false;
	setLastIndent(false);
	return *this;
}

void XmlStream::processingInstruction(const QString& aText)
{
	if (mStreamP && mIsOpen && mCanWrite) {
		closeElementDeclIfOpen();
		*mStreamP << "<?" << aText << "?>";
	}
	//mCanIndent = true;
}

void XmlStream::comment(const QString& aText)
{
	if (mStreamP && mIsOpen && mCanWrite) {
		closeElementDeclIfOpen();
		*mStreamP << "<!-- " << aText << " -->";
	}
	//mCanIndent = true;
}

void XmlStream::endElement(const QString& aElemName)
{
	if (mStreamP && mIsOpen && mCanWrite) {
		if (mInElement) {
			// Use minimal form
			*mStreamP << "/>";
			mInElement = false;
			mElemStack.pop();
		} else {
			indent(1);
			*mStreamP << "</" << *(mElemStack.pop()) << ">";
		}
	}
	mCanIndentList.removeLast();
}

void XmlStream::closeElementDeclIfOpen()
{
	if (mStreamP && mIsOpen && mCanWrite) {
		if (mInElement) {
			*mStreamP << ">";
			mInElement = false;
		}
	}
}

void XmlStream::indent(unsigned int aInitVal)
{
	if (mStreamP && mIsOpen && canIndent() && mCanWrite) {
		*mStreamP << XML_OUTPUT_ENDL;
		for (unsigned int i = aInitVal; i < mElemStack.count(); i++) {
			*mStreamP << XML_INDENT;
		}
	}
}

/** Returns 1 if the character is in the legal unicode range
See: http://www.w3.org/TR/REC-xml/#charsets
*/
inline bool XmlStream::isLegalXmlChar(QChar c) const
{
	ushort u = c.unicode();
	//printf("XmlStream::isLegalXmlChar() testing 0x%X\n", u);
	// This is what the code should be:
	/*
	bool result = (u == 0x09 || u == 0x0A || u == 0x0D || \
				((u >= 0x20) && (u <= 0xD7FF)) || \
				((u >= 0xE000) && (u <= 0xFFFD)) \
			);
	*/
	// An this is the kludge that prevents weird characters (e.g. 0xA0)
	// that appear in the source code from getting into the XML.
	bool result = (u == 0x09 || u == 0x0A || u == 0x0D || \
				((u >= 0x20) && (u <= 0x7F)) \
			);
	if (!result) {
		msg("XmlStream::isLegalXmlChar() rejecting 0x%X\n", u);
	}
	return result;
}

QString XmlStream::encodeText(const QString& aStr) const
{
	QCString result;
	//printf("XmlStream::encodeText() encoding \"%s\"\n", aStr.data());
	for (unsigned int i=0; i < aStr.length(); ++i) {
		if (isLegalXmlChar(aStr[i])) {
			char c = aStr[i];
			if (mustEncodeChar(c)) {
				result += encodeChar(c);
			} else {
				result += c;
			}
		} else {
			result += ILLEGAL_UNICODE_REPLACEMENT;
		}
  }
  return result;
}

/** Converts a char to a QString using XML entity transformaiton */
QString XmlStream::encodeChar(char c) const
{
	switch (c) {
		case '<': return QString("&lt;");	break;
		case '>': return QString("&gt;"); break;
		case '&': return QString("&amp;");  break;
		case '\'': return QString("&apos;"); break; 
		case '"': return QString("&quot;"); break;
		default:
			QString s;
			s += c;
			return s;
			break;
	}
}

/** Returns true if a char needs to be converted using XML entity transformaiton */
bool XmlStream::mustEncodeChar(char c) const
{
	switch (c) {
		// Note fall through
		case '<':
		case '>':
		case '&':
		case '\'':
		case '"':
			return true;
			break;
		default:
			break;
	}
	return false;
}

bool XmlStream::canIndent()
{
	bool *bP;
	for (bP = mCanIndentList.first(); bP != 0; bP = mCanIndentList.next()) {
		if (!*bP) {
			return false;
		}
	}
	return true;
}

void XmlStream::setLastIndent(bool theB)
{
	mCanIndentList.removeLast();
	mCanIndentList.append(new bool(theB));
}

/// Suspend output
void XmlStream::outputSuspend()
{
	mCanWrite = false;
}

/// Resume output
void XmlStream::outputResume()
{
	mCanWrite = true;
}

void XmlStream::close()
{
	if (mStreamP) {
		// Ignore mCanWrite
		outputResume();
		closeElementDeclIfOpen();
		while(mElemStack.count()){
			endElement(mElemStack[mElemStack.count()-1]);
		}
		// Delete the stream and close the file
		delete mStreamP;
		mStreamP = 0;
		mFile.close();
		mIsOpen = false;
	}
}


XmlStream::~XmlStream()
{
	try {
		close();
	}
	catch(...) {}
}
/******************** END: XmlStream ********************/

/******************** XmlElement ********************/
XmlElement::XmlElement(XmlStream& aStream, const QString& aElemName) : mStream(aStream), mElemName(aElemName)
{
	AttributeMap attrs;
	mStream.startElement(mElemName, attrs);
}

XmlElement::XmlElement(XmlStream& aStream, const QString& aElemName, const QString& aAttr, const QString& aAttrValue) : mStream(aStream), mElemName(aElemName)
{
	AttributeMap attrs;
	attrs[aAttr] = aAttrValue;
	mStream.startElement(mElemName, attrs);
}

XmlElement::XmlElement(XmlStream& aStream, const QString& aElemName, const QString& aAttr, char aAttrValue) : mStream(aStream), mElemName(aElemName)
{
	AttributeMap attrs;
	attrs[aAttr] = QChar(aAttrValue);
	mStream.startElement(mElemName, attrs);
}

XmlElement::XmlElement(XmlStream& aStream, const QString& aElemName, AttributeMap& aAttrs) : mStream(aStream), mElemName(aElemName)
{
	mStream.startElement(mElemName, aAttrs);
}

/*
// Parse an attribute string of the form "attr_0=value_0 attr_1=value_1"
XmlElement::XmlElement(XmlStream& aStream, const QString& aElemName, const QString& aAttrString) : mStream(aStream), mElemName(aElemName)
{
	AttributeMap attrMap;
	QString myStr = aAttrString.simplifyWhiteSpace();
	int s = 0; // Index of start of attr
	int e = 0; // Index of '='
	int v = 0; // Index of end of value
	while (s < (int) myStr.length()) {
		e = s;
		v = s;
		e = myStr.find('=', s);
		if (e == -1) {
			break;
		}
		v = myStr.find(' ', s);
		if (v == -1) {
			v = myStr.length();
		}
		attrMap[myStr.mid(s, e-s)] = myStr.mid(e+1, v-(e+1));
		s = v+1;
	}
	mStream.startElement(mElemName, attrMap);
}
*/

XmlElement::~XmlElement()
{
	try {
		mStream.endElement(mElemName);
	}
	catch(...) {}
}
/******************** END: XmlElement ********************/

/******************** XmlElementStack ********************/
XmlElementStack::XmlElementStack(XmlStream& aStream) : mStream(aStream)
{
}

void XmlElementStack::push(const QString& aElementName)
{
	mElemStack.push(new XmlElement(mStream, aElementName));
}

void XmlElementStack::push(const QString& aElementName, const QString& aAttr, const QString& aAttrValue)
{
	mElemStack.push(new XmlElement(mStream, aElementName, aAttr, aAttrValue));
}

void XmlElementStack::push(const QString& aElementName, AttributeMap& aAttrs)
{
	mElemStack.push(new XmlElement(mStream, aElementName, aAttrs));
}

void XmlElementStack::pop(const QString &aElementName)
{
	XmlElement *pElem = mElemStack.pop();
	if (pElem->getElemName() != aElementName) {
		err(pElem->getElemName() + " is not equal to " + aElementName +"\n");
	}
	ASSERT(pElem->getElemName() == aElementName);
	delete pElem;
}

void XmlElementStack::pop()
{
	XmlElement *pElem = mElemStack.pop();
	delete pElem;
}

void XmlElementStack::pushpop(const QString &aElementName)
{
	mElemStack.push(new XmlElement(mStream, aElementName));
	pop(aElementName);
}

void XmlElementStack::pushpop(const QString &aElementName, const QString& aText)
{
	mElemStack.push(new XmlElement(mStream, aElementName));
	mStream.characters(aText);
	pop(aElementName);
}

bool XmlElementStack::isEmpty() const
{
	return mElemStack.isEmpty();
}

const XmlElement& XmlElementStack::peek() const 
{
	return *mElemStack.top();
}

void XmlElementStack::addAttribute(const QString &name, const QString &value)
{
	XmlElement *pElem = mElemStack.pop();
	QString elemenName = pElem->getElemName();
	delete pElem;
	XmlElement *elem = new XmlElement(mStream, elemenName, name, value);
	mElemStack.push(elem);
}

void XmlElementStack::close()
{
	while(mElemStack.count()){
		pop();
	}
}

XmlElementStack::~XmlElementStack()
{
	try {
		close();
	}
	catch(...) {}
}
/******************** END: XmlElementStack ********************/

