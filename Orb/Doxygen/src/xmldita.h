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

#ifndef XMLDITA_H
#define XMLDITA_H

/** @file
This file contains common macros etc that affect DITA generation. For example
macros 
*/

/** If 1 then the internal Doxygen ID is used as the value of the id attribute
otherwise another ID is used, for example the Fully Qualified name and that
may contain characters that are not acceptable as an XML ID
*/
#define USE_DOXYGEN_ID_AS_XML_ID 1

//#define DITA_TRACE
#undef DITA_TRACE
// If defined then the trace output (if any) is written as a comment in the XML
// Otherwise it appears on stdout.
#define DITA_TRACE_TO_XML

#define DITA_OT_BUG_ATTRIBUTE_VALUE_HACK

#define DITA_SUPRESS_NAMESPACE_LINKS 1

#endif // XMLDITA_H
