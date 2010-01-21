# Copyright (c) 2007-2010 Nokia Corporation and/or its subsidiary(-ies) All rights reserved.
# This component and the accompanying materials are made available under the terms of the License 
# "Eclipse Public License v1.0" which accompanies this distribution, 
# and is available at the URL "http://www.eclipse.org/legal/epl-v10.html".
#
# Initial Contributors:
# Nokia Corporation - initial contribution.
#
# Contributors:
# System Documentation Tools
# Description:
#
import os.path
import sys
import unittest
import xml
import stat
from cStringIO import StringIO
from xml.etree import ElementTree as etree
from lib import scan, main


__version__ = '0.1'


UNSAFE_CHARS = ("\n", "\t", ":", "?", ",", "=", ".", "\\", "/", "[", "]", "|", "<", ">", "+", ";", '"', "-")


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


class FileRenamer(object):
    """
    Given an xml file this class returns a MODE compatable filename

    >>> fr = FileRenamer(xmlparser=StubXmlParser())
    >>> fr.rename(r"c:\\temp\\xml\\class_c_active_scheduler.xml")
    'class_c_active_scheduler=GUID-BED8A733-2ED7-31AD-A911-C1F4707C67F=1=en=.reference'
    """
    def __init__(self, xmlparser=XmlParser()):
        self.parser = xmlparser
    
    def _escape(self, filename):
        for char in UNSAFE_CHARS:
            filename = filename.replace(char, "")            
        filename = filename.encode('unicode-escape', 'ignore')
        filename = filename.replace(" ", "-")
        return filename        
    
    def rename(self, xmlfile):
        """
        Return DITA MODE compliant filename.
        Format of resultant filenames is:
            title=identifier=version=language=resolution.extension    
        Examples:
            Test-Document=GUID-1234=1=en=.reference
        """
        id = self.parser.parse(xmlfile)
        filename = os.path.basename(xmlfile)
        filename, ext = os.path.splitext(filename)
        filename = self._escape(filename) 
        newfilename = "=".join((filename, id, '1', 'en', ''))
        ext = ext if ext == ".ditamap" else ".reference"
        return newfilename + ext


def rename(indir):
    fr = FileRenamer()
    for filepath in scan(indir):
        newfilename = os.path.join(os.path.dirname(filepath), fr.rename(filepath))
        os.chmod(filepath, stat.S_IWRITE)
        #print "Renaming %s to %s" % (filepath, newfilename)
        os.rename(filepath, newfilename)


if __name__ == '__main__':
    sys.exit(main(rename, __version__))

######################################
# Test code
######################################
class StubXmlParser(object):
    def parse(self, path):
        return "GUID-BED8A733-2ED7-31AD-A911-C1F4707C67F"


class TestXmlParser(unittest.TestCase):
    def test_i_issue_a_warning_and_continue_if_a_file_is_invalid(self):
        xml = XmlParser()
        try:
            xml.parse(StringIO("<foo><bar</foo>"))
        except Exception:
            self.fail("I shouldn't have raised an exception") 

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
 

class TestFileRenamer(unittest.TestCase):
    def test_i_can_return_a_files_new_name(self):
        fr = FileRenamer(xmlparser=StubXmlParser())
        newfile = fr.rename("hello.xml")
        self.assertTrue(newfile == "hello=GUID-BED8A733-2ED7-31AD-A911-C1F4707C67F=1=en=.reference")

    def test_i_can_return_a_ditamaps_new_name(self):
        fr = FileRenamer(xmlparser=StubXmlParser())
        newfile = fr.rename("hello.ditamap")
        self.assertTrue(newfile == "hello=GUID-BED8A733-2ED7-31AD-A911-C1F4707C67F=1=en=.ditamap")


    def test_i_can_return_a_files_new_name_if_passed_an_absolute_path(self):
        fr = FileRenamer(xmlparser=StubXmlParser())
        newfile = fr.rename("c:\\temp\\xml\\hello.xml")
        self.assertTrue(newfile == "hello=GUID-BED8A733-2ED7-31AD-A911-C1F4707C67F=1=en=.reference")
        
    def test_i_can_remove_incompatable_characters_from_a_filename(self):
        fr = FileRenamer(xmlparser=StubXmlParser())
        newfile = fr.rename("hello:?,=..xml")
        self.assertTrue(newfile == "hello=GUID-BED8A733-2ED7-31AD-A911-C1F4707C67F=1=en=.reference")        

    
brokencxxclass = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.1.0//EN" "dtd/cxxClass.dtd" >
<cxxClass>
    <apiName>CActiveScheduler</apiName>
    <shortdesc/>
</cxxClass>
"""

cxxclass = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.1.0//EN" "dtd/cxxClass.dtd" >
<cxxClass id="class_c_active_scheduler">
    <apiName>CActiveScheduler</apiName>
    <shortdesc/>
</cxxClass>
"""