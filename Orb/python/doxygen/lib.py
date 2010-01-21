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
from optparse import OptionParser


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
        return """<!DOCTYPE cxxUnion PUBLIC "-//NOKIA//DTD DITA C++ API Union Reference Type//EN" "dtd/cxxUnion.dtd">"""   
    elif doctype == "cxxStruct":
        return """<!DOCTYPE cxxStruct PUBLIC "-//NOKIA//DTD DITA C++ API Struct Reference Type//EN" "dtd/cxxStruct.dtd">"""
    elif doctype == "cxxPackage":
        return """<!DOCTYPE cxxPackage PUBLIC "-//NOKIA//DTD DITA cxx API Package Reference Type//EN" "dtd/cxxPackage.dtd">"""
    elif doctype == "cxxFile":
        return """<!DOCTYPE cxxFile PUBLIC "-//NOKIA//DTD DITA C++ API File Reference Type//EN" "dtd/cxxFile.dtd">"""
    elif doctype == "cxxClass":
        return """<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type//EN" "dtd/cxxClass.dtd">"""
    elif doctype == "cxxAPIMap":
        return """<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type//EN" "dtd/cxxAPIMap.dtd" >"""
    else:
        raise Exception('Unknown Doctype \"%s\"' % doctype)


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
        self.assertEquals(doctype_identifier("cxxUnion"), """<!DOCTYPE cxxUnion PUBLIC "-//NOKIA//DTD DITA C++ API Union Reference Type//EN" "dtd/cxxUnion.dtd">""")
    
    def test_i_can_return_a_cxxStruct_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("cxxStruct"), """<!DOCTYPE cxxStruct PUBLIC "-//NOKIA//DTD DITA C++ API Struct Reference Type//EN" "dtd/cxxStruct.dtd">""")
        
    def test_i_can_return_a_cxxPackage_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("cxxPackage"), """<!DOCTYPE cxxPackage PUBLIC "-//NOKIA//DTD DITA cxx API Package Reference Type//EN" "dtd/cxxPackage.dtd">""")
        
    
    def test_i_can_return_a_cxxFile_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("cxxFile"), """<!DOCTYPE cxxFile PUBLIC "-//NOKIA//DTD DITA C++ API File Reference Type//EN" "dtd/cxxFile.dtd">""")
        
    def test_i_can_return_a_cxxClass_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("cxxClass"), """<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type//EN" "dtd/cxxClass.dtd">""")
        
    def test_i_can_return_a_cxxAPIMap_doctype_identifier(self):        
        self.assertEquals(doctype_identifier("cxxAPIMap"), """<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type//EN" "dtd/cxxAPIMap.dtd" >""")
                
        