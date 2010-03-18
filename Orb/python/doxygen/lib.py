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
import xml
import re
import sys
from optparse import OptionParser
from cStringIO import StringIO
from xml.etree import ElementTree as etree

nmtoken_regex = re.compile("[^a-zA-Z0-9_\.]")

def scan(dir):
    for root, _, files in os.walk(dir):
        for fname in files:
            yield os.path.join(root, fname) 
            
def xml_decl():
    return """<?xml version="1.0" encoding="UTF-8"?>"""
    
def doctype_identifier(doctype):
    """
    Return a doctype declaration string for a given doctype.
    Understands DITA and cxxapiref DITA specialisation doctypes.
    """
    # DITA Doctype Identifiers (no specific version number in identifier means latest DITA DTD version)
    if doctype == "map":
        return """<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">"""
    elif doctype == "topic":
        return """<!DOCTYPE topic PUBLIC "-//OASIS//DTD DITA Topic//EN" "topic.dtd">"""
    elif doctype == "task":
        return """<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">"""
    elif doctype == "reference":
        return """<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">"""
    elif doctype == "glossary":
        return """<!DOCTYPE glossary PUBLIC "-//OASIS//DTD DITA Glossary//EN" "glossary.dtd">"""
    elif doctype == "concept":
        return """<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">"""
    elif doctype == "bookmap":
        return """<!DOCTYPE bookmap PUBLIC "-//OASIS//DTD DITA BookMap//EN" "bookmap.dtd">""" 
    # cxxapiref DITA specialisation Doctype Identifiers
    elif doctype == "cxxUnion":
        return """<!DOCTYPE cxxUnion PUBLIC "-//NOKIA//DTD DITA C++ API Union Reference Type v0.5.0//EN" "dtd/cxxUnion.dtd">"""   
    elif doctype == "cxxStruct":
        return """<!DOCTYPE cxxStruct PUBLIC "-//NOKIA//DTD DITA C++ API Struct Reference Type v0.5.0//EN" "dtd/cxxStruct.dtd">"""
    elif doctype == "cxxPackage":
        return """<!DOCTYPE cxxPackage PUBLIC "-//NOKIA//DTD DITA cxx API Package Reference Type v0.5.0//EN" "dtd/cxxPackage.dtd">"""
    elif doctype == "cxxFile":
        return """<!DOCTYPE cxxFile PUBLIC "-//NOKIA//DTD DITA C++ API File Reference Type v0.5.0//EN" "dtd/cxxFile.dtd">"""
    elif doctype == "cxxClass":
        return """<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.5.0//EN" "dtd/cxxClass.dtd">"""
    elif doctype == "cxxAPIMap":
        return """<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >"""
    else:
        raise Exception('Unknown Doctype \"%s\"' % doctype)

def get_valid_nmtoken(attribute_value):
    new_value = attribute_value
    matches = nmtoken_regex.findall(new_value)
    for char in set(matches):
        new_value = new_value.replace(char,"")
    return new_value

class XmlParser(object):
    """
    Simple class that reads an XML and returns its id

    >>> xp = XmlParser()
    >>> xp.parse(StringIO("<root id='rootid'>some content</root>"))
    'rootid'
    """
    def parse(self, xmlfile):
        try:
            root = etree.parse(xmlfile).getroot()
        except xml.parsers.expat.ExpatError, e:
            sys.stderr.write("ERROR: %s could not be parse: %s\n" % (xmlfile, str(e)))
            return ""
        if 'id' not in root.attrib:
            return ""
        return root.attrib['id']

def main(func, version):
    usage = "usage: %prog <Path to the XML content>"
    parser = OptionParser(usage, version='%prog ' + version)
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        parser.error("Please supply the path to the XML content")
    func(args[0])
    
######################################
# Test code
######################################

class Testxml_decl(unittest.TestCase):
    def testi_can_return_anxml_declaration(self):
        self.assertEquals(xml_decl(), """<?xml version="1.0" encoding="UTF-8"?>""")
    
    
