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
This file contains common macros etc that affect DITA generation.
*/

/** If 1 then the internal Doxygen ID is used as the value of the id attribute
otherwise another ID is used, for example the Fully Qualified name and that
may contain characters that are not acceptable as an XML ID
*/
#define USE_DOXYGEN_ID_AS_XML_ID 1

/** If 1 then the internal Doxygen ID is used to determine if a member is
a duplicate of one that has already been written. If 0 another technique
is used, for example the lookup name.
This only has an affect if Config_getBool("XML_DITA_OMIT_DUPLICATE_MEMBERS")
is True.
*/
#define USE_DOXYGEN_ID_AS_DUPLICATE_TEST 0

#undef DITA_TRACE
//#define DITA_TRACE
// If defined then the trace output (if any) is written as a comment in the XML
// Otherwise it appears on stdout.
//#undef DITA_TRACE_TO_XML
#define DITA_TRACE_TO_XML

#define DITA_SUPRESS_NAMESPACE_LINKS 1

// If set to 1 then the DumpDocBlockContents will be written to stdout.
#define DITA_DUMP_DOC_BLOCK_CONTENTS 0

#endif // XMLDITA_H
