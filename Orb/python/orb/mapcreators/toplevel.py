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
from orb.lib import xml_decl
import logging
import os
import copy


logger = logging.getLogger('orb.mapcreators.toplevel')


def component_map_lookup(rel_dir, mapname):
    "Checks the file system to see if a component level map exists"
    exists = os.path.exists(os.path.join(rel_dir, mapname))
    if not exists:
        logger.debug("Asked for a component map for '%s' but it does not exist" % mapname)
    return exists


class TopLevelMapCreator(object):
    """
    Uses the information in a SystemDefinition object to create a top level map that
    links to all the component level maps together.
    """
    def __init__(self, sysdef, rel_dir, lookupmethod=component_map_lookup):
        self.sysdef = sysdef
        self._rel_dir = rel_dir
        self._lookup = lookupmethod
        self._root = etree.Element("map", title=sysdef.name, id=sysdef.name)

    def _add_subelems(self, parent, item):
        return etree.SubElement(parent, "topichead", navtitle=item.name, id=item.id)

    def getmap(self):
        def sort(item):
            return item.name
        layers = self.sysdef.layers
        layers.sort(key=sort)
        for layer in layers:
            layer_elem = self._add_subelems(self._root, layer)
            packages = layer.packages
            packages.sort(key=sort)
            for package in packages:
                pkg_elem = self._add_subelems(layer_elem, package)
                collections = package.collections
                collections.sort(key=sort)                
                for collection in collections:                    
                    col_elem = self._add_subelems(pkg_elem, collection)
                    components = collection.components
                    components.sort(key=sort)
                    for item in components:                        
                        if self._lookup(self._rel_dir, "cmp_%s.ditamap" % item.id):
                            col_header = self._add_subelems(col_elem, item) 
                            etree.SubElement(col_header, "topicref", navtitle=item.name, href="cmp_%s.ditamap" % item.id, format="ditamap")
        self._remove_empty_headings()
        return self._root

    def write(self, path):
        with open(path, "w") as f:
            f.write(xml_decl()+"\n")
            f.write(etree.tostring(self.getmap()))
            
    def _remove_empty_headings(self):
        new_root = copy.deepcopy(self._root)
        empty_nodes = True
        nodes_removed = 0
        while empty_nodes:
            nodes_removed = 0
            for parent, newparent in zip(self._root.getiterator(), new_root.getiterator()):
                for child, newchild in zip(parent, newparent):
                    if len(list(child)) == 0 and not 'href' in child.attrib:
                        newparent.remove(newchild)
                        nodes_removed += 1
            self._root = copy.deepcopy(new_root)
            if nodes_removed == 0:
                empty_nodes = False
        self._root = new_root  


################################################################
# Unit test code
################################################################
import unittest
from _shared import StubSysdef


def mock_component_map_lookup(mapname, rel_dir):
    return True


