# Copyright (c) 2008-2010 Nokia Corporation and/or its subsidiary(-ies).
# All rights reserved.
# This component and the accompanying materials are made available
# under the terms of the License "Eclipse Public License v1.0"
# which accompanies this distribution, and is available
# at the URL "http://www.eclipse.org/legal/epl-v10.html".
#
# Initial Contributors:
# Nokia Corporation - initial contribution.
#
# Contributors:
#
# Description: 
# Filter class for doing --what and --check operations
#
from __future__ import with_statement
import os
import re
import filter_interface
import xml
import logging
try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree
from orb import guidiser, filerenamer
from orb.sysdef import SystemDefinition
from orb.hrefloader import HrefLoader
from orb.mapcreators import ComponentMapCreator, TopLevelMapCreator, PackageLevelMapCreator, ComponentExportsManager, PackageLevelMapFilter


logger = logging.getLogger('filter_orb')

# Check environment for logging variable
if "ORB_LOGGING_LEVEL" in os.environ.keys():
    logging.basicConfig(level=int(os.environ["ORB_LOGGING_LEVEL"]))


class Configuration(object):
    "Object used to encapsulate build configuration info (sdk vs pdk etc.)"
    publishing_target = "ditaot"
    sdk = False
    
    def parse(self, config):
        if "sdk" in config:
            self.sdk = True
        if "mode" in config:
            self.publishing_target = "mode"


class LogLineParser(object):
    "Parses the info lines from the log file passed to the filter by Raptor."
    def __init__(self):
        self.info_handlers = {
            "<info>Current working directory (.*)</info>": "_store_cwd",
            "<info>System Definition file (.*)</info>": "_store_sysdef",
            "<info>SBS_HOME (.*)</info>": "_store_sbs_home",
            "<info>Buildable configuration '(.*)'</info>": "_update_config"
        }
        self.cwd = ""
        self.systemdefinition = ""
        self.sbs_home = ""
        self._config = Configuration()
        
    @property
    def sdk(self):
        return self._config.sdk
    
    @property
    def pub_target(self):
        return self._config.publishing_target

    def _update_sysdef(self, ):
        if self.cwd != "" and self.systemdefinition != "":
            self.systemdefinition = os.path.abspath(os.path.join(self.cwd, self.systemdefinition))

    def _store_cwd(self, value):
        self.cwd = value
        self._update_sysdef()
    
    def _store_sysdef(self, value):
        self.systemdefinition = value.replace("/", os.sep)
        self._update_sysdef()
    
    def _store_sbs_home(self, value):
        self.sbs_home = os.path.abspath(value)

    def _update_config(self, value):
        self._config.parse(value)

    def parse(self, logline):
        if not logline.startswith("<info>"):
            return
        for regex, fn in self.info_handlers.items():
            search = re.search(regex, logline)
            if search:
                getattr(self, fn)(search.group(1))


class WhatLogParser(object):
    """
    Parses whatlog lines from the log file passed to the filter by Raptor.
    whatlog lines contain information about project exports.
    """
    def __init__(self):
        self.store = False
        self.exports = {}
        self._buffer = []

    def parse(self, text):
        text = text.strip()
        logger.debug("Text passed to WhatLogParser was: %s" % text)
        if text.startswith("</whatlog>") or (
           text.startswith("<whatlog") and text.endswith("</whatlog>")):
            self._buffer.append(text)
            self.store = False
            self._parse_xml("".join(self._buffer))
            self._buffer = []
        elif text.startswith("<whatlog"):
            self._buffer.append(text)
            self.store = True
        elif self.store:
            self._buffer.append(text)

    def _parse_xml(self, xmlfile):
        try:
            root = etree.fromstring(xmlfile)
        #except xml.parsers.expat.ExpatError, e:
        except Exception, e:
            logger.error("%s could not be parsed: %s\n" % (xmlfile, str(e)))
            return None
        bldinf = root.attrib["bldinf"]
        self.exports[bldinf] = set()
        for child in [c for c in root.getiterator() if c.tag == "export"]:
            self.exports[bldinf].add(
                (child.attrib["destination"], child.attrib["source"])
            )


