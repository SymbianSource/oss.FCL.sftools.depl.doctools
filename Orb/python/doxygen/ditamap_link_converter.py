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
from __future__ import with_statement
import unittest
import os
import shutil
import sys
import xml
import logging
from cStringIO import StringIO
from xml.etree import ElementTree as etree


class DitamapLinkConverterError(Exception):
    """ Raised if an invalid toc is input """

class DitamapLinkConverter():
    
    def __init__(self,out_dir, toc_path):
        self.out_dir = os.path.abspath(out_dir)
        self.toc_path = os.path.abspath(toc_path)
        self.toc_dir = os.path.dirname(self.toc_path)
        if not os.path.exists(self.out_dir):
            os.mkdir(self.out_dir)
            
    def _convert_link_to_html(self, link):
        if link.attrib["href"].endswith(".xml"):
            link.attrib["href"] = link.attrib["href"].replace(".xml", ".html")
            link.attrib["scope"] = "peer"
        return link
    
    def _convert_links(self, tree):
        for element in tree.getiterator():
            if element.attrib.get("href") != None:
                element = self._convert_link_to_html(element)
        return tree
    
    def _handle_map(self, ditamap):
        try:
            root = etree.parse(ditamap).getroot()
        except xml.parsers.expat.ExpatError, e:
            logging.error("%s could not be parsed: %s\n" % (ditamap, str(e)))
            return
        except IOError, e:
            logging.error("Component map \"%s\" does not exist" % ditamap)
            return
        root = self._convert_links(root)
        self._write_file(root, os.path.basename(ditamap))

    def _write_file(self, root, file_name):
        filepath = self.out_dir+os.sep+file_name
        logging.debug('Writing file \"%s\"' % filepath)
        
        if root is not None:
            with open(filepath, 'w') as f:
                f.write("""<?xml version="1.0" encoding="UTF-8"?>"""+'\n')
                f.write("""<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >"""+'\n')
                f.write(etree.tostring(root))        
                f.close()
    
    def _get_component_map_paths(self, tree):
        all_hrefs = []
        for element in tree.getiterator():
            if element.tag == "topicref":
                all_hrefs.append(self.toc_dir+os.sep+element.attrib["href"])
        return all_hrefs
    
    def convert(self):
        try:
            tree = etree.parse(self.toc_path).getroot()
        except xml.parsers.expat.ExpatError, e:
            raise DitamapLinkConverterError("%s could not be parsed: %s\n" % (self.toc_path, str(e)))
        component_maps = self._get_component_map_paths(tree)
        for component_map in component_maps:
            self._handle_map(component_map)
        shutil.copyfile(self.toc_path, self.out_dir+os.sep+os.path.basename(self.toc_path))
        

class TestDitamapLinkConverter(unittest.TestCase):
    def setUp(self):
        self._create_test_dir()
        self.dlc = DitamapLinkConverter(self.out_dir, '')
        
    def tearDown(self):
        self._clean_test_dir()
        
    def _create_test_dir(self):
        self.test_dir = "ditamap_link_converter_test_dir"
        self.out_dir = self.test_dir+os.sep+"out"
        self.cmap_path = self.test_dir+os.sep+"cmap.xml"
        os.mkdir(self.test_dir)
        f = open(self.cmap_path, "w")
        f.write(cmap)
        f.close()
        
    def _clean_test_dir(self):
        shutil.rmtree(self.test_dir)        
        
    def _write_string_to_file(self, string, filepath):
        f = open(filepath, "w")
        f.write(string)
        f.close()        
    
    def test_i_can_change_a_link_to_an_xml_file_to_link_to_an_html_file(self):
        link = etree.Element("cxxStructRef", href="GUID-AE25CF37-B862-306B-B7B3-4A1226B83DA2.xml", navtitle="_SChannels")
        link = self.dlc._convert_link_to_html(link)
        self.assertEquals(link.attrib["href"], "GUID-AE25CF37-B862-306B-B7B3-4A1226B83DA2.html")
        self.assertTrue(link.get("scope", None) and link.attrib["scope"] == "peer")
        
    def test_i_can_find_all_link_elements_in_a_tree(self):
        tree = etree.parse(StringIO(cmap))
        tree = self.dlc._convert_links(tree)
        self.assertTrue(tree.find("cxxStructRef").attrib["href"].endswith(".html"))
        self.assertTrue(tree.find("cxxFileRef").attrib["href"].endswith(".html"))
        self.assertTrue(tree.find("cxxClassRef").attrib["href"].endswith(".html"))
        
    def test_i_can_write_a_converted_map_to_an_output_directory(self):
        self.dlc._handle_map(self.cmap_path)
        self.assertTrue(os.path.exists(self.out_dir+os.sep+"cmap.xml"))
        self.assertEquals(open(self.out_dir+os.sep+"cmap.xml").read(), converted_cmap)
        
    def test_i_gracefully_handle_a_link_to_component_map_that_doesnt_exist(self):
        try:
            self.dlc._handle_map("non_existsant_ditamap.ditamap")
        except:
            self.fail("Didn't handle a component ditamap that doesn't exist")
        else:
            pass # Expected (silently handled non existant map)
        
    def test_i_parse_all_hrefs_in_a_toc(self):
        converter = DitamapLinkConverter(self.out_dir, os.getcwd()+os.sep+'toc.ditamap')
        tree = etree.parse(StringIO(toc))
        paths = converter._get_component_map_paths(tree)
        expected = [os.getcwd()+os.sep+"GUID-F59DFBA0-B60B-334A-9B18-4B4E1E756DFA.ditamap"]       
        self.assertEquals(paths, expected)
        
    def test_i_raise_an_exception_if_i_am_given_an_invalid_toc(self):        
        invalid_toc_path = self.test_dir+os.sep+"invalid_toc.xml"
        self._write_string_to_file(invalid_toc, invalid_toc_path)
        dlc = DitamapLinkConverter(self.out_dir, invalid_toc_path)
        self.assertRaises(DitamapLinkConverterError, dlc.convert)
           
