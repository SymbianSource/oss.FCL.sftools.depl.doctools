
#ifndef _XMLDITATRACE_H
#define _XMLDITATRACE_H

/** \file This contains trace macros for DITA XML processing */

#include "xmldita.h"

// DITA_DOC_VISITOR_TRACE will work on all DocNode objects.
#ifdef DITA_TRACE
//#define DITA_DOC_VISITOR_TRACE(fn,op) printf("DITA_DOC_VISITOR: %s(): type=%d first=%d, last=%d text=`%s'\n", \
//fn,op->type(),op->isFirst(),op->isLast(),op->text().data());
#ifdef DITA_TRACE_TO_XML
#define DITA_DOC_VISITOR_TRACE(fn,pNode) xmlStream.comment(QString(fn));
#define DITA_DOC_VISITOR_TRACE_NOARG(fn) xmlStream.comment(QString(fn));
#else
#define DITA_DOC_VISITOR_TRACE(fn,pNode) printf("DITA_DOC_VISITOR: `%s': kind=%d node=0x%X, parent=0x%X\n", \
	fn, pNode->kind(), pNode,pNode->parent());
#define DITA_DOC_VISITOR_TRACE_NOARG(fn) printf("DITA_DOC_VISITOR: `%s'\n", fn);
#endif
#else
#define DITA_DOC_VISITOR_TRACE(fn,op)
#define DITA_DOC_VISITOR_TRACE_NOARG(fn)
#endif


#endif //_XMLDITATRACE_H