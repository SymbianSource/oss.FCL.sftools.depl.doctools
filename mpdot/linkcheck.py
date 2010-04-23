# Copyright (c) 2007-2010 Nokia Corporation and/or its subsidiary(-ies) All rights reserved.
# This component and the accompanying materials are made available under the terms of the License 
# "Eclipse Public License v1.0" which accompanies this distribution, 
# and is available at the URL "http://www.eclipse.org/legal/epl-v10.html".
#
# Initial Contributors:
# Nokia Corporation - initial contribution.
#
# Contributors:
#
# Description:
# Checks links in DITA XML and reports issues.
"""
Created on 12 Feb 2010

@author: p2ross

Definitions
===========
Doctype
-------
See: http://www.w3.org/TR/2008/REC-xml-20081126/#dt-root
Note: this is sometimes called the Doctype because of http://www.w3.org/TR/2008/REC-xml-20081126/#vc-roottype

ID
--
The value of the 'id' attribute of an element.

Root ID
-------
The value of the 'id' attribute of the root element.
Note: A development would allow differently named attributes provided that they
were ID types. See http://www.w3.org/TR/2008/REC-xml-20081126/#sec-attribute-types
for validity constraints for ID types.

Reference
---------
The value of the href attribute of an element.

Map
---
An XML file whose root element name is 'map' or ends with 'Map'.   

Topic
-----
An XML file that is not a Map.

Lonely topic
------------
A topic whose root ID is not referenced by any map. 

Lonely map
----------
A map whose root ID is not referenced by any map. 

Map Cycle
---------
A sequence of map references whose members are not unique.

"""

import os
import unittest
import sys
import logging
import pprint
import fnmatch
import re
import urllib
import time
from optparse import OptionParser, check_choice
try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree
import urlparse
import multiprocessing
# used for DitaFileObj persistence
import shelve

__version__ = '0.1.5'

class ExceptionLinkCheck(Exception):
    pass

class CountDict(dict):
    """Dictionary with a default value of 0 for unknown keys."""
    def __getitem__(self, key):
        if key not in self: 
            self[key] = 0
        return self.get(key)

# Matches stuff like: GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E
RE_GUID = re.compile(r'GUID-[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}', re.IGNORECASE)

# Of the form {integer_error_code : (format_string, num_args), ...}
PROBLEM_CODE_FORMAT = {
    # 'id_syntax'
    100 : ('Character \'#\' not allowed in id="%s"', 1),
    101 : ('NMTOKEN character \'%s\' not allowed in id="%s"', 2),
    102 : ('GUID specification does not match id="%s"', 1),
    # 'ref_syntax'
    200 : ('Multiple \'#\' not allowed in reference "%s"', 1),
    201 : ('Reference element "%s" is missing href=... attribute', 1),
    202 : ('URL has missing type/format in reference "%s"', 1),
    203 : ('GUID specification does not match file reference "%s"', 1),
    204 : ('GUID specification does not match fragment reference "%s"', 1),
    # 'ref'
    300 : ('Can not resolve URI "%s"', 1),
    # 'file'
    400 : ('Failed to open: "%s"', 1),
    401 : ('Multiple id="%s"', 1),
    402 : ('No id attribute on root element', 0),
    403 : ('Root ID in cycle: %s', 1),
    404 : ('Can not parse: "%s"', 1),
    410 : ('Can not resolve reference to file "%s"', 1),
    411 : ('Can resolve reference to file "%s" but not to fragment "%s"', 2),
    412 : ('Referencing element "%s" does not match target root element "%s"', 2),
    413 : ('Referencing element "%s" does not match target element "%s" for id="%s"', 3),
    414 : ('topicref element with format="ditamap" does not match target root element "%s"', 1),
    415 : ('topicref to <map> does not have format="ditamap" but format="%s"', 1),
    416 : ('topicref element type="%s" does not match target root element "%s"', 2),
    417 : ('topicref element type="%s" does not match target element "%s" for id="%s"', 3),
    418 : ('Unknown referencing element "%s" does not match target root element "%s"', 2),
    419 : ('Unknown referencing element "%s" does not match target element "%s" for id="%s"', 3),
    # 'file_set'
    500 : ('Not a directory: %s', 1),
    501 : ('Duplicate root id="%s" in files: %s', 2), 
    #502 : ('Can not resolve reference to "%s"', 1),
    #503 : ('Reference type "%s" does not match target type "%s" for id="%s"', 3),
    504 : ('Duplicate file path: "%s"', 1),
    505 : ('Duplicate id="%s" in files: %s', 2),
    # 'topic_set'
    600 : ('Topic id="%s" is not referenced by any map', 1), 
    # 'map_set'
    700 : ('More than one top level map exists: %s', 1),  
    701 : ('Maps "%s" are in a a cycle.', 1),
}

GENERIC_STRING = '...'
PRINT_WIDTH = 75

def genericStringForErrorCode(ec):
    assert(PROBLEM_CODE_FORMAT.has_key(ec))
    f, c = PROBLEM_CODE_FORMAT[ec]
    if c == 0:
        return f
    return f % ((GENERIC_STRING,) * c)

def writeGenericStringsForErrorCodes(s=sys.stdout):
    s.write(' All Error Codes '.center(PRINT_WIDTH, '='))
    s.write('\n')
    s.write('%4s  %s\n' % ('Code', 'Error'))
    s.write('%4s  %s\n' % ('----', '-----'))
    ecS = PROBLEM_CODE_FORMAT.keys()
    ecS.sort()
    for ec in ecS:
        s.write('%4d  %s\n' % (ec, genericStringForErrorCode(ec)))
    s.write('='*PRINT_WIDTH)
    s.write('\n\n')

def normalisePath(thePath):
    # TODO: How come this does not work?
    #return os.path.abspath(thePath)
    return os.path.abspath(thePath).replace('\\', '/')

FNMATCH_PATTERNS = ['*.xml', '*.dita', '*.ditamap']
FNMATCH_STRING = ' '.join(FNMATCH_PATTERNS)

# These elements descend from topic/xref so can be treated as referencing elements
XREF_DESCENDENTS = set(
    (
        # From the api specialisation
        'apiRelation',
        'apiBaseClassifier',
        'apiOtherClassifier',
        'apiOperationClassifier',
        'apiValueClassifier',
        # From the C++ specialisation
        'cxxfile',
        'cxxclass',
        'cxxstruct',
        'cxxunion',
        'cxxfunction',
        'cxxdefine',
        'cxxtypedef',
        'cxxvariable',
        'cxxenumeration',
        'cxxClassBaseClass',
        'cxxClassBaseStruct',
        'cxxClassBaseUnion',
        'cxxClassNestedClass',
        'cxxClassNestedStruct',
        'cxxClassNestedUnion',
        'cxxClassEnumerationInherited',
        'cxxClassEnumeratorInherited',
        'cxxClassFunctionInherited',
        'cxxClassVariableInherited',
        'cxxDefineReimplemented',
        'cxxEnumerationReimplemented',
        'cxxFunctionReimplemented',
        'cxxStructBaseClass',
        'cxxStructBaseStruct',
        'cxxStructBaseUnion',
        'cxxStructNestedClass',
        'cxxStructNestedStruct',
        'cxxStructNestedUnion',
        'cxxStructEnumerationInherited',
        'cxxStructEnumeratorInherited',
        'cxxStructFunctionInherited',
        'cxxStructVariableInherited',
        'cxxTypedefReimplemented',
        'cxxUnionBaseClass',
        'cxxUnionBaseStruct',
        'cxxUnionBaseUnion',
        'cxxUnionNestedClass',
        'cxxUnionNestedStruct',
        'cxxUnionNestedUnion',
        'cxxUnionEnumerationInherited',
        'cxxUnionFunctionInherited',
        'cxxUnionVariableInherited',
        'cxxVariableReimplemented',
    )
)

class UrlAccessCache(object):
    def __init__(self):
        # {URL : True/False, ...}
        self._cache = {}
        
    def clear(self):
        self._cache = {}
        
    def canAccess(self, theUrl):
        if not self._cache.has_key(theUrl):
            try:
                u = urllib.urlopen(theUrl)#, data, proxies)
                u.read()
                self._cache[theUrl] = True
                logging.debug('URL: %s  for %s' % (True, theUrl))
            except IOError:
                self._cache[theUrl] = False
                logging.debug('URL: %s for %s' % (False, theUrl))
        return self._cache[theUrl]

GlobalUrlCache = UrlAccessCache()
 
class DitaLinkCheckBase(object):
    """Base class that holds some common functionality."""
    def __init__(self, theIdentity):#=None):
        self.__identity = theIdentity
        # Set of error strings, lazily evaluated
        self._errS = None
    
    @property
    def identity(self):
        return self.__identity
    
    def __cmp__(self, other):
        assert(self.identity is not None)
        assert(other.identity is not None)
        return cmp(self.identity, other.identity)

    def __eq__(self, other):
        assert(self.identity is not None)
        assert(other.identity is not None)
        return self.identity == other.identity

    def __hash__(self):
        assert(self.identity is not None)
        return hash(self.identity)
    
    def __str__(self):
        return str(self.__identity)

    def debugDump(self, s=sys.stdout, prefix=''):
        """Dump of IR for debug purposes."""
        raise NotImplementedError
    
    def addError(self, errCode, argTuple):
        assert(errCode in PROBLEM_CODE_FORMAT.keys()), 'No error code: %s' % errCode
        assert(PROBLEM_CODE_FORMAT[errCode][1] == len(argTuple)), \
            'Length missmatch for error code %d: %d != %d for %s' \
            % (errCode, PROBLEM_CODE_FORMAT[errCode][1], len(argTuple), str(argTuple))
        if self._errS is None:
            self._errS = {}
        try:
            self._errS[errCode].add(argTuple)
        except KeyError:
            self._errS[errCode] = set((argTuple,))

    def errStrings(self, generic, theFilter):
        """Return a sorted list of error messages without duplicates."""
        if self._errS is not None:
            mySet = set()
            for ec in self._errS.keys():
                if theFilter is None or ec in theFilter:
                    assert(ec in PROBLEM_CODE_FORMAT.keys())
                    for tu in self._errS[ec]:
                        if generic:
                            mySet.add(genericStringForErrorCode(ec))
                        else:
                            f, c = PROBLEM_CODE_FORMAT[ec]
                            assert(len(tu) == c)
                            mySet.add(f % tu)
            l = list(mySet)
            l.sort()
            return l
        return []
    
    def updateErrorCount(self, theMap):
        """Updates a map of {error_code, : count, ...}.
        Overridden for file and file set."""
        if self._errS is not None:
            for e in self._errS.keys():
                theMap[e] += len(self._errS[e])
    
    def writeErrors(self, isGeneric, theFilter, theStream=sys.stdout):
        """Can be overridden in child classes to recurse into
        their data structures."""
        theStream.write('\n'.join(self.errStrings(isGeneric, theFilter)))
    
