
#ifndef _XMLDITATRACE_H
#define _XMLDITATRACE_H

/** \file This contains trace macros for DITA XMl processing */

// TODO DITA_DOC_VISITOR_TRACE won't work on all DocNode objects, probably most have:
// op->type() and op->test().data() though.
#ifdef DITA_TRACE
#define DITA_DOC_VISITOR_TRACE(fn,op) printf("DITA_DOC_VISITOR: %s(): type=%d first=%d, last=%d text=`%s'\n", \
fn,op->type(),op->isFirst(),op->isLast(),op->text().data());
#else
#define DITA_DOC_VISITOR_TRACE(fn,op)
#endif


#endif //_XMLDITATRACE_H