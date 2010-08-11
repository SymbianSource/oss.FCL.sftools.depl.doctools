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
Created on 24 May 2010

@author: p2ross
"""
import os
import sys
import logging
#import pprint
#import fnmatch
#import re
import string
import time
from optparse import OptionParser#, check_choice
try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree
#import multiprocessing

__version__ = "0.1.0"


class XsdBase(object):
    PREFIX = '{http://www.w3.org/2001/XMLSchema}'
    def _addSchemaPrefix(self, theTag):
        return '%s%s' % (self.PREFIX, theTag)
    
    def _tagSchemaMatches(self, theN, theTag):
        return theN.tag == self._addSchemaPrefix(theTag)
    
    def _tagSchemaMatchesList(self, theN, theTagS):
        for aTag in theTagS:
            if theN.tag == self._addSchemaPrefix(aTag):
                return True
        return False
    
    def _stripSchemaPrefix(self, theN):
        """Returns theNode.tag without the schema prefix."""
        return theN.tag[len(self.PREFIX):]

class XsdNodeBase(XsdBase):
    PREFIX = '{http://www.w3.org/2001/XMLSchema}'
    def __init__(self, theN):
        super(XsdNodeBase, self).__init__()
        self._name = theN.get('name')
        self._ref = theN.get('ref')
        # This will be prefix+element
        self._tag = theN.tag
        self._min = int(theN.get('minOccurs') or 1)
        if theN.get('maxOccurs') == 'unbounded':
            self._max = -1
        else:
            self._max = int(theN.get('maxOccurs') or 1)
        logging.debug(
            'XsdNodeBase.__init__(): tag=%s, name=%s, ref=%s, min=%d, max=%d',
            self.tag,
            self._name,
            self._ref,
            self._min,
            self._max,
            )
    
    @property
    def tag(self):
        return self._tag[len(self.PREFIX):]
    
    @property
    def attrRef(self):
        return self._ref
    
    @property
    def attrName(self):
        return self._name
    
    @property
    def isUnbounded(self):
        return self._max == -1
    
    @property
    def minOccurs(self):
        return self._min

    @property
    def maxOccurs(self):
        return self._max
    
    @property
    def boundedString(self):
        """Returns a natural language description of bounds."""
        if self._min == 1 and self._max == 1:
            return ''
        elif self._min == 0:
            if self._max == 1:
                # minOccurs="0" -> 'optional'
                return 'optional'
            elif self.isUnbounded:
                # minOccurs="0" maxOccurs="unbounded" -> 'any number'
                return 'any number'
            else:
                # minOccurs="0" maxOccurs="42" -> 'up to 42'
                return 'up to %d' % self._max
        elif self.isUnbounded:
            # minOccurs="17" maxOccurs="unbounded" -> 'at least 17'
            return 'at least %d' % self._min
        # minOccurs="17" maxOccurs="42" -> 'at least 17 and up to 42'
        return 'at least %d, and up to %d' % (self._min, self._max)

class Attribute(XsdNodeBase):
    """Represents an element describing an attribute."""
    def __init__(self, theN):
        super(Attribute, self).__init__(theN)
        assert(self._tagSchemaMatches(theN, 'attribute'))
        self._default = theN.get('default')
        self._use = theN.get('use')
        
    @property
    def default(self):
        return self._default

    @property
    def use(self):
        return self._use

class RefBase(XsdNodeBase):
    """Represents a reference to a group or element"""
    def __init__(self, theN):
        super(RefBase, self).__init__(theN)
        assert(self._tagSchemaMatchesList(theN, ('group', 'element')))
        assert(self.attrRef is not None)

    @property
    def isSequence(self):
        return False

class RefSequence(XsdNodeBase):
    """Holds information on an xs:all, xs:choice or xs:sequence."""
    def __init__(self, theN):
        super(RefSequence, self).__init__(theN)
        assert(self._tagSchemaMatchesList(theN, ('all', 'choice', 'sequence'))), 'Tag %s not in list' % theN.tag
        # List of class RefBase or, recursively, a class RefSequence
        self._refS = []
        self._type = self.tag
        for aChild in theN.getchildren():
            if not self._tagSchemaMatchesList(aChild, ('group', 'all', 'choice', 'sequence')):
                continue
            #self._type = self._stripSchemaPrefix(aChild)
            if self._tagSchemaMatches(aChild, 'group'):
                self._refS.append(RefBase(aChild))
            elif self._tagSchemaMatchesList(
                        aChild,
                        ('choice', 'sequence', 'any',)
                    ):
                self._refS.append(RefSequence(aChild))

    def genRefs(self):
        """Generates the list of RefBase or RefSequence"""
        for aRef in self._refS:
            yield aRef

    @property
    def numRefs(self):
        return len(self._refS)
    
    @property
    def refs(self):
        return self._refS
    
    @property
    def isSequence(self):
        return True

    def qualifierString(self):
        if self._type == 'all':
            return '(any number, any order)'
        elif self._type == 'choice':
            return '(any number)'
        elif self._type == 'sequence':
            return ''
        return 'Unknown'
    
    def joinString(self):
        if self._type == 'all':
            return ' or '
        elif self._type == 'choice':
            return ' or '
        elif self._type == 'sequence':
            return ' then '
        return ''
    
    @property
    def seqType(self):
        return self._type

class DefBase(XsdNodeBase):
    """Represents a definition of a group, element or complexType"""
    def __init__(self, theN):
        super(DefBase, self).__init__(theN)
        assert(self._tagSchemaMatchesList(theN, ('group', 'element', 'complexType'))), 'Tag %s not in list' % theN.tag
        assert(self.attrName is not None or self._tagSchemaMatches(theN, 'complexType'))
        # List of class RefBase of class RefSequence
        self._refS = []

    def genRefs(self):
        """Generates the list of RefBase"""
        for aRef in self._refS:
            yield aRef

    @property
    def numRefs(self):
        return len(self._refS)
    
    @property
    def refs(self):
        return self._refS
            
class GroupDef(DefBase):
    """Represents the definition of a group i.e. <xs:group name="...">...</xs:group>.
    See: http://www.w3.org/TR/2004/REC-xmlschema-1-20041028/structures.html#element-group"""
    def __init__(self, theN):
        super(GroupDef, self).__init__(theN)
        assert(theN.tag == self._addSchemaPrefix('group'))
        # http://www.w3.org/TR/2004/REC-xmlschema-1-20041028/structures.html#element-group
        # Content: (annotation?, (all | choice | sequence)?)
        self._type = None
        for aChild in theN.getchildren():
            if self._tagSchemaMatchesList(aChild, ('all', 'choice', 'sequence')):
                self._type = self._stripSchemaPrefix(aChild)
            else:
                # Unrecognised element or annotation
                continue
            if self._type is not None:
                # Read grand children and break
                for aGrandChild in aChild.getchildren():
                    if aGrandChild.get('ref') is not None \
                    and self._tagSchemaMatchesList(
                                aGrandChild,
                                (
                                    'element',
                                    'group',
                                    #'choice',
                                    #'sequence',
                                    #'any',
                                )):
                        self._refS.append(RefBase(aGrandChild))
                break
        
    def __str__(self):
        #print 'TRACE:', self._refS
        return self.joinString().join(['%s' % r.attrRef for r in self._refS]) \
            + ' ' \
            + self.qualifierString() 
    
    def qualifierString(self):
        if self._type == 'all':
            return '(any number, any order)'
        elif self._type == 'choice':
            return '(any number)'
        elif self._type == 'sequence':
            return ''
        return 'Unknown'
    
    def joinString(self):
        if self._type == 'all':
            return ' or '
        elif self._type == 'choice':
            return ' or '
        elif self._type == 'sequence':
            return ' then '
        return ''
    
    @property
    def groupType(self):
        return self._type
    
class ComplexTypeDef(DefBase):#XsdNodeBase):
    """Represents the definition of a complexType definition i.e. <xs:complexType name="...">...</xs:group>.
    See: http://www.w3.org/TR/2004/REC-xmlschema-1-20041028/structures.html#element-complexType"""
    def __init__(self, theN):
        super(ComplexTypeDef, self).__init__(theN)
        assert(theN.tag == self._addSchemaPrefix('complexType'))
        # http://www.w3.org/TR/2004/REC-xmlschema-1-20041028/structures.html#element-complexType
        # Simplified content: ((group | all | choice | sequence)?
        self._type = None
        # Get xs:attribute
        self._attrS = []
        for aChild in theN.getchildren():
            # We only handle complexType
            if not self._tagSchemaMatchesList(
                    aChild,
                    ('group', 'all', 'choice', 'sequence', 'attribute')):
                # Unrecognised element or annotation
                continue
            self._type = self._stripSchemaPrefix(aChild)
            if self._tagSchemaMatches(aChild, 'group'):
                self._refS.append(RefBase(aChild))
            elif self._tagSchemaMatchesList(
                                aChild,
                                ('choice', 'sequence', 'any',),
                                ):
                self._refS.append(RefSequence(aChild))
            elif self._tagSchemaMatches(aChild, 'attribute'):
                self._attrS.append(Attribute(aChild))

    @property
    def groupType(self):
        return self._type
    
    def namedAttribute(self, theName):
        """Returns an Attribute object or None."""
        for anA in self._attrS:
            if anA.attrName == theName:
                return anA

class ElementDef(DefBase):
    """Represents the definition of a element definition i.e. <xs:element name="...">...</xs:group>.
    See: http://www.w3.org/TR/2004/REC-xmlschema-1-20041028/structures.html#element-group"""
    def __init__(self, theN):
        super(ElementDef, self).__init__(theN)
        assert(theN.tag == self._addSchemaPrefix('element'))
        # http://www.w3.org/TR/2004/REC-xmlschema-1-20041028/structures.html#element-element
        # Simplified content: (annotation?, ((simpleType | complexType)?
        self._type = None
        self._complexType = None
        for aChild in theN.getchildren():
            # We only handle complexType
            if not self._tagSchemaMatchesList(aChild, ('complexType',)):
                # Unrecognised element or annotation
                continue
            # Process a <complexType>
            self._complexType = ComplexTypeDef(aChild)
            break
    
    @property
    def complexType(self):
        return self._complexType

class GroupRef(RefBase):
    """Represents a reference of a group i.e. <xs:group ref="..." .../>.
    See: http://www.w3.org/TR/2004/REC-xmlschema-1-20041028/structures.html#element-group"""
    def __init__(self, theN):
        super(GroupRef, self).__init__(theN)
        assert(theN.tag == self._addSchemaPrefix('group'))

class ElementRef(RefBase):
    """Represents a reference to an element i.e. <xs:element ref="..." .../>.
    See: http://www.w3.org/TR/2004/REC-xmlschema-1-20041028/structures.html#element-group"""
    def __init__(self, theN):
        super(ElementRef, self).__init__(theN)
        assert(theN.tag == self._addSchemaPrefix('element'))

class XsdToPackageDef(XsdBase):
    """Create a PackageDef.xml file from a set of XSD files."""
    DUMP_PREFIX = '  '
    def __init__(self, thePrefix):#, theOutFile=None, theTitle=''):
        super(XsdToPackageDef, self).__init__()
        # Maps of group definitions and references
        self._groupDefMap = {}
        self._groupRefMap = {}
        # Maps of element definitions and references
        self._elemDefMap = {}
        self._elemRefMap = {}
        # Top level complex types
        self._complexTypeMap = {}
        # Element prefix
        self._prefix = thePrefix
            
    ##########################
    # Section: Add an XSD file
    ##########################
    def addXsdFile(self, thePath):
        """Read an XSD and add it to the representation."""
        t = etree.parse(thePath)
        r = t.getroot()
        self._addGroups(r)
        self._addElements(r)
        self._addComplexTypes(r)
    
    def addXsdPath(self, thePath):
        if os.path.isfile(thePath):
            if os.path.splitext(thePath)[1].lower() == '.xsd':
                self.addXsdFile(thePath)
        elif os.path.isdir(thePath):
            for aName in os.listdir(thePath):
                self.addXsdPath(os.path.join(thePath, aName))

    def _addGroups(self, root):
        """Adds to the group maps."""
        for anE in root.getchildren():
            if self._tagSchemaMatches(anE, 'group'):
                if anE.get('name') is not None:
                    self._groupDefMap[anE.get('name')] = GroupDef(anE)
                elif anE.get('ref') is not None:
                    self._groupRefMap[anE.get('ref')] = GroupRef(anE)
                
    def _addElements(self, root):
        """Adds to the element maps."""
        for anE in root.getchildren():
            if self._tagSchemaMatches(anE, 'element'):
                if anE.get('name') is not None:
                    self._elemDefMap[anE.get('name')] = ElementDef(anE)
                elif anE.get('ref') is not None:
                    self._elemRefMap[anE.get('ref')] = ElementRef(anE)
    
    def _addComplexTypes(self, root):
        for anE in root.getchildren():
            if self._tagSchemaMatches(anE, 'complexType'):
                self._complexTypeMap[anE.get('name')] = ComplexTypeDef(anE)
    ##########################
    # End: Add an XSD file
    ##########################

    ##########################
    # Section: Query the IR
    ##########################
    def elemContains(self, theElemName):
        """Returns a list of immediate child elements that this element contains."""
        logging.debug('elemContains(%s)' % theElemName)
        retVal = []
        if not self._elemDefMap.has_key(theElemName):
            return retVal
        myElem = self._elemDefMap[theElemName]
        if myElem.complexType is not None:
            logging.debug('elemContains(): complexType: %s', myElem.complexType)
            #print 'myElem', myElem
            for aRef in myElem.complexType.genRefs():
                logging.debug('elemContains(): complexType tag: %s, attrRef: %s',
                              aRef.tag,
                              aRef.attrRef,
                        )
                self._addFromComplexTypeSequence(aRef, retVal)
#                myRef = aRef.attrRef
#                #print 'myRef', myRef
#                #if self._elemDefMap.has_key(myRef):
#                #    retVal.append(myRef)
#                if self._groupDefMap.has_key(myRef):
#                    self._addContainsGroup(myRef, retVal)
#                else:
#                    retVal.append(myRef)
        logging.debug('elemContains(%s) returns %s', theElemName, str(retVal))
        return retVal
    
    def _addFromComplexTypeSequence(self, theRefObj, theList):
        """Recursively add containing elements."""
        myRef = theRefObj.attrRef
        logging.debug('_addFromComplexTypeSequence(%s):', myRef) 
        if theRefObj.isSequence:
            for aSubRef in theRefObj.refs:
                logging.debug('_addFromComplexTypeSequence(): recursing on: %s',
                              myRef)
                self._addFromComplexTypeSequence(aSubRef, theList)
        elif myRef is not None:
            if self._groupDefMap.has_key(myRef):
                self._addContainsGroup(myRef, theList)
            else:
                logging.debug('_addFromComplexTypeSequence(): adding: %s',
                              myRef)
                theList.append(myRef)
    
    def _addContainsGroup(self, theRef, theList):
        logging.debug('_addContainsGroup(%s)' % theRef)
        assert(self._groupDefMap.has_key(theRef))
        for aRef in self._groupDefMap[theRef].genRefs():
            #print 'TRACE: aRef', aRef.tag
            logging.debug('_addContainsGroup(): aRef.tag: %s aRef.attrRef: %s' \
                          % (aRef.tag, aRef.attrRef))
            if aRef.tag == 'element':
                theList.append(aRef.attrRef)
            elif aRef.tag == 'group' and self._groupDefMap.has_key(aRef.attrRef):
                self._addContainsGroup(aRef.attrRef, theList)

    ##########################
    # End: Query the IR
    ##########################
    
    ##########################
    # Section: Debug/trace
    ##########################
    def dump(self, s=sys.stdout):
        s.write(' Group definitions '.center(75, '-')+'\n')
        keyS = self._groupDefMap.keys()
        keyS.sort()
        for k in keyS:
            s.write('%40s : %s\n' % (k, self._groupDefMap[k]))
        s.write(' EOL '.center(75, '-')+'\n\n') 
        s.write(' Group references '.center(75, '-')+'\n') 
        keyS = self._groupRefMap.keys()
        keyS.sort()
        for k in keyS:
            s.write('%40s : %s\n' % (k, self._groupRefMap[k]))
        s.write(' EOL '.center(75, '-')+'\n\n') 
        s.write(' Element definitions '.center(75, '-')+'\n') 
        keyS = self._elemDefMap.keys()
        keyS.sort()
        for k in keyS:
            s.write('%40s : %s\n' % (k, self._elemDefMap[k]))
        s.write(' EOL '.center(75, '-')+'\n\n') 
        s.write(' Element references '.center(75, '-')+'\n') 
        keyS = self._elemRefMap.keys()
        keyS.sort()
        for k in keyS:
            s.write('%40s : %s\n' % (k, self._elemRefMap[k]))
        s.write(' EOL '.center(75, '-')+'\n\n') 
        s.write(' Complex types '.center(75, '-')+'\n') 
        keyS = self._complexTypeMap.keys()
        keyS.sort()
        for k in keyS:
            s.write('%40s : %s\n' % (k, self._complexTypeMap[k]))
        s.write(' EOL '.center(75, '-')+'\n\n') 
        s.write(' Parent to child relationship '.center(75, '-')+'\n')
        # A map {element_name : [parent element, ...], ...}
        myPcMap = self._retContainedByMap()
        keyS = myPcMap.keys()
        keyS.sort()
        for k in keyS:
            s.write('Child: %s\n' % k)
            s.write('    Contained by: %s\n' % myPcMap[k])
        s.write(' EOL '.center(75, '-')+'\n\n') 
        # Run through the elements
        keyS = self._elemDefMap.keys()
        keyS.sort()
        for k in keyS:
            myElem = self._elemDefMap[k]
            s.write('Element: %s\n' % k)
            if myElem.complexType is not None:
                for aRef in myElem.complexType.genRefs():
                    #print 'TRACE: aRef', aRef
                    if aRef.isSequence:
                        self._dumpSequenceRef(s, aRef, level=1)
                    else:
                        self._dumpRef(s, aRef, level=1)
            else:
                s.write('  No complexType\n')
            s.write('\n')
            
    def _dumpRef(self, s, theRef, level=1):
        assert(not theRef.isSequence)
        if self._groupDefMap.has_key(theRef.attrRef):
            s.write('%s%s %s [%s]\n' \
                    % (self.DUMP_PREFIX*level,
                       theRef.attrRef,
                       '(group)',
                       theRef.boundedString,
                       #self._groupDefMap[aRef.attrRef].boundedString,
                    )
                )
            self._dumpGroupRef(s, theRef.attrRef, level)
            #for aGm in self._groupDefMap[aRef.attrRef].genRefs():
            #    print '  <%s> %s %s %s' \
            #        % (aGm.tag, aGm.attrName, aGm.attrRef, aGm.boundedString)
        elif self._elemDefMap.has_key(theRef.attrRef):
            s.write('%s%s %s\n' % (self.DUMP_PREFIX*level, theRef.attrRef, '(element)'))
        elif self._complexTypeMap.has_key(theRef.attrRef):
            s.write('%s%s %s\n' % (self.DUMP_PREFIX*level, theRef.attrRef, '(complex)'))
        else:
            s.write('%s%s %s\n' % (self.DUMP_PREFIX*level, theRef.attrRef, '(not in my IR)'))

    def _dumpGroupRef(self, s, theR, level=1):
        """Dump out references to groups, recursively using self._groupDefMap."""
        assert(self._groupDefMap.has_key(theR))
        if self._groupDefMap[theR].numRefs == 1 \
        and self._groupDefMap[theR].refs[0].tag == 'element':
            s.write('%sELEMENT<%s> %s %s "%s" [%s]\n' \
                    % (
                       self.DUMP_PREFIX*level,
                       self._groupDefMap[theR].refs[0].tag,
                       self._groupDefMap[theR].refs[0].attrName,
                       self._groupDefMap[theR].refs[0].attrRef,
                       self._groupDefMap[theR].refs[0],
                       self._groupDefMap[theR].refs[0].boundedString,
                       )
                )
        else:
            s.write('%sGROUP  <%s>%s\n' \
                % (self.DUMP_PREFIX*level, self._groupDefMap[theR].tag, self._groupDefMap[theR]))
            for aGm in self._groupDefMap[theR].genRefs():
                #print '%s<%s> %s %s "%s"' \
                #    % (self.DUMP_PREFIX*level, aGm.tag, aGm.attrName, aGm.attrRef, aGm)#aGm.boundedString)
                if aGm.tag == 'group' \
                and aGm.attrRef \
                and self._groupDefMap.has_key(aGm.attrRef):
                    self._dumpGroupRef(s, aGm.attrRef, level+1)
                elif aGm.tag == 'element':
                    s.write('%sCHLDELE<%s> %s %s "%s"\n' \
                        % (self.DUMP_PREFIX*level, aGm.tag, aGm.attrName, aGm.attrRef, aGm))#aGm.boundedString)

    def _dumpSequenceRef(self, s, theR, level=1):
        """Dump out sequences recursively."""
        assert(theR.isSequence)
        for i, aRef in enumerate(theR.genRefs()):
            if i > 0:
                s.write('%s[%s]\n' % (self.DUMP_PREFIX*level, theR.joinString()))
            #print '%sTRACE: _dumpSequenceRef aRef: %s' % (self.DUMP_PREFIX*level, aRef)
            if aRef.isSequence:
                self._dumpSequenceRef(s, aRef, level=level+1)
            else:
                self._dumpRef(s, aRef, level=level+1)
        s.write('%s[%s]\n' % (self.DUMP_PREFIX*level, theR.qualifierString()))
    ##########################
    # End: Debug/trace
    ##########################
        
    ##########################
    # Section: Output
    ##########################
    def _writeHeader(self, theS, theTitle):
        self._writeLine(theS, '<?xml version="1.0" encoding="UTF-8"?>')
        self._writeLine(theS, """<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "../../dtd/reference.dtd">""")
        self._writeLine(theS, """<reference id="%sapiref" xml:lang="en-us">""" % self._prefix)
        self._writeLine(theS, '<title>%s</title>' % theTitle)
        
    def _writeLine(self, theS, theL):
        theS.write(theL)
        theS.write('\n')
        
    def _write(self, theS, theStr):
        theS.write(theStr)

    def close(self, theS):
        self._writeLine(theS, '</reference>')
        theS.close()
    
    def _retContainedByMap(self):
        """Returns a map {element_name : [parent element, ...], ...}."""
        retMap = {}
        keyS = self._elemDefMap.keys()
        # Ensure that every element is represented
        for myName in keyS:
            retMap[myName] = []
        for myName in keyS:
            myContainS = self.elemContains(myName)
            for aChild in myContainS:
                try:
                    retMap[aChild].append(myName)
                except KeyError:
                    retMap[aChild] = [myName]
        return retMap

    def _retDirName(self, theName):
        assert(theName.startswith(self._prefix))
        # Slice the name to get the directory
        # e.g. 'cxxVariableDeclarationFile' becomes 'cxxVariable'
        # Special case where all ...Ref.dita are in cxxAPIMap/
        if theName.endswith('Ref') \
        or theName == 'cxxAPIMap':
            return 'cxxAPIMap'
        i = len(self._prefix) + 1
        while i < len(theName) and theName[i] in string.lowercase:
            i += 1
        retVal = theName[:i]
        # This is a bit clunky for these special cases
        if retVal in ('cxxEnumerator', 'cxxEnumerators'):
            retVal = 'cxxEnumeration'
        return retVal

    def _writeElementNameToFile(self, theS, theName):
        if self._elemDefMap.has_key(theName) \
        and theName.startswith(self._prefix):
            # Slice the name to get the directory
            theDir = self._retDirName(theName)
            self._writeLine(theS, '<xref href="%s/%s.dita">%s</xref> ' \
                            % (theDir, theName, theName)
                        )
        else:
            # Write out as a keyword
            self._writeLine(theS, '<keyword>%s</keyword>, ' % theName)

    def _writeContentModelToStream(self, theS, theName):
        assert(self._elemDefMap.has_key(theName))
        hasWritten = False
        myElem = self._elemDefMap[theName]
        if myElem.complexType is not None:
            for aRef in myElem.complexType.genRefs():
                #print 'TRACE: aRef', aRef
                if aRef.isSequence:
                    if self._writeContentModelSequenceRef(theS, aRef):
                        hasWritten = True
                else:
                    if self._writeContentModelRef(theS, aRef):
                        hasWritten = True
        return hasWritten

    def _writeContentModelSequenceRef(self, theS, theR):
        assert(theR.isSequence)
        hasWritten = False
        if theR.numRefs > 0:
            self._write(theS, '(')
        for i, aRef in enumerate(theR.genRefs()):
            if i > 0:
                self._writeLine(theS, ' %s ' % theR.joinString())
                hasWritten = True
            if aRef.isSequence:
                if self._writeContentModelSequenceRef(theS, aRef):
                    hasWritten = True
            else:
                if self._writeContentModelRef(theS, aRef):
                    hasWritten = True
        if theR.qualifierString():
            self._writeLine(theS, '<i>%s</i>' % theR.qualifierString())
        if theR.numRefs > 0:
            self._write(theS, ')')
        return hasWritten

    def _writeContentModelRef(self, theS, theR):
        assert(not theR.isSequence)
        hasWritten = False
        if self._groupDefMap.has_key(theR.attrRef):
            #s.write('%s %s\n' % (theR.attrRef, '(group)'))
            self._writeContentModelGroupRefToStream(theS, theR)#.attrRef)
            hasWritten = True
        elif self._elemDefMap.has_key(theR.attrRef):
            pass#s.write('%s %s\n' % (theR.attrRef, '(element)'))
        elif self._complexTypeMap.has_key(theR.attrRef):
            pass#s.write('%s %s\n' % (theR.attrRef, '(complex)'))
        else:
            #s.write('%s %s\n' % (theR.attrRef, '(not in my IR)'))
            self._writeLine(theS, '<keyword>%s</keyword>, ' % theR.attrRef)
            hasWritten = True
        return hasWritten

    def _writeContentModelGroupRefToStream(self, theS, theR):
        assert(self._groupDefMap.has_key(theR.attrRef))
        myGroup = self._groupDefMap[theR.attrRef]
        if myGroup.numRefs == 1 \
        and myGroup.refs[0].tag == 'element':
#            s.write('%sELEMENT<%s> %s %s "%s"\n' \
#                    % (
#                       self.DUMP_PREFIX*level,
#                       self._groupDefMap[theR.attrRef].refs[0].tag,
#                       self._groupDefMap[theR.attrRef].refs[0].attrName,
#                       self._groupDefMap[theR.attrRef].refs[0].attrRef,
#                       self._groupDefMap[theR.attrRef].refs[0],
#                       )
#                )
            #self._write(theS, '(')
            aN = myGroup.refs[0].attrRef
            self._writeElementNameToFile(theS, aN)
            #self._writeLine(theS, '<xref href="%s/%s.dita">%s</xref>, %s' \
            #                % (aN, aN, aN, theR.boundedString))
            if theR.boundedString:
                self._writeLine(theS, '(<i>%s</i>)' % theR.boundedString)
            #self._write(theS, ')')
        else:
            #s.write('%sGROUP  <%s>%s\n' \
            #    % (self.DUMP_PREFIX*level, self._groupDefMap[theR.attrRef].tag, self._groupDefMap[theR.attrRef]))
            if myGroup.numRefs > 0:
                self._write(theS, '(')
            for i, aGm in enumerate(myGroup.genRefs()):
                #print '%s<%s> %s %s "%s"' \
                #    % (self.DUMP_PREFIX*level, aGm.tag, aGm.attrName, aGm.attrRef, aGm)#aGm.boundedString)
                if i > 0:
                    self._writeLine(theS, myGroup.joinString())
                if aGm.tag == 'group' \
                and aGm.attrRef \
                and self._groupDefMap.has_key(aGm.attrRef):
                    self._writeContentModelGroupRefToStream(theS, aGm)#.attrRef)
                elif aGm.tag == 'element' \
                and aGm.attrRef:
                    self._writeElementNameToFile(theS, aGm.attrRef)
                    #if self._elemDefMap.has_key(aGm.attrRef):
                    #    aN = aGm.attrRef
                    #    self._writeLine(theS, '<xref href="%s/%s.dita">%s</xref>, ' % (aN, aN, aN))
                    #else:
                    #    self._writeLine(theS, '<keyword>%s</keyword>, ' % aGm.attrRef)
                #elif aGm.tag == 'element':
                #    s.write('%sCHLDELE<%s> %s %s "%s"\n' \
                #        % (self.DUMP_PREFIX*level, aGm.tag, aGm.attrName, aGm.attrRef, aGm))#aGm.boundedString)
            self._writeLine(theS, self._groupDefMap[theR.attrRef].qualifierString())
            if myGroup.numRefs > 0:
                self._write(theS, ')')
    
    def writeToFile(self, thePath, theTitle):
        myS = open(thePath, 'w')
        self._writeHeader(myS, theTitle)
        #self.dump()
        myChildParentMap = self._retContainedByMap()
        #print 'TRACE: myChildParentMap', myChildParentMap
        # Run through the elements
        keyS = self._elemDefMap.keys()
        keyS.sort()
        for myName in keyS:
            myElem = self._elemDefMap[myName]
            logging.info('Writing element: <%s>' % myName)
            self._writeLine(myS, '<reference id="%s-reference" xml:lang="en-us">' % myName)
            self._writeLine(myS, '<title>Element: %s</title>' % myName)
            self._writeLine(myS, '<refbody>')
            # Section: Contained by
            self._writeLine(myS, '<section id="%s-containedBy-section" outputclass="elementContainedBy">' % myName)
            self._writeLine(myS, '<title>Contained by</title>')
            self._writeLine(myS, '<p id="%s-containedBy-p">' % myName)
            for aParent in myChildParentMap[myName]:
                self._writeElementNameToFile(myS, aParent)
                #if self._elemDefMap.has_key(aParent):
                #    self._writeLine(myS, '<xref href="%s/%s.dita">%s</xref>, ' \
                #                    % (aParent, aParent, aParent))
                #else:
                #    # Write out as a keyword
                #    self._writeLine(myS, '<keyword>%s</keyword>, ' % aParent)
            self._writeLine(myS, '</p>')
            self._writeLine(myS, '</section>')
            # Section: Contains
            self._writeLine(myS,
                '<section id="%s-contains-section" outputclass="elementContains">' % myName)
            self._writeLine(myS, '<title>Contains</title>')
            self._writeLine(myS, '<p id="%s-contains-p">' % myName)
            myContainS = self.elemContains(myName)
            myContainS.sort()
            #print 'myContainS', myContainS
            for aN in myContainS:
                self._writeElementNameToFile(myS, aN)
            self._writeLine(myS, '</p>')
            self._writeLine(myS, '</section>')
            # Section: Content Model
            self._writeLine(myS, '<section id="%s-contentModel-section" outputclass="elementContentModel">' % myName)
            self._writeLine(myS, '<title>Content Model</title>')
            self._writeLine(myS, '<p id="%s-contentModel-p">' % myName)
            # Content model contents
            if not self._writeContentModelToStream(myS, myName):
                self._writeLine(myS, 'No content.')
            self._writeLine(myS, '</p>')
            self._writeLine(myS, '</section>')
            # Section: Attributes - empty
            self._writeLine(myS, '<section id="%s-attList-section" outputclass="elementAttList" />' % myName)
            # Section: classValue
            self._writeLine(myS, '<section id="%s-classValue-section" outputclass="elementClassValue">' % myName)
            self._writeLine(myS, '<title>Inheritance</title>')
            self._writeLine(myS, '<p id="%s-classValue-p">' % myName)
            if myElem.complexType is not None:
                myClassAttr = myElem.complexType.namedAttribute('class')
                if myClassAttr is not None \
                and myClassAttr.default is not None:
                    #print 'TRACE: myClassAttr.default: "%s"' % myClassAttr.default
                    for aStr in myClassAttr.default[1:].strip().split():
                        if aStr.find('/') != -1:
                            a,b = aStr.split('/')
                            myS.write(' %s/' % a)
                            myS.write('<keyword>%s</keyword>' % b)
            self._writeLine(myS, '</p>')
            self._writeLine(myS, '</section>')
            self._writeLine(myS, '</refbody>')
            self._writeLine(myS, '</reference>')
        self.close(myS)
    
    ##########################
    # End: Output
    ##########################

def main():
    usage = """usage: %prog [options] file_or_dir
Takes a XSD file or directory and generates a packagedef.dita file with
the documentation for the XSD file(s)."""
    print 'Cmd: %s' % ' '.join(sys.argv)
    optParser = OptionParser(usage, version='%prog ' + __version__)
    optParser.add_option("-d", action="store_true", dest="dump", default=False, 
                      help="Dump IR (for debugging). [default: %default]")
    optParser.add_option(
            "-l", "--loglevel",
            type="int",
            dest="loglevel",
            default=20,
            help="Log Level (debug=10, info=20, warning=30, error=40, critical=50) [default: %default]"
        )      
    optParser.add_option("-o", "--out",
                         type="string",
                         dest="output",
                         default=None, 
                         help="Output file. [default: %default]")
#===============================================================================
#    optParser.add_option("-u", "--unittest",
#                         action="store_true",
#                         dest="unit_test",
#                         default=False, 
#                         help="Execute unit tests. [default: %default]")
#===============================================================================
    optParser.add_option("-t", "--title", type="string", dest="title",
                         default='C++ API Reference Content Model Definitions', 
                         help="Title for the packagedef.dita. [default: %default]")
    optParser.add_option("-p", "--prefix", type="string", dest="prefix",
                         default='cxx', 
                         help="Prefix, only the elements starting with this will be documented. Use '' for all. [default: %default]")
    opts, args = optParser.parse_args()
    clkStart = time.clock()
    # Initialise logging etc.
    logging.basicConfig(level=opts.loglevel,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    #datefmt='%y-%m-%d % %H:%M:%S',
                    stream=sys.stdout)
#===============================================================================
#    if opts.unit_test:
#        unitTest()
#===============================================================================
    if len(args) > 0:
        # Your code here
        myX = XsdToPackageDef(opts.prefix)
        for aFile in args:
            myX.addXsdPath(aFile)
        myX.writeToFile(opts.output, opts.title)
        if opts.dump:
            myX.dump()
    else:
        optParser.print_help()
        optParser.error("No arguments!")
        return 1
    clkExec = time.clock() - clkStart
    print 'CPU time = %8.3f (S)' % clkExec
    print 'Bye, bye!'
    return 0

if __name__ == '__main__':
    #multiprocessing.freeze_support()
    sys.exit(main())
 
