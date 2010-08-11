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
from orb.lib import xml_decl, doctype_identifier
import logging
import os


logger = logging.getLogger('orb.mapcreators.componentlevel')


class ComponentExportsManager(object):
    """
    Retrieves bld.infs from the systemdefinition and exports from 
    the log file. 
    
    get_export_path_for: When called with the path to a header file,
    returns the path the header file is exported to.
    """
    def __init__(self, sysdef, component, exportsmap):
        self.sysdef = sysdef
        self.exportsmap = exportsmap
        self._fullpaths = [a[0] for a in self._get_export_headers(component)]
        self._basenames = [os.path.basename(a) for a in self._fullpaths]

    def _get_export_headers(self, component):
        export_headers = set()
        for bld_inf in self.sysdef.get_bldinfs(component.id):
            component_exports = self.exportsmap.get_exports(bld_inf)
            if component_exports != None:
                export_headers = export_headers.union(component_exports)
        logger.debug("I got these export headers from the log: %s" % (str(export_headers)))            
        return export_headers
    
    def get_export_path_for(self, filepath):
        export_path = None
        for basename, fullpath in zip(self._basenames, self._fullpaths):
            if basename == os.path.basename(filepath):
                export_path = fullpath
        return export_path

    def is_public(self, filepath):
        return self.exportsmap.is_public(filepath)


class ComponentMapCreator(object):
    "Writes out component level DITAMAPS"
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def _process_elems(self, parent, entries):
        entries.sort(key=lambda item: item.navtitle)
        for entry in entries:
            href = entry.href if entry.href is not None else "" 
            navtitle = entry.navtitle if entry.navtitle is not None else ""
            elem = etree.SubElement(parent, entry.tag, href=href, navtitle=navtitle)
            if len(entry.children) > 0:
                self._process_elems(elem, entry.children)

    def get_component_level_map(self, component, entries):
        root = etree.Element("cxxAPIMap", id="cmp_%s" % component.id, title=component.name)
        self._process_elems(root, entries)
        return root

    def write(self, root):        
        if len(root) == 0:
            return
        with open(os.path.join(self.output_dir, root.get("id")+".ditamap"), "w") as f:
            f.write(xml_decl()+"\n")
            f.write(doctype_identifier("cxxAPIMap")+"\n")
            f.write(etree.tostring(root))


################################################################
# Unit test code
################################################################
import unittest
import shutil
from _shared import StubSysdef, StubBldInfExportsMap, StubPackageLevelMapCreator


class TestComponentExportsManager(unittest.TestCase):
    def test_i_get_the_correct_declaration_path_for_a_file(self):
        component_classicui_pub = StubSysdef().get_components("classicui")[0]
        cm = ComponentExportsManager(StubSysdef(), component_classicui_pub, StubBldInfExportsMap())
        fpath = cm.get_export_path_for("W:/foo/bar/aknSoundinfo.h")
        self.assertEqual(fpath, "W:/epoc32/include/mw/aknSoundinfo.h")


