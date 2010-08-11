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
import stat
import logging
from lib import scan, main, XmlParser, StubXmlParser
from optparse import OptionParser

__version__ = '0.1'


UNSAFE_CHARS = ("\n", "\t", ":", "?", ",", "=", ".", "\\", "/", "[", "]", "|", "<", ">", "+", ";", '"', "-")


logger = logging.getLogger('orb.filerenamer')


class FileRenamer(object):
    """
    Given an xml file this class returns a MODE compatable filename

    >>> fr = FileRenamer(xmlparser=StubXmlParser())
    >>> fr.rename(r"c:\\temp\\xml\\class_c_active_scheduler.xml")
    'class_c_active_scheduler=GUID-BED8A733-2ED7-31AD-A911-C1F4707C67F=1=en=.reference'
    """
    def __init__(self, xmlparser=XmlParser(), publishing_target="mode"):
        self.parser = xmlparser
        self.publishing_target = publishing_target
    
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
        if self.publishing_target == "mode":
            filename = self._escape(filename) 
            newfilename = "=".join((filename, id, '1', 'en', ''))
            ext = ext if ext == ".ditamap" else ".reference"
        elif self.publishing_target == "ditaot":
            newfilename = id
            ext = ext = ext if ext == ".ditamap" else ".xml"
        return newfilename + ext


def rename(indir, publishing_target):
    fr = FileRenamer(publishing_target=publishing_target)
    for filepath in scan(indir):
        newfilename = os.path.join(os.path.dirname(filepath), fr.rename(filepath))
        try:
            os.chmod(filepath, stat.S_IWRITE)
        except Exception, e:
            logger.error('Unable to make file \"%s\" writable, error was: %s' % (filepath, e))
            continue
        else:
            logger.debug("Renaming %s to %s" % (filepath, newfilename))
            try:
                os.rename(filepath, newfilename)
            except Exception, e:
                logger.error('Unable to rename file \"%s\" to \"%s\", error was: %s' % (filepath, newfilename, e))

def main():        
    usage = "usage: %prog <Path to the XML content> <publishing_target>\n"
    parser = OptionParser(usage, version='%prog ' + __version__)
    parser.add_option("-p", dest="publishing_target", type="choice", choices=["mode", "ditaot"], default="mode", 
                          help="Publishing Target: mode|ditaot, [default: %default]")
    parser.add_option("-l", "--loglevel", type="int", default=30, help="Log Level (debug=10, info=20, warning=30, [error=40], critical=50)")
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        parser.error("Please supply the path to the XML content")
        
    if options.loglevel:
        logger.basicConfig(level=options.loglevel)
    
    rename(args[0],options.publishing_target)

if __name__ == '__main__':
    sys.exit(main())

######################################
# Test code
######################################

class TestFileRenamer(unittest.TestCase):
    def test_i_can_return_a_files_new_mode_name(self):
        fr = FileRenamer(xmlparser=StubXmlParser(),publishing_target="mode")
        newfile = fr.rename("hello.xml")
        self.assertTrue(newfile == "hello=GUID-BED8A733-2ED7-31AD-A911-C1F4707C67F=1=en=.reference")

    def test_i_can_return_a_ditamaps_new_mode_name(self,publishing_target="mode"):
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
        self.assertTrue(newfile , "hello=GUID-BED8A733-2ED7-31AD-A911-C1F4707C67F=1=en=.reference")        

    def test_i_can_return_a_files_new_ditaot_name(self):
        fr = FileRenamer(xmlparser=StubXmlParser(),publishing_target="ditaot")
        newfile = fr.rename("hello.xml")
        self.assertEquals(newfile, "GUID-BED8A733-2ED7-31AD-A911-C1F4707C67F.xml")

    def test_i_can_return_a_ditamaps_new_ditaot_name(self):
        fr = FileRenamer(xmlparser=StubXmlParser(),publishing_target="ditaot")
        newfile = fr.rename("hello.ditamap")
        self.assertEquals(newfile, "GUID-BED8A733-2ED7-31AD-A911-C1F4707C67F.ditamap")        
