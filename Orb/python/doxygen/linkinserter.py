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
import unittest
import sys
from cStringIO import StringIO
from optparse import OptionParser
from xml.etree import ElementTree as etree
import os.path
import logging
import shutil
from guidiser import Guidiser

__version__ = "0.1"


class LinkFile(object):
    """
    Parses string representations of cxxapiref XML files and returns an updated
    string representation with inserted ids for linking to cxxFunctions.
    """
    
    def __init__(self, guidise=False):
        self.guidiser = Guidiser()
        self.guidise = guidise
    def _get_cxxfunction_elems(self, elem):
        """
        Takes an elements and generates a list of all child elements that are called cxxFunction 
        """
        return [e for e in elem.getiterator() if e.tag == "cxxFunction"]
    
    def _get_funcs_with_no_params(self, func_elem_list):
        """
        Takes a list of cxxFunction elements and returns a list of those with no parameters.
        """
        no_params = []
        for func in func_elem_list:
            apiname = func.find("apiName").text
            params_elem = func.find("cxxFunctionDetail/cxxFunctionDefinition/cxxFunctionParameters")
            # if cxxFunctionParameters has no children
            if len(params_elem.getiterator()) == 1:
                no_params.append(apiname)            
        return no_params
    
    
    def _filter_funcs_with_no_params(self, func_elem_list):
        """
        Takes a list of cxxFunction elements and returns a list with parameterless functions
        and all of their overloads removed.
        """
        no_param_funcs = self._get_funcs_with_no_params(func_elem_list)
        return [func_elem for func_elem in func_elem_list if not func_elem.find("apiName").text in no_param_funcs]
    
    def _filter_duplicate_funcs(self, func_elem_list):
        """
        Takes a list of cxxFunction elements and returns a list ones with unique apiName text.
        In the case of overloads the first instance found is taken and the rest are filtered.
        """
        seen_func_names = []
        filtered = []
        for func_elem in func_elem_list:
            this_apiname = func_elem.find("apiName").text
            if not this_apiname in seen_func_names:
                filtered.append(func_elem)
                seen_func_names.append(this_apiname)
        return filtered
    
    def _insert_id_into_cxxfunction_apiname(self, func_elem):
        """
        Takes a cxxFunction element. Returns the element with an id inserted into the child apiName element.
        """
        function_scoped_name=func_elem.find("cxxFunctionDetail/cxxFunctionDefinition/cxxFunctionScopedName").text
        
        if function_scoped_name == None:
            function_scoped_name = ""
        else:
            function_scoped_name+="::"
        
        apiname_id = "".join([function_scoped_name,func_elem.find("apiName").text,"()"])
       
        if self.guidise:
            apiname_id = self.guidiser._get_guid(apiname_id)

        func_elem.find("apiName").attrib["id"] = apiname_id
        return func_elem
        
    def get_func_elems_to_linkify(self, root):
        cxxfunction_elems = self._get_cxxfunction_elems(root)
        cxxfunction_elems = self._filter_funcs_with_no_params(cxxfunction_elems)
        cxxfunction_elems = self._filter_duplicate_funcs(cxxfunction_elems)
        return cxxfunction_elems
    
    def get_linkified(self, file_as_string):
        """
        Takes a string representation of a cxxapiref file and returns the string
        with inserted cxxFunction ids for any functions that fit the insertion rule.
        
        The id insertion rule is:
        
        If a function and none of its overloads have no arguments then insert an
        id that represents a function with no arguments over the first function definition encountered.
        The id is inserted into the apiName child element of the function.
        """
        try:
            root = etree.fromstring(file_as_string)
        except Exception, e:
            raise Exception("Failed to parse string as xml file error was %s" % e)
        funcs_to_linkify = self.get_func_elems_to_linkify(root)
        for index in xrange(0, len(funcs_to_linkify)):
            func = self._insert_id_into_cxxfunction_apiname(funcs_to_linkify[index])
        return etree.tostring(root)
        