cmap = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="GUID-0D9E5D45-5A07-302C-BEB3-2D0252214F2E" title="wlmplatform">
    <cxxStructRef href="GUID-AE25CF37-B862-306B-B7B3-4A1226B83DA2.xml" navtitle="_SChannels" />
    <cxxFileRef href="GUID-E1984316-685F-394E-B71A-9816E1495C1F.xml" navtitle="wlanerrorcodes.h" />
    <cxxClassRef href="GUID-F795E994-BCB6-3040-872A-90F8ADFC75E7.xml" navtitle="MWlanMgmtNotifications" />
</cxxAPIMap>
"""
                        # 
converted_cmap = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="GUID-0D9E5D45-5A07-302C-BEB3-2D0252214F2E" title="wlmplatform">
    <cxxStructRef href="GUID-AE25CF37-B862-306B-B7B3-4A1226B83DA2.html" navtitle="_SChannels" scope="peer" />
    <cxxFileRef href="GUID-E1984316-685F-394E-B71A-9816E1495C1F.html" navtitle="wlanerrorcodes.h" scope="peer" />
    <cxxClassRef href="GUID-F795E994-BCB6-3040-872A-90F8ADFC75E7.html" navtitle="MWlanMgmtNotifications" scope="peer" />
</cxxAPIMap>"""

        
toc = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">
<map id="GUID-445218BA-A6BF-334B-9337-5DCBD993AEB3" title="Symbian^3">
    <topichead id="GUID-6B11027F-F9AF-3FA0-8A9D-8EA68E3D0F8D" navtitle="Applications">
        <topichead id="GUID-4766FA96-56F3-3E37-9B2C-6F280673BBA1" navtitle="Camera Apps">
          <topichead id="GUID-34AB7AC3-E64C-39E0-B6B1-53FEF84566F2" navtitle="s60">
            <topichead id="GUID-4766FA96-56F3-3E37-9B2C-6F280673BBA1" navtitle="camera">
              <topicref format="ditamap" href="GUID-F59DFBA0-B60B-334A-9B18-4B4E1E756DFA.ditamap" navtitle="camera" />
            </topichead>
            <topichead id="GUID-A0EFE059-67DA-372B-AB98-9DB79584972E" navtitle="camera_help" />
          </topichead>
        </topichead>
     </topichead>
 </map>
 """
 
invalid_toc = """<?xml version="1.0" encoding="UTF-8"?
<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">
<map id="GUID-445218BA-A6BF-334B-9337-5DCBD993AEB3" title="Symbian^3">
    <topichead id="GUID-6B11027F-F9AF-3FA0-8A9D-8EA68E3D0F8D" navtitle="Applications">
        <topichead id="GUID-4766FA96-56F3-3E37-9B2C-6F280673BBA1" navtitle="Camera Apps">
          <topichead id="GUID-34AB7AC3-E64C-39E0-B6B1-53FEF84566F2" navtitle="s60">
            <topichead id="GUID-4766FA96-56F3-3E37-9B2C-6F280673BBA1" navtitle="camera">
              <topicref format="ditamap" href="GUID-F59DFBA0-B60B-334A-9B18-4B4E1E756DFA.ditamap" navtitle="camera" />
            </topichead>
            <topichead id="GUID-A0EFE059-67DA-372B-AB98-9DB79584972E" navtitle="camera_help" />
          </topichead>
        </topichead>
     </topichead>
 </map>
 """      
