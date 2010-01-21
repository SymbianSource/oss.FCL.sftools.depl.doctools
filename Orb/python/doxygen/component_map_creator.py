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
    
    def _get_ditamap_names_for_component_dir(self, component_dir):
        self._check_dir_exists(component_dir)
        ditamap_names = []
        for root, dirs, files in os.walk(component_dir):
            ditamap_names.extend([os.path.splitext(f)[0] for f in files if f.lower().endswith(".ditamap")])
        ditamap_names.sort()
        return ditamap_names
    
    def _get_component_dir_for_component(self, component):
        return os.path.join(self.build_dir, component)
    
    def _create_topicref(self, target_name):
        return etree.Element("topicref", href=target_name+".ditamap", type="ditamap")
    
    def _create_topichead(self, target_name):
        topichead = etree.Element("topichead", navtitle=target_name)
        topichead.append(self._create_topicref(target_name))
        return topichead
    
    def _create_map(self, component_name):
        return etree.Element("map", title=component_name, id="cmp_"+component_name)
    
    def _create_ditamap(self, component_name):
        root = self._create_map(component_name)
        for topichead in self._get_topicheads_for_component(component_name):
            root.append(topichead)
        return root
    
    def _get_topicheads_for_component(self, component_name):
        topicheads = []
        for ditamap_name in self._get_ditamap_names_for_component_dir(self._get_component_dir_for_component(component_name)):
            topicheads.append(self._create_topichead(ditamap_name))
        topicheads.sort()
        return topicheads
    
    def _write_ditamap_for_component(self, component_name):
        f = open(os.path.join(self.output_dir, "cmp_"+component_name+".ditamap"), "w")
        f.write(xml_decl()+"\n")
        f.write(doctype_identifier("map")+"\n")
        map = self._create_ditamap(component_name)
        f.write(etree.tostring(map))
        f.close()
                
    def create_component_maps(self):
        components = self._get_component_names()
        for component in components:
            self._write_ditamap_for_component(component)     
            
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
<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">
<map id="cmp_audiomsg" title="audiomsg"><topichead navtitle="audiomessage"><topicref href="audiomessage.ditamap" type="ditamap" /></topichead></map>"""

audiomessage_ditamap = """
<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.1.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="audiomessage" title="audiomessage">
    <cxxStructRef href="struct___array_util.xml#_ArrayUtil" navtitle="_ArrayUtil"/>
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
        # Create 3 components
        for comp_name in ("audiomsg", "console", "autotest"):
            os.makedirs(os.path.join(self.test_build_dir, comp_name))
        # Create logfiles
        makefile = open(os.path.join(self.test_build_dir, "Makefile"), "w")
        logfile = open(os.path.join(self.test_build_dir, "logfile.log"), "w")
        # Create target ditamap
        audiomessage_ditamap_dir = os.path.join(self.test_build_dir, "audiomsg", "c_96422b786aab3b96", "audiomessage_exe", "dox", "dita")
        audiomessage_ditamap_path = os.path.join(audiomessage_ditamap_dir, "audiomessage.ditamap") 
        os.makedirs(audiomessage_ditamap_dir)
        audiomessage_ditamap_handle = open(audiomessage_ditamap_path, "w")
        audiomessage_ditamap_handle.write(audiomessage_ditamap)
        audiomessage_ditamap_handle.close()

    def _create_output_dir(self):
        os.mkdir(self.output_dir)    
            
    def _clean_test_build_dir(self):
        shutil.rmtree(self.test_build_dir)
                    
    def _clean_output_dir(self):
        shutil.rmtree(self.output_dir)    
                    
    def test_i_return_all_the_component_names_when_passed_a_dir(self):
        component_names = self.cmp._get_component_names()
        self.assertEquals(component_names, ["audiomsg", "autotest", "console"])
            
    def test_i_return_all_target_ditamap_names_for_a_component(self):
        target_ditamap_names = self.cmp._get_ditamap_names_for_component_dir(os.path.join(self.test_build_dir, "audiomsg"))
        self.assertEquals(target_ditamap_names, ["audiomessage"])
        
    def test_i_return_a_component_directory_for_a_component(self):
        component_dir = self.cmp._get_component_dir_for_component("audiomsg")
        self.assertEquals(component_dir, os.path.join(self.test_build_dir, "audiomsg"))
        
    def test_i_return_a_topicref_element_for_a_target(self):
        topicref = self.cmp._create_topicref("audiomessage")
        self.assertEquals(topicref.attrib["href"], "audiomessage.ditamap")
        self.assertEquals(topicref.attrib["type"], "ditamap")
        
    def test_i_return_a_list_of_topicheads_for_a_component(self):
        topicheads = self.cmp._get_topicheads_for_component("audiomsg")
        self.assertEquals(len(topicheads), 1)
        
        
    def test_i_create_a_ditamap_for_a_component(self):
        ditamap = self.cmp._create_ditamap("audiomsg")
        self.assertEquals(ditamap.tag, "map") 
        self.assertEquals(ditamap.attrib.get("title", ""), "audiomsg")
        self.assertEquals(ditamap.attrib.get("id", ""), "cmp_audiomsg")
        
    def test_i_can_write_out_a_ditamap_file_for_a_component(self): 
        self.cmp._write_ditamap_for_component("audiomsg")
        self.assertTrue(os.path.exists(os.path.join(self.output_dir,"cmp_audiomsg.ditamap")))
        map = open(os.path.join(self.output_dir,"cmp_audiomsg.ditamap"),"r").read()
        print map
        print cmp_audiomsg_ditamap
        self.assertEquals(map, cmp_audiomsg_ditamap)
        
    def test_i_write_component_maps(self):
        self.cmp.create_component_maps()
        file_list = os.listdir(self.output_dir)
        file_list.sort()
        self.assertEquals(file_list, ["cmp_audiomsg.ditamap", "cmp_autotest.ditamap", "cmp_console.ditamap"])    