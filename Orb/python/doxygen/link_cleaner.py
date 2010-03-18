from copy import deepcopy
from cStringIO import StringIO
import unittest
from xml.sax import parseString
from xml.sax.handler import ContentHandler
import xml.sax.saxutils as saxutils
from optparse import OptionParser
import os
import sys
import logging
import shutil
import re
from lib import get_valid_nmtoken
from lib import doctype_identifier

__version__="0.0.1"
EPL = """<!-- Copyright (c) 2007-2010 Nokia Corporation and/or its subsidiary(-ies) All rights reserved. -->
<!-- This component and the accompanying materials are made available under the terms of the License 
"Eclipse Public License v1.0" which accompanies this distribution, 
and is available at the URL "http://www.eclipse.org/legal/epl-v10.html". -->
<!-- Initial Contributors:
	Nokia Corporation - initial contribution.
Contributors: 
-->  """
XML_DECLERATION = """<?xml version="1.0" encoding="utf-8"?>\n"""
FILE_TYPES = [".dita", ".xml", ".ditamap", ".reference"]
ATTRIBUTE_TYPES = ["id","href"]
    
class MyContentHandler(ContentHandler):

    def __init__(self):
        self.text = ""
        self.is_root_element = True
        self.doctype = ""
        
    def startElement(self, name, attributes):
        if self.is_root_element:
            self.doctype = doctype_identifier(name)
            self.is_root_element = False
            
        self.text += '<%s' % name
        matches = []
        attribute_value = ""
        for name, value in attributes.items():
            localname = name
            attribute_value = value
            if localname in ATTRIBUTE_TYPES:
                attribute_value = get_valid_nmtoken(attribute_value)
            self.text += ' %s="%s"' % (localname, attribute_value)
        self.text += '>'
    
    def _split_qname(self, qname):
        qname_split = qname.split(':')
        if len(qname_split) == 2:
            prefix, local = qname_split
        else:
            prefix = None
            local = qname_split
        return prefix, local

    def characters(self, data):
        self.text += saxutils.escape(data)

    def endElement(self, name):
        self.text += '</%s>' % name



class LinkCleaner(object):
    def modify(self, xml):
        #parser = etree.XMLParser(resolve_entities=False)
        #tree = etree.parse(xml, parser=parser)
        handler = MyContentHandler()
        parseString(xml, handler)
        #lxml.sax.saxify(tree, handler)
        doctype = ""#tree.docinfo.doctype
        return XML_DECLERATION + EPL + handler.doctype + handler.text

class LinkFile(object):
    """
    Parses string representations of dita XML files and returns an updated
    string representation with hrefs and ids that are DITA OT compatable
    """
    def get_modified(self, file_as_string):
        """
        Takes a string representation of a dita file and returns the string
        with id and href attributes on any element cleaned of characters that are not compatible with
        NMTOKEN as defined in the xml specification and as used by the DITA OT in ids
        """
        try:
            alr = LinkCleaner()
            outxml = alr.modify(file_as_string)
        except Exception, e:
            raise Exception("Failed process file error was %s" % e)
        return outxml
        

class LinkFileHandler(object):

    def __init__(self, link_file):
        self.link_file = link_file
        

    def _handle_xml_file(self, xml_file_path):
        """
        Runs xref modifcation function on each file and writes the result to disk
        """
        logging.info("Modifying xrefs in %s" % xml_file_path)
        content = open(xml_file_path, "r").read()
        try:
            modified_contents = self.link_file.get_modified(content)
        except Exception,e:
            logging.error("%s %s" %(e, xml_file_path))
            return

        try:
            f = open(xml_file_path, "w")
        except Exception, e:
            raise IOError("Could not open dita file %s for writing, error was: %s" % (xml_file_path, e))
        else:
            try:
                f.write(modified_contents.encode('utf-8'))
                f.close()
            except Exception, e:
                print "Error writing file: %s, error was: %s" % (xml_file_path, e)
    
    def _handle_xml_files(self, xml_files):
        """
        Iterates over a list of files and calls _handle_dita_file on them
        """
        for dita_file in xml_files:
            self._handle_xml_file(dita_file)    
    
    def _do_link_modification(self, dir):
        """
        Takes a directory and calls a handler function on a list of .dita files in that and sub directories.
        """
        for root, dirs, files in os.walk(dir):
            dita_file_paths = [os.path.join(root, f) for f in os.listdir(root) if os.path.splitext(f)[1].lower() in FILE_TYPES]
            self._handle_xml_files(dita_file_paths)
            
    def modify_xml_in_dir(self, dir):
        if not os.path.exists(os.path.abspath(dir)):
            raise IOError("Directory to modify the xml in does not exist: %s" % dir) 
        self._do_link_modification(dir)

def modify_links(xml_dir):
    link_modifier = LinkFileHandler(LinkFile())
    link_modifier.modify_xml_in_dir(xml_dir)
    