class FilterOrb(filter_interface.Filter):
    """
    Class that interacts with Raptor. 
    open is called when raptor opens a log file
    write is called every time raptor writes a line to a log file.
    summary is closed just before raptor closes a log file
    close is called when raptor closes a log file
    """
    def __init__(self):
        self.configuration = Configuration()
        self.line_parser = LogLineParser()
        self.whatparser = WhatLogParser()        

    def open(self, build_parameters):
        self.epocroot = build_parameters.epocroot
        return True

    def write(self, text):
        "process some log text"
        if text.startswith("<whatlog") or self.whatparser.store:
            self.whatparser.parse(text)
        elif text.startswith("<info>"):
            self.line_parser.parse(text)
        return True

    def _write_maps(self, build_dir, rel_dir):
        sysdef = SystemDefinition(self.line_parser.systemdefinition, self.line_parser.cwd)       
        for package in sysdef.get_packages():
            logger.debug("Creating PLM for: '%s'" % package.id)
            plmcreator = PackageLevelMapCreator(sysdef, build_dir)
            plm = plmcreator.get_package_level_map(package.id)
            logger.debug("PLM is: '%s'" % plm)
            plmfilter = PackageLevelMapFilter(plm, HrefLoader(rel_dir), self.line_parser.sdk)
            for component in sysdef.get_components(package.id):
                cmapcreator = ComponentMapCreator(rel_dir)            
                logger.debug("Creating component level map for: %s" % component.id)
                comp_exports_manager = ComponentExportsManager(sysdef, component, BldInfToExportsMap(self.whatparser.exports))
                logger.debug("Creating comp_exports_manager for: '%s'" % comp_exports_manager._basenames)
                filtered_entries = plmfilter.filter(comp_exports_manager)   
                logger.debug("Creating filtered_entries for: '%s'" % filtered_entries)
                map = cmapcreator.get_component_level_map(component, filtered_entries)
                cmapcreator.write(map)        
        tc = TopLevelMapCreator(sysdef, rel_dir)
        tc.write(os.path.join(rel_dir, "Symbian_platform.ditamap"))        

    def _run_postprocessing(self, rel_dir):  
        guidiser.updatefiles(rel_dir, self.line_parser.pub_target)
        filerenamer.rename(rel_dir, self.line_parser.pub_target)

    def _update_epocroot(self):
        self.epocroot = self.epocroot.replace("/", os.sep) 
        (drive, _) = os.path.splitdrive(self.line_parser.cwd)
        self.epocroot = os.path.join(drive, self.epocroot)

    def summary(self):        
        self._update_epocroot()
        build_dir = os.path.join(self.epocroot, "epoc32", "build")
        rel_dir = os.path.join(self.epocroot, "epoc32", "release", "doxygen", "dita")
        # If it is a component build (-b bld.inf) we don't have access to the sys def
        # so don't create top level maps and continue
        if self.line_parser.systemdefinition != "":                
            self._write_maps(build_dir, rel_dir)
        self._run_postprocessing(rel_dir)
        return True

    def close(self):
        return True


class BldInfToExportsMap(object):
    "Encapsulates information about project exports"
    def __init__(self, bld_inf_to_export_dict):
        logger.debug("Export dict is: %s" % bld_inf_to_export_dict)
        self.mapping = bld_inf_to_export_dict
    
    def get_exports(self, bld_inf_path):
        if bld_inf_path in self.mapping: 
            return self.mapping[bld_inf_path]
        else:
            return None
   
    def is_platform(self, header):
        return "epoc32/include/platform".upper() in header.upper() 

    def is_public(self, header):
        return not(self.is_platform(header)) and not(self.is_internal(header))    

    def is_internal(self, header):
        return not "epoc32/include".upper() in header.upper()

        
###################################################################################
## Test it on a real build from the CLI by passing it the path to a logfile'
## Didnt use optparse etc as it should NEVER be used by a user, just useful for 
## developers
###################################################################################
class BuildParameters(object):
        epocroot = "\\"

def run(logfile):
    filter = FilterOrb()
    filter.open(BuildParameters())    
    with open(logfile) as log:
        for line in log.readlines():
            filter.write(line)
    filter.summary()
    
if __name__ == "__main__":
    import sys
    import time
    print "Welcome..."
    start = time.time()
    run(sys.argv[1])
    print "Run took: %s mins" % str((time.time() - start)/60)


###################################################################################
## Test code
###################################################################################
import unittest


