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
import os
import re   
import sys
import logging
from optparse import OptionParser

__version__ = '0.1'
 

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


def do_report(ant_validation_log, report_file):
    if not os.path.exists(os.path.dirname(os.path.abspath(ant_validation_log))):
        os.makedirs(os.path.dirname(os.path.abspath(ant_validation_log)))
    f = open(ant_validation_log, "r")
    if not os.path.exists(os.path.dirname(os.path.abspath(report_file))):
        os.makedirs(os.path.dirname(os.path.abspath(report_file)))
    out = open(report_file, "w")
    lines = f.readlines()

    error_msg_map = {}
    invalid_docs = []
    unmatched_msgs = []
    for line in lines:
        error_msg = getDocErrorMsg(line)
        if error_msg:
            try:
                error_msg_map[error_msg[1]].append(error_msg[0])
            except KeyError, e:
                error_msg_map[error_msg[1]] = [error_msg[0]]
        else:
            invalid_doc = getInvalidDocMsg(line)
            if invalid_doc:
                invalid_docs.append(invalid_doc)
            else:
                unmatched_msgs.append(line)
                
    error_msgs = [(len(error_msg_map[x]), x) for x in error_msg_map.keys()]
    error_msgs.sort()
    error_msgs.reverse()
    msg_count = 0
    for msg in error_msgs:
        out.write("%s: %s:\t%s\n" % (msg_count, msg[0], msg[1]))
        msg_count += 1
    out.write("\n\nDetailed results:\n\n")
    msg_count = 0
    for msg in error_msgs:
        out.write("%s: %s:\t%s\n" % (msg_count, msg[0], msg[1]))
        msg_count += 1
        filepaths = error_msg_map[msg[1]]
        filepaths.sort()
        for filepath in filepaths:
            out.write("\t%s\n" % filepath)
    
    out.close()
    
def main(func):
    usage = "usage: %prog [options] FILE"
    parser = OptionParser(usage, version='%prog ' + __version__)
    parser.add_option("-l", type="int", dest="loglevel", default=logging.WARNING, 
                      help="Level of logging required")
    parser.add_option("-r", "--report", dest="report_filepath", default="validation_report.txt", 
                      help="Path to output validation report")    
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        parser.error("Please supply an input ant validation log")
    logging.basicConfig(level=options.loglevel, format='%(asctime)s %(levelname)-8s %(message)s', stream=sys.stdout)
    infile = os.path.abspath(args[0])
    if not os.path.exists(infile):
        parser.error('Input file "%s" does not exist' % infile)
    func(infile, os.path.abspath(options.report_filepath))


if __name__ == '__main__':
    sys.exit(main(func=do_report))
                   
                
        
            
            
             
        
        
        