class LinkInserter(object):
    
    def __init__(self, link_file):
        self.link_file = link_file
        
    def _handle_xml_file(self, xml_file):
        """
        Runs linkify function on each file and writes the result to disk
        """
        logging.info("Inserting links into %s" % xml_file)
        content = open(xml_file, "r").read()
        try:
            linkified_contents = self.link_file.get_linkified(content)
        except Exception,e:
            logging.error("%s %s" %(e, xml_file))
            return

        try:
            f = open(xml_file, "w")
        except Exception, e:
            raise IOError("Could not open xml file %s for writing, error was: %s" % (xml_file, e))
        else:
            f.write(linkified_contents)
            f.close()
        
    def _handle_xml_files(self, xml_files):
        """
        Iterates over a list of files and calls _handle_xml_file on them
        """
        for xml_file in xml_files:
            self._handle_xml_file(xml_file)
            
    def _do_linkifying(self, dir):
        """
        Takes a directory and calls a handler function on a list of xml files in that and sub directories.
        """
        for root, dirs, files in os.walk(dir):
            xml_file_paths = [os.path.join(root, f) for f in os.listdir(root) if os.path.splitext(f)[1].lower() == (".xml")]
            self._handle_xml_files(xml_file_paths)
            
    def linkify_dir(self, dir):
        if not os.path.exists(os.path.abspath(dir)):
            raise IOError("Directory to linkify does not exist: %s" % dir) 
        self._do_linkifying(dir)
        

def insertlinks(xml_dir):
    link_inserter = LinkInserter(LinkFile(guidise=True))
    link_inserter.linkify_dir(xml_dir)


def main():
    usage = "usage: %prog <Path to the XML content>"
    parser = OptionParser(usage, version='%prog ' + __version__)
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        parser.error("Please supply the path to the XML content")
    insertlinks(args[0])


if __name__ == '__main__':
    sys.exit(main())

    
######################################
# Test code
######################################