class DitaId(DitaLinkCheckBase):
    """Represents a node with an id."""
    def __init__(self, theN):
        assert(theN.get('id', None) is not None)
        super(DitaId, self).__init__(theN.get('id', None))
        self._elem = theN.tag
        if '#' in self.id:
            self.addError(100, (self.id,))
        # TODO: NMTOKENS
    
    @property
    def elem(self):
        return self._elem

    @property
    def id(self):
        return self.identity

    def checkGuid(self):
        """optionally applies additional checks for GUID requirements."""
        if RE_GUID.match(self.id) is None:
            self.addError(102, (self.id,))

    def debugDump(self, s=sys.stdout, prefix=''):
        """Dump of IR for debug purposes."""
        s.write('%sID:  <%s id="%s" />\n' % (prefix, self.elem, self.id))
        
class DitaRef(DitaLinkCheckBase):
    """Represents a reference node."""
    def __init__(self, theN):
        self._elem = theN.tag
        self._href = theN.get('href', None)
        super(DitaRef, self).__init__('%s %s' % (self._elem, self._href))
        # This is used when figuring out of the target is the correct element
        # e.g. in Vanilla DITA
        # <topicref href="batcaring.dita" type="task"></topicref>
        self._refType = theN.get('type', None)
        # Format attribute, this can be format="ditamap"
        self._format = theN.get('format', None)
        if self._href is None:
            self.addError(201, (self._elem,))
            self._url = None
        else:
            self._url = urlparse.urlparse(self._href)
            if '#' in self._url.fragment:
                self.addError(200, (self._href,))

    @property
    def elem(self):
        return self._elem

    @property
    def href(self):
        """The value of the href attribute."""
        return self._href
    
    @property
    def refType(self):
        """The value of the type attribute."""
        return self._refType
    
    @property
    def format(self):
        """The value of the format attribute."""
        return self._format
    
    @property
    def path(self):
        """The value of the path part of the href attribute."""
        return self._url.path
        
    @property
    def fragment(self):
        """The value of the fragment part of the href attribute."""
        return self._url.fragment
        
    @property
    def scheme(self):
        """The URI scheme e.g. 'http' or '' if no scheme."""
        return self._url.scheme
    
    def fileFragment(self, theRefFile):                               
        """The absolute path of the file and the fragment identifier or (None, None)."""
        if self.scheme not in ('', 'file'):
            return (None, None)
        if len(self.path) == 0:
            myPath = theRefFile
        else:
            myPath = os.path.join(os.path.dirname(theRefFile), self.path)
        return normalisePath(myPath), self.fragment
    
    def checkGuid(self):
        """optionally applies additional checks for GUID requirements."""
        if RE_GUID.match(self.path) is None:
            self.addError(203, (self.path,))
        if RE_GUID.match(self.fragment) is None:
            self.addError(204, (self.fragment,))                

    def checkUrl(self):
        if self.scheme:
            myU = urlparse.urlunparse(self._url)
            if not GlobalUrlCache.canAccess(myU):
                self.addError(300, (myU,))

    def debugDump(self, s=sys.stdout, prefix=''):
        """Dump of IR for debug purposes."""
        s.write('%sREF: <%s href="%s" />\n' % (prefix, self.elem, self._href))

class DitaFileObj(DitaLinkCheckBase):
    """Base class for a DITA topic or map."""
    def __init__(self, theFileObj, theFileName=None):
        """Initialiser with a file object and a file path"""
        #print '\nDitaFileObj(%s, %s)' % (theFileObj, theFileName)
        if theFileName is not None:
            super(DitaFileObj, self).__init__(normalisePath(theFileName))
        elif theFileObj is not None:
            super(DitaFileObj, self).__init__(theFileObj.name)
        else:
            super(DitaFileObj, self).__init__(None)
        self._rootId = None
        self._doctype = None
        # Sets of class DitaId
        self._idS = set()
        self._dupeIdS = set()
        # Set of class DitaRef
        self._xrefS = set()
        # Ouptut control
        self._hasWritten = False
        # Size of input
        try:
            self._bytes = os.path.getsize(theFileName)
        except Exception:
            # Try as if a StringIO
            try:
                self._bytes = theFileObj.len
            except AttributeError:
                # Give up
                self._bytes = 0
        # Process the file object
        if theFileObj is not None:
            try:
                # TODO: use iterparse?
                theTree = etree.parse(theFileObj)
            except SyntaxError, err:
                self.addError(404, (str(err),))
            else:
                # Walk the tree
                for i, e in enumerate(theTree.getiterator()):
                    #print 'TRACE: e', e
                    # Element [0] is the root element
                    if i == 0:
                        assert(self._rootId is None)
                        assert(self._doctype is None)
                        self._doctype = e.tag
                        if e.get('id', None) is not None:
                            self._rootId = DitaId(e)
                            self._addId(self._rootId)
                        else:
                            self.addError(402, ())
                    else:
                        # NOTE: Elements with id attributes can also have href
                        # attributes. For example a <topicref> in a <bookmap>
                        # Thus these tests are not exclusive
                        if e.get('id', None) is not None:
                            self._addId(DitaId(e))
                        if e.get('href', None) is not None:
                            # TODO: Do we limit ourselves to only a certain set of elements?
                            self._xrefS.add(DitaRef(e))
        else:
            self.addError(400, (self.identity,))
    
    def _addId(self, theId):
        #print 'TRACE: adding %s' % theId
        #print 'TRACE: self._idS %s' % self._idS
        if theId in self._idS:
            # Remove from self._idS
            #print 'TRACE: removing %s' % theId
            self._idS.remove(theId)
            self._dupeIdS.add(theId)
            self.addError(401, (theId.identity,))
        elif theId not in self._dupeIdS:
            self._idS.add(theId)
    
    @property
    def bytes(self):
        return self._bytes
    
    @property
    def doctype(self):
        return self._doctype
    
    @property
    def rootId(self):
        if self._rootId is not None:
            return self._rootId.id
    
    @property
    def isMap(self):
        return self.doctype == "map" \
        or self.doctype == 'bookmap' \
        or (self.doctype is not None and self.doctype.endswith('Map'))
    
    @property
    def idS(self):
        """The set of IDs."""
        return self._idS
    
    @property
    def refS(self):
        """The set of DitaRef objects."""
        return self._xrefS
    
    def idElemMap(self):
        """Returns a map {id : elem name, ...}."""
        retVal = {}
        for anId in self._idS:
            retVal[anId.id] = anId.elem
        return retVal
    
    def hasId(self, theString):
        for anId in self._idS:
            if theString == anId.id:
                return True
        return False

    def idElem(self, theString):
        for anId in self._idS:
            if theString == anId.id:
                return anId.elem
        return None

    def idObj(self, theString):
        for anId in self._idS:
            if theString == anId.id:
                return anId
        return None

    def updateErrorCount(self, theMap):
        """Updates a map of {error_code, : count, ...}."""
        if self._errS is not None:
            for e in self._errS.keys():
                theMap[e] += len(self._errS[e])
        for idObj in self.idS:
            idObj.updateErrorCount(theMap)
        for refObj in self.refS:
            refObj.updateErrorCount(theMap)
    
    def writeErrorList(self, theList, theSubHead='', theS=sys.stdout):
        if len(theList) > 0:
            theList.sort()
            if not self._hasWritten:
                theS.write('File: %s\n' % self.identity)
            self._hasWritten = True
            if len(theSubHead) > 0:
                theS.write('%s [%d]:\n' % (theSubHead, len(theList)))
            theS.write('\n'.join(theList))
            theS.write('\n')
    
    def writeErrors(self, isGeneric, theFilter, theStream=sys.stdout):
        """Writes out errors for me, my IDs and my Refs."""
        self._hasWritten = False
        self.writeErrorList(self.errStrings(isGeneric, theFilter), 'File errors:', theStream)
#===============================================================================
#        # Duplicate IDs
#        myList = (list(self._dupeIdS))
#        if len(myList):
#            self.writeErrorList(
#                    [i.identity for i in myList],
#                    'Duplicate ID',
#                    theStream)
#===============================================================================
        # Now IDs
        myList = (list(self.idS))
        myList.sort()
        for anId in myList:
            self.writeErrorList(anId.errStrings(isGeneric, theFilter), 'ID=%s' % anId.identity, theStream)
        # Now Refs
        myList = (list(self._xrefS))
        myList.sort()
        for anId in myList:
            self.writeErrorList(anId.errStrings(isGeneric, theFilter), 'Ref=%s' % anId.identity, theStream)
        if self._hasWritten:
            theStream.write('\n')
    
    def debugDump(self, s=sys.stdout, prefix=''):
        """Dump of IR for debug purposes."""
        s.write('%sFile: %s\n' % (prefix, self.identity))
        for anId in self._idS:
            anId.debugDump(s, prefix=prefix+'  ')
        for aRef in self._xrefS:
            aRef.debugDump(s, prefix=prefix+'  ')
    
class DitaFilePath(DitaFileObj):
    """Base class for a DITA topic or map from the file system."""
    def __init__(self, theFilePath):
        """Initialiser with a file path"""
        try:
            f = open(theFilePath)
        except IOError:
            f = None
        #print 'DitaFilePath(%s)' % theFilePath
        super(DitaFilePath, self).__init__(f, theFilePath)
        if f is None:
            self.addError(400, (theFilePath,))
            
            
class DitaFileMapBase(object):
    """Base class for holding a map of {file path : class DitaFile, ...}
    Actual implementation can be in-memory or via a database e.g. the
    shelve module."""
    def keys(self):
        """Returns an unsorted list of keys in the map."""
        raise NotImplementedError()
    
    def has_key(self, thePath):
        """Return True if the key exists."""
        raise NotImplementedError()
    
    def remove(self, thePath):
        """Remove the entry corresponding to thePath, may raise KeyError."""
        raise NotImplementedError()
    
    def getDitaFileObj(self, thePath):
        """Return a DitaFileObj that corresponds to thePath, may raise KeyError."""
        raise NotImplementedError()
        
    def setDitaFileObj(self, thePath, theObj):
        """Load a DitaFileObj or update a mutated DitaFileObj."""
        raise NotImplementedError()
        
