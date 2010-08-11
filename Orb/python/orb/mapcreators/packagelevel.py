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
from __future__ import with_statement
try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree
from mapentry import MapEntry
import logging
import os


logger = logging.getLogger('orb.mapcreators.packagelevel')


class PackageLevelMapFilter(object):
    """
    Takes a PackageLevelMap (a list of MapEntries) and filters out
    any that dont belong to a component
    """
    def __init__(self, plm, href_loader, sdk_build=False):
        self._plm = plm
        self.sdk_build = sdk_build
        self.href_loader = href_loader

    def filter(self, exports_manager):
        component_map_entries = []
        logging.debug("Mapentries: '%s'" % self._plm)      
        for mapentry in [e for e in self._plm if e.href is not None]:            
            header_file = self.href_loader.get(mapentry.href)
            export_path = exports_manager.get_export_path_for(header_file)
            logger.debug("Looking up href: '%s', exported as: '%s'" % (mapentry.href, export_path))
            if export_path:   
                if self.sdk_build and not exports_manager.is_public(export_path):
                    logger.debug('Filtering out "%s". Not exported as public.' % (mapentry.navtitle))                  
                else:
                    component_map_entries.append(mapentry)          
            else: # File was not exported so filter it out
                logger.debug('Filtering out "%s". Not exported in the sbs log file' % (mapentry.navtitle))          
        return component_map_entries


class PackageLevelMapCreator(object):
    """
    Reads all the target level maps created for a package by doxygen and
    returns the items in them as a list of MapEntry objects.
    """
    def __init__(self, sysdef, build_dir):
        self.sysdef = sysdef
        self.build_dir = build_dir

    def _get_targetmap_paths_for_component(self, component_id):
        sbs_out_dir = self.sysdef.get_sbs_output_dir(component_id)
        logger.debug("Got sbs_out_dir: '%s'" % sbs_out_dir)
        if sbs_out_dir is None or sbs_out_dir == "":
            logger.warning("sbs_out_dir could not be retrieved for: '%s'" % component_id)
            return [] 
        sbs_output_dir = os.path.abspath(self.build_dir + os.sep + sbs_out_dir)
        logger.debug("sbs_output_dir is: '%s'" % sbs_output_dir)
        if sbs_output_dir is None:
            logger.warning("No known build output directory for component '%s', no target maps discovered" % component_id)
            return []
        if not os.path.exists(sbs_output_dir):
            logger.warning("Build output directory '%s' for component '%s' does not exist, no target maps discovered" % (sbs_output_dir, component_id))
            return []
        targetmaps = []
        for root, _, files in os.walk(sbs_output_dir):
            for filename in (filename for filename in files if filename.lower().endswith(".ditamap")):
                targetmaps.append(os.path.join(root, filename))
        logging.debug("Found the following targetmaps: '%s'" % targetmaps)
        return targetmaps
        
    def _get_targetmap(self, ditamap):
        try:
            return etree.parse(ditamap).getroot()
        except Exception, e:
        #except xml.parsers.expat.ExpatError, e:
            logger.error("Could not parse ditamap: %s, error was: %s " % (ditamap, e))
            return None

    def _get_map_entries(self, elems):
        entries = set()
        for elem in elems:
            children = []
            if len(elem) > 0:
                children = self._get_map_entries(elem.getchildren())
            entries.add(MapEntry(
                    tag = elem.tag,
                    href = elem.get('href'),
                    navtitle = elem.get('navtitle'),
                    children = list(children)
            ))
        return entries

    def _get_targetmap_for(self, component_id):
        entries = set()
        for targetmap_path in self._get_targetmap_paths_for_component(component_id):
            logger.debug("Got target map path: '%s'" % targetmap_path)
            for entry in self._get_map_entries(self._get_targetmap(targetmap_path).getchildren()):
                entries.add(entry)
        return entries
            
    def get_package_level_map(self, package_id):    
        """
        Returns an etree map of topics for a package
        """
        entries = set()
        for component in self.sysdef.get_components(package_id):
            logger.debug("Adding component: '%s'" % component.id)
            for targetmap in self._get_targetmap_for(component.id):
                logger.debug("Adding target map: '%s'" % targetmap.navtitle)
                entries.add(targetmap)                        
        return list(entries)