class TestConfiguration(unittest.TestCase):
    def setUp(self):
        self.config = Configuration()
        self.target = "doxygen" # "orb"

    def test_my_defaults_are_correct(self):        
        self.assertTrue(self.config.publishing_target == "ditaot")
        self.assertTrue(self.config.sdk == False)

    def test_i_can_detect_a_pdk_build(self):
        self.config.parse(self.target)
        self.assertTrue(self.config.sdk == False)
        
    def test_i_can_detect_a_sdk_build(self):    
        self.config.parse(self.target + "-sdk")
        self.assertTrue(self.config.sdk == True)

    def test_i_can_detect_a_ditaot_pdk_build(self):    
        self.config.parse(self.target + "-ditaot")
        self.assertTrue(self.config.publishing_target == "ditaot")        

    def test_i_can_detect_a_ditaot_sdk_build(self):    
        self.config.parse(self.target + "-sdk-ditaot")
        self.assertTrue(self.config.sdk == True)
        self.assertTrue(self.config.publishing_target == "ditaot")
    
    def test_i_can_detect_a_ditaot_sdk_build_if_called_incorrectly(self):
        self.config.parse(self.target + "-ditaot-sdk")
        self.assertTrue(self.config.sdk == True)
        self.assertTrue(self.config.publishing_target == "ditaot")
        
    def test_i_can_detect_a_mode_pdk_build(self):    
        self.config.parse(self.target + "-mode")
        self.assertTrue(self.config.publishing_target == "mode")        

    def test_i_can_detect_a_mode_sdk_build(self):    
        self.config.parse(self.target + "-sdk-mode")
        self.assertTrue(self.config.sdk == True)
        self.assertTrue(self.config.publishing_target == "mode")

    def test_i_can_detect_a_mode_sdk_build_if_called_incorrectly(self):    
        self.config.parse(self.target + "-sdk-mode")
        self.assertTrue(self.config.sdk == True)
        self.assertTrue(self.config.publishing_target == "mode")


class TestLogLineParser(unittest.TestCase):
    def setUp(self):
        self.parser = LogLineParser()

    def test_i_handle_invalid_info_lines(self):
        self.assertEqual(self.parser.cwd, "")
        try:
            self.parser.parse("<info>Current working directory W:\sf")
        except Exception:
            self.fail("An exception should not have been raised")

    def test_i_ignore_non_info_lines(self):
        ret = self.parser.parse("<foo>Current working directory W:\sf")
        self.assertEqual(ret, None)
 
    def test_i_can_parse_cwd_info(self):
        self.assertEqual(self.parser.cwd, "")
        self.parser.parse("<info>Current working directory W:\sf</info>") 
        self.assertEqual(self.parser.cwd, "W:\\sf")

    def test_i_can_parse_system_def_info(self):
        self.assertEqual(self.parser.systemdefinition, "")
        self.parser.parse("<info>System Definition file os/deviceplatformrelease/foundation_system/system_model/system_definition_schema2.xml</info>")
        self.assertEqual(self.parser.systemdefinition, "os\\deviceplatformrelease\\foundation_system\\system_model\\system_definition_schema2.xml")
            
    def test_i_can_parse_full_system_def_info(self):
        self.parser.parse("<info>Current working directory W:\sf</info>")
        self.parser.parse("<info>System Definition file os/deviceplatformrelease/foundation_system/system_model/system_definition_schema2.xml</info>")
        self.assertEqual(self.parser.systemdefinition, "W:\\sf\\os\\deviceplatformrelease\\foundation_system\\system_model\\system_definition_schema2.xml")

    def test_i_can_parse_full_system_def_info_irespective_of_order(self):
        self.parser.parse("<info>System Definition file os/deviceplatformrelease/foundation_system/system_model/system_definition_schema2.xml</info>")        
        self.parser.parse("<info>Current working directory W:\sf</info>")
        self.assertEqual(self.parser.systemdefinition, "W:\\sf\\os\\deviceplatformrelease\\foundation_system\\system_model\\system_definition_schema2.xml")

    def test_i_can_parse_sbs_home_info(self):
        self.assertEqual(self.parser.sbs_home, "")
        self.parser.parse("<info>SBS_HOME C:/APPS/sbs</info>") 
        self.assertEqual(self.parser.sbs_home, "C:\\APPS\\sbs")

    def test_i_can_parse_configuration_info(self):
        self.parser.parse("<info>Buildable configuration 'doxygen-sdk-mode'</info>") 
        self.assertEqual(self.parser.sdk, True)
        self.assertEqual(self.parser.pub_target, "mode")


