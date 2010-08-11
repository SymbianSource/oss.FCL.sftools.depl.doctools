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

#ifndef XMLPARAMMAP_H
#define XMLPARAMMAP_H
#include "xmldita.h"
#include <qmap.h>
#include <qstring.h>

/** Used for extracting parameter descriptions */
typedef QMap<QString, QString> ParamDescriptionMap;

/** A structure that is used to extract documetation for paramaters, template parameters
and return value froma documentation (comment) block. This is used by the DITA doc visitor
the DITA generator.
*/
typedef struct DocBlockContents {
	ParamDescriptionMap paramMap;
	ParamDescriptionMap tparamMap;
	QString returnDoc;
} DocBlockContentsType;

void DumpDocBlockContents(const DocBlockContentsType& theBlock);

#endif // XMLPARAMMAP_H