################################################################
# Unit test code
################################################################
import unittest
import shutil
from _shared import StubSysdef, StubPackageLevelMapCreator 


class HrefLoaderStub(object):
    def __init__(self, path):
        pass
    
    def get(self, href):
        if href.startswith("struct___array_util.xml"):
            return "W:/epoc32/include/mw/aknSoundinfo.h"
        elif href.startswith("class_b_trace.xml"):
            return "W:/epoc32/include/platform/mw/pslnfwappthemehandler.h"
        elif href.startswith("class_c_active.xml"):
            return "W:/sf/os/graphics/displayconfiguration.h"
        elif href.startswith("class_c_active_scheduler.xml"):
            return "W:/epoc32/include/mw/AiwServiceHandler.h"
        elif href.startswith("class_c_active_scheduler_wait.xml"):
            return "W:/epoc32/include/platform/mw/pslnfwappthemehandler.h"
        elif href.startswith("class_c_always_online_disk_space_observer.xml"):
            return "W:/sf/os/graphics/extensioncontainer.h"
        elif href.startswith("class_c_always_online_e_com_interface.xml"):
            return "W:/epoc32/include/mw/aknSoundinfo.h"
        elif href.startswith("class_c_always_online_manager.xml"):
            return "W:/epoc32/include/platform/mw/mpslnfwappthemeobserver.h"
        elif href.startswith("nested_and_removed.xml"):
            return "W:/epoc32/include/mw/foo/not_in_a_this_component.h"
        elif href.startswith("class_c_active_scheduler_1_1_t_cleanup_bundle.xml"):
            return "W:/epoc32/include/mw/bar/in_a_this_component.h"        
        else:
            return "D:/no/header.h"


class StubComponentExportsManager(object):
    def __init__(self, sdk=False):
        self.sdk = sdk

    def get_export_path_for(self, filepath):
        if filepath in ("W:/epoc32/include/mw/aknSoundinfo.h", 
                        "W:/epoc32/include/platform/mw/pslnfwappthemehandler.h",
                        "W:/epoc32/include/mw/AiwServiceHandler.h"):
            return filepath
        elif filepath == "W:/sf/os/graphics/displayconfiguration.h":
            return "W:/epoc32/include/displayconfiguration.h"
        elif filepath == "W:/sf/os/graphics/extensioncontainer.h":
            return "W:/epoc32/include/extensioncontainer.h"
        else:
            return None

    def is_public(self, filepath):
        return "platform" in filepath


class TestPackageLevelMapFilter(unittest.TestCase):
    def setUp(self):
        sysdef = StubSysdef()
        plmcreator = StubPackageLevelMapCreator(sysdef, "")
        self.plm = plmcreator.get_package_level_map('classicui')
    
    def test_i_correctly_filter_a_pdk_map(self):
        plmfilter = PackageLevelMapFilter(self.plm, HrefLoaderStub("."), sdk_build=False)
        filtered_map = plmfilter.filter(StubComponentExportsManager())
        self.assertEqual(len(filtered_map), 7)
    
    def test_i_correctly_filter_a_sdk_map(self):
        plmfilter = PackageLevelMapFilter(self.plm, HrefLoaderStub("."), sdk_build=True)
        filtered_map = plmfilter.filter(StubComponentExportsManager(True))
        self.assertEqual(len(filtered_map), 2)    


