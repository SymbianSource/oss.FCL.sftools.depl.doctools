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
import os
import shutil
import sys
import xml
import logging
from optparse import OptionParser
from xml.etree import ElementTree as etree
from lib import scan, xml_decl, doctype_identifier

__version__ = "0.1"


class ComponentMapCreator(object):
    
    def __init__(self, build_dir, output_dir):
        self.build_dir = os.path.abspath(build_dir)
        self._check_dir_exists(self.build_dir)
        self.output_dir = output_dir
    
    def _check_dir_exists(self, dir):
        dir = os.path.abspath(dir)
        if not os.path.exists(dir):
            raise Exception("Directory path %s does not exist" % dir)    
        
    def _get_component_names(self):
        component_names = [d for d in os.listdir(self.build_dir) if os.path.isdir(os.path.join(self.build_dir, d))]
        component_names.sort()
        return component_names 
    
    def _get_ditamaps_for_component(self, component_name):
        component_dir = self._get_component_dir_for_component(component_name)
        ditamaps = []
        for root, dirs, files in os.walk(component_dir):
            for filename in (filename for filename in files if filename.lower().endswith(".ditamap")):
                ditamaps.append(os.path.join(root, filename))
        return ditamaps
    
    def _get_component_dir_for_component(self, component):
        return os.path.join(self.build_dir, component)
    
    def _create_topicref(self, target_name):
        return etree.Element("topicref", href=target_name+".ditamap", format="ditamap")
    
    def _get_topicrefs_from_map(self, ditamap):
        try:
            root = etree.parse(ditamap).getroot()
        except xml.parsers.expat.ExpatError, e:
            logging.error("Could not parse ditamap: %s, error was: %s " % (ditamap, e))
            return None
        else:
            return root.getchildren()
    
    def _get_topicrefs_for_component(self, component_name):
        topicrefs = []
        seen = []
        for ditamap in self._get_ditamaps_for_component(component_name):
            target_topicrefs = self._get_topicrefs_from_map(ditamap)
            if target_topicrefs is not None:
                for topicref in target_topicrefs:
                    if not topicref.attrib['navtitle'] in seen:
                        seen.append(topicref.attrib['navtitle'])
                        topicrefs.append(topicref)
        topicrefs.sort()
        return topicrefs
    
    def _create_map_root(self, component_name):
        return etree.Element("cxxAPIMap", title=component_name, id='cmp_'+component_name)    

    def _get_ditamap(self, component_name):
        root = self._create_map_root(component_name)
        for topicref in self._get_topicrefs_for_component(component_name):
            root.append(topicref)
        if len(root.getchildren()) > 0: # If the component does not link to anything 
            return root                 # return None (instead of an empty map)
        else:
            return None    
    
    def _handle_component(self, component_name):
        map = self._get_ditamap(component_name)
        if map is not None:
            f = open(os.path.join(self.output_dir, 'cmp_'+component_name+".ditamap"), "w")
            f.write(xml_decl()+"\n")
            f.write(doctype_identifier("cxxAPIMap")+"\n")
            f.write(etree.tostring(map))
            f.close()
        else:
            logging.info("No component ditamap needed to be generated for component \"%s\"" % component_name)
                
    def create_component_maps(self):
        components = self._get_component_names()
        for component in components:
            self._handle_component(component)     
            
            
def create_component_maps(build_dir, output_dir):
    cmp = ComponentMapCreator(build_dir, output_dir)
    cmp.create_component_maps()
            
def main(func):
    usage = "usage: %prog [options] build_dir output_dir"
    parser = OptionParser(usage, version='%prog ' + __version__)
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.print_help()
    build_dir, output_dir = os.path.abspath(args[0]), os.path.abspath(args[1])
    if not os.path.exists(build_dir):
        parser.error('build_dir: "%s" does not exist' % build_dir)
    func(build_dir, output_dir)
        
if __name__ == '__main__':
    sys.exit(main(func=create_component_maps))
    
                
cmp_audiomsg_ditamap = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="cmp_audiomsg" title="audiomsg"><cxxStructRef href="struct___array_util.xml#_ArrayUtil" navtitle="_ArrayUtil" />
    </cxxAPIMap>"""

audiomessage_ditamap = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.1.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="audiomessage" title="audiomessage">
    <cxxStructRef href="struct___array_util.xml#_ArrayUtil" navtitle="_ArrayUtil"/>
    <cxxStructRef href="struct___array_util.xml#_ArrayUtil" navtitle="_ArrayUtil"/>
</cxxAPIMap>
"""

