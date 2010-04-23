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


#ifndef _XMLWRITER_H
#define _XMLWRITER_H

#include <qdir.h>
#include <qfile.h>
#include <qtextstream.h>
#include <qmap.h>
#include <qdict.h>
#include <qstack.h>

typedef QMap<QString, QString> AttributeMap;
typedef QMapConstIterator<QString, QString> AttributeMapIter;

static QString XML_INDENT("\t");
static QString XML_OUTPUT_ENDL("\n");

// TODO: If the output file fails to open then write to an internal string that can be
// accessed by the caller after they call close(). This might be useful for internal
// XML snippets.

/**
Class that handles writing to an XML file. It guarentees well-formedness,
handles the encoding of PCDATA and indents the output.

Individual elements are created as objects, they are written to the file on
creation and closed when the element is destroyed.
*/
class XmlStream
{
	friend class XmlElement;
public:
	/// Create an XML stream that writes to a file with the given encoding
	XmlStream(const QString &fileName,
				const QString &aEncoding="UTF-8",
				const QString &aStandalone="no",
				const QString &doctypeStr="");
	/// Returns true of the file tha tthis stream is writing to is currently open.
	bool isOpen() const { return mIsOpen; }
	/// Write PCDATA to the output file, entities will be translated
	void characters(const QString &aText);
	void characters(char c);
	/// Write a processing instruction to the output file.
	void processingInstruction(const QString &aText);
	/// Write a comment to the output file.
	void comment(const QString &aText);
	/// Output operator overloading, these equate to calling characters()
	XmlStream& operator<<(const QCString &s);
	XmlStream& operator<<(const char *s);
	XmlStream& operator<<(char s);
	/// Write a unicode character to the stream
	XmlStream& writeUnicode(const QCString &s);
	/// Close the XML file (if open), this will flush any unclosed elements
	void close();
	/// Get the file name
	QString getFileName() const { return mFile.name(); }
	/// Suspend and resume output
	void outputSuspend();
	void outputResume();
	/// Destructor, this will call close()
	~XmlStream();
private:
	QDict<char> unicodeCharTable;
	/// Write out the start of element and register that element name on the stack
	void startElement(const QString &aElemName, const AttributeMap &aAttrs);
	/// Write out the end of element and remove that element name on the stack
	void endElement(const QString &aElemName);
	void closeElementDeclIfOpen();
	void indent(unsigned int aInitVal=0);
	inline bool isLegalXmlChar(QChar c) const;
	QString encodeText(const QString &aStr) const;
	QString encodeChar(char c) const;
	bool mustEncodeChar(char c) const;
	bool canIndent();
	void setLastIndent(bool theB);
private:
	QFile mFile;
	QTextStream *mStreamP;
	QStack<QString> mElemStack;
	QList<bool> mCanIndentList;
	bool mInElement;
	//bool mCanIndent;
	bool mIsOpen;
	bool mCanWrite;
private:
	// Private cctor and op=
	XmlStream (const XmlStream &rhs);
	XmlStream& operator=(const XmlStream &rhs);
};

/**
XmlElement

Usage example:
@code
// Start an XML file
XmlStream t(fileName);
if (!t.isOpen()) {
  err("Cannot open file %s for writing!\n", fileName.data());
  return;
}
// Create and persist a root element with no attributes
XmlElement elemRoot(t, QString("root"), AttributeMap());
// Note the use of {} that causes elem to go out of scope an thus
// its destructor will be called so closing the element
{
	// Create and persist a root element with attributes
	// First create the attributes
	AttributeMap attrs;
	attrs["attr_1"]	= "value_1";
	attrs["attr_2"]	= "value_2";
	// Create the element
	XmlElement elem(t, "Element", attrs);
	// Write some text
	t.characters("Some stuff");
	// Now elem is going out of scope
}
// Open and close and element
XmlElement(t, "OpenClose");
// Open and close and element with one attribute
XmlElement(t, "WhatsForDinner", "spam", "eggs");
// t goes out of scope and will close the file
@endcode

The result is:
@verbatim
<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<root>
	<Element attr_1="value_1" attr_2="value_2">Some stuff</Element>
	<OpenClose/>
	<WhatsForDinner spam="eggs"/>
</root>
@endverbatim

*/
class XmlElement
{
public:
	/// Constructor with no attributes
	XmlElement(XmlStream &aStream, const QString &aElemName);
	/// Constructor with one attribute
	XmlElement(XmlStream &aStream, const QString &aElemName, const QString &aAttr, const QString &aAttrValue);
	/// Constructor with one attribute the values of which is a char
	XmlElement(XmlStream &aStream, const QString &aElemName, const QString &aAttr, char aAttrValue);
	/// Constructor with any number of attributes
	XmlElement(XmlStream &aStream, const QString &aElemName, AttributeMap &aAttrs);
	const QString& getElemName() const { return mElemName; }
	/// Destructor, this closes the element on the stream
	~XmlElement();
private:
	XmlStream& mStream;
	QString mElemName;
private:
	// Private cctor and op=
	XmlElement (const XmlElement &rhs);
	XmlElement& operator=(const XmlElement &rhs);
};

/*
This can be used in the case that elements need to persist over scope.

So given this kind of code:
void XmlDocVisitor::visitPre(DocHtmlDescTitle *)
{
  if (m_hide) return;
  m_t << "<varlistentry><term>";
}

void XmlDocVisitor::visitPost(DocHtmlDescTitle *) 
{
  if (m_hide) return;
  m_t << "</term></varlistentry>\n";
}

It can be replaced by this (assuming XmlDocVisitor has a member XmlElementStack m_es;):
void XmlDocVisitor::visitPre(DocHtmlDescTitle *)
{
  if (m_hide) return;
  m_es.push("varlistentry", AttributeMap());
  m_es.push("term", AttributeMap());
}

void XmlDocVisitor::visitPost(DocHtmlDescTitle *) 
{
  if (m_hide) return;
  m_es.pop();
  m_es.pop();
}

*/
class XmlElementStack
{
public:
	XmlElementStack(XmlStream &aStream);
	/// Push element with no attributes
	void push(const QString &aElemName);
	/// Constructor with one attribute
	void push(const QString &aElemName, const QString &aAttr, const QString &aAttrValue);
	/// Push element with any number of attributes
	void push(const QString &aElementName, AttributeMap &aAttrs);
	/// Method that will check the element name matches
	void pop(const QString &aElementName);
	/// Push and pop an element with no attributes
	void pushpop(const QString &aElemName);
	/// Push and pop an element with no attributes but with some content
	void pushpop(const QString &aElemName, const QString &aText);
	/// Add attribute to item currently on top of the stack
	void addAttribute(const QString &name, const QString &value);
	/// Return a reference to the top of the stack. The stack is not modified.
	const XmlElement& peek() const;
	/// Return true if the stack is empty
	bool isEmpty() const;
	void close();
	~XmlElementStack();
private:
	XmlStream& mStream;
	QStack<XmlElement> mElemStack;
private:
	// Private cctor and op=
	XmlElementStack (const XmlElementStack &rhs);
	XmlElementStack& operator=(const XmlElementStack &rhs);
	// Used by destructor
	void pop();
};

#endif // _XMLWRITER_H