def main():
    usage = "usage: %prog <Path to the XML content>"
    parser = OptionParser(usage, version='%prog ' + __version__)
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        parser.error("Please supply the path to the XML content")
    modify_links(args[0])


if __name__ == '__main__':
    sys.exit(main())

basic_concept_file_str = """
        <concept>
            <conbody>
                <ol>
                    <li>
                        <p>
                            <xref href="jar:GUID-759FBC7F-5384-4487-8457-A8D4B76F6AA6.jar!/html/CAknDocumentclass.html" format="application/java-archive"/>
                        </p>
                    </li>
                </ol>
            </conbody>
        </concept>"""

xml_files = {
               "basic_xml_file_1.dita": """<tag1></tag1>""",
               "basic_xml_file_2.dita": """<tag2></tag2>""",
               }
no_xml_files = {
               "non_xml_file.txt": """Some text""",                     
               }
               
class TestApiRemover(unittest.TestCase):
	

    def test_i_remove_invalid_characters_from_xref_elements(self):
        inxml = """<reference><p>This is a paragraph with a <xref href="afilename^{}:">link</xref></p></reference>"""
        exxml = XML_DECLERATION + EPL + doctype_identifier("reference") + """<reference><p>This is a paragraph with a <xref href="afilename">link</xref></p></reference>"""
        alr = LinkCleaner()
        outxml = alr.modify(inxml)
        self.assertEquals(exxml, outxml)
        
    def test_i_remove_invalid_characters_from_conref_elements(self):
        inxml = """<reference><p>This is a paragraph with a <conref href="afilename^{}:">link</conref></p></reference>"""
        exxml = XML_DECLERATION + EPL + doctype_identifier("reference") + """<reference><p>This is a paragraph with a <conref href="afilename">link</conref></p></reference>"""
        alr = LinkCleaner()
        outxml = alr.modify(inxml)
        self.assertEquals(exxml, outxml)
        
    def test_i_remove_invalid_characters_from_link_elements(self):
        inxml = """<reference><p>This is a paragraph with a <link href="afilename^{}:">link</link></p></reference>"""
        exxml = XML_DECLERATION + EPL + doctype_identifier("reference") + """<reference><p>This is a paragraph with a <link href="afilename">link</link></p></reference>"""
        alr = LinkCleaner()
        outxml = alr.modify(inxml)
        self.assertEquals(exxml, outxml)    

    def test_i_remove_invalid_characters_from_id_attributes(self):
        inxml = """<reference><p>This is a paragraph with a <anelement id="afilename^{}:">link</anelement></p></reference>"""
        exxml = XML_DECLERATION + EPL + doctype_identifier("reference") + """<reference><p>This is a paragraph with a <anelement id="afilename">link</anelement></p></reference>"""
        alr = LinkCleaner()
        outxml = alr.modify(inxml)
        self.assertEquals(exxml, outxml)   
        
    def test_i_preserve_entity_refs(self):
        inxml = """<reference>&lt;text_between_entity_refs&gt;</reference>"""
        exxml = XML_DECLERATION + EPL + doctype_identifier("reference") + """<reference>&lt;text_between_entity_refs&gt;</reference>"""	
        alr = LinkCleaner()
        outxml = alr.modify(inxml)
        self.assertEquals(exxml, outxml)

        
class DummyLinkFile(object):
    
    def __init__(self):
        self.visited_files = []
    
    def get_modified(self, file_as_string):
        self.visited_files.append(file_as_string)
        return file_as_string
        
class TestXrefModifier(unittest.TestCase):
    
    def setUp(self):
        self.dummy_link_file = DummyLinkFile()
        self.link_modifier = LinkFileHandler(self.dummy_link_file)
        
    def test_i_handle_xml_file_writes_to_a_file(self):
        tmp_file_path = os.getcwd() + os.sep + "tmp_file.xml"
        tmp_file = open(tmp_file_path, "w")
        tmp_file.write(basic_concept_file_str)
        tmp_file.close()
        self.link_modifier._handle_xml_file(tmp_file_path)
        self.assertEquals(self.dummy_link_file.visited_files, [basic_concept_file_str])
        os.remove(tmp_file_path)
        
    def test_i_raise_an_exception_when_dir_doesnt_exist(self):
        self.assertRaises(IOError, self.link_modifier.modify_xml_in_dir, "non_existant_dir")
        
    def test_i_call_modify_xml_in_dir_on_each_file_xml_file_in_a_dir(self):
        basic_files = {}
        basic_files.update(xml_files)
        basic_files.update(no_xml_files)
        test_dir = os.path.join(os.getcwd(), "test_dir")
        os.mkdir(test_dir)
        for filename,file_content in basic_files.items():
            handle = open(os.path.join(test_dir, filename),"w")
            handle.write(file_content)
            handle.close()
        self.link_modifier._do_link_modification(test_dir)
        self.dummy_link_file.visited_files.sort()
        xml_files_input = xml_files.values()
        xml_files_input.sort()
        self.assertEquals(self.dummy_link_file.visited_files, xml_files_input)      
        shutil.rmtree(test_dir)   