class DitaFileMapInMemory(DitaFileMapBase):
    """Holds map of {file path : class DitaFile, ...} in memory."""
    def __init__(self):
        # Map of {file path : class DitaFile, ...}
        self._fileMap = {}
    
    def keys(self):
        """Returns an unsorted list of keys in the map."""
        return self._fileMap.keys()
    
    def has_key(self, thePath):
        """Return True if the key exists."""
        return self._fileMap.has_key(thePath)
        
    def remove(self, thePath):
        """Remove the entry corresponding to thePath, may raise KeyError."""
        del self._fileMap[thePath]
    
    def getDitaFileObj(self, thePath):
        """Return a DitaFileObj that corresponds to thePath, may raise KeyError."""
        return self._fileMap[thePath]
        
    def setDitaFileObj(self, thePath, theObj):
        """Load a DitaFileObj or update a mutated DitaFileObj."""
        self._fileMap[thePath] = theObj
        
class DitaFileMapShelve(DitaFileMapBase):
    """Holds map of {file path : class DitaFile, ...} in a shelve database."""
    DBASE_FILENAME = 'linkchecker.dbase'
    def __init__(self):
        if os.path.exists(self.DBASE_FILENAME):
            os.remove(self.DBASE_FILENAME)
        self._db = shelve.open(self.DBASE_FILENAME)
        # Use this as a 'cache' as shelf.keys() is slow
        self._keys = set()
    
    def keys(self):
        """Returns an unsorted list of keys in the map."""
        return list(self._keys)
    
    def has_key(self, thePath):
        """Return True if the key exists."""
        return thePath in self._keys
        
    def remove(self, thePath):
        """Remove the entry corresponding to thePath, may raise KeyError."""
        del self._db[thePath]
        self._keys.remove(thePath)
    
    def getDitaFileObj(self, thePath):
        """Return a DitaFileObj that corresponds to thePath, may raise KeyError."""
        return self._db[thePath]
        
    def setDitaFileObj(self, thePath, theObj):
        """Load a DitaFileObj or update a mutated DitaFileObj."""
        self._db[thePath] = theObj
        self._keys.add(thePath)
        