class TestWhatLogParser(unittest.TestCase):
    def setUp(self):
        self.parser = WhatLogParser()

    def test_i_can_handle_an_invalid_whatlog_line(self):
        try:
            self.parser.parse("<whatlog><oops></whatlog>")
        except xml.parsers.expat.ExpatError:
            self.fail("Should not have raised an XML exception")

    def test_i_can_parse_a_whatlog_line(self):        
        self.parser.parse(example_what)
        self.assertTrue("C:/hydra/sf/os/commsfw/datacommsserver/esockserver/group/bld.inf" in self.parser.exports.keys())
        exports = self.parser.exports["C:/hydra/sf/os/commsfw/datacommsserver/esockserver/group/bld.inf"]
        self.assertEqual(len(exports), 2)
        self.assertTrue("C:/epoc32/include/comms-infras/ss_esockstates.h" in exports.pop())
        self.assertTrue("C:/epoc32/include/comms-infras/ss_esockactivities.h" in exports.pop())

    def test_i_can_parse_a_multiline_whatlog_line(self):
        for line in example_what_lines:
            self.parser.parse(line)
        self.assertTrue("C:/hydra/sf/os/commsfw/datacommsserver/esockserver/group/bld.inf" in self.parser.exports.keys())
        exports = self.parser.exports["C:/hydra/sf/os/commsfw/datacommsserver/esockserver/group/bld.inf"]
        self.assertEqual(len(exports), 2)
        self.assertTrue("C:/epoc32/include/comms-infras/ss_esockstates.h" in exports.pop())
        self.assertTrue("C:/epoc32/include/comms-infras/ss_esockactivities.h" in exports.pop())

    def test_i_can_parse_a_multiline_whatlog_line_at_once(self):
        self.parser.parse("<info>Up-to-date: s:/epoc32/rom/include/shimnotifier.iby</info>")
        self.parser.parse(example_what_line)
        self.parser.parse("<info>Up-to-date: s:/epoc32/rom/include/netsm.iby</info>")
        self.assertTrue("s:/sf/os/commsfw/commsconfig/commsdatabaseshim/group/bld.inf" in self.parser.exports.keys())        
        exports = self.parser.exports["s:/sf/os/commsfw/commsconfig/commsdatabaseshim/group/bld.inf"]
        self.assertEqual(len(exports), 16)
        self.assertTrue('s:/epoc32/include/platform/commdbconnpref.inl' in exports.pop())
        self.assertTrue('s:/epoc32/rom/include/shimnotifier.iby' in exports.pop())

    
class TestFilterOrb(unittest.TestCase):
    def setUp(self):
        self.filterorb = FilterOrb()
        
    def test_i_have_access_to_exports(self):
        self.filterorb.write(example_what)
        exports = self.filterorb.whatparser.exports["C:/hydra/sf/os/commsfw/datacommsserver/esockserver/group/bld.inf"]
        self.assertEqual(len(exports), 2)

    def test_i_catch_invalid_xml_errors(self):
        try:
            self.filterorb.write("<invalid")
        except xml.parsers.expat.ExpatError, e:
            self.fail("Should not have raised an XML exception")
            
    def test_i_have_access_to_configuration_info(self):
        class Store(object):
            epocroot = "/"
        self.filterorb.open(Store())
        for line in build_info.split("\n"):
            self.filterorb.write(line)
        self.filterorb._update_epocroot()
        self.assertEqual(self.filterorb.line_parser.systemdefinition, 
                         "W:\\sf\\os\\deviceplatformrelease\\foundation_system\\system_model\\system_definition_schema2.xml")
        self.assertEqual(self.filterorb.line_parser.sdk, False)
        self.assertEqual(self.filterorb.line_parser.pub_target, "ditaot")
        self.assertEqual(self.filterorb.line_parser.cwd, "W:\\sf")
        self.assertEqual(self.filterorb.line_parser.sbs_home, "C:\\APPS\\sbs")
        self.assertEqual(self.filterorb.epocroot, "W:\\")

    def test_close_returns_true(self):
        self.assertTrue(self.filterorb.close())


class TestBldInfToExportsMap(unittest.TestCase):
    def setUp(self):
        self.bldinf = "C:/My/bldinf/path/bld.inf"
        self.exports = set(("C:/epoc32/include/myfile.h", "C:/sf/myfile.h"))
        self.bitem = BldInfToExportsMap({self.bldinf: self.exports})
        
    def test_i_can_lookup_the_exports_for_a_bldinf(self):
        self.assertEquals(self.bitem.get_exports(self.bldinf), self.exports)
        
    def test_i_gracefully_handle_a_lookup_on_an_export_that_doesnt_exist(self):
        try:
            exports = self.bitem.get_exports("bad/bldinf/path/bld.inf")
        except Exception:
            self.fail("Shouldnt have excepted on a bad lookup")
        else:
            self.assertEquals(exports, None)                    
    
    def test_i_can_return_whether_a_header_is_exported_as_platform(self):
        self.assertTrue(self.bitem.is_platform("Y:/epoc32/include/platform/mw/tacticon.h"))
        
    def test_i_can_return_whether_a_header_is_exported_as_public(self):
        self.assertTrue(self.bitem.is_public("Y:/epoc32/include/mw/touchfeedback.h"))
        
    def test_i_can_return_whether_a_header_is_exported_as_public_case_insensitive(self):
        self.assertTrue(self.bitem.is_public("Y:/EPOC32/INCLUDE/MW/TOUCHFEEDBACK.H"))
        
    def test_i_can_return_whether_a_header_is_exported_as_internal(self):
        self.assertTrue(self.bitem.is_internal("Y:/sf/mw/hapticsservices/tactilefeedback/inc/tactilearearegistry.h"))