class Testdoctype_identifier(unittest.TestCase):
    
    def test_i_raise_an_exception_for_an_unknown_doctype(self):
        self.assertRaises(Exception, doctype_identifier, "invaliddoctype")
        
    def test_i_can_return_a_map_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("map"), """<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">""")
        
    def test_i_can_return_a_topic_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("topic"), """<!DOCTYPE topic PUBLIC "-//OASIS//DTD DITA Topic//EN" "topic.dtd">""")
        
    def test_i_can_return_a_task_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("task"), """<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">""")
        
    def test_i_can_return_a_reference_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("reference"), """<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">""")
        
    def test_i_can_return_a_glossary_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("glossary"), """<!DOCTYPE glossary PUBLIC "-//OASIS//DTD DITA Glossary//EN" "glossary.dtd">""")
        
    def test_i_can_return_a_concept_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("concept"), """<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">""")
        
    def test_i_can_return_a_bookmap_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("bookmap"), """<!DOCTYPE bookmap PUBLIC "-//OASIS//DTD DITA BookMap//EN" "bookmap.dtd">""")

    def test_i_can_return_a_cxxUnion_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("cxxUnion"), """<!DOCTYPE cxxUnion PUBLIC "-//NOKIA//DTD DITA C++ API Union Reference Type v0.5.0//EN" "dtd/cxxUnion.dtd">""")
    
    def test_i_can_return_a_cxxStruct_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("cxxStruct"), """<!DOCTYPE cxxStruct PUBLIC "-//NOKIA//DTD DITA C++ API Struct Reference Type v0.5.0//EN" "dtd/cxxStruct.dtd">""")
        
    def test_i_can_return_a_cxxPackage_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("cxxPackage"), """<!DOCTYPE cxxPackage PUBLIC "-//NOKIA//DTD DITA cxx API Package Reference Type v0.5.0//EN" "dtd/cxxPackage.dtd">""")
        
    def test_i_can_return_a_cxxFile_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("cxxFile"), """<!DOCTYPE cxxFile PUBLIC "-//NOKIA//DTD DITA C++ API File Reference Type v0.5.0//EN" "dtd/cxxFile.dtd">""")
        
    def test_i_can_return_a_cxxClass_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("cxxClass"), """<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.5.0//EN" "dtd/cxxClass.dtd">""")
        
    def test_i_can_return_a_cxxAPIMap_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("cxxAPIMap"), """<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >""")
        
                
class Testget_valid_nmtoken(unittest.TestCase):
    
    def test_i_remove_non_alpha_numeric_characters(self):
        input = "this is an alphanumeric string with non alpha numeric characters inside.()_+=-string0123456789"
        expout = "thisisanalphanumericstringwithnonalphanumericcharactersinside._string0123456789"
        output = get_valid_nmtoken(input)
        self.assertEquals(output, expout)        
        
        
class StubXmlParser(object):
    def parse(self, path):
        return "GUID-BED8A733-2ED7-31AD-A911-C1F4707C67F"


class TestXmlParser(unittest.TestCase):
    def test_i_issue_a_warning_and_continue_if_a_file_is_invalid(self):
        xml = XmlParser()
        try:
            xml.parse(StringIO("<foo><bar</foo>"))
        except Exception, e:
            self.fail("I shouldn't have raised an exception. Exception was %s" % e) 

    def test_i_issue_a_warning_and_continue_if_a_file_does_not_have_an_id(self):
        xml = XmlParser()
        try:
            id = xml.parse(StringIO(brokencxxclass))
        except Exception:
            self.fail("I shouldn't have raised an exception")
        self.assertTrue(id == "") 

    def test_i_return_a_files_id(self):
        xml = XmlParser()
        id = xml.parse(StringIO(cxxclass))
        self.assertTrue(id == "class_c_active_scheduler")
        
brokencxxclass = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.5.0//EN" "dtd/cxxClass.dtd" >
<cxxClass>
    <apiName>CActiveScheduler</apiName>
    <shortdesc/>
</cxxClass>
"""

cxxclass = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.5.0//EN" "dtd/cxxClass.dtd" >
<cxxClass id="class_c_active_scheduler">
    <apiName>CActiveScheduler</apiName>
    <shortdesc/>
</cxxClass>
"""