class DitaFileSet(DitaLinkCheckBase):
    """Holds information about a set of DITA files."""
    STATS_KEYS = ('Maps', 'Non-maps', 'Files', 'Bytes', 'IDs', 'Refs')
    def __init__(self,
                 theDir,
                 procDir=True,
                 thePatterns=None,
                 recursive=False,
                 testExt=False,
                 useDbase=False):
        """Constructor. theDir is the root directory of DITA XML.
        procDir - If True then process this directory immediately, otherwise
                    the directory can be processed independently and
                    _addFileObj() or _addDitaFileObj() invoked.
        thePatterns - If supplied this should be a space separated string of
                        fnmatch extensions.
        recursive - If True and procDir True the directory is processed recursively.
        testExt - If True then test external URLs.
        useDbase - If True then store all DitaFile objects in an external dbase
                    (slower but less memory issues).
        """
        if thePatterns is None:
            thePatterns = FNMATCH_STRING.split(' ')
        if theDir is not None:
            theDir = normalisePath(theDir)
        super(DitaFileSet, self).__init__(theDir)
        logging.info('DitaFileSet starting to read...')
        GlobalUrlCache.clear()
        self._testExt = testExt
        # Set up how we store the DitaFile objects
        if useDbase:
            self._fileMap = DitaFileMapShelve()
        else:
            self._fileMap = DitaFileMapInMemory()
        # Map of (str(rootId) : filepath, ...) with no duplicates
        # Keys will be in self._uniqueRootIds
        self._rootIdToFilePathMap = {}
        # Path to the unique DITA map
        self._uniqueMapPath = None
        # Count of {error_code : count, ...}
        self._errCountMap = CountDict()
        # Statistics
        self._statsMap = CountDict()
        ## and initialise
        #for k in self.STATS_KEYS:
        #    self._statsMap[k]
        # Finalisation control (weak)
        self._hasFinalised = False
        # Timers
        self._timeRead = time.clock()
        self._timeAnalyse = 0.0
        if procDir:
            if theDir is not None and os.path.isdir(theDir):
                self._readDir(theDir, thePatterns, recursive)
            else:
                self.addError(500, (theDir,))
            # Finalise and run all the tests
            self.finalise()
    
    @property
    def errCountMap(self):
        return self._errCountMap
    
    @property
    def statsMap(self):
        return self._statsMap
    
    def writeStatistics(self, s=sys.stdout):
        """Writes out read statistics."""
        s.write(' Statistics '.center(PRINT_WIDTH, '='))
        s.write('\n')
        if len(self._statsMap) > 0:
            o = self.STATS_KEYS
            #assert(set(o) == set(self._statsMap.keys())), \
            #    '%s != %s' % (o, self._statsMap.keys())
            for k in o:
                try:
                    m = self._statsMap[k] / (1024.0*1024.0)
                    s.write('%20s: %10d [%10.3f M]\n' % (k, self._statsMap[k], m))
                except KeyError:
                    s.write('%20s: %10s \n' % (k, 'Not seen'))
            s.write('%20s: %10.3f (s)\n' % ('Read time', self._timeRead))
            s.write('%20s: %10.3f (s)\n' % ('Analysis time', self._timeAnalyse))
            s.write('='*PRINT_WIDTH)
        else:
            s.write('Nothing processed.')
        s.write('\n')
        
    def writeErrorSummary(self, s=sys.stdout):
        s.write(' Error Summary '.center(PRINT_WIDTH, '='))
        s.write('\n')
        if len(self._errCountMap):
            s.write('%4s %10s %s\n' % ('Code', 'Count', 'Error'))
            s.write('%4s %10s %s\n' % ('----', '-----', '-----'))
            errCodeS = self._errCountMap.keys()
            errCodeS.sort()
            for c in errCodeS:
                s.write('%4d %10d %s\n' \
                        % (c, self._errCountMap[c], genericStringForErrorCode(c)))
        else:
            s.write('No errors\n')            
        s.write('='*PRINT_WIDTH)
        s.write('\n')
        
    def writeErrors(self, isGeneric, theFilter, theStream=sys.stdout):
        """Writes out errors for me and my files."""
        theStream.write('\n'.join(self.errStrings(isGeneric, theFilter)))
        fileS = self._fileMap.keys()
        fileS.sort()
        for aFile in fileS:
            # Immutable call so just use get
            self._fileMap.getDitaFileObj(aFile).writeErrors(isGeneric, theFilter, theStream)
        
    def allErrStrings(self, isGeneric, theFilter):
        """Return a sorted list of error messages without duplicates including
        files."""
        retSet = set(self.errStrings(isGeneric, theFilter))
        fileS = self._fileMap.keys()
        fileS.sort()
        for aFilePath in self._fileMap.keys():
            # Immutable call so just use get
            for anErr in self._fileMap.getDitaFileObj(aFilePath).errStrings(isGeneric, theFilter): 
                retSet.add(anErr)
        retList = list(retSet)
        retList.sort()
        return retList
            
    def _readDir(self, theDir, thePatS, recursive):    
        assert(os.path.isdir(theDir))
        for aName in os.listdir(theDir):
            aPath = os.path.join(theDir, aName)
            if os.path.isdir(aPath) and recursive:
                self._readDir(aPath, thePatS, recursive)
            elif os.path.isfile(aPath):
                for aPat in thePatS:
                    if fnmatch.fnmatch(aName, aPat):
                        assert(not self._fileMap.has_key(aPath))
                        logging.debug(' Reading %s' % aPath)
                        try:
                            f = open(aPath)
                        except IOError:
                            f = None
                        self._addFileObj(f, aPath)
                        break

    def _addFileObj(self, theFileObj, theFilePath):
        myObj = DitaFileObj(theFileObj, theFilePath)
        self._addDitaFileObj(myObj)

    def _addDitaFileObj(self, theDitaFileObj):
        if self._fileMap.has_key(theDitaFileObj.identity):
            self.addError(504, (theDitaFileObj.identity,))
        else:
            # Mutable call so use set
            self._fileMap.setDitaFileObj(theDitaFileObj.identity, theDitaFileObj)
        # Update statistics (files, bytes, ids, refs) etc.
        self._statsMap['Files'] += 1
        self._statsMap['Bytes'] += theDitaFileObj.bytes
        self._statsMap['IDs'] += len(theDitaFileObj.idS)
        self._statsMap['Refs'] += len(theDitaFileObj.refS)
        if theDitaFileObj.isMap:
            self._statsMap['Maps'] += 1
        else:
            self._statsMap['Non-maps'] += 1
    
    def finalise(self):
        """Creates the environment for all checks and then runs them."""
        logging.info('DitaFileSet.finalise() start...')
        if not self._hasFinalised:
            self._timeRead = time.clock() - self._timeRead
            self._timeAnalyse = time.clock()
            self._initRootIdToFilePathMap()
            self._checkDupeIdS()
            self._setMapCycles()
            self._checkLonely()
            self._checkRefArcs()
            self._errCountMap = CountDict()
            self.updateErrorCount(self._errCountMap)
            self._hasFinalised = True
            self._timeAnalyse = time.clock() - self._timeAnalyse
        logging.info('DitaFileSet.finalise() done.')
        
    def _initRootIdToFilePathMap(self):
        # Map of (str(rootId) : filepath, ...) with no duplicates
        self._rootIdToFilePathMap = {}
        # Temporary map of (str(rootId) : [filepath, ...], ...)
        myDupeIdFiles = {}
        for fPath in self._fileMap.keys():
            # fObj is not written to so we don't need to use set
            fObj = self._fileMap.getDitaFileObj(fPath)
            #print 'TRACE: _initRootIdToFilePathMap() fPath:', fPath
            rId = fObj.rootId
            if rId is not None:
                if myDupeIdFiles.has_key(rId):
                    #print 'TRACE: _initRootIdToFilePathMap() another dupe:', fPath
                    myDupeIdFiles[rId].append(fObj.identity)
                elif self._rootIdToFilePathMap.has_key(rId):
                    #print 'TRACE: _initRootIdToFilePathMap() first dupe:', fPath
                    # Remove from map and add to myDupeIdFiles
                    myFile = self._rootIdToFilePathMap.pop(rId)
                    try:
                        myDupeIdFiles[rId].append(myFile)
                    except KeyError:
                        myDupeIdFiles[rId] = [myFile,]
                    myDupeIdFiles[rId].append(fPath)
                else:
                    #print 'TRACE: _initRootIdToFilePathMap() adding:', fPath
                    self._rootIdToFilePathMap[rId] = fObj.identity
        # Set duplicate errors
        for k in myDupeIdFiles.keys():
            myDupeIdFiles[k].sort()
            self.addError(501, (k, tuple(myDupeIdFiles[k])))
            #self.addError(501, (k, str([str(a) for a in myDupeIdFiles[k]])))
    
    def _checkDupeIdS(self):
        """Checks if there are any duplicate IDs anywhere."""
        # {ID : [fileS, ...], ...}
        myDupeIdMap = {}
        # Temporary data structure
        # {ID : first file ID is seen in, ...}
        seenIdMap = {}
        for f in self._fileMap.keys():
            # o is not written to so we don't need set...
            o = self._fileMap.getDitaFileObj(f)
            for anId in o.idS:
                if seenIdMap.has_key(anId):
                    try:
                        myDupeIdMap[anId].append(f)
                    except KeyError:
                        myDupeIdMap[anId] = [seenIdMap[anId],]
                        myDupeIdMap[anId].append(f)
                else:
                    seenIdMap[anId] = f
        # Now add to errs as a 505 error message
        # Sort the files in the map
        for k in myDupeIdMap.keys():
            myDupeIdMap[k].sort()
            self.addError(505, (k, tuple(myDupeIdMap[k])))
            #self.addError(505, (k, str([str(a) for a in myDupeIdMap[k]])))
                    
    def _retMapAdjList(self):
        """Create an adjacency list {file_path : set(refs), ...} (all strings)"""
        adjList = {}
        for f in self._fileMap.keys():
            fObj = self._fileMap.getDitaFileObj(f)
            if fObj.isMap:# and fObj.rootId is not None:
                assert(fObj.identity not in adjList.keys())
                refSet = set()
                for r in fObj.refS:
                    refSet.add(r.fileFragment(fObj.identity)[0])
                adjList[fObj.identity] = refSet
        return adjList

    def _setMapCycles(self):
        """Sets any cyclic references seen in DITA maps."""
        adjList = self._retMapAdjList()
        # A branch
        myBr = []
        myCycles = set()
        for aPath, aSet in adjList.items():
            myBr.append(aPath)
            self._recurseCycles(adjList, myBr, myCycles)
            myBr.pop()
        self._setCycleErrors(myCycles)      
            
    def _recurseCycles(self, a, b, c):
        assert(len(b) > 0)
        try:
            myPath = b[-1]
            for r in a[myPath]:
                #print '_recurseCycles() testing r', r
                #print '_recurseCycles() testing b', b
                if r in b:
                    #print 'Adding cycle', tuple(b[b.index(r):])
                    c.add(tuple(b[b.index(r):]))
                else:
                    b.append(r)
                    self._recurseCycles(a, b, c)
                    b.pop()
        except KeyError:
            pass
        
    def _setCycleErrors(self, theC):
        for aT in theC:
            self.addError(701, (str(aT),))
            myL = list(aT)
            assert(len(myL) > 0)
            i = 0
            while i < len(myL):
                myL.append(myL[0])
                # Should this be in the file thus, or in the files set?
                # As we are mutating the file object we need to use both
                # getDitaFileObj() and setDitaFileObj()
                fObj = self._fileMap.getDitaFileObj(myL[0])
                fObj.addError(701, (str(myL),))
                self._fileMap.setDitaFileObj(myL[0], fObj)
                myL.pop()
                myL.append(myL.pop(0))
                i += 1    

    def _checkLonely(self):
        self._checkLonelyMaps()
        self._checkLonelyTopics()
        
    def _checkLonelyMaps(self):
        """Checks for lonely maps."""
        mapPathSet = set()
        pathSetRemain = set()
        for f in self._fileMap.keys():
            if self._fileMap.getDitaFileObj(f).isMap:
                mapPathSet.add(f)
                pathSetRemain.add(f)
        for aPath in mapPathSet:
            myMapObj = self._fileMap.getDitaFileObj(aPath)
            for r in myMapObj.refS:
                refFile, frag = r.fileFragment(f)
                try:
                    pathSetRemain.remove(refFile)
                except KeyError:
                    # refFile is a topic or an already seen map
                    pass
        if len(pathSetRemain) > 1:
            for aPath in pathSetRemain:
                self.addError(700, (aPath,))
        elif len(pathSetRemain) == 1:
            self._uniqueMapPath = pathSetRemain.pop()

    def _checkLonelyTopics(self):
        """Checks for topics that are not referenced by any map."""
        mapPathSet = set()
        pathSetRemain = set()
        for f in self._fileMap.keys():
            #print 'TRACE: f:', f
            if self._fileMap.getDitaFileObj(f).isMap:
                mapPathSet.add(f)
            else:
                pathSetRemain.add(f)
        #print 'TRACE: mapPathSet', mapPathSet
        #print 'TRACE: pathSetRemain', pathSetRemain
        for aMapPath in mapPathSet:
            myMapObj = self._fileMap.getDitaFileObj(aMapPath)
            for r in myMapObj.refS:
                refFile, frag = r.fileFragment(aMapPath)
                #print 'TRACE: removing:', refFile
                try:
                    pathSetRemain.remove(refFile)
                except KeyError:
                    # topic has already been seen in another map
                    pass
        if len(pathSetRemain) > 0:
            for aPath in pathSetRemain:
                self.addError(600, (aPath,))
            
    def _checkRefArcs(self):
        """Checks all references are reachable."""
        for fPath in self._fileMap.keys():
            fObjSrc = self._fileMap.getDitaFileObj(fPath)
            hasMutated = False
            for rObjSrc in fObjSrc.refS:
                if rObjSrc.scheme:
                    # Decide whether to test and external URL
                    if self._testExt:
                        rObjSrc.checkUrl()
                else:
                    fi, fr = rObjSrc.fileFragment(fPath)
                    assert(fi is not None), 'fi is None for rObjSrc: %s in file: %s' % (rObjSrc, fPath)
                    assert(fr is not None), 'fr is None for rObjSrc: %s in file: %s' % (rObjSrc, fPath)
                    ## If a url then fileFragment() returns (None, None)
                    #if fi is None:
                    #    print 'fPath', fPath
                    #    print 'rObjSrc', rObjSrc
                    #    print 'fi', fi
                    #    print 'fr', fr
                    try:
                        fObjTgt = self._fileMap.getDitaFileObj(fi)
                    except KeyError:
                        # Target file can not be found in the IR
                        # check the file system to see if it is a non-DITA resource
                        if not os.path.isfile(fi):
                            #print 'TRACE: adding 410 to', fObj.identity
                            fObjSrc.addError(410, (fi,))
                            hasMutated = True
                    else:
                        if len(fr) > 0:
                            # Target file is found, test fragment
                            if not fObjTgt.hasId(fr):
                                # Fragment not found
                                fObjSrc.addError(411, (fi, fr))
                                hasMutated = True
                        if self._checkRefArcElemName(fObjSrc, rObjSrc, fObjTgt, fr):
                            hasMutated = True
            if hasMutated:
                self._fileMap.setDitaFileObj(fPath, fObjSrc)

    def _checkRefArcElemName(self, fObjSrc, rObjSrc, fObjTgt, frag):
        """Test source and target element names
        e.g. Source <cxxClassRef> should match target <cxxClass>
        And in vanilla DITA:
        <topicref href="batcaring.dita" type="task"></topicref>
        or:
        <topicref href="batcaring.dita" format="ditamap"></topicref>
        Should match target element <task>."""
        isRootTgt = False
        hasMutated = False
        if len(frag) == 0:
            # iObjTgt is the root element of fObjTgt
            if fObjTgt.rootId is None or fObjTgt.idElem(fObjTgt.rootId) is None:
                # Covered by other error codes
                return
            iObjTgt = fObjTgt.idObj(fObjTgt.rootId)
            isRootTgt = True
        elif fObjTgt.hasId(frag):
            iObjTgt = fObjTgt.idObj(frag)
        else:
            # frag not found that will be a 411 error (handled by caller).
            return
        # Have an rObjSrc + iObjTgt so check elements
        # First case:
        if rObjSrc.elem.endswith('Ref'):
            if rObjSrc.elem[:-3] != iObjTgt.elem:
                if isRootTgt:
                    fObjSrc.addError(412, (rObjSrc.elem, iObjTgt.elem))
                else:
                    fObjSrc.addError(413, (fObjTgt.idElem(frag), rObjSrc.elem, frag))
                hasMutated = True
        # Second case(s) for vanilla DITA
        elif rObjSrc.elem == 'topicref':
            # Check DITA map links
            if rObjSrc.format == 'ditamap' and iObjTgt.elem != 'map':
                # Target must be a root element (actually we don't care)
                fObjSrc.addError(414, (iObjTgt.elem,))
                hasMutated = True
            elif iObjTgt.elem == 'map' and rObjSrc.format != 'ditamap':
                fObjSrc.addError(415, (rObjSrc.format,))
                hasMutated = True
            elif not (rObjSrc.format == 'ditamap' and iObjTgt.elem == 'map'):
                # Treat refType None as type="topic", see DITA standard for <topicref>
                # Well, also look at the type attribute in chapter 25
                # "When the type attribute is unspecified, it should be
                # determined by inspecting the target if possible. If the
                # target cannot be inspected for some reason, the value
                # should default to "topic".
                # Note: DITA 1.2 takes a different view...
                # Was:
                #if (rObjSrc.refType is None and iObjTgt.elem != 'topic') \
                #or (rObjSrc.refType is not None and rObjSrc.refType != iObjTgt.elem):
                if rObjSrc.refType is not None and rObjSrc.refType != iObjTgt.elem:
                    if isRootTgt:
                        fObjSrc.addError(416, (rObjSrc.refType, iObjTgt.elem,))
                        hasMutated = True
                    else:
                        fObjSrc.addError(417, (rObjSrc.refType, iObjTgt.elem, frag,))
                        hasMutated = True
                # Otherwise topicref looks OK
        elif rObjSrc.elem != 'xref' and rObjSrc.elem not in XREF_DESCENDENTS:
            # Unknown referencing element
            if isRootTgt:
                fObjSrc.addError(418, (rObjSrc.elem, fObjTgt.doctype))
                hasMutated = True
            else:
                fObjSrc.addError(419, (rObjSrc.elem, fObjTgt.idElem(frag), frag))
                hasMutated = True
        return hasMutated
                                        
    def updateErrorCount(self, theMap):
        """Updates a map of {error_code, : count, ...}."""
        if self._errS is not None:
            for e in self._errS.keys():
                theMap[e] += len(self._errS[e])
        for fPath in self._fileMap.keys():
            fObj = self._fileMap.getDitaFileObj(fPath)
            # Mutable call so need to update
            fObj.updateErrorCount(theMap)
            self._fileMap.setDitaFileObj(fPath, fObj)

    def debugDump(self, s=sys.stdout, prefix=''):
        """Dump of IR for debug purposes."""
        s.write(' Debug Dump '.center(PRINT_WIDTH, '+'))
        s.write('\n')
        fileS = self._fileMap.keys()
        fileS.sort()
        for f in fileS:
            self._fileMap.getDitaFileObj(f).debugDump(s, prefix)
        s.write(' END Debug Dump '.center(PRINT_WIDTH, '+'))
        s.write('\n\n')
    
