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
import re   
import sys
import logging
import shutil
from optparse import OptionParser
import unittest

__version__ = '0.1'


class AntXMLValidationLogParser(object):
    """
    Can parse an ant XML validation log file and return an
    object that represents the parsed log file. 
    """
    
    LOG_MSG_UNKNOWN = 0
    LOG_MSG_VALIDATION_ERROR = 1
    LOG_MSG_INVALID_DOC = 2
    
    def __init__(self):
        self.antXmlValidationLog = AntXMLValidationLog
    
    def _get_validation_error_log_msg(self, log_msg):
        LOG_MSG_VALIDATION_ERROR_RE = re.compile(r"(\[xmlvalidate\])(.*):(.*):(.*):(.*)")
        match = LOG_MSG_VALIDATION_ERROR_RE.match(log_msg)
        if match:
            invalid_document_path = match.group(2).strip()
            error_line = int(match.group(3).strip())
            error_col = int(match.group(4).strip())
            error_msg = match.group(5).strip()
            return {"log_msg_type": self.LOG_MSG_VALIDATION_ERROR,
                    "invalid_document_path": invalid_document_path,
                    "error_line": error_line,
                    "error_col": error_col,
                    "error_msg": error_msg}
        else:
            return None
        
    def _get_invalid_doc_log_msg(self, log_msg):
        LOG_MSG_INVALID_DOC_RE = re.compile(r"\[xmlvalidate\](.*)is not a valid XML document")
        match = LOG_MSG_INVALID_DOC_RE.match(log_msg)
        if match:
            invalid_document_path = match.group(1).strip() 
            return {"log_msg_type": self.LOG_MSG_INVALID_DOC,
                    "invalid_document_path": invalid_document_path}
        else:
            return None
    
    def _parse_log_msg(self, log_msg):
        msg = self._get_validation_error_log_msg(log_msg)
        if not msg:
            msg = self._get_invalid_doc_log_msg(log_msg)
        if not msg:
            msg = {"log_msg_type": self.LOG_MSG_UNKNOWN, "log_msg": log_msg}
        return msg
            
    def parse(self, ant_validation_log):
        ant_xml_validation_log = self.antXmlValidationLog()
        log_msgs = ant_validation_log.read()
        for log_msg in log_msgs:
            msg = self._parse_log_msg(log_msg)
            
        
    

class TestAntXMLValidationLogParser(unittest.TestCase):
    
    def setUp(self):
        self.parser = AntXMLValidationLogParser()
        
    def test_i_can_handle_an_unknown_msg_type(self):
        alien_msg = """[xmlvalidate] Unknown log message type"""
        returned  = self.parser._parse_log_msg(alien_msg)
        self.assertEquals(returned, {"log_msg_type": 0,
                                     "log_msg": """[xmlvalidate] Unknown log message type"""})
                
    def test_i_can_parse_a_log_error_msg(self):
        log_error_msg = """[xmlvalidate] C:\InvalidFileDir\InvalidFile.xml:1:58: Document root element "cxxClass", must match DOCTYPE root "null"."""
        returned = self.parser._parse_log_msg(log_error_msg)
        self.assertEquals(returned, {"log_msg_type": 1,
                                     "invalid_document_path": """C:\InvalidFileDir\InvalidFile.xml""",
                                     "error_line": 1,
                                     "error_col": 58,
                                     "error_msg": """Document root element "cxxClass", must match DOCTYPE root "null"."""})
        
    def test_i_can_parse_an_invalid_document_msg(self):
        log_invalid_doc_msg = """[xmlvalidate] C:\InvalidFileDir\InvalidFile.xml is not a valid XML document"""
        returned = self.parser._parse_log_msg(log_invalid_doc_msg)
        self.assertEquals(returned, {"log_msg_type": 2,
                                     "invalid_document_path": """C:\InvalidFileDir\InvalidFile.xml"""})
 
               

    
class AntXMLValidationLog(object):
    """
    Represents an ant XML validation log file.
    """
    def add_log_error_msg(self, log_line_number, filepath, error_msg, error_line, error_col):
        pass    
    
class AntXMLValidationLogStats(object):
    """
    Represents an ant XML validation log file.
    """
    
    def __init__(self, ant_xml_validation_log):
        pass
    
    def get_invalid_document_filepaths(self):
        pass
    
    def get_invalid_document_error_msgs(self):
        pass
    
    def get_invalid_document_filepaths_for_error_msg(self, error_msg):
        pass
    
    def get_error_msgs_for_invalid_document_filepath(self, invalid_doc_filepath):
        pass
 

def getDocErrorMsg(log_msg):
    DOC_ERROR_RE = re.compile(r"(\[xmlvalidate\])(.*):.*:.*:(.*)")
    match = DOC_ERROR_RE.match(log_msg)
    if match:
        filepath = match.group(2).strip()
        error_msg = match.group(3).strip()
        return (filepath, error_msg)
    else:
        return None
    
def getInvalidDocMsg(log_msg):
    INVALID_DOC_RE = re.compile(r"\[xmlvalidate\](.*)is not a valid XML document")
    match = INVALID_DOC_RE.match(log_msg)
    if match:
        filepath = match.group(1).strip()
        return filepath
    else:
        return None
    
bad_msgs = ["Invalid byte 1 of 1-byte UTF-8 sequence."]


def do_filter_invalid_xml(ant_validation_log, filter_dir, log_filepath):
    f = open(ant_validation_log, "r")
    if os.path.exists(filter_dir):
        shutil.rmtree(filter_dir)
    os.mkdir(filter_dir)
    if not os.path.exists(os.path.dirname(os.path.abspath(log_filepath))):
        os.makedirs(os.path.dirname(os.path.abspath(log_filepath)))
    out = open(log_filepath, "w")
    lines = f.readlines()

    error_msg_map = {}
    invalid_docs = []
    unmatched_msgs = []
    for line in lines:
        error_msg = getDocErrorMsg(line)
        if error_msg:
            if error_msg[1].find("Invalid byte") != -1 or error_msg[1].find("Content is not allowed in trailing section") != -1 or error_msg[1].find("The markup in the document following the root element must be well-formed") != -1:
                out.write("Filtering out bad document %s with error msg %s\n" % (error_msg[0], error_msg[1]))
                try:
                    shutil.move(error_msg[0], filter_dir)
                except Exception, e:
                    out.write("ERROR: couldn't filter out bad file %s, error was: %s\n" % (error_msg[0], e))   
    out.close()
    
def main(func):
    usage = "usage: %prog [options] ANT_VALIDATION_LOG FILTER_DIR"
    parser = OptionParser(usage, version='%prog ' + __version__)
    parser.add_option("-l", type="int", dest="loglevel", default=logging.WARNING, 
                      help="Level of logging required")
    parser.add_option("-f", "--log-file", dest="log_filepath", default="filter-invalid-xml-log.txt", 
                      help="Path to log file")    
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.print_help()
        parser.error("Please supply an input ant validation log and a filter-to directory")
    logging.basicConfig(level=options.loglevel, format='%(asctime)s %(levelname)-8s %(message)s', stream=sys.stdout)
    val_log, filter_dir = os.path.abspath(args[0]), os.path.abspath(args[1])
    if not os.path.exists(val_log):
        parser.error('Ant validation log "%s" does not exist' % val_log)
        
    func(val_log, filter_dir, os.path.abspath(options.log_filepath))


if __name__ == '__main__':
    sys.exit(main(func=do_filter_invalid_xml))
                   
                
        
            
            
             
        
        
        