class TestLinkFile(unittest.TestCase):

    def setUp(self):
        self.link_file = LinkFile()
        
    def test__get_funcs_with_no_params(self):
        func = """    
        <cxxClass><cxxFunction id="class_b_trace_1a7217f2fa88e99af3dbb5827fdc8507b7">
        <apiName>Init0</apiName>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionParameters/>
            </cxxFunctionDefinition>
        </cxxFunctionDetail>
    </cxxFunction></cxxClass>
"""
        root = etree.fromstring(func)
        func_list = [e for e in root.getiterator() if e.tag == "cxxFunction"]
        expected = ["Init0"]
        returned = self.link_file._get_funcs_with_no_params(func_list)
        self.assertEqual(expected, returned)
        
    def test__get_funcs_with_no_params_ignores_a_func_with_params(self):
        func = """    
        <cxxClass><cxxFunction id="class_b_trace_1a7217f2fa88e99af3dbb5827fdc8507b7">
        <apiName>Init0</apiName>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                    <cxxFunctionParameterDeclaredType>
                        <apiRelation keyref="_always_online_manager_client_8cpp_1a8240e11f17c80b6b222fc2af50234da4">TUint32</apiRelation>
                        </cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>a0</cxxFunctionParameterDeclarationName>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
            </cxxFunctionDefinition>
        </cxxFunctionDetail>
    </cxxFunction></cxxClass>
"""
        root = etree.fromstring(func)
        func_list = [e for e in root.getiterator() if e.tag == "cxxFunction"]
        expected = []
        returned = self.link_file._get_funcs_with_no_params(func_list)
        self.assertEqual(expected, returned)    
    
    def test_filter_duplicate_funcs_ignores_duplicate_funcs(self):
        func = """    
        <cxxClass>
            <cxxFunction id="class_b_trace_1a7217f2fa88e99af3dbb5827fdc8507b7">
                <apiName>Init0</apiName>
            </cxxFunction>
            <cxxFunction id="class_b_trace_1a7217f2fa88e99af3dbb5827fdc8507b7">
                <apiName>Init0</apiName>
            </cxxFunction>
        </cxxClass>
"""     
        root = etree.fromstring(func)   
        func_list = [e for e in root.getiterator() if e.tag == "cxxFunction"]
        expected = [func_list[0]]
        returned = self.link_file._filter_duplicate_funcs(func_list)
        self.assertEqual(expected, returned)  
        
    def test__filter_funcs_with_no_params_filters_funcs_with_no_params(self):
        func = """    
        <cxxClass>
            <cxxFunction id="class_b_trace_1a7217f2fa88e99af3dbb5827fdc8507b7">
                <apiName>Init0</apiName>
                <cxxFunctionDetail>
                    <cxxFunctionDefinition>
                        <cxxFunctionParameters/>
                    </cxxFunctionDefinition>
                </cxxFunctionDetail>
            </cxxFunction>
            <cxxFunction id="class_b_trace_1a7217f2fa88e99af3dbb5827fdc8507b7">
                <apiName>Init1</apiName>
                <cxxFunctionDetail>
                    <cxxFunctionDefinition>
                        <cxxFunctionParameters>
                            <cxxFunctionParameter>
                                <cxxFunctionParameterDeclaredType>
                                    <apiRelation keyref="_always_online_manager_client_8cpp_1a8240e11f17c80b6b222fc2af50234da4">TUint32</apiRelation>
                                </cxxFunctionParameterDeclaredType>
                                <cxxFunctionParameterDeclarationName>a0</cxxFunctionParameterDeclarationName>
                                <apiDefNote/>
                            </cxxFunctionParameter>
                        </cxxFunctionParameters>
                    </cxxFunctionDefinition>
                </cxxFunctionDetail>
            </cxxFunction>
        </cxxClass>
"""     
        root = etree.fromstring(func)   
        func_list = [e for e in root.getiterator() if e.tag == "cxxFunction"]
        expected = [func_list[1]]
        returned = self.link_file._filter_funcs_with_no_params(func_list)
        self.assertEqual(expected, returned)
        
    def test__insert_id_into_cxxfunction_apiname(self):
        func_str = """<cxxFunction id="class_b_trace_1a7217f2fa88e99af3dbb5827fdc8507b7">
        <apiName>Init0</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionDeclaredType>void</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>BTrace</cxxFunctionScopedName>
                <cxxFunctionPrototype>static void Init0(TUint32 a0)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>BTrace::Init0(TUint32 a0)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>
                            <apiRelation keyref="_always_online_manager_client_8cpp_1a8240e11f17c80b6b222fc2af50234da4">TUint32</apiRelation>
                        </cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>a0</cxxFunctionParameterDeclarationName>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/e32btrace.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="3882"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>"""
        func_elem = etree.fromstring(func_str)
        returned = self.link_file._insert_id_into_cxxfunction_apiname(func_elem)
        self.assertEquals(returned.find("apiName").attrib["id"], "BTrace::Init0()")

    def test__insert_id_into_cxxfunction_apiname_when_the_cxxfunction_has_no_scoped_name(self):
        func_str = """<cxxFunction id="class_b_trace_1a7217f2fa88e99af3dbb5827fdc8507b7">
        <apiName>Init0</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionDeclaredType>void</cxxFunctionDeclaredType>
                <cxxFunctionScopedName/>
                <cxxFunctionPrototype>static void Init0(TUint32 a0)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>BTrace::Init0(TUint32 a0)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>
                            <apiRelation keyref="_always_online_manager_client_8cpp_1a8240e11f17c80b6b222fc2af50234da4">TUint32</apiRelation>
                        </cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>a0</cxxFunctionParameterDeclarationName>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/e32btrace.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="3882"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>"""
        func_elem = etree.fromstring(func_str)
        returned = self.link_file._insert_id_into_cxxfunction_apiname(func_elem)
        self.assertEquals(returned.find("apiName").attrib["id"], "Init0()")
        
    def test_i_can_insert_an_id_to_a_cxxfunction_apiname(self):
        file_as_string = """    
        <cxxClass>
<cxxFunction id="class_b_trace_1a7217f2fa88e99af3dbb5827fdc8507b7">
        <apiName>Init0</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionDeclaredType>void</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>BTrace</cxxFunctionScopedName>
                <cxxFunctionPrototype>static void Init0(TUint32 a0)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>BTrace::Init0(TUint32 a0)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>
                            <apiRelation keyref="_always_online_manager_client_8cpp_1a8240e11f17c80b6b222fc2af50234da4">TUint32</apiRelation>
                        </cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>a0</cxxFunctionParameterDeclarationName>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/e32btrace.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="3882"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>
        </cxxClass>"""
        returned = self.link_file.get_linkified(file_as_string)
        self.assertEquals(etree.fromstring(returned).find("cxxFunction/apiName").attrib["id"], "BTrace::Init0()")

        
    def test__insert_a_guidised_id_into_cxxfunction_apiname(self):
        self.link_file = LinkFile(guidise=True)
        func_str = """<cxxFunction id="class_b_trace_1a7217f2fa88e99af3dbb5827fdc8507b7">
        <apiName>Init0</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionDeclaredType>void</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>BTrace</cxxFunctionScopedName>
                <cxxFunctionPrototype>static void Init0(TUint32 a0)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>BTrace::Init0(TUint32 a0)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>
                            <apiRelation keyref="_always_online_manager_client_8cpp_1a8240e11f17c80b6b222fc2af50234da4">TUint32</apiRelation>
                        </cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>a0</cxxFunctionParameterDeclarationName>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/e32btrace.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="3882"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>"""
        func_elem = etree.fromstring(func_str)
        returned = self.link_file._insert_id_into_cxxfunction_apiname(func_elem)
        self.assertEquals(returned.find("apiName").attrib["id"], "GUID-C8A77671-4E2F-3290-9592-84A70B14F88D")

    def test__insert_a_guidised_id_into_cxxfunction_apiname_when_the_cxxfunction_has_no_scoped_name(self):
        self.link_file = LinkFile(guidise=True)
        func_str = """<cxxFunction id="class_b_trace_1a7217f2fa88e99af3dbb5827fdc8507b7">
        <apiName>Init0</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionDeclaredType>void</cxxFunctionDeclaredType>
                <cxxFunctionScopedName/>
                <cxxFunctionPrototype>static void Init0(TUint32 a0)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>BTrace::Init0(TUint32 a0)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>
                            <apiRelation keyref="_always_online_manager_client_8cpp_1a8240e11f17c80b6b222fc2af50234da4">TUint32</apiRelation>
                        </cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>a0</cxxFunctionParameterDeclarationName>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/e32btrace.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="3882"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>"""
        func_elem = etree.fromstring(func_str)
        returned = self.link_file._insert_id_into_cxxfunction_apiname(func_elem)
        self.assertEquals(returned.find("apiName").attrib["id"], "GUID-76C4A377-8597-3952-9E6B-3E61D068EE38")
        
    def test_i_can_insert_a_guidised_id_to_a_cxxfunction_apiname(self):
        self.link_file = LinkFile(guidise=True)
        file_as_string = """    
        <cxxClass>
<cxxFunction id="class_b_trace_1a7217f2fa88e99af3dbb5827fdc8507b7">
        <apiName>Init0</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionDeclaredType>void</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>BTrace</cxxFunctionScopedName>
                <cxxFunctionPrototype>static void Init0(TUint32 a0)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>BTrace::Init0(TUint32 a0)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>
                            <apiRelation keyref="_always_online_manager_client_8cpp_1a8240e11f17c80b6b222fc2af50234da4">TUint32</apiRelation>
                        </cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>a0</cxxFunctionParameterDeclarationName>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/e32btrace.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="3882"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>
        </cxxClass>"""
        returned = self.link_file.get_linkified(file_as_string)
        self.assertEquals(etree.fromstring(returned).find("cxxFunction/apiName").attrib["id"], "GUID-C8A77671-4E2F-3290-9592-84A70B14F88D")
        