example_what = """<whatlog bldinf='C:/hydra/sf/os/commsfw/datacommsserver/esockserver/group/bld.inf' mmp='' config=''><export destination='C:/epoc32/include/comms-infras/ss_esockstates.h' source='C:/hydra/sf/os/commsfw/datacommsserver/esockserver/core_states/ss_esockstates.h'/><export destination='C:/epoc32/include/comms-infras/ss_esockactivities.h' source='C:/hydra/sf/os/commsfw/datacommsserver/esockserver/core_states/ss_esockactivities.h'/></whatlog>"""


example_what_lines = [
    "<whatlog bldinf='C:/hydra/sf/os/commsfw/datacommsserver/esockserver/group/bld.inf' mmp='' config=''>",
    "<export destination='C:/epoc32/include/comms-infras/ss_esockstates.h' source='C:/hydra/sf/os/commsfw/datacommsserver/esockserver/core_states/ss_esockstates.h'/>",
    "<export destination='C:/epoc32/include/comms-infras/ss_esockactivities.h' source='C:/hydra/sf/os/commsfw/datacommsserver/esockserver/core_states/ss_esockactivities.h'/>",
    "</whatlog>"
]

example_what_line = """<whatlog bldinf='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/group/bld.inf' mmp='' config=''>
<export destination='s:/epoc32/include/cdblen.h' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/INC/CDBLEN.H'/>
<export destination='s:/epoc32/include/cdbcols.h' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/INC/CDBCOLS.H'/>
<export destination='s:/epoc32/include/platform/cdbover.h' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/INC/CDBOVER.H'/>
<export destination='s:/epoc32/include/platform/cdbover.inl' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/INC/CDBOVER.INL'/>
<export destination='s:/epoc32/include/platform/cdbstore.h' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/INC/CDBSTORE.H'/>
<export destination='s:/epoc32/include/platform/cdbstore.inl' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/INC/CDBSTORE.INL'/>
<export destination='s:/epoc32/include/commdbconnpref.h' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/INC/CommDbConnPref.h'/>
<export destination='s:/epoc32/include/platform/commdbconnpref.inl' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/INC/CommDbConnPref.inl'/>
<export destination='s:/epoc32/include/commdb.h' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/INC/COMMDB.H'/>
<export destination='s:/epoc32/include/platform/commdb.inl' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/INC/COMMDB.INL'/>
<export destination='s:/epoc32/include/cdbtemp.h' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/INC/CDBTEMP.H'/>
<export destination='s:/epoc32/include/cdbpreftable.h' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/INC/CDBPREFTABLE.H'/>
<export destination='s:/epoc32/include/platform/comms-infras/commdb/protection/protectdb.h' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/ProtectedDB/ProtectDB.h'/>
<export destination='s:/epoc32/include/platform/comms-infras/commdb/protection/protectcpdb.h' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/ProtectedDB/protectcpdb.h'/>
<export destination='s:/epoc32/rom/include/commdb.iby' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/group/commdb.iby'/>
<export destination='s:/epoc32/rom/include/shimnotifier.iby' source='s:/sf/os/commsfw/commsconfig/commsdatabaseshim/commdbshim/Notifier/group/ShimNotifier.iby'/>
</whatlog>

"""


build_info = """<info>sbs: version 2.10.0 [2009-10-05 sf release]
</info>
<info>SBS_HOME C:/APPS/sbs</info>
<info>Set-up C:/APPS/sbs/sbs_init.xml</info>
<info>Command-line-arguments -c doxygen -s os\deviceplatformrelease\foundation_system\system_model\system_definition_schema2.xml -k -j 12</info>
<info>Current working directory W:\sf</info>
<info>Environment EPOCROOT=\</info>
<info>Buildable configuration 'doxygen'</info>
<info>System Definition file os/deviceplatformrelease/foundation_system/system_model/system_definition_schema2.xml</info>"""