class TestComponentMapCreator(unittest.TestCase):

    def setUp(self):
        self.plmcreator = StubPackageLevelMapCreator(StubSysdef(),"")
        self.cmc = ComponentMapCreator(".")
        self.test_dir = os.path.abspath(os.path.join("TestComponentMapCreator_test"))
        os.makedirs(self.test_dir)        

    def tearDown(self):
        shutil.rmtree(self.test_dir)
  
    def test_i_create_a_correct_component_level_map(self):
        expected_clm = """<cxxAPIMap id="cmp_classicui_pub" title="Classic UI Public Interfaces">
    <cxxClassRef href="class_b_trace.xml#class_b_trace" navtitle="class_b_trace">
        <cxxStructRef href="struct_b_trace_1_1_s_exec_extension.xml#struct_b_trace_1_1_s_exec_extension" navtitle="struct_b_trace_1_1_s_exec_extension" />
    </cxxClassRef>
    <cxxClassRef href="class_c_active.xml#class_c_active" navtitle="class_c_active" />
    <cxxClassRef href="class_c_active_scheduler.xml#class_c_active_scheduler" navtitle="class_c_active_scheduler">
        <cxxClassRef href="class_c_active_scheduler_1_1_t_cleanup_bundle.xml#class_c_active_scheduler_1_1_t_cleanup_bundle" navtitle="class_c_active_scheduler_1_1_t_cleanup_bundle" />
    </cxxClassRef>
    <cxxClassRef href="class_c_active_scheduler_wait.xml#class_c_active_scheduler_wait" navtitle="class_c_active_scheduler_wait" />
    <cxxClassRef href="class_c_always_online_disk_space_observer.xml#class_c_always_online_disk_space_observer" navtitle="class_c_always_online_disk_space_observer" />
    <cxxClassRef href="class_c_always_online_e_com_interface.xml#class_c_always_online_e_com_interface" navtitle="class_c_always_online_e_com_interface">
        <cxxStructRef href="nested_and_removed.xml" navtitle="" />
        <cxxStructRef href="struct_c_always_online_e_com_interface_1_1___c_e_com_interface_init_params.xml#struct_c_always_online_e_com_interface_1_1___c_e_com_interface_init_params" navtitle="struct_c_always_online_e_com_interface_1_1___c_e_com_interface_init_params" />
    </cxxClassRef>
    <cxxClassRef href="class_c_always_online_manager.xml#class_c_always_online_manager" navtitle="class_c_always_online_manager" />
    <cxxClassRef href="class_c_always_online_manager_server.xml#class_c_always_online_manager_server" navtitle="class_c_always_online_manager_server" />
    <cxxStructRef href="struct___array_util.xml#struct___array_util" navtitle="struct___array_util" />
    <cxxClassRef href="test_class_defined_in_src_path.xml#test_class_defined_in_src_path" navtitle="test_class_defined_in_src_path" />
</cxxAPIMap>"""
        classicui_comp = StubSysdef().get_components("classicui")[0]
        plm = self.plmcreator.get_package_level_map("classicui")
        exp_clm = etree.fromstring(expected_clm)
        clm = self.cmc.get_component_level_map(classicui_comp, plm)
        self.assertEqual(len(clm), len(exp_clm))
        print etree.tostring(clm)
        for recieved, expected in zip(clm.getiterator(), exp_clm.getiterator()):
            self.assertEqual(recieved.tag, expected.tag)
            self.assertEqual(recieved.attrib, expected.attrib)
  
    def test_i_can_write_a_component_map_to_the_file_system(self):        
        map = etree.fromstring(expected_clm)
        self.cmc.output_dir = self.test_dir
        self.cmc.write(map)
        map_path = os.path.join(self.test_dir, "cmp_classicui_pub.ditamap") # map names should be cmp_ + mapid
        self.assertTrue(os.path.exists(map_path))
        content = open(map_path, "r").read()
        self.assertTrue(content.find("<?xml") == 0) # it has a doctype declaration
        self.assertTrue(content.find("<!DOCTYPE cxxAPIMap") != -1) # it has doctype decl
        self.assertTrue(content.find('<cxxAPIMap id="cmp_classicui_pub"') != -1) # it has the map
        
    def test_i_dont_write_out_an_empty_component_map_to_the_file_system(self):        
        map = etree.fromstring(empty_clm)
        self.cmc.output_dir = self.test_dir
        self.cmc.write(map)
        map_path = os.path.join(self.test_dir, "cmp_classicui_pub.ditamap") # map names should be cmp_ + mapid
        self.assertFalse(os.path.exists(map_path)) # Shouldnt have been written out as map was empty        


expected_clm = """<cxxAPIMap id="cmp_classicui_pub" title="Classic UI Public Interfaces">
    <cxxStructRef href="struct___array_util.xml#struct___array_util" navtitle="struct___array_util" />
    <cxxClassRef href="class_c_active_scheduler.xml#class_c_active_scheduler" navtitle="class_c_active_scheduler">
        <cxxClassRef href="class_c_active_scheduler_1_1_t_cleanup_bundle.xml#class_c_active_scheduler_1_1_t_cleanup_bundle" navtitle="class_c_active_scheduler_1_1_t_cleanup_bundle" />
    </cxxClassRef>
    <cxxClassRef href="class_c_always_online_e_com_interface.xml#class_c_always_online_e_com_interface" navtitle="class_c_always_online_e_com_interface">
        </cxxClassRef>
    </cxxAPIMap>"""

empty_clm = """<cxxAPIMap id="cmp_classicui_pub" title="Classic UI Public Interfaces"></cxxAPIMap>"""        