class TestTopLevelMapCreator(unittest.TestCase):
    def setUp(self):
        self.mc = TopLevelMapCreator(StubSysdef(), ".", mock_component_map_lookup)
        
    def test_i_create_a_map_root_from_a_system_definition(self):                
        root = self.mc.getmap()
        self.assertTrue(root.tag == "map")
        self.assertTrue(root.attrib['title'] == "Symbian^3")
        self.assertTrue(root.attrib['id'] == "Symbian^3")

    def test_i_create_correct_topicheads_from_layers(self):
        root = self.mc.getmap()
        self.assertEquals(len(root.findall("topichead")), 1)
        os_elem = root.findall("topichead")[0]
        self.assertEqual(os_elem.attrib["navtitle"], "OS")
        self.assertEqual(os_elem.attrib["id"], "os")

    def test_i_create_correct_topicheads_from_packages(self):
        root = self.mc.getmap()
        os_elem = root.findall("topichead")[0]
        self.assertEquals(len(os_elem.findall("topichead")), 1)
        pkg_elem = os_elem.findall("topichead")[0]        
        self.assertEqual(pkg_elem.attrib["navtitle"], "Kernel and Hardware Services")
        self.assertEqual(pkg_elem.attrib["id"], "kernelhwsrv")

    def test_i_create_correct_topicheads_from_collections(self):
        root = self.mc.getmap()
        os_elem = root.findall("topichead")[0]
        pkg_elem = os_elem.findall("topichead")[0]
        self.assertEquals(len(pkg_elem.findall("topichead")), 1)
        bootldr_elem = pkg_elem.findall("topichead")[0]
        self.assertEqual(bootldr_elem.attrib["navtitle"], "Board Boot Loader")
        self.assertEqual(bootldr_elem.attrib["id"], "brdbootldr")

    def test_i_create_correct_topicheads_for_components(self):
        root = self.mc.getmap()
        os_elem = root.findall("topichead")[0]
        pkg_elem = os_elem.findall("topichead")[0]
        com_elem = pkg_elem.findall("topichead")[0]
        comp_elem_header = com_elem.findall("topichead")[0]        
        self.assertEqual(comp_elem_header.attrib["navtitle"], "Boot Loader")
        self.assertEqual(comp_elem_header.attrib["id"], "ubootldr")

    def test_i_create_correct_topicrefs_from_components(self):
        root = self.mc.getmap()
        os_elem = root.findall("topichead")[0]
        pkg_elem = os_elem.findall("topichead")[0]
        comp_elem = pkg_elem.findall("topichead")[0]
        comp_elem_header = comp_elem.findall("topichead")[0]
        self.assertEquals(len(comp_elem_header.findall("topicref")), 1)
        ubootldr_elem = comp_elem_header.findall("topicref")[0]
        self.assertEqual(ubootldr_elem.attrib["navtitle"], "Boot Loader")
        self.assertEqual(ubootldr_elem.attrib["href"], "cmp_ubootldr.ditamap")
        self.assertEqual(ubootldr_elem.attrib["format"], "ditamap")

    def test_i_can_remove_empty_headings_from_a_top_level_map(self):
        self.mc._root = etree.fromstring(empty_headings_toc)
        self.mc._remove_empty_headings()
        self.assertEquals(etree.tostring(self.mc._root), removed_empty_headings_toc)

    def test_i_sort_the_map(self):
        root = self.mc.getmap()
        os_elem = root.findall("topichead")[0]
        pkg_elem = os_elem.findall("topichead")[0]
        com_elem = pkg_elem.findall("topichead")[0]
        comp_elem_header = com_elem.findall("topichead")[0]        
        self.assertEqual(comp_elem_header.attrib["navtitle"], "Boot Loader")
        comp_elem_header = com_elem.findall("topichead")[1]        
        self.assertEqual(comp_elem_header.attrib["navtitle"], "Kernel Architecture")


empty_headings_toc = """\
<map id="Symbian^3" title="Symbian^3">
  <topichead id="os" navtitle="OS" >
    <topichead id="kernelhwsrv" navtitle="Kernel and Hardware Services">
      <topichead id="brdbootldr" navtitle="Board Boot Loader">
        <topichead id="ubootldr" navtitle="Boot Loader"/>
      </topichead>
      <topichead id="bsptemplate" navtitle="Board Support Package Template">
        <topichead id="asspandvariant" navtitle="Template ASSP and Variant">
          <topicref format="ditamap" href="cmp_template_variant.ditamap" navtitle="template_variant" />
        </topichead>
      </topichead>      
    </topichead>
  </topichead>
</map>"""


removed_empty_headings_toc = """\
<map id="Symbian^3" title="Symbian^3">
  <topichead id="os" navtitle="OS">
    <topichead id="kernelhwsrv" navtitle="Kernel and Hardware Services">
      <topichead id="bsptemplate" navtitle="Board Support Package Template">
        <topichead id="asspandvariant" navtitle="Template ASSP and Variant">
          <topicref format="ditamap" href="cmp_template_variant.ditamap" navtitle="template_variant" />
        </topichead>
      </topichead>      
    </topichead>
  </topichead>
</map>""" 