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
#
import os
import unittest
import sys
import logging
import pprint
from optparse import OptionParser, check_choice
try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree

__version__ = '0.1.0'

class ExceptionDoxyIdRedirect(Exception):
    pass

class ExceptionDoxyIdRedirectInit(Exception):
    """Raise if there any construction issues."""
    pass

class ExceptionDoxyIdRedirectLookup(ExceptionDoxyIdRedirect):
    """Raise if there any lookup issues."""
    pass

class DoxyIdRedirect(object):
    """This class scans Doxygen DITA output and builds an IR of the IDs, the
    files that they appear in and the corresponding LookupName.
    
    """
    CHILD_ELEMENT_SET = set(
                (
                    'cxxFunction',
                    'cxxDefine',
                    'cxxVariable',
                    'cxxEnumeration',
                    'cxxEnumerator',
                    'cxxTypedef'
                )
            )
    def __init__(self, theDir):
        """Takes a directory of Doxygen DITA output and builds the IR.
        May raise an ExceptionDoxyIdRedirectInit on failure."""
        # Map of {doxygen_id : (LookupName, File_name), ...}
        # For example:
        # {
        #    'class_c_buf_base_1a6eaa287d4c84a123867bf2a6c6d804da' : 
        #        (
        #            'CBufBase::Read(TInt,TDes8 &amp;)const',
        #            'class_c_buf_base.xml',
        #        )
        # }
        self._didLuNameFileMap = {}
        if theDir is not None:
            try:
                for aFileName in os.listdir(theDir):
                    #logging.debug("doxyidredirect reading file %s"%aFileName)
                    self._addFileName(os.path.join(theDir, aFileName))
            except Exception, err:
                logging.error(str(err))
                raise ExceptionDoxyIdRedirectInit(str(err))
    
    def _addFileName(self, theFileName):
        """Opens the file and reads it into the IR."""
        # Explicitly open and close the file
        fObj = open(theFileName)
        retVal = self._addFile(fObj, os.path.basename(theFileName))
        fObj.close()
        return retVal
    
    def _addFile(self, theFileObj, theFileName):
        """Reads the file object into the IR."""
        #print '_addFile(%s):' % theFileName
        tree = self._getElementTree(theFileObj, theFileName)
        if tree == None:
            return
        root = tree.getroot()
        apiNameNode = root.find('apiName')
        if apiNameNode is None:
            # Non-cxx file such as deprecated.xml
            return
        # Handle the root ID
        self._addToIr(root.get('id'), theFileName, root.find('apiName').text)
        for c in root.getchildren():
            if c.tag in self.CHILD_ELEMENT_SET:
                self._processNode(c, theFileName)
    
    def _getElementTree(self, theFileObj, theFileName):
        try:
            tree = etree.parse(theFileObj)
            return tree
        except Exception, err:
            logging.error("%s could not be parsed: %s\n" % (theFileName, str(err)))
            return None

    def _processNode(self, n, theFileName):
        """Process a child node."""
        assert(n.tag in self.CHILD_ELEMENT_SET), '"%s" not in self.CHILD_ELEMENT_SET' % n.tag 
        i = n.get('id')
       
        if i is None:
            return
        if n.tag == 'cxxEnumerator':
            luNode = n.find('%sNameLookup' % n.tag)
        else:
            luNode = n.find('%sDetail/%sDefinition/%sNameLookup' % (n.tag, n.tag, n.tag))
        if luNode is None:
            raise ExceptionDoxyIdRedirectInit('No find on %s node of id %s' % (n,i))
        self._addToIr(i, theFileName, luNode.text)
        # Special case: Enum, recurse on enumerator
        if n.tag == 'cxxEnumeration':
            enumS = n.find('cxxEnumerationDetail/cxxEnumerationDefinition/cxxEnumerators')
            if enumS is not None:
                for aEnum in enumS:
                    self._processNode(aEnum, theFileName)
        
    def _addToIr(self, theDoxyId, theFileName, theLuName):
        self._didLuNameFileMap[theDoxyId] = (theFileName, theLuName)
    
    def lookupId(self, theDoxyId):
        """Returns a pair (file name, lookup name) that has supplied
        Doxygen ID. The file name is the file that the Doxygen ID appears in
        and the lookup name is text in the corresponding ...LookupName element
        or None if no corresponding look up name.
        The latter is a candidate for guidisation.
        
        For example given:
        "class_test_1a20150ce78c8b5b15a941dddf30ae9a4c"
        This might return:
        ("class_test.xml", "Test::member(const char*,int) const")
        
        May raise an ExceptionDoxyIdRedirectLookup on lookup failure."""
        try:
            return self._didLuNameFileMap[theDoxyId]
        except KeyError:
            raise ExceptionDoxyIdRedirectLookup('DoxyIdRedirect.lookupId(%s) failed' % theDoxyId)
    
    def getKeys(self):
        return self._didLuNameFileMap.keys()
    