class TestPackageLevelMapCreator(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath("filter_orb_test_dir"+os.sep+"TestPackageLevelMapCreator_test_dir")
        self.build_dir = self.test_dir+os.sep+"build"
        self.plmc = PackageLevelMapCreator(StubSysdef(), self.build_dir)
        self._create_test_build_dir()

    def _create_test_build_dir(self):
        # Create test component directories
        akncapserver_ditamap_dir = os.path.join(self.build_dir, "aknglobalui", "c_f539995457c01233", "akncapserver_exe", "dox", "dita")
        commonui_ditamap_dir = os.path.join(self.build_dir, "commonui", "c_e0f69e4ef2e4676e", "commonui_dll", "dox", "dita")
        badly_formed_ditamap_dir = os.path.join(self.build_dir, "badly_formed")
        for dir in (akncapserver_ditamap_dir, commonui_ditamap_dir, badly_formed_ditamap_dir):             
            os.makedirs(dir)
        # Create test ditamaps
        self.akncapserver_ditamap_path = os.path.join(akncapserver_ditamap_dir, "akncapserver.ditamap")
        self.commonui_ditamap_path = os.path.join(commonui_ditamap_dir, "commonui.ditamap") 
        self.badly_formed_ditamap_path = os.path.join(badly_formed_ditamap_dir, "badly_formed.ditamap")
        with open(self.akncapserver_ditamap_path, "w") as adh:
            adh.write(akncapserver_ditamap)
        with open(self.commonui_ditamap_path, "w") as cdh: 
            cdh.write(commonui_ditamap)
        with open(self.badly_formed_ditamap_path, "w") as bfdh:
            bfdh.write(badly_formed_ditamap)
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)    
 
    def test_i_can_return_targetmap_paths_for_a_component(self):
        targetmaps = self.plmc._get_targetmap_paths_for_component("aknglobalui")
        self.assertEquals(targetmaps, [self.akncapserver_ditamap_path])
                
    def test_i_gracefully_handle_a_badly_formed_target_map(self):
        root = self.plmc._get_targetmap(self.badly_formed_ditamap_path)
        self.assertEquals(root, None)

    def test_the_list_of_mapentries_i_returned_is_filtered(self):
        plm = self.plmc.get_package_level_map("classicui")
        self.assertEquals(len(plm), 4)
        for entry in plm:
            self.assertTrue(
                entry.href in (
                    "class_c_akn_sound_info.xml#class_c_akn_sound_info", 
                    "class_c_aiw_service_handler.xml#class_c_aiw_service_handler",
                    "class_c_active_scheduler.xml#class_c_active_scheduler",
                    "class_c_service_handler.xml"
                )
            )
            self.assertTrue(
                entry.navtitle in (
                    "CAknSoundInfo", 
                    "CAiwServiceHandler",
                    "class_c_active_scheduler",
                    "CServiceHandler"
                )
            )  


akncapserver_ditamap = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="akncapserver" title="akncapserver">
    <cxxClassRef href="class_c_akn_sound_info.xml#class_c_akn_sound_info" navtitle="CAknSoundInfo" />
    <cxxClassRef href="class_c_aiw_service_handler.xml#class_c_aiw_service_handler" navtitle="CAiwServiceHandler" />
    <cxxClassRef href="class_c_active_scheduler.xml#class_c_active_scheduler" navtitle="class_c_active_scheduler">
        <cxxClassRef href="class_c_active_sub.xml#class_c_active_scheduler" navtitle="class_c_active_scheduler_1_1_t_cleanup_bundle"/>
    </cxxClassRef>    
</cxxAPIMap>"""

 
commonui_ditamap = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="CommonUI" title="CommonUI">
    <cxxClassRef href="class_c_aiw_service_handler.xml#class_c_aiw_service_handler" navtitle="CAiwServiceHandler" />
    <cxxClassRef href="class_c_service_handler.xml" navtitle="CServiceHandler" />
</cxxAPIMap>"""     

 
badly_formed_ditamap = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="BadlyFormed" title="BadlyFormed">
    <cxxClassRef href="class_c_aiw_service_handler.xml#class_c_aiw_service_handler" navtitle="CAiwServiceHandler" />
</cxxAPIMap"""  