basic_class_file_str = """\    
<cxxClass>
    <cxxFunction id="function_id">
        <apiName>Init0</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionDeclaredType>void</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>BTrace</cxxFunctionScopedName>
                <cxxFunctionPrototype>static void Init0()</cxxFunctionPrototype>
                <cxxFunctionNameLookup>BTrace::Init0()</cxxFunctionNameLookup>
                <cxxFunctionParameters/>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/e32btrace.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="3882"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>
</cxxClass>"""


xml_files = {
               "basic_xml_file_1.xml": """<tag1></tag1>""",
               "basic_xml_file_2.xml": """<tag2></tag2>""",
               }
no_xml_files = {
               "non_xml_file.txt": """Some text""",                     
               }


class DummyLinkFile(object):
    
    def __init__(self):
        self.visited_files = []
    
    def get_linkified(self, file_as_string):
        self.visited_files.append(file_as_string)
        return file_as_string
        
class TestLinkInserter(unittest.TestCase):
    
    def setUp(self):
        self.dummy_link_file = DummyLinkFile()
        self.inserter = LinkInserter(self.dummy_link_file)
        
    def test__handle_xml_file_writes_to_a_file(self):
        tmp_file_path = os.getcwd() + os.sep + "tmp_file.xml"
        tmp_file = open(tmp_file_path, "w")
        tmp_file.write(basic_class_file_str)
        tmp_file.close()
        self.inserter._handle_xml_file(tmp_file_path)
        self.assertEquals(self.dummy_link_file.visited_files, [basic_class_file_str])
        os.remove(tmp_file_path)
        
    def test_i_raise_an_exception_when_dir_doesnt_exist(self):
        self.assertRaises(IOError, self.inserter.linkify_dir, "non_existant_dir")
        
    def test_i_call_linkify_on_each_file_xml_file_in_a_dir(self):
        basic_files = {}
        basic_files.update(xml_files)
        basic_files.update(no_xml_files)
        test_dir = os.path.join(os.getcwd(), "test_dir")
        os.mkdir(test_dir)
        for filename,file_content in basic_files.items():
            handle = open(os.path.join(test_dir, filename),"w")
            handle.write(file_content)
            handle.close()
        self.inserter._do_linkifying(test_dir)
        self.dummy_link_file.visited_files.sort()
        xml_files_input = xml_files.values()
        xml_files_input.sort()
        self.assertEquals(self.dummy_link_file.visited_files, xml_files_input)      
        shutil.rmtree(test_dir)   