#####################################
# Multiprocessing code
#####################################
def retDitaFileObj(thePath):
    return DitaFilePath(thePath)
 
def genDitaPath(theDir, thePatS, recursive):
    assert(os.path.isdir(theDir))
    for aName in os.listdir(theDir):
        aPath = os.path.join(theDir, aName)
        if os.path.isdir(aPath) and recursive:
            for p in genDitaPath(aPath, thePatS, recursive):
                yield p
        elif os.path.isfile(aPath):
            for aPat in thePatS:
                if fnmatch.fnmatch(aName, aPat):
                    #logging.info('genDitaPath(): %s' % aPath)
                    yield aPath
                    break    
    
def retMpDitaFileSetObj(theDir,
                        thePatterns,
                        recursive,
                        numJobs, 
                        checkExt,
                        useDb):
    assert(os.path.isdir(theDir))
    assert(numJobs >= 0)
    retObj = DitaFileSet(theDir, procDir=False, testExt=checkExt, useDbase=useDb)
    myNumJobs = numJobs
    if numJobs == 0:
        myNumJobs = multiprocessing.cpu_count()
        logging.info('Set multiprocessing number of jobs to %d' % myNumJobs)
    myPool = multiprocessing.Pool(processes=myNumJobs)
    for result in [
            myPool.apply_async(retDitaFileObj, (f,))
                for f in genDitaPath(theDir, thePatterns, recursive)
            ]:
        myObj = result.get()
        logging.debug('Got %s' % myObj.identity)
        retObj._addDitaFileObj(myObj)
    # Note: finalise() is a serial process
    logging.info('retMpDitaFileSetObj(): finalising')
    retObj.finalise()
    return retObj

######################################
# Test code
######################################
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

class NullClass(unittest.TestCase):
    pass

class TestCountDict(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def testSetUpTearDown(self):
        """TestCountDict: test setUp() and tearDown()."""
        pass
    
    def test_basic(self):
        """TestCountDict: test basic functionality."""
        myMap = CountDict()
        self.assertEqual(myMap.has_key('wtf'), False)
        self.assertEqual(myMap['wtf'], 0)
        self.assertEqual(myMap.has_key('wtf'), True)
        myMap['wtf'] += 1
        self.assertEqual(myMap['wtf'], 1)

class TestDitaId(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def testSetUpTearDown(self):
        """DitaId: test setUp() and tearDown()."""
        pass
    
    def test_basic(self):
        """DitaId: basic read of an node with an id"""
        myXml = """<cxxClass id="class_big_endian"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaId(myTree.getroot())
        self.assertEqual(myObj.id, 'class_big_endian')
        self.assertEqual(str(myObj), 'class_big_endian')
        self.assertEqual(myObj.errStrings(True, None), [])
        self.assertEqual(myObj.errStrings(False, None), [])
        
    def test_guid_00(self):
        """DitaId: basic read of an node with an GUID id"""
        myXml = """<cxxClass id="GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaId(myTree.getroot())
        self.assertEqual(myObj.id, 'GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E')
        myObj.checkGuid()
        self.assertEqual(myObj.errStrings(True, None), [])
        self.assertEqual(myObj.errStrings(False, None), [])

    def test_guid_01(self):
        """DitaId: basic read of an node with an GUID id fails"""
        myXml = """<cxxClass id="25825EC4-341F-3EA4-94AA-7DCE380E6D2E"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaId(myTree.getroot())
        self.assertEqual(myObj.id, '25825EC4-341F-3EA4-94AA-7DCE380E6D2E')
        myObj.checkGuid()
        self.assertEqual(
            myObj.errStrings(False, None),
            [
             'GUID specification does not match id="25825EC4-341F-3EA4-94AA-7DCE380E6D2E"'
            ])
        self.assertEqual(
            myObj.errStrings(True, None),
            [
             'GUID specification does not match id="%s"' % GENERIC_STRING,
            ])

    def test_cmp_eq_00(self):
        """DitaId: cmp(), == of two identical nodes"""
        myXml = """<cxxClass id="class_big_endian"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj_00 = DitaId(myTree.getroot())
        myObj_01 = DitaId(myTree.getroot())
        self.assertEqual(cmp(myObj_00, myObj_01), 0)
        self.assertEqual((myObj_00 == myObj_01), True)

    def test_cmp_eq_01(self):
        """DitaId: cmp(), == of two identical nodes from different elements."""
        myXml_00 = """<cxxClass id="big_endian"/>"""
        myTree_00 = etree.parse(StringIO.StringIO(myXml_00))
        myObj_00 = DitaId(myTree_00.getroot())
        myXml_01 = """<cxxStruct id="big_endian"/>"""
        myTree_01 = etree.parse(StringIO.StringIO(myXml_01))
        myObj_01 = DitaId(myTree_01.getroot())
        self.assertEqual(cmp(myObj_00, myObj_01), 0)
        self.assertEqual((myObj_00 == myObj_01), True)

    def test_set(self):
        """DitaId: read of an node with an id several times into a set and check unique,"""
        myXml = """<cxxClass id="class_big_endian"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        s = set()
        i = 0
        while i < 8:
            s.add(DitaId(myTree.getroot()))
            i += 1
        self.assertEqual(len(s), 1)
        self.assertEqual(DitaId(myTree.getroot()) in s, True)

    def test_map(self):
        """DitaId: read of an node with an id several times into a map and check unique,"""
        myXml = """<cxxClass id="class_big_endian"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        m = {}
        i = 0
        while i < 8:
            m[DitaId(myTree.getroot())] = 1
            i += 1
        self.assertEqual(len(m), 1)
        self.assertEqual(m.has_key(DitaId(myTree.getroot())), True)

    def test_error_hash(self):
        """DitaId: error with a '#' in an id"""
        myXml = """<cxxClass id="class_#big_endian"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaId(myTree.getroot())
        self.assertEqual(myObj.id, 'class_#big_endian')
        self.assertEqual(str(myObj), 'class_#big_endian')
        self.assertEqual(
                myObj.errStrings(True, None),
                [
                    genericStringForErrorCode(100),
                ]
            )
        self.assertEqual(
                myObj.errStrings(False, None),
                [
                 'Character \'#\' not allowed in id="class_#big_endian"',
                 ]
            )
        


class TestDitaRef(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def testSetUpTearDown(self):
        """DitaRef: test setUp() and tearDown()."""
        pass
    
    def test_basic(self):
        """DitaRef: basic read of an xref node, no fragment"""
        myXml = """<xref href="class_big_endian"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaRef(myTree.getroot())
        self.assertEqual(myObj.href, 'class_big_endian')
        self.assertEqual(myObj.path, 'class_big_endian')
        self.assertEqual(myObj.elem, 'xref')
        self.assertEqual(str(myObj), 'xref class_big_endian')
        self.assertEqual(myObj.fragment, '')
        self.assertEqual(myObj.scheme, '')
        self.assertEqual(myObj.errStrings(False, None), [])
        self.assertEqual(myObj.errStrings(True, None), [])

    def test_basic_frag(self):
        """DitaRef: basic read of an xref node, with fragment"""
        myXml = """<xref href="class_big_endian.xml#function"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaRef(myTree.getroot())
        self.assertEqual(myObj.href, 'class_big_endian.xml#function')
        self.assertEqual(myObj.path, 'class_big_endian.xml')
        self.assertEqual(myObj.fragment, 'function')
        self.assertEqual(myObj.scheme, '')
        self.assertEqual(myObj.errStrings(False, None), [])
        self.assertEqual(myObj.errStrings(True, None), [])

    def test_file_frag_00(self):
        """DitaRef: accessing an xref node, with a file and a fragment"""
        myXml = """<xref href="class_big_endian.xml#function"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaRef(myTree.getroot())
        self.assertEqual(myObj.href, 'class_big_endian.xml#function')
        self.assertEqual(myObj.path, 'class_big_endian.xml')
        self.assertEqual(myObj.fragment, 'function')
        self.assertEqual(myObj.scheme, '')
        srcPath = normalisePath(os.path.join('C:%s' % os.sep, 'spam', 'eggs.xml'))
        expPath = normalisePath(os.path.join('C:%s' % os.sep, 'spam', 'class_big_endian.xml'))
        self.assertEqual(
            myObj.fileFragment(srcPath),
            (expPath, 'function')
        )
        self.assertEqual(myObj.errStrings(False, None), [])
        self.assertEqual(myObj.errStrings(True, None), [])
        
    def test_file_frag_01(self):
        """DitaRef: accessing an xref node, with a file and a fragment and relative path with '\\'."""
        myXml = """<xref href="..\\chips\\class_big_endian.xml#function"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaRef(myTree.getroot())
        srcPath = normalisePath(os.path.join('C:%s' % os.sep, 'spam', 'eggs.xml'))
        expPath = normalisePath(os.path.join('C:%s' % os.sep, 'chips', 'class_big_endian.xml'))
        self.assertEqual(
            myObj.fileFragment(srcPath),
            (expPath, 'function')
        )
        self.assertEqual(myObj.errStrings(False, None), [])
        self.assertEqual(myObj.errStrings(True, None), [])
        
    def test_file_frag_02(self):
        """DitaRef: accessing an xref node, with a file and a fragment and relative path with '/'."""
        myXml = """<xref href="../chips/class_big_endian.xml#function"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaRef(myTree.getroot())
        srcPath = normalisePath(os.path.join('C:%s' % os.sep, 'spam', 'eggs.xml'))
        expPath = normalisePath(os.path.join('C:%s' % os.sep, 'chips', 'class_big_endian.xml'))
        self.assertEqual(
            myObj.fileFragment(srcPath),
            (expPath, 'function')
        )
        self.assertEqual(myObj.errStrings(False, None), [])
        self.assertEqual(myObj.errStrings(True, None), [])
        
    def test_file_frag_03(self):
        """DitaRef: accessing an xref node, with a no file but with a fragment"""
        myXml = """<xref href="#function"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaRef(myTree.getroot())
        self.assertEqual(myObj.href, '#function')
        self.assertEqual(myObj.path, '')
        self.assertEqual(myObj.fragment, 'function')
        self.assertEqual(myObj.scheme, '')
        srcPath = normalisePath(os.path.join('C:%s' % os.sep, 'spam', 'eggs.xml'))
        expPath = normalisePath(os.path.join('C:%s' % os.sep, 'spam', 'eggs.xml'))
        self.assertEqual(
            myObj.fileFragment(srcPath),
            (expPath, 'function')
        )
        self.assertEqual(myObj.errStrings(False, None), [])
        self.assertEqual(myObj.errStrings(True, None), [])
        
    def test_basic_scheme(self):
        """DitaRef: an xref node with a URI scheme"""
        myXml = """<xref href="http://www.cwi.nl:80/%7Eguido/Python.html#fragment"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaRef(myTree.getroot())
        self.assertEqual(myObj.href, 'http://www.cwi.nl:80/%7Eguido/Python.html#fragment')
        self.assertEqual(myObj.path, '/%7Eguido/Python.html')
        self.assertEqual(myObj.fragment, 'fragment')
        self.assertEqual(myObj.scheme, 'http')
        self.assertEqual(myObj.errStrings(False, None), [])
        self.assertEqual(myObj.errStrings(True, None), [])

    def test_basic_scheme_file_frag(self):
        """DitaRef: an xref node with a URI scheme, invoking fileFragment()"""
        myXml = """<xref href="http://www.cwi.nl:80/%7Eguido/Python.html#fragment"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaRef(myTree.getroot())
        self.assertEqual(myObj.href, 'http://www.cwi.nl:80/%7Eguido/Python.html#fragment')
        self.assertEqual(myObj.path, '/%7Eguido/Python.html')
        self.assertEqual(myObj.fragment, 'fragment')
        self.assertEqual(myObj.scheme, 'http')
        srcPath = os.path.join('C:%s' % os.sep, 'spam', 'eggs.xml')
        self.assertEqual(
            myObj.fileFragment(srcPath),
            (None, None)
        )
        self.assertEqual(myObj.errStrings(False, None), [])
        self.assertEqual(myObj.errStrings(True, None), [])

    def test_fail_no_href(self):
        """DitaRef: Fails on an xref node with no href attribute"""
        myXml = """<xref />"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaRef(myTree.getroot())
        self.assertEqual(
            myObj.errStrings(False, None),
            [
             'Reference element "xref" is missing href=... attribute',
             ]
        )
        self.assertEqual(
            myObj.errStrings(True, None),
            [
             'Reference element "%s" is missing href=... attribute' % GENERIC_STRING,
             ]
        )

    def test_fail_bad_frag(self):
        """DitaRef: Fails on an xref node with href attribute that has multiple '#' characters"""
        myXml = """<xref href="a#b#c" />"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaRef(myTree.getroot())
        self.assertEqual(
            myObj.errStrings(False, None),
            [
             'Multiple \'#\' not allowed in reference "a#b#c"',
             ]
        )
        self.assertEqual(
            myObj.errStrings(True, None),
            [
             'Multiple \'#\' not allowed in reference "%s"' % GENERIC_STRING,
             ]
        )

    def test_guid_00(self):
        """DitaRef: basic read of an node with an GUID file/fragment reference"""
        myXml = """<xref href="GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E.xml#GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaRef(myTree.getroot())
        self.assertEqual(myObj.href, 'GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E.xml#GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E')
        self.assertEqual(myObj.path, 'GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E.xml')
        self.assertEqual(myObj.elem, 'xref')
        self.assertEqual(str(myObj), 'xref GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E.xml#GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E')
        self.assertEqual(myObj.fragment, 'GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E')
        self.assertEqual(myObj.scheme, '')
        self.assertEqual(myObj.errStrings(False, None), [])
        self.assertEqual(myObj.errStrings(True, None), [])

    def test_guid_01(self):
        """DitaRef: basic read of an node with an GUID file part fails"""
        myXml = """<xref href="GUID-.xml#GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaRef(myTree.getroot())
        self.assertEqual(myObj.href, 'GUID-.xml#GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E')
        self.assertEqual(myObj.path, 'GUID-.xml')
        self.assertEqual(myObj.elem, 'xref')
        self.assertEqual(str(myObj), 'xref GUID-.xml#GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E')
        self.assertEqual(myObj.fragment, 'GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E')
        self.assertEqual(myObj.errStrings(False, None), [])
        self.assertEqual(myObj.errStrings(True, None), [])
        myObj.checkGuid()
        self.assertEqual(
            myObj.errStrings(False, None),
            [
             'GUID specification does not match file reference "GUID-.xml"'
            ])
        self.assertEqual(
            myObj.errStrings(True, None),
            [
             genericStringForErrorCode(203),
            ]
        )

    def test_guid_02(self):
        """DitaRef: basic read of an node with an GUID fragment part fails"""
        myXml = """<xref href="GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E.xml#GUID-25825EC4"/>"""
        myTree = etree.parse(StringIO.StringIO(myXml))
        myObj = DitaRef(myTree.getroot())
        self.assertEqual(myObj.href, 'GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E.xml#GUID-25825EC4')
        self.assertEqual(myObj.path, 'GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E.xml')
        self.assertEqual(myObj.elem, 'xref')
        self.assertEqual(str(myObj), 'xref GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E.xml#GUID-25825EC4')
        self.assertEqual(myObj.fragment, 'GUID-25825EC4')
        self.assertEqual(myObj.errStrings(False, None), [])
        self.assertEqual(myObj.errStrings(True, None), [])
        myObj.checkGuid()
        self.assertEqual(
            myObj.errStrings(False, None),
            [
             'GUID specification does not match fragment reference "GUID-25825EC4"'
            ])
        self.assertEqual(
            myObj.errStrings(True, None),
            [
             genericStringForErrorCode(204),
            ]
        )

class TestDitaFile(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def testSetUpTearDown(self):
        """DitaFile: test setUp() and tearDown()."""
        pass
    
    def test_Basic(self):
        """DitaFile: basic read of an XML file"""
        myXml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.1.0//EN" "dtd/cxxClass.dtd" >
<cxxClass id="class_big_endian">
    <apiName>BigEndian</apiName>
    <shortdesc/>
    <cxxClassDetail>
        <cxxClassDefinition>
            <cxxClassAccessSpecifier value="public"/>
            <cxxClassAPIItemLocation>
                <cxxClassDeclarationFile name="filePath" value="K:/sf/os/commsfw/datacommsserver/esockserver/inc/es_sock.h"/>
                <cxxClassDeclarationFileLine name="lineNumber" value="1520"/>
                <cxxClassDefinitionFile name="filePath" value="K:/sf/os/commsfw/datacommsserver/esockserver/inc/es_sock.h"/>
                <cxxClassDefinitionFileLineStart name="lineNumber" value="1516"/>
                <cxxClassDefinitionFileLineEnd name="lineNumber" value="1526"/>
            </cxxClassAPIItemLocation>
        </cxxClassDefinition>
        <apiDesc>
            <p>Inserts and extracts integers in big-endian format.   </p>
        </apiDesc>
    </cxxClassDetail>
    <cxxFunction id="class_big_endian_1a9f78fb092e713acf6ffe3e8e11f1626f">
    </cxxFunction>
    <cxxFunction id="class_big_endian_1aedf702f5c0118e4294d1a6d9684f8441">
    </cxxFunction>
    <cxxFunction id="class_big_endian_1ae266722f7bb965c971155a3315bad484">
    </cxxFunction>
    <cxxFunction id="class_big_endian_1a497d5248ea259f8490fb40ac4f2aafb2">
    </cxxFunction>
</cxxClass>"""
        myFile = StringIO.StringIO(myXml)
        myObj = DitaFileObj(myFile, 'foo')
        self.assertEqual(myObj.identity, normalisePath('foo'))
        self.assertEqual(myObj.doctype, 'cxxClass')
        self.assertEqual(myObj.rootId, 'class_big_endian')
        #print myObj.idMap()
        self.assertEqual(
            myObj.idElemMap(),
            {
                'class_big_endian_1a9f78fb092e713acf6ffe3e8e11f1626f'   : 'cxxFunction',
                'class_big_endian_1aedf702f5c0118e4294d1a6d9684f8441'   : 'cxxFunction',
                'class_big_endian'                                      : 'cxxClass',
                'class_big_endian_1a497d5248ea259f8490fb40ac4f2aafb2'   : 'cxxFunction',
                'class_big_endian_1ae266722f7bb965c971155a3315bad484'   : 'cxxFunction',
                }
        )
        self.assertEqual(myObj.errStrings(False, None), [])
        self.assertEqual(myObj.errStrings(True, None), [])

    def test_missing_file(self):
        """DitaFile: read an missing XML file"""
        myObj = DitaFileObj(None, 'foo')
        self.assertEqual(
            myObj.errStrings(False, None),
            [
             'Failed to open: "%s"' % normalisePath('foo'),
             ]
        )
        self.assertEqual(
            myObj.errStrings(True, None),
            [
             genericStringForErrorCode(400),
             ]
        )
    
    def test_IllFormedFile(self):
        """DitaFile: read an ill-formed XML file"""
        myXml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.1.0//EN" "dtd/cxxClass.dtd" >
<cxxClass id="class_big_endian">
"""
        myFile = StringIO.StringIO(myXml)
        myObj = DitaFileObj(myFile, 'foo')
        self.assertEqual(myObj.identity, normalisePath('foo'))
        self.assertEqual(myObj.doctype, None)
        self.assertEqual(myObj.rootId, None)
        #print myObj.idMap()
        self.assertEqual(myObj.idElemMap(), {})
        self.assertEqual(
            myObj.errStrings(False, None),
            [
             'Can not parse: "no element found: line 4, column 0"',
             ]
        )
        self.assertEqual(
            myObj.errStrings(True, None),
            [
             genericStringForErrorCode(404),
             ]
        )

    def test_missing_root_id(self):
        """DitaFile: read of an XML file with no id on root element"""
        myXml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.1.0//EN" "dtd/cxxClass.dtd" >
<cxxClass>
    <xref href="OtherClass">OtherClass</xref>
    <cxxFunction id="class_big_endian_1a9f78fb092e713acf6ffe3e8e11f1626f"/>
</cxxClass>"""
        myFile = StringIO.StringIO(myXml)
        myObj = DitaFileObj(myFile, 'foo')
        self.assertEqual(myObj.identity, normalisePath('foo'))
        self.assertEqual(myObj.doctype, 'cxxClass')
        self.assertEqual(myObj.rootId, None)
        self.assertEqual(
            myObj.idElemMap(),
            {
                'class_big_endian_1a9f78fb092e713acf6ffe3e8e11f1626f'   : 'cxxFunction',
                }
        )
        self.assertEqual(myObj.errStrings(False, None), [genericStringForErrorCode(402)])
        self.assertEqual(myObj.errStrings(True, None), [genericStringForErrorCode(402)])

    def test_duplicate_id(self):
        """DitaFile: duplicate IDs"""
        myXml = """<root id="AnID">
<elem id="AnID"/>
</root>"""
        myFile = StringIO.StringIO(myXml)
        myObj = DitaFileObj(myFile, 'spam.xml')
        self.assertEqual(myObj.identity, normalisePath('spam.xml'))
        self.assertEqual(myObj.doctype, 'root')
        self.assertEqual(myObj.rootId, 'AnID')
        self.assertEqual(myObj.idElemMap(), {})
        self.assertEqual(
            myObj.errStrings(False, None),
            [
                'Multiple id="AnID"',
            ]
        )
        self.assertEqual(myObj.errStrings(True, None), [genericStringForErrorCode(401)])

    def test_ismap_00(self):
        """DitaFile: Is a map for <map>."""
        myXml = """<map id="myMap"/>"""
        myFile = StringIO.StringIO(myXml)
        myObj = DitaFileObj(myFile, 'spam.xml')
        self.assertEqual(myObj.isMap, True)
    
    def test_ismap_01(self):
        """DitaFile: Is a map for <cxxAPIMap>."""
        myXml = """<cxxAPIMap id="myMap"/>"""
        myFile = StringIO.StringIO(myXml)
        myObj = DitaFileObj(myFile, 'spam.xml')
        self.assertEqual(myObj.isMap, True)
    
    def test_Basic_01(self):
        """DitaFile: read of an simple XML file with id and xref"""
        myXml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.1.0//EN" "dtd/cxxClass.dtd" >
<cxxClass id="class_big_endian">
    <xref href="OtherClass">OtherClass</xref>
    <cxxFunction id="class_big_endian_1a9f78fb092e713acf6ffe3e8e11f1626f"/>
</cxxClass>"""
        myFile = StringIO.StringIO(myXml)
        myObj = DitaFileObj(myFile, 'foo')
        self.assertEqual(myObj.identity, normalisePath('foo'))
        self.assertEqual(myObj.doctype, 'cxxClass')
        self.assertEqual(myObj.rootId, 'class_big_endian')
        self.assertEqual(myObj.isMap, False)
        self.assertEqual(len(myObj.idS), 2)
        self.assertEqual(len(myObj.refS), 1)
        self.assertEqual(myObj.hasId('class_big_endian'), True)
        self.assertEqual(myObj.hasId('class_big_endian_1a9f78fb092e713acf6ffe3e8e11f1626f'), True)
        self.assertEqual(myObj.hasId('noID'), False)
        self.assertEqual(myObj.idElem('class_big_endian'), 'cxxClass')
        self.assertEqual(myObj.idElem('noID'), None)
        self.assertEqual(
            myObj.idElem('class_big_endian_1a9f78fb092e713acf6ffe3e8e11f1626f'),
            'cxxFunction'
        )
        #print myObj.idMap()
        self.assertEqual(
            myObj.idElemMap(),
            {
                'class_big_endian_1a9f78fb092e713acf6ffe3e8e11f1626f'   : 'cxxFunction',
                'class_big_endian'                                      : 'cxxClass',
                }
        )
        self.assertEqual(myObj.errStrings(False, None), [])
        self.assertEqual(myObj.errStrings(True, None), [])

class TestDitaFileSet(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def testSetUpTearDown(self):
        """DitaFileSet: test setUp() and tearDown()."""
        pass
    
    def test_None(self):
        """DitaFileSet: read of None."""
        myO = DitaFileSet(None)
        myO.finalise()
        self.assertEqual(myO.errStrings(False, None), ['Not a directory: None'])
        self.assertEqual(myO.errStrings(True, None), ['Not a directory: %s' % GENERIC_STRING, ])
        self.assertEqual(myO.errCountMap, {500 : 1})

    def test_basic(self):
        """DitaFileSet: Test reading a map and a couple of files."""
        myO = DitaFileSet(None, procDir=False)
        myO._addFileObj(
            StringIO.StringIO(
"""<map id="map_00">
    <topicref href="spam.dita" />
    <topicref href="eggs.dita" />
</map>"""
            ),
            'map.ditamap'
        )
        myO._addFileObj(StringIO.StringIO('<topic id="spam"/>'), 'spam.dita')
        myO._addFileObj(StringIO.StringIO('<topic id="eggs"/>'), 'eggs.dita')
        myO.finalise()
        #print 'HI'
        #myO.writeErrors(False)
        self.assertEqual(myO.allErrStrings(False, None), [])
        self.assertEqual(myO.allErrStrings(True, None), [])
        self.assertEqual(myO.errCountMap, {})

    def test_duplicate_paths(self):
        """DitaFileSet: Test reading a couple of files in duplicate paths."""
        myO = DitaFileSet(None, procDir=False)
        myO._addFileObj(
            StringIO.StringIO(
"""<map id="map_00">
    <topicref href="spam.dita" />
</map>"""
            ),
            'map.ditamap'
        )
        myO._addFileObj(StringIO.StringIO('<topic id="spam"/>'), 'spam.dita')
        myO._addFileObj(StringIO.StringIO('<topic id="eggs"/>'), 'spam.dita')
        myO.finalise()
        self.assertEqual(
            myO.errStrings(False, None),
            [
                'Duplicate file path: "%s"' % normalisePath('spam.dita'),
            ]
        )
        self.assertEqual(myO.errStrings(True, None), [genericStringForErrorCode(504),])
        self.assertEqual(myO.errCountMap, {504 : 1})

    def test_duplicate_ids(self):
        """DitaFileSet: Test reading a map and a couple of files with duplicate IDs."""
        myO = DitaFileSet(None, procDir=False)
        myO._addFileObj(
            StringIO.StringIO(
"""<map id="map_00">
    <topicref href="spam.dita" />
    <topicref href="eggs.dita" />
    <topicref href="chips.dita" />
</map>"""
            ),
            'map.ditamap'
        )
        myO._addFileObj(StringIO.StringIO('<topic id="chips"/>'), 'spam.dita')
        myO._addFileObj(StringIO.StringIO('<topic id="chips"/>'), 'eggs.dita')
        myO._addFileObj(StringIO.StringIO('<topic id="chips"/>'), 'chips.dita')
        myO.finalise()
        #print 'HI'
        #myO.writeErrors(False)
        #pprint.pprint(myO.errStrings(False, None))
        self.assertEqual(
            myO.errStrings(True, None),
            [
             genericStringForErrorCode(505),
             genericStringForErrorCode(501),
             ]
        )
        expErrs = [
                """Duplicate id="chips" in files: ('%s', '%s', '%s')""" \
                    % (normalisePath('chips.dita'), normalisePath('eggs.dita'), normalisePath('spam.dita')),
                """Duplicate root id="chips" in files: ('%s', '%s', '%s')""" \
                    % (normalisePath('chips.dita'), normalisePath('eggs.dita'), normalisePath('spam.dita')),
            ]
        myErrs = myO.errStrings(False, None)
#===============================================================================
#        for i in range(2):
#            if myErrs[i] != expErrs[i]:
#                print myErrs[i]
#                print expErrs[i]
#                print
#===============================================================================
        self.assertEqual(myErrs, expErrs)
        self.assertEqual(myO.errCountMap, {505: 1, 501: 1})
    
    def test_lonely_topics(self):
        """DitaFileSet: Test a couple of lonely topics."""
        myO = DitaFileSet(None, procDir=False)
        myO._addFileObj(StringIO.StringIO('<spam id="spam"/>'), 'spam')
        myO._addFileObj(StringIO.StringIO('<eggs id="eggs"/>'), 'eggs')
        myO.finalise()
        self.assertEqual(
            myO.errStrings(False, None),
            [
             'Topic id="%s" is not referenced by any map' % normalisePath('eggs'),
             'Topic id="%s" is not referenced by any map' % normalisePath('spam'),
             ]
        )
        self.assertEqual(
            myO.errStrings(True, None),
            [
                genericStringForErrorCode(600),
            ]
        )

    def test_map_cycles_00(self):
        """DitaFileSet: Cyclic references between two maps."""
        myO = DitaFileSet(None, procDir=False)
        myO._addFileObj(
            StringIO.StringIO(
"""<map id="map_00">
    <topicref href="map_01.ditamap" format="ditamap" />
</map>"""
            ),
            'map_00.ditamap'
        )
        myO._addFileObj(
            StringIO.StringIO(
"""<map id="map_01">
    <topicref href="map_00.ditamap" format="ditamap" />
</map>"""
            ),
            'map_01.ditamap'
        )
        myO.finalise()
        #print 'HI test_map_cycles_00()'
        #pprint.pprint(myO._retMapAdjList())
        self.assertEqual(
            myO.errStrings(False, None),
            [
                'Maps "%s" are in a a cycle.' % str(
                    (
                     normalisePath('map_00.ditamap'),
                     normalisePath('map_01.ditamap'),
                     )
                ),
                'Maps "%s" are in a a cycle.' % str(
                    (
                     normalisePath('map_01.ditamap'),
                     normalisePath('map_00.ditamap'),
                     )
                ),
            ]
        )
        #print
        #pprint.pprint(myO.allErrStrings(False, None))
        self.assertEqual(myO.allErrStrings(True, None), [genericStringForErrorCode(701)])
        self.assertEqual(myO.errCountMap, {701 : 4})

    def test_map_cycles_01(self):
        """DitaFileSet: Cyclic references between three maps."""
        myO = DitaFileSet(None, procDir=False)
        myO._addFileObj(
            StringIO.StringIO(
"""<map id="map_00">
    <topicref href="map_01.ditamap" format="ditamap" />
</map>"""
            ),
            'map_00.ditamap'
        )
        myO._addFileObj(
            StringIO.StringIO(
"""<map id="map_01">
    <topicref href="map_02.ditamap" format="ditamap" />
</map>"""
            ),
            'map_01.ditamap'
        )
        myO._addFileObj(
            StringIO.StringIO(
"""<map id="map_02">
    <topicref href="map_00.ditamap" format="ditamap" />
</map>"""
            ),
            'map_02.ditamap'
        )
        myO.finalise()
        #print 'HI test_map_cycles_00()'
        #pprint.pprint(myO._retMapAdjList())
        self.assertEqual(
            myO.errStrings(False, None),
            [
                'Maps "%s" are in a a cycle.' % str(
                    (
                     normalisePath('map_00.ditamap'),
                     normalisePath('map_01.ditamap'),
                     normalisePath('map_02.ditamap'),
                     )
                ),
                'Maps "%s" are in a a cycle.' % str(
                    (
                     normalisePath('map_01.ditamap'),
                     normalisePath('map_02.ditamap'),
                     normalisePath('map_00.ditamap'),
                     )
                ),
                'Maps "%s" are in a a cycle.' % str(
                    (
                     normalisePath('map_02.ditamap'),
                     normalisePath('map_00.ditamap'),
                     normalisePath('map_01.ditamap'),
                     )
                ),
            ]
        )
        self.assertEqual(myO.errStrings(True, None), [genericStringForErrorCode(701)])
        self.assertEqual(myO.errCountMap, {701 : 6})

    def test_refarc_00(self):
        """DitaFileSet: Test ref arcing - all resolve."""
        myO = DitaFileSet(None, procDir=False)
        myO._addFileObj(
            StringIO.StringIO(
"""<map id="map_00">
    <topicref href="spam.dita#spam" />
    <topicref href="eggs.dita#eggs" />
</map>"""
            ),
            'map.ditamap'
        )
        myO._addFileObj(StringIO.StringIO('<topic id="spam"/>'), 'spam.dita')
        myO._addFileObj(StringIO.StringIO('<topic id="eggs"/>'), 'eggs.dita')
        myO.finalise()
        self.assertEqual(myO.errCountMap, {})
        self.assertEqual(myO.allErrStrings(False, None), [])
        self.assertEqual(myO.allErrStrings(True, None), [])
        self.assertEqual(myO.errStrings(False, None), [])
        self.assertEqual(myO.errStrings(True, None), [])

    def test_refarc_fail_00(self):
        """DitaFileSet: Test ref arcing - can't find file."""
        myO = DitaFileSet(None, procDir=False)
        myO._addFileObj(
            StringIO.StringIO(
"""<map id="map_00">
    <topicref href="spam_.dita" />
    <topicref href="eggs_for_tea.dita" />
</map>"""
            ),
            'map.ditamap'
        )
        myO.finalise()
        self.assertEqual(myO.errCountMap, {410: 2})
        #print 'HI'
        #pprint.pprint(myO.allErrStrings(False, None))
        self.assertEqual(
            myO.allErrStrings(False, None),
            [
                'Can not resolve reference to file "%s"' % normalisePath('eggs_for_tea.dita'),
                'Can not resolve reference to file "%s"' % normalisePath('spam_.dita'),
            ]
        )
        self.assertEqual(
            myO.allErrStrings(True, None),
            [
                'Can not resolve reference to file "..."',
            ]
        )
        self.assertEqual(myO.errStrings(False, None), [])
        self.assertEqual(myO.errStrings(True, None), [])

    def test_refarc_fail_01(self):
        """DitaFileSet: Test ref arcing - can't find fragment."""
        myO = DitaFileSet(None, procDir=False)
        myO._addFileObj(
            StringIO.StringIO(
"""<map id="map_00">
    <topicref href="spam.dita#spam_" />
    <topicref href="eggs.dita#eggs_" />
</map>"""
            ),
            'map.ditamap'
        )
        myO._addFileObj(StringIO.StringIO('<spam id="spam"/>'), 'spam.dita')
        myO._addFileObj(StringIO.StringIO('<eggs id="eggs"/>'), 'eggs.dita')
        myO.finalise()
        self.assertEqual(myO.errCountMap, {411: 2})
        #print 'HI'
        #pprint.pprint(myO.allErrStrings(False, None))
        self.assertEqual(
            myO.allErrStrings(False, None),
            [
                'Can resolve reference to file "%s" but not to fragment "eggs_"' % normalisePath('eggs.dita'),
                'Can resolve reference to file "%s" but not to fragment "spam_"' % normalisePath('spam.dita'),
            ]
        )
        self.assertEqual(
            myO.allErrStrings(True, None),
            [
                'Can resolve reference to file "%s" but not to fragment "%s"' % (GENERIC_STRING, GENERIC_STRING),
            ]
        )
        self.assertEqual(myO.errStrings(False, None), [])
        self.assertEqual(myO.errStrings(True, None), [])

    def test_refarc_url_00(self):
        """DitaFileSet: Test ref arcing - URL."""
        myO = DitaFileSet(None, procDir=False, testExt=True)
        myO._addFileObj(
            StringIO.StringIO(
"""<map id="map_00">
    <topicref href="spam.dita#spam" />
    <topicref href="eggs.dita#eggs" />
</map>"""
            ),
            'map.ditamap'
        )
        myO._addFileObj(StringIO.StringIO("""<topic id="spam">
        <xref href="http://www.nokia.com">Nokia</xref>
</topic>"""), 'spam.dita')
        myO._addFileObj(StringIO.StringIO("""<topic id="eggs">
        <xref href="http://www.google.com">Google</xref>
</topic>"""), 'eggs.dita')
        myO.finalise()
        #print 'HI'
        #pprint.pprint(myO.allErrStrings(False, None))
        self.assertEqual(myO.errCountMap, {})
        self.assertEqual(
            myO.allErrStrings(False, None),
            [
            ]
        )
        self.assertEqual(
            myO.allErrStrings(True, None),
            [
            ]
        )
        self.assertEqual(myO.errStrings(False, None), [])
        self.assertEqual(myO.errStrings(True, None), [])

class TestDitaBookmapFileSet(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def testSetUpTearDown(self):
        """TestDitaBookmapFileSet: test setUp() and tearDown()."""
        pass
    
    def test_basic(self):
        """TestDitaBookmapFileSet: Test reading a bookmap and a topic."""
        myO = DitaFileSet(None, procDir=False)
        myO._addFileObj(
            StringIO.StringIO(
"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE bookmap PUBLIC "-//OASIS//DTD DITA BookMap//EN"
"bookmap.dtd">
<bookmap id="GUID-5BDFDB6B-7801-4804-9F41-2BDC5BE53DDF">
  <booktitle>
    <mainbooktitle>My Bookmap</mainbooktitle>
    <booktitlealt>Alternate title</booktitlealt>
  </booktitle>
  <frontmatter id="GUID-DA857913-F826-4CF7-A135-93F2AEB48353">
    <topicref href="GUID-00025EAD-C4B6-5408-96A3-FFDBBBDC7CAB.dita" id="GUID-994B1764-393F-401F-8571-CE0955AB6CA6" />
  </frontmatter>
</bookmap>
"""
            ),
            'bookmap.ditamap'
        )
        myO._addFileObj(StringIO.StringIO("""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE concept  PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">
<concept id="GUID-00025EAD-C4B6-5408-96A3-FFDBBBDC7CAB" xml:lang="en">
    <title>How to read and write a file</title>
</concept>
"""), 'GUID-00025EAD-C4B6-5408-96A3-FFDBBBDC7CAB.dita')
        myO.finalise()
        #print
        #myO.debugDump()
        #print 'HI'
        #myO.writeErrors(False)
        self.assertEqual(myO.allErrStrings(False, None), [])
        self.assertEqual(myO.allErrStrings(True, None), [])
        self.assertEqual(myO.errCountMap, {})

class Special(unittest.TestCase):
    pass

def unitTest(theVerbosity=2):
    suite = unittest.TestLoader().loadTestsFromTestCase(NullClass)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCountDict))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDitaId))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDitaRef))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDitaFile))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDitaFileSet))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDitaBookmapFileSet))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(Special))
    myResult = unittest.TextTestRunner(verbosity=theVerbosity).run(suite)
    return (myResult.testsRun, len(myResult.errors), len(myResult.failures))

######################################
# main() stuff
######################################
def main():
    print 'CMD: %s' % ' '.join(sys.argv)
    usage = "usage: %prog [options] <Directory of XML content>"
    parser = OptionParser(usage, version='%prog ' + __version__)
    parser.add_option("-d", action="store_true", dest="dump", default=False, 
                      help="Dump internal representation. [default: %default]")
    parser.add_option(
            "-e", "--errors",
            type="str",
            dest="error_codes",
            default='All',
            help="Only report on certain error codes (space seperated list). [default: \"%default\"]"
        )      
    parser.add_option("-f", "--file", dest="file", type="str", default='None', 
                      help="Report of errors by file either 'None', 'generic', 'specific'. [default: %default]")
    parser.add_option("-g", action="store_true", dest="guid", default=False, 
                      help="Enforce GUID specification. [default: %default]")
    parser.add_option(
            "-j", "--jobs",
            type="int",
            dest="jobs",
            default=-1,
            help="Max processes when multiprocessing. 0 takes CPUs, -1 no MP. [default: %default]"
        )      
    parser.add_option(
            "-l", "--loglevel",
            type="int",
            dest="loglevel",
            default=20,
            help="Log Level (debug=10, info=20, warning=30, [error=40], critical=50) [default: %default]"
        )      
    parser.add_option(
            "-p", "--pattern",
            type="str",
            dest="pattern",
            default=FNMATCH_STRING,
            help="Pattern match. [default: \"%default\"]"
        )      
    parser.add_option("-r", action="store_true", dest="recursive", default=False, 
                      help="Recursive. [default: %default]")
    parser.add_option("-s", action="store_true", dest="shelve", default=False, 
                      help="Use the shelve dBase rather than storing the internal representation in memory. This is slower but is useful for large data sets where a memory error might occur. [default: %default]")
    parser.add_option("-u", action="store_true", dest="unit_test", default=False, 
                      help="Execute unit tests and exit. [default: %default]")
    parser.add_option("-x", action="store_true", dest="ext_url", default=False, 
                      help="Test external |URLs. [default: %default]")
    parser.add_option("-?", action="store_true", dest="query_errors", default=False, 
                      help="Display the error types that are detected. [default: %default]")
    (options, args) = parser.parse_args()
    logging.basicConfig(
        level=options.loglevel,
        format='%(asctime)s %(levelname)-8s %(message)s',
        stream=sys.stdout,
    )
    if options.file not in ('None', 'generic', 'specific'):
        parser.error("--file option must be: 'None' | 'generic' | 'specific'")
        return 1
    if options.unit_test:
        unitTest()
    if options.query_errors:
        writeGenericStringsForErrorCodes()
    if len(args) < 1 and not options.unit_test:
        parser.print_help()
        parser.error("I can't do much without a path to the XML content.")
        return 1
    elif len(args) == 1:
        if options.jobs > -1:
            myObj = retMpDitaFileSetObj(
                        args[0],
                        options.pattern.split(' '),
                        options.recursive,
                        options.jobs,
                        options.ext_url,
                        options.shelve,
                        )
        else:
            myObj = DitaFileSet(args[0],
                                procDir=True,
                                thePatterns=options.pattern.split(' '),
                                recursive=options.recursive,
                                testExt=options.ext_url,
                                useDbase=options.shelve,
                                )
            #print 'MyObj:', myObj
        if options.dump:
            myObj.debugDump()
        myObj.writeStatistics()
        myObj.writeErrorSummary()
        #pprint.pprint(myObj.statsMap)
        # TODO: Write out the results in different ways
        errFilter = set(PROBLEM_CODE_FORMAT.keys())
        if options.error_codes != 'All':
            errFilter = set([int(i) for i in options.error_codes.split()])
        if options.file == 'generic':
            print 'Generic problems:'
            myObj.writeErrors(True, errFilter)
        elif options.file == 'specific':
            print 'Specific problems:'
            myObj.writeErrors(False, errFilter)
    elif len(args) > 1:
        parser.error("Too many arguments, I need only one.")
        return 1
    return 0

if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.exit(main())