empty_target_ditamap = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.1.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="empty_target" title="empty_target">
</cxxAPIMap>
"""


class TestComponentCreator(unittest.TestCase):
    def setUp(self):
        self.test_build_dir = os.path.join(os.getcwd(), "test_build_dir")
        self._create_test_build_dir()
        self.output_dir = os.path.join(os.getcwd(), "output")
        self.cmp = ComponentMapCreator(self.test_build_dir, self.output_dir)
        self._create_output_dir()
        
    def tearDown(self):
        self._clean_test_build_dir()
        self._clean_output_dir()
        
    def _create_test_build_dir(self):
        # Create 2 components
        for comp_name in ("audiomsg", "component_with_no_dita_in_it"):
            os.makedirs(os.path.join(self.test_build_dir, comp_name))
        # Create logfiles
        makefile = open(os.path.join(self.test_build_dir, "Makefile"), "w")
        logfile = open(os.path.join(self.test_build_dir, "logfile.log"), "w")
        # Create target ditamaps
        audiomessage_ditamap_dir = os.path.join(self.test_build_dir, "audiomsg", "c_96422b786aab3b96", "audiomessage_exe", "dox", "dita")
        empty_target_ditamap_dir = os.path.join(self.test_build_dir, "audiomsg", "c_96422b786aab3b96", "empty_target_exe", "dox", "dita")
        self.audiomessage_ditamap_path = os.path.join(audiomessage_ditamap_dir, "audiomessage.ditamap")
        self.empty_target_ditamap_path = os.path.join(empty_target_ditamap_dir, "empty_target.ditamap") 
        os.makedirs(audiomessage_ditamap_dir)
        os.makedirs(empty_target_ditamap_dir)
        audiomessage_ditamap_handle = open(self.audiomessage_ditamap_path, "w")
        audiomessage_ditamap_handle.write(audiomessage_ditamap)
        audiomessage_ditamap_handle.close()
        empty_target_ditamap_handle = open(self.empty_target_ditamap_path, "w")
        empty_target_ditamap_handle.write(empty_target_ditamap)
        empty_target_ditamap_handle.close()
        
    def _create_output_dir(self):
        os.mkdir(self.output_dir)    
            
    def _clean_test_build_dir(self):
        shutil.rmtree(self.test_build_dir)
                    
    def _clean_output_dir(self):
        shutil.rmtree(self.output_dir)    
                    
    def test_i_return_all_the_component_names_when_passed_a_dir(self):
        component_names = self.cmp._get_component_names()
        self.assertEquals(component_names, ["audiomsg", "component_with_no_dita_in_it"])
            
    def test_i_return_all_target_ditamaps_for_a_component(self):
        target_ditamaps = self.cmp._get_ditamaps_for_component("audiomsg")
        self.assertEquals(target_ditamaps, [self.audiomessage_ditamap_path, self.empty_target_ditamap_path])
        
    def test_i_return_a_component_directory_for_a_component(self):
        component_dir = self.cmp._get_component_dir_for_component("audiomsg")
        self.assertEquals(component_dir, os.path.join(self.test_build_dir, "audiomsg"))
        
    def test_i_create_a_ditamap_for_a_component(self):
        ditamap = self.cmp._get_ditamap("audiomsg")
        self.assertEquals(ditamap.tag, "cxxAPIMap") 
        self.assertEquals(ditamap.attrib.get("title", ""), "audiomsg")
        self.assertEquals(ditamap.attrib.get("id", ""), "cmp_audiomsg")
        
    def test_i_dont_create_a_ditamap_for_a_component_with_no_dita(self):
        ditamap = self.cmp._get_ditamap("component_with_no_dita_in_it")
        self.assertEquals(ditamap, None)
        
    def test_i_can_write_out_a_ditamap_file_for_a_component(self): 
        self.cmp._handle_component("audiomsg")
        self.assertTrue(os.path.exists(os.path.join(self.output_dir,"cmp_audiomsg.ditamap")))
        map = open(os.path.join(self.output_dir,"cmp_audiomsg.ditamap"),"r").read()        
        self.assertEquals(map, cmp_audiomsg_ditamap)
        
    def test_i_write_component_maps(self):
        self.cmp.create_component_maps()
        file_list = os.listdir(self.output_dir)
        file_list.sort()
        self.assertEquals(file_list, ["cmp_audiomsg.ditamap"])    