######################################
# Test code
######################################
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

class NullClass(unittest.TestCase):
    pass

class TestDoxyIdRedirect(unittest.TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def test_setUp_tearDown(self):
        """Test setUp() and tearDown()."""
        pass
    
    def testInit(self):
        """Test init with None."""
        DoxyIdRedirect(None)

    def testInitFail(self):
        """Test ctor fails with garbage directory."""
        try:
            DoxyIdRedirect('not a directory')
            self.fail('DoxyIdRedirect() with garbage directory succeeded!')
        except ExceptionDoxyIdRedirectInit, err:
            self.assertEqual(
                str(err),
                "[Error 3] The system cannot find the path specified: 'not a directory/*.*'",
                )
                
    def test__getElementTree_returns_ElementTree_for_valid_xml(self):
        myXml = """<a>hello</a>"""
        myObj = DoxyIdRedirect(None)
        myTree = myObj._getElementTree(StringIO.StringIO(myXml), 'class_c_active_scheduler_1_1_t_cleanup_bundle.xml')
        self.failUnless(isinstance(myTree,etree.ElementTree))
        
    def test__getElementTree_returns_none_for_invalid_xml(self):
        myXml = """not a valid xml file"""
        myObj = DoxyIdRedirect(None)
        myTree = myObj._getElementTree(StringIO.StringIO(myXml), 'class_c_active_scheduler_1_1_t_cleanup_bundle.xml')
        self.assertEqual(myTree, None)
        
    def test_01(self):
        """Basic read and lookup test on "class_c_active_scheduler_1_1_t_cleanup_bundle.xml" """
        myXml = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.1.0//EN" "dtd/cxxClass.dtd" >
<cxxClass id="class_c_active_scheduler_1_1_t_cleanup_bundle">
    <apiName>CActiveScheduler::TCleanupBundle</apiName>
    <shortdesc/>
    <cxxClassDetail>
        <cxxClassDefinition>
            <cxxClassAccessSpecifier value="private"/>
            <cxxClassAPIItemLocation>
                <cxxClassDeclarationFile name="filePath" value="K:/epoc32/include/e32base.h"/>
                <cxxClassDeclarationFileLine name="lineNumber" value="2832"/>
                <cxxClassDefinitionFile name="filePath" value="K:/sf/os/commsfw/datacommsserver/esockserver/csock/CS_CLI.CPP"/>
                <cxxClassDefinitionFileLineStart name="lineNumber" value="2831"/>
                <cxxClassDefinitionFileLineEnd name="lineNumber" value="2836"/>
            </cxxClassAPIItemLocation>
        </cxxClassDefinition>
        <apiDesc/>
    </cxxClassDetail>
    <cxxVariable id="class_c_active_scheduler_1_1_t_cleanup_bundle_1aaa7a637534aa0b9164dda2816be6fbf4">
        <apiName>iCleanupPtr</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="public"/>
                <cxxVariableDeclaredType>
                    <apiRelation keyref="class_c_cleanup">CCleanup</apiRelation> *</cxxVariableDeclaredType>
                <cxxVariableScopedName>CActiveScheduler::TCleanupBundle</cxxVariableScopedName>
                <cxxVariablePrototype>CCleanup * iCleanupPtr</cxxVariablePrototype>
                <cxxVariableNameLookup>CActiveScheduler::TCleanupBundle::iCleanupPtr</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="K:/epoc32/include/e32base.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="2834"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc/>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="class_c_active_scheduler_1_1_t_cleanup_bundle_1ad750b8dbf966def2486a52b6c3d236fc">
        <apiName>iDummyInt</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="public"/>
                <cxxVariableDeclaredType>
                    <apiRelation keyref="_c_s___c_l_i_8_c_p_p_1abb88f5378e8305d934297176fe5fa298">TInt</apiRelation>
                </cxxVariableDeclaredType>
                <cxxVariableScopedName>CActiveScheduler::TCleanupBundle</cxxVariableScopedName>
                <cxxVariablePrototype>TInt iDummyInt</cxxVariablePrototype>
                <cxxVariableNameLookup>CActiveScheduler::TCleanupBundle::iDummyInt</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="K:/epoc32/include/e32base.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="2835"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc/>
        </cxxVariableDetail>
    </cxxVariable>
	<cxxEnumeration id="class_b_trace_1a289a8c50777f50be7f2d0535670c1e8d">
		<apiName>THeaderStructure</apiName>
		<cxxEnumerationDetail>
			<cxxEnumerationDefinition>
				<cxxEnumerationAccessSpecifier value="public"/>
				<cxxEnumerationScopedName>BTrace</cxxEnumerationScopedName>
				<cxxEnumerationPrototype>THeaderStructure</cxxEnumerationPrototype>
				<cxxEnumerationNameLookup>BTrace:THeaderStructure</cxxEnumerationNameLookup>
				<cxxEnumerators>
					<cxxEnumerator id="class_b_trace_1a289a8c50777f50be7f2d0535670c1e8da4d224d41f3e9e6dcd6da55532e6576ce">
						<apiName>ESubCategoryIndex</apiName>
						<cxxEnumeratorScopedName>BTrace</cxxEnumeratorScopedName>
						<cxxEnumeratorPrototype>ESubCategoryIndex = 3</cxxEnumeratorPrototype>
						<cxxEnumeratorNameLookup>BTrace::ESubCategoryIndex</cxxEnumeratorNameLookup>
						<cxxEnumeratorInitialiser value="3"/>
						<cxxEnumeratorAPIItemLocation>
							<cxxEnumeratorDeclarationFile name="filePath" value="K:/epoc32/include/e32btrace.h"/>
							<cxxEnumeratorDeclarationFileLine name="lineNumber" value="37"/>
						</cxxEnumeratorAPIItemLocation>
						<apiDesc>
							<p>Sub-category value. The meaning of this is dependent on the Category. </p>
						</apiDesc>
					</cxxEnumerator>
				</cxxEnumerators>
				<cxxEnumerationAPIItemLocation>
					<cxxEnumerationDeclarationFile name="filePath" value="K:/epoc32/include/e32btrace.h"/>
					<cxxEnumerationDeclarationFileLine name="lineNumber" value="8"/>
					<cxxEnumerationDefinitionFile name="filePath" value="K:/sf/os/commsfw/datacommsserver/esockserver/csock/cs_datamon_apiext.cpp"/>
					<cxxEnumerationDefinitionFileLineStart name="lineNumber" value="7"/>
					<cxxEnumerationDefinitionFileLineEnd name="lineNumber" value="36"/>
				</cxxEnumerationAPIItemLocation>
			</cxxEnumerationDefinition>
			<apiDesc>
				<p>Byte indices into the trace header for specific fields. </p>
			</apiDesc>
		</cxxEnumerationDetail>
	</cxxEnumeration>  
</cxxClass>"""
        myObj = DoxyIdRedirect(None)
        myObj._addFile(StringIO.StringIO(myXml), 'class_c_active_scheduler_1_1_t_cleanup_bundle.xml')
        keyS = myObj.getKeys()
        keyS.sort()
        #print
        #pprint.pprint(keyS)
        self.assertEqual(
                         keyS,
                         ['class_b_trace_1a289a8c50777f50be7f2d0535670c1e8d', 'class_b_trace_1a289a8c50777f50be7f2d0535670c1e8da4d224d41f3e9e6dcd6da55532e6576ce', 'class_c_active_scheduler_1_1_t_cleanup_bundle', 'class_c_active_scheduler_1_1_t_cleanup_bundle_1aaa7a637534aa0b9164dda2816be6fbf4', 'class_c_active_scheduler_1_1_t_cleanup_bundle_1ad750b8dbf966def2486a52b6c3d236fc']
                    )
        self.assertEqual(
                myObj.lookupId('class_b_trace_1a289a8c50777f50be7f2d0535670c1e8d'),
                ('class_c_active_scheduler_1_1_t_cleanup_bundle.xml', 'BTrace:THeaderStructure'),
                )
        self.assertEqual(
                myObj.lookupId('class_b_trace_1a289a8c50777f50be7f2d0535670c1e8da4d224d41f3e9e6dcd6da55532e6576ce'),
                ('class_c_active_scheduler_1_1_t_cleanup_bundle.xml', 'BTrace::ESubCategoryIndex'),
                )                
        self.assertEqual(
                myObj.lookupId('class_c_active_scheduler_1_1_t_cleanup_bundle'),
                ('class_c_active_scheduler_1_1_t_cleanup_bundle.xml', 'CActiveScheduler::TCleanupBundle'),
                )
        self.assertEqual(
                myObj.lookupId('class_b_trace_1a289a8c50777f50be7f2d0535670c1e8d'),
                ('class_c_active_scheduler_1_1_t_cleanup_bundle.xml', 'BTrace:THeaderStructure'),
                )                
        self.assertEqual(
                myObj.lookupId('class_c_active_scheduler_1_1_t_cleanup_bundle_1aaa7a637534aa0b9164dda2816be6fbf4'),
                ('class_c_active_scheduler_1_1_t_cleanup_bundle.xml', 'CActiveScheduler::TCleanupBundle::iCleanupPtr'),
                )
        self.assertEqual(
                myObj.lookupId('class_c_active_scheduler_1_1_t_cleanup_bundle_1ad750b8dbf966def2486a52b6c3d236fc'),
                ('class_c_active_scheduler_1_1_t_cleanup_bundle.xml', 'CActiveScheduler::TCleanupBundle::iDummyInt'),
                )
        try:
            myObj.lookupId('rubbish')
            self.fail('lookupId() failed to raise on garbage key')
        except ExceptionDoxyIdRedirectLookup, err:
            self.assertEqual(str(err), 'DoxyIdRedirect.lookupId(rubbish) failed')

def unitTest(theVerbosity=2):
    suite = unittest.TestLoader().loadTestsFromTestCase(NullClass)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDoxyIdRedirect))
    myResult = unittest.TextTestRunner(verbosity=theVerbosity).run(suite)
    return (myResult.testsRun, len(myResult.errors), len(myResult.failures))

######################################
# main() stuff
######################################
def main():
    usage = "usage: %prog [options] <Directory of XML content>"
    parser = OptionParser(usage, version='%prog ' + __version__)
    parser.add_option("-l", "--loglevel", type="int", default=30, help="Log Level (debug=10, info=20, warning=30, [error=40], critical=50)")      
    parser.add_option("-u", action="store_true", dest="unit_test", default=False, 
                      help="Execute unit tests and exit: [default: %default]")
    (options, args) = parser.parse_args()
    if options.unit_test:
        unitTest()
    else:
        if len(args) < 1:
            parser.print_help()
            parser.error("Please supply the path to the XML content")
        if options.loglevel:
            logging.basicConfig(level=options.loglevel)
        myObj = DoxyIdRedirect(args[0])
        print 'MyObj:', myObj
        pprint.pprint(myObj._didLuNameFileMap)

if __name__ == '__main__':
    sys.exit(main())

