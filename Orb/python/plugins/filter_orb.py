
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
import sys
import re
import filter_interface
import xml
import logging
import itertools
import shutil
import copy
import weakref
from xml.etree import ElementTree as etree
from cStringIO import StringIO
from copy import deepcopy
from os.path import abspath, join, exists
from orb.lib import xml_decl, doctype_identifier
from orb import guidiser, filerenamer


class Configuration(object):
    publishing_target = "ditaot"
    sdk = False
    
    def parse(self, config):
        if "sdk" in config:
            self.sdk = True
        if "mode" in config:
            self.publishing_target = "mode"


class LogLineParser(object):
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
    def __init__(self):
        self.store = False
        self.exports = {}
        self._buffer = []

    def parse(self, text):
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
        except xml.parsers.expat.ExpatError, e:
            logging.error("%s could not be parsed: %s\n" % (xmlfile, str(e)))
            return None
        bldinf = root.attrib["bldinf"]
        self.exports[bldinf] = set()
        for child in [c for c in root.getiterator() if c.tag == "export"]:
            self.exports[bldinf].add(
                (child.attrib["destination"], child.attrib["source"])
            )


class FilterOrb(filter_interface.Filter):
    def __init__(self):
        self.configuration = Configuration()
        self.line_parser = LogLineParser()
        self.whatparser = WhatLogParser()        

    def open(self, build_parameters):
        self.epocroot = build_parameters.epocroot
        return True

    def write(self, text):
        "process some log text"
        text = text.strip()
        if text.startswith("<whatlog") or self.whatparser.store:
            self.whatparser.parse(text)
        elif text.startswith("<info>"):
            self.line_parser.parse(text)
        return True

    def _write_maps(self, build_dir, rel_dir):
        sysdef = SystemDefintion(self.line_parser.systemdefinition, self.line_parser.cwd)
        component_mapcreator = ComponentMapCreator(
            PackageLevelMapCreator(sysdef, build_dir), 
            HrefLoader(rel_dir), 
            rel_dir, 
            BldInfToExportsMap(self.whatparser.exports),
            self.line_parser.sdk
        )
        component_mapcreator.write_component_level_maps()
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
        self._write_maps(build_dir, rel_dir)
        self._run_postprocessing(rel_dir)
        return True

    def close(self):
        return True


class BldInfToExportsMap(object):
    def __init__(self, bld_inf_to_export_dict):
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

        
class ComponentMapCreator(object):
    def __init__(self, package_level_map, href_loader, output_dir, exports_map, sdk_build=False):
        self.package_level_map = package_level_map
        self.href_loader = href_loader
        self.output_dir = output_dir
        self.exportsmap = exports_map
        self.sdk_build = sdk_build
        self.sysdef = self.package_level_map.sysdef
        
    def write_component_level_maps(self):        
        for package in self.sysdef.get_packages():
            plm = self.package_level_map.get_package_level_map(package.id)
            for component in self.sysdef.get_components(package.id):
                new_map = self.get_component_level_map(component, plm)
                self._write(new_map)

    def get_component_level_map(self, component, plm):
        """
        for each component in this package get all bld inf files (SystemDefinition)
        generate filtered list:for each bld inf get h files exported from that bld inf from sbs log (BldInfToExportsMap)
        for each href in the package level map (PackageLevelMapCreator)
        get what h file that xml was defined from (hrefloader)
        if this h file is in the filtered list leave it in if not delete it.        
        """
        logging.debug("getting component level map for component: %s"%component.id)        
        bld_infs = self.package_level_map.sysdef.get_bldinfs(component.id)
        logging.debug("I got these bld infs from system definition: %s"%( str(bld_infs) ))
        export_headers = self.get_export_headers(bld_infs)
        new_map = self.get_new_map(export_headers, plm, component)
        return new_map
            
    def get_export_headers(self, bld_infs):
        export_headers = set()
        for bld_inf in bld_infs:
            component_exports = self.exportsmap.get_exports(bld_inf)
            if component_exports != None:
                export_headers = export_headers.union(component_exports)
        logging.debug("I got these export headers from the log: %s"%( str(export_headers) ))            
        return export_headers
    
    def _getelementinfo(self, element):
        return '\"%s\" '%element.tag+' '.join(['%s=\"%s\"'%(k, v) for k, v in element.items()])
        
    def get_new_map(self, export_headers, plm, component):
        child_to_parent = {}
        newroot = deepcopy(plm)        
        for parent in newroot.getiterator():
            for child in parent:
                child_to_parent[child] = parent
        for elem, newelem in zip(plm.getiterator(), newroot.getiterator()):
            href = elem.get('href')
            if href == None:
                continue
            declfile = self.href_loader.get(href)
            logging.debug( "For href %s href loader returned %s" % (href, declfile) )
            logging.debug('Processing element %s, declared in \"%s\"' % ( self._getelementinfo(elem), declfile))
            export_header_basenames = [os.path.basename(a[0]) for a in export_headers]
            export_headers_fullnames = [a[0] for a in export_headers]
            declfile_export_path = None
            for basename, fullpath in zip(export_header_basenames, export_headers_fullnames):
                if basename == os.path.basename(declfile):
                    declfile_export_path = fullpath
            if not declfile_export_path:   # File was not exported so filter it out
                logging.debug('Filtering out of map \"%s\" element %s,  as its definition file \"%s\" was not exported in the sbs log file'
                              % (plm.get("id"), self._getelementinfo(elem), declfile))
                parent = child_to_parent[newelem]
                parent.remove(newelem)
                continue
            if self.sdk_build and not self.exportsmap.is_public(declfile_export_path):
                logging.debug('Filtering out map element %s, as its definition file \"%s\" was not exported as public in log file exports. \
                Log file entry was \"%s\"' % (self._getelementinfo(elem), declfile, declfile_export_path))                  
                parent = child_to_parent[newelem]
                parent.remove(newelem)
                continue
            logging.debug("Kept %s %s %s was not filtered out"%(self._getelementinfo(elem), declfile, declfile_export_path))
        newroot.attrib["id"] = "cmp_" + component.id
        newroot.attrib["title"] = component.name 
        return newroot                
        
    def _write(self, map):
        if len(map.getchildren()) == 0:
            logging.info("Not writing out component map for component '%s' as map was empty" % map.get("id"))
            return
        map_path = join(self.output_dir, map.get("id")+".ditamap")
        try:
            with open(map_path, "w") as f:
                f.write(xml_decl()+"\n")
                f.write(doctype_identifier("cxxAPIMap")+"\n")
                f.write(etree.tostring(map))
        except Exception, e:
            logging.error("Unable to write component map '%s'" % map.get("id"))

        
class SystemDefinitionParserException(Exception):
    "Raised if a System defintion file is invalid"


"""
When move to 2.6
try:
    from collections import namedtuple

    Layer = namedtuple('Layer', 'id name packages')
    Package = namedtuple('Package', 'id name collections')
    Collection = namedtuple('Collection', 'id name components')    
    Component = namedtuple('Component', 'id name bldinfs')    
except ImportError, e:
"""
class Layer(object):
    def __init__(self, id, name, packages):
        self.id = id
        self.name = name
        self.packages = packages

class Package(object):
    def __init__(self, id, name, collections):
        self.id = id
        self.name = name
        self.collections = collections


class Collection(object):
    def __init__(self, id, name, components):
        self.id = id
        self.name = name
        self.components = components


class Component(object):
    def __init__(self, id, name, bldinfs):
        self.id = id
        self.name = name
        self.bldinfs = bldinfs


class PackageDefinionNotFoundError(Exception):
    "Raised if a package definition file could not be found"


class PackageDefinitionLoader(object):
    def __init__(self, sysdefpath, path=os.path):
        self.sysdefpath = ""
        if not hasattr(sysdefpath, "read"):
            self.sysdefpath = path.abspath(path.dirname(sysdefpath))
        self.path = path
    
    def _get_pkgdef_path(self, pkgpath):
        return self.path.abspath(self.path.join(self.sysdefpath, pkgpath))
    
    def load(self, pkgpath):
        if hasattr(pkgpath, "read"):
            return pkgpath
        fullpkgpath = self._get_pkgdef_path(pkgpath)
        if not self.path.exists(fullpkgpath):
            raise PackageDefinionNotFoundError(
             '''Package definition "%s" was not found. 
                System definition directory is: "%s".
                Relative path in System definition was "%s"''' % (fullpkgpath, self.sysdefpath, pkgpath))
        return fullpkgpath


class SystemDefinitionParser(object):
    """
    NOTE: Variable names and comments use System definition 3 terminology
    
    Creates an ElementTree from a System definition file and creates
    a parser (depending on the schema version) and stores the packages
    and components mentioned in the file.
    """
    def __init__(self, sysdeffile, pkgloader=PackageDefinitionLoader):
        self.parser = None
        try:        
            tree = etree.parse(sysdeffile)
        except xml.parsers.expat.ExpatError, e:
            raise SystemDefinitionParserException(str(e))
        root = tree.getroot()
        if "schema" not in root.attrib:
            raise SystemDefinitionParserException("Unknown XML file found, root node does not have a schema attribute")
        schema = root.attrib["schema"]
        if schema.startswith("2.0"):
            logging.debug("Creating a version 2 system definition parser, schema was: " + schema)
            self._parser = SystemDefinitionV2Parser(sysdeffile, pkgloader, tree)
        elif schema.startswith("3.0"):
            logging.debug("Creating a version 3 system definition parser, schema was: " + schema)
            self._parser = SystemDefinitionV3Parser(sysdeffile, pkgloader, tree)
        else:
            raise SystemDefinitionParserException("Unsupported system definition scheme: '%s'" % schema)
        self._parser.parse()

    def __getattr__(self, name):
        return getattr(self._parser, name)


class SystemDefinitionParserBase(object):
    "Base class inherited by System definition parsers"
    # Default to version 3 values
    _id = "id"
    _name = "name"
    _layer = "layer"
    _pkgname = "package"
    _collection = "collection"
    _component = "component"    

    def __init__(self, sysdefpath, pkgloader, tree):
        self._pkgloader = pkgloader(sysdefpath)
        self._tree = tree
        self.__name = ""
        self.layers = []
        # Dict of id -> weakrefs to cut down on searches
        self._components = {}
        self._packages = {}

    @property
    def name(self):
        if self.__name != "":
            return self.__name
        root = self._tree.getroot()
        if "name" in root.attrib:
            self.__name = root.attrib["name"]
        else:
            sysmodel = root.find("systemModel")
            if "name" in sysmodel.attrib:
                self.__name =  sysmodel.attrib["name"]
        return self.__name

    def _load_distributed_pkg(self, href):
        try:              
            return etree.parse(self._pkgloader.load(href)).find("//" + self._pkgname)                    
        except PackageDefinionNotFoundError, e:
            logging.error("Package definition not found: %s" % str(e))
            return None     
    
    def _get_bldfile_prefix(self, href):
        bldFile_prefix = ""
        for p in href.split(".."):
            if p != "/":
                bldFile_prefix = p.replace("package_definition.xml", "")                           
        return bldFile_prefix

    def _get_name_and_id(self, item):
        id = item.attrib[self._id] if self._id in item.attrib else ""
        name = item.attrib[self._name] if self._name in item.attrib else id        
        return (id, name)

    def _get_bldinfs(self, component, bldFile_prefix):
        bldinfs = []
        for unit in [unit for unit in component.findall("unit") if "bldFile" in unit.attrib]:
            bldinfs.append(bldFile_prefix + unit.attrib["bldFile"])
            logging.debug("Found bldFile: %s" % unit.attrib["bldFile"])        
        return bldinfs
            
    def _get_components(self, pkgel, bldFile_prefix):
        components = []
        for component in pkgel.findall(self._component):
            id, name = self._get_name_and_id(component)
            logging.debug("Adding component to components list: %s" % id)
            c = Component(
                id = id,
                name = name,
                bldinfs = self._get_bldinfs(component, bldFile_prefix)  
            )
            components.append(c)
            self._components[c.id] = weakref.ref(c)
        return components

    def _get_collections(self, parent, bldFile_prefix):
        collections = []
        for coll in parent.findall(self._collection):
            id, name = self._get_name_and_id(coll)
            logging.debug("Adding collection to collections list: %s" % id)
            collections.append(Collection(
                id = id,
                name = name,
                components = self._get_components(coll, bldFile_prefix)
            ))
        return collections

    def _get_packages(self, parent):
        packages = []
        bldFile_prefix = ""
        for pkg in parent.findall(self._pkgname):
            if "href" in pkg.attrib:
                href = pkg.attrib["href"]
                pkg = self._load_distributed_pkg(href)
                bldFile_prefix = self._get_bldfile_prefix(href)
            if pkg is not None:                   
                logging.debug("Adding package to packages list: %s" % pkg.attrib[self._id])
                id, name = self._get_name_and_id(pkg)
                p = Package(
                    id = id,
                    name = name,
                    collections = self._get_collections(pkg, bldFile_prefix)
                )
                packages.append(p)
                self._packages[p.id] = weakref.ref(p)
        return packages
    
    def parse(self):
        """
        Parses a system definition file and builds a hierarchical list of objects.
        Hierarchy is:
        Layer
         +- Package
             +- Collection
                 +- Component
        So a Layer contains information about itself and a list of Packages. A
        Package contains infromation about itself and a list of collections, etc.
        
        Supports both distributed and non-distributed sysdef 3 files. (Also supports
        distributed sysdef 2 files for coding simplicity, not sure if they ever existed).
        """
        for layer in self._tree.findall("//" + self._layer):
            id, name = self._get_name_and_id(layer)
            self.layers.append(Layer(
                id = id, 
                name = name, 
                packages = self._get_packages(layer)
            ))


class SystemDefinitionV2Parser(SystemDefinitionParserBase):
    "Changes required to get base class to support sysdef 2"
    _id = "name"
    _name = "long-name"
    _pkgname = "block"


class SystemDefinitionV3Parser(SystemDefinitionParserBase):
    "Base class covers sysdef 3 support by default"


class SystemDefintion(object):
    """
    Used to represent a System Definition file. Presents a queryable
    interface to clients. Uses a SystemDefinitionParser to query the
    underlying system definition XML file.
    """
    def __init__(self, sysdeffile, cwd="", sysdefparser=SystemDefinitionParser, pkgloader=PackageDefinitionLoader):
        self._parser = sysdefparser(sysdeffile, pkgloader)
        self.cwd = cwd.replace("\\", "/")
        if self.cwd.endswith("/"):
            self.cwd = self.cwd[:-1]
        self._pkgs = None

    @property
    def name(self):
        return self._parser.name

    @property
    def layers(self):
        return self._parser.layers

    def get_packages(self):
        """
        Returns the list of Package objects found in the System definition
        file
        """
        return [p() for p in self._parser._packages.values()]            

    def get_components(self, package_id):
        """
        Returns the list of Component objects found in the Package in
        the System definition file
        """
        comps = []
        try:
            for collection in self._parser._packages[package_id]().collections:
                comps.extend(collection.components)
        except KeyError:
            logging.error("Package with package_id: %s, was not found" % package_id)
        return comps

    def _get_component(self, component_id):
        try:
            return self._parser._components[component_id]()
        except KeyError:
            return None

    def get_sbs_output_dir(self, component_id):
        """
        Returns the list of "sbs output directories" found under the
        Component in the System definition file.
        
        An "sbs output directory" is the directory name used by sbs 
        when creating its output directories.
        If the bld.inf file is in a directory called "group", it is 
        the parent directory of the group directory.
        If the bld.inf file is not in a directory called group, it is
        the name of the directory that contains the bld.inf file. 
        """        
        component = self._get_component(component_id)
        if component is None:
            logging.error("Component with an id of: %s, was not found" % component_id)
            return None
        if len(component.bldinfs) == 0:
            logging.info('No bldFiles found for: %s' % component_id)
            return None
        # Otherwise take the first one?
        bldinf = component.bldinfs[0]
        search = re.search(r".*/(.*)/group", bldinf, re.IGNORECASE)
        if not search:
            search = re.search(r".*/(.*)", bldinf)
            if not search:
                logging.error('Could not determine bldFile dir name from unit bldFile attribute: "%s"' % bldinf)
                return ""
        return search.group(1)

    def get_bldinfs(self, component_id):
        """
        Returns the list of "bld.inf" files found in the Component in
        the System definition file
        """         
        bldfiles = []
        component = self._get_component(component_id)
        if component is None:
            logging.error("Component with id: '%s' not found" % component_id)
        else:
            for bf in component.bldinfs:
                logging.debug("Found bldFile (or directory): %s" % bf)
                if not bf.endswith("bld.inf"):
                    bf = "%s/%s" % (bf, "bld.inf")
                if bf.startswith("/"):
                    bf = bf[1:]
                bf = "%s/%s" % (self.cwd, bf)
                logging.debug("Saving bldFile as: %s" % bf)
                bldfiles.append(bf)
        return bldfiles


def component_map_lookup(rel_dir, mapname):
    exists = os.path.exists(os.path.join(rel_dir, mapname))
    if not exists:
        logging.debug("Asked for a component map for '%s' but it does not exist" % mapname)
    return exists


class TopLevelMapCreator(object):
    def __init__(self, sysdef, rel_dir, lookupmethod=component_map_lookup):
        self.sysdef = sysdef
        self._rel_dir = rel_dir
        self._lookup = lookupmethod
        self._root = etree.Element("map", title=sysdef.name, id=sysdef.name)

    def _add_subelems(self, parent, item):
        return etree.SubElement(parent, "topichead", navtitle=item.name, id=item.id)
        
    def getmap(self):
        for layer in self.sysdef.layers:
            layer_elem = self._add_subelems(self._root, layer)
            for package in layer.packages:
                pkg_elem = self._add_subelems(layer_elem, package)
                for collection in package.collections:
                    col_elem = self._add_subelems(pkg_elem, collection)
                    for item in collection.components:                        
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


class PackageLevelMapCreator(object):
    
    def __init__(self, sysdef, build_dir):
        self.sysdef = sysdef
        self.build_dir = build_dir
        
    def _get_map_root(self, id):
        return etree.Element("cxxAPIMap", title=id, id=id)

    def _get_targetmap_paths_for_component(self, component_id):
        sbs_out_dir = self.sysdef.get_sbs_output_dir(component_id)
        if sbs_out_dir is None or sbs_out_dir == "":
            return [] 
        sbs_output_dir = os.path.abspath(self.build_dir + os.sep + sbs_out_dir)
        if sbs_output_dir is None:
            logging.warning("No known build output directory for component '%s', no target maps discovered"%
                            component_id)
            return []
        if not os.path.exists(sbs_output_dir):
            logging.warning("Build output directory '%s' for component '%s' does not exist, no target maps discovered"%
                            (sbs_output_dir, component_id))
            return []
        targetmaps = []
        for root, dirs, files in os.walk(sbs_output_dir):
            for filename in (filename for filename in files if filename.lower().endswith(".ditamap")):
                targetmaps.append(os.path.join(root, filename))
        return targetmaps
        
    def _get_targetmap(self, ditamap):
        try:
            root = etree.parse(ditamap).getroot()
        except xml.parsers.expat.ExpatError, e:
            logging.error("Could not parse ditamap: %s, error was: %s " % (ditamap, e))
            return None
        else:
            return root
    
    def _get_componentmap(self, component_id):
        root = self._get_map_root(component_id)
        for targetmap_path in self._get_targetmap_paths_for_component(component_id):
            target_map = self._get_targetmap(targetmap_path)
            if target_map:
                for child in target_map.getchildren(): 
                    root.append(child)            
        return root  
    
    def _filter_duplicates(self, element):
        def get_child_to_parent_dict():
            child_to_parent_dict = {}
            for parent in element.getiterator():
                for child in parent:
                    child_to_parent_dict[child] = parent
            return child_to_parent_dict
        
        child_to_parent_dict = get_child_to_parent_dict()
        seen = []
        for child in element.getiterator():
            if child.get("navtitle") in seen:
                parent = child_to_parent_dict[child]
                parent.remove(child)
            else:
                seen.append(child.get("navtitle"))
        return element
            
    def get_package_level_map(self, package_id):    
        """
        Returns an etree map of topics for a package
        """
        root = self._get_map_root(package_id)
        for component in self.sysdef.get_components(package_id):
            for child in self._get_componentmap(component.id).getchildren(): 
                root.append(child)                        
        return self._filter_duplicates(root)        
        
        
class HrefLoader(object):
    """
    Class that parses DITA cxx files and returns the header file an API is declared in.
    
    >>> refloader = HrefLoader(".", parser=EtreeStub()) # Pass in a stub parser for testing
    >>> refloader.get("class_c_always_online_e_com_interface.xml#class_c_always_online_e_com_interface")
    'D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h'
    """
    def __init__(self, filedir, parser=etree):
        self.basedir = filedir
        self.parser = parser
        self.decls = ['cxxClassDeclarationFile', 'cxxTypedefDeclarationFile', 'cxxFunctionDeclarationFile', 'cxxVariableDeclarationFile',]

    def get(self, url):
        filename = url.split('#')[0].split('::')[-1]
        id = url.split('#')[1] if '#' in url else filename
        filepath = os.path.join(self.basedir, filename)      
        try:
            tree = self.parser.parse(filepath)
        except xml.parsers.expat.ExpatError, e:
            logging.error("%s could not be parsed: %s\n" % (filepath, str(e)))
            return ""
        except IOError:
            return ""
        in_correct_element = False
        for el in tree.getiterator():
            if 'id' in el.attrib and el.attrib['id'] == id:
                in_correct_element = True
            if el.tag in self.decls and in_correct_element:
                return el.attrib['value']            
        return ""
        

###################################################################################
## Test code
###################################################################################
import unittest


class PathMock(object):
    "Mock os.path so I can change os.path.exists return values"

    @classmethod
    def abspath(self, p):
        return os.path.abspath(p)
    
    @classmethod
    def dirname(self, p):
        return os.path.dirname(p)

    @classmethod
    def join(self, a, b):
        return os.path.join(a, b)
    
    @classmethod
    def exists(self, p):
        if "data" in p:
            return True
        else:
            return False


class TestPackageDefinitionLoader(unittest.TestCase):
    def setUp(self):
        self.sysdefpath = __file__

    def test_i_can_raise_an_exception_if_i_cannot_load_a_pkg_definition(self):
        pl = PackageDefinitionLoader(self.sysdefpath, path=PathMock)
        try:
            pl.load("package_definition.xml")
            self.fail("Should have raised a PackageDefinionNotFoundError")
        except PackageDefinionNotFoundError:
            pass # Expected

    def test_i_can_load_a_pkg_definition(self):
        pl = PackageDefinitionLoader(self.sysdefpath, path=PathMock)
        try:
            pl.load("data/package_definition.xml")
        except Exception:
            self.fail("PackageLoader.load did not find a file that exists (mocked)")

    def test_if_passed_a_file_like_object_i_just_return_it(self):
        pl = PackageDefinitionLoader(self.sysdefpath, path=PathMock)
        pkgdef = pl.load(StringIO(kernelhwsrv_pkg_def))
        try:
            etree.parse(pkgdef)
        except Exception:
            self.fail("PackageLoader.load did not find a file that exists (mocked)")

    def test_if_passed_a_file_like_object_as_a_sysdef_i_use_it(self):
        try:
            PackageDefinitionLoader(StringIO(sysdefv3_nondistributed))
        except Exception:
            self.fail("PackageLoader did not handle a file-like object as sysdef")


class MockPackageDefinitionLoader(object):
    def __init__(self, sysdefpath):
        pass

    def load(self, pkgpath):
        if "kernelhwsrv" in pkgpath:
            return StringIO(kernelhwsrv_pkg_def)
        elif "classicui" in pkgpath:
            return StringIO(classicui_pkg_def)
        else:
            raise PackageDefinionNotFoundError("File not found")


class TestSystemDefinitionParser(unittest.TestCase):

    def setUp(self):
        self.sysdefs = {
            "System definition V2": sysdefv2,
            "System definition V3 distributed": sysdefv3_distributed,
            "System definition V3 non-distributed": sysdefv3_nondistributed
        }
        self.unsupported_sysdefs = {
            "System definition V1.4": sysdefv1_unsupported,
            "System definition V2.1": sysdefv2_unsupported,
            "System definition V3.1": sysdefv3_unsupported
        }
        
    def test_i_raise_an_exception_if_the_sysdef_file_is_invalid(self):
        try:
            parser = SystemDefinitionParser(StringIO("<boo><foo/>"))
            self.fail("An exception should have been raised")
        except SystemDefinitionParserException, e:
            pass # Expected

    def test_i_raise_an_exception_if_given_an_unkown_xml_file(self):
        try:
            parser = SystemDefinitionParser(StringIO("<SystemDefinition></SystemDefinition>"))
            self.fail("An exception should have been raised")
        except SystemDefinitionParserException, e:
            pass # Expected


    def test_i_raise_an_exception_if_given_an_unsupported_systemdefintion_version(self):
        for name, sysdef in self.unsupported_sysdefs.items():
            try:
                SystemDefinitionParser(StringIO(sysdef))
                self.fail("Should have raised a SystemDefinitionParserException as I do not support %s" % name)
            except SystemDefinitionParserException, e:
                pass # Expected 

    def test_i_can_parse_supported_sysdefs_files(self):
        for name, sysdef in self.sysdefs.items():
            try:
                SystemDefinitionParser(StringIO(sysdef), pkgloader=MockPackageDefinitionLoader)
            except Exception, e:
                self.fail("An exception should not have been raised. Using '%s': %s" % (name, str(e)))

    def test_i_store_all_the_layers_in_a_sysdef_file(self):
        for name, sysdef in self.sysdefs.items():
            parser = SystemDefinitionParser(StringIO(sysdef), pkgloader=MockPackageDefinitionLoader)
            items = len(parser.layers)
            layer = parser.layers[0]
            self.assertEquals(items, 2, msg="Expected number of layers '%s' not stored, using %s" % (items, name))
            self.assertEquals(layer.id, "os", msg="Expected layer id '%s' not stored, using %s" % (parser.layers[0].id, name))
            self.assertEquals(layer.name, "OS", msg="Expected layer name '%s' not stored, using %s" % (parser.layers[0].name, name))

    def test_i_store_all_the_packages_in_a_layer(self):
        for name, sysdef in self.sysdefs.items():
            parser = SystemDefinitionParser(StringIO(sysdef), pkgloader=MockPackageDefinitionLoader)
            items = len(parser.layers[0].packages)             
            self.assertEquals(items, 1, msg="Expected number of packages '%s' not stored, using %s" % (items, name))              
            item = parser.layers[0].packages[0]
            self.assertEquals(item.id, "kernelhwsrv", msg="Expected package id '%s' not stored, using %s" % (item.id, name))
            self.assertEquals(item.name, "Kernel and Hardware Services", msg="Expected package name '%s' not stored, using %s" % (item.name, name))


    def test_i_store_all_the_collections_in_a_package(self):
        for name, sysdef in self.sysdefs.items():
            parser = SystemDefinitionParser(StringIO(sysdef), pkgloader=MockPackageDefinitionLoader)
            items = len(parser.layers[0].packages[0].collections)
            self.assertEquals(items, 12, msg="Expected number of collections '%s' not stored, using %s" % (items, name))              
            item = parser.layers[0].packages[0].collections[0]
            self.assertEquals(item.id, "brdbootldr", msg="Expected collection id '%s' not stored, using %s" % (item.id, name))
            self.assertEquals(item.name, "Board Boot Loader", msg="Expected collection name '%s' not stored, using %s" % (item.name, name))

    def test_i_store_all_the_components_in_a_collection(self):
        for name, sysdef in self.sysdefs.items():
            parser = SystemDefinitionParser(StringIO(sysdef), pkgloader=MockPackageDefinitionLoader)
            items = len(parser.layers[0].packages[0].collections[0].components)
            self.assertEquals(items, 1, msg="Expected number of components '%s' not stored, using %s" % (items, name))              
            item = parser.layers[0].packages[0].collections[0].components[0]
            self.assertEquals(item.id, "ubootldr", msg="Expected component id '%s' not stored, using %s" % (item.id, name))
            self.assertEquals(item.name, "Boot Loader", msg="Expected component name '%s' not stored, using %s" % (item.name, name))

    def test_i_store_all_the_bldinfs_in_a_component(self):
        for name, sysdef in self.sysdefs.items():
            parser = SystemDefinitionParser(StringIO(sysdef), pkgloader=MockPackageDefinitionLoader)
            items = len(parser.layers[0].packages[0].collections[1].components[0].bldinfs)
            self.assertEquals(items, 1, msg="Expected number of bldinfs '%s' not stored, using %s" % (items, name))              

    def test_i_store_a_sysdefs_name(self):
        for name, sysdef in self.sysdefs.items():
            parser = SystemDefinitionParser(StringIO(sysdef), pkgloader=MockPackageDefinitionLoader)
            self.assertEquals(parser.name, "Symbian^3", msg="Expected name not stored. Recieved: '%s', using %s" % (parser.name, name))


class TestSystemDefinition(unittest.TestCase):
    def setUp(self):
        self.sysdefs = {
            "sysdefv2":         SystemDefintion(StringIO(sysdefv2), "y:\\"),
            "sysdefv3_dist":    SystemDefintion(StringIO(sysdefv3_distributed), "y:\\", pkgloader=MockPackageDefinitionLoader),
            "sysdefv3_nondist": SystemDefintion(StringIO(sysdefv3_nondistributed), "y:\\")
        }
        
    def test_i_return_the_list_of_packages(self):
        for name, sysdef in self.sysdefs.items():
            packages = sysdef.get_packages()
            self.assertEquals(len(packages), 2, msg="Correct number of packages were not found, using %s" % name)
            self.assertEquals(packages[0].id, "kernelhwsrv", msg="Incorrect package id found, using %s" % name)
            self.assertEquals(packages[1].id, "classicui", msg="Incorrect package id found, using %s" % name)

    def test_i_can_handle_invalid_href_urls(self):
        sysdefv3 = SystemDefintion(StringIO(sysdefv3_distributed_invalid_href), "y:\\", pkgloader=MockPackageDefinitionLoader)
        try:
            packages = sysdefv3.get_packages()
        except Exception, e:
            self.fail("Should have carried on and not raised an exception. %s" % str(e))
        self.assertEquals(len(packages), 1)

    def test_i_can_handle_being_asked_for_components_given_an_nonexistent_packageid(self):
        for name, sysdef in self.sysdefs.items():
            components = sysdef.get_components("classicgui")
            self.assertEquals(len(components), 0, msg="Incorrect number of components returned, using %s" % name)        

    def test_i_can_return_components_given_a_packageid(self):
        for name, sysdef in self.sysdefs.items():
            components = sysdef.get_components("classicui")
            self.assertEquals(len(components), 34, msg="Incorrect number of components returned, using %s" % name)
            self.assertTrue("pslngsplugin" in [component.id for component in components], msg="Expected component not found, using %s" % name)        

    def test_i_can_handle_being_asked_for_bldinfs_given_a_nonexistant_component_name(self):
        for name, sysdef in self.sysdefs.items():
            bldfiles = sysdef.get_bldinfs("classicgui")
            self.assertEquals(len(bldfiles), 0, msg="Incorrect number of bldfiles returned, using %s" % name)

    def test_i_can_return_bldinfs_given_a_component_name(self):
        for name, sysdef in self.sysdefs.items():
            bldfiles = sysdef.get_bldinfs("pslngsplugin")
            self.assertEquals(len(bldfiles), 1, msg="Incorrect number of bldfiles returned, using %s" % name)
            self.assertTrue(bldfiles[0].endswith("bld.inf"))
            self.assertEquals(bldfiles[0], "y:/mw/classicui/psln/pslngsplugin/Group/bld.inf", msg="%s != %s. using %s" % (bldfiles[0], "y:/mw/classicui/psln/pslngsplugin/group/bld.inf", name))

    def test_i_handle_being_asked_for_sbsdir_when_a_given_component_is_not_found(self):
        for name, sysdef in self.sysdefs.items():
            self.assertEquals(sysdef.get_sbs_output_dir("foobar"), None, msg="Did not handle an invalid component name correctly, using: %s" % name)

    def test_i_handle_being_asked_for_sbsdir_when_a_given_component_has_no_bldinfs(self):
        for name, sysdef in self.sysdefs.items():
            self.assertEquals(sysdef.get_sbs_output_dir("pslnengine"), None, msg="Did not handle an invalid component name correctly, using: %s" % name)

    def test_i_can_return_sbs_output_dir_given_a_component(self):
        for name, sysdef in self.sysdefs.items():
            self.assertEquals(sysdef.get_sbs_output_dir("pslngsplugin"), "pslngsplugin", msg="Expected directory value not returned, using %s" % name)
            outdir = sysdef.get_sbs_output_dir("rofs")
            self.assertEquals(outdir, "srofs", msg="Expected directory value not returned '%s', using %s" % (outdir, name))

    def test_i_can_handle_invalid_bldfile_lines_when_asked_for_a_sbs_output_dir(self):
        for name, sysdef in self.sysdefs.items():
            self.assertEquals(sysdef.get_sbs_output_dir("uiklaf"), "", msg="Expected directory value not returned, using %s" % name)

    def test_i_can_return_a_sysdef_name(self):
        for name, sysdef in self.sysdefs.items():
            self.assertEquals(sysdef.name, "Symbian^3", msg="Expected title value not returned, using %s" % name)
            
            
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


class StubSysdef(object):    
    def __init__(self):
        self.name = "Symbian^3"
        kernelhwsrv_comps = [
            Component(id="ubootldr", name="Boot Loader", bldinfs=[]),
            Component(id="asspandvariant", name="Template ASSP and Variant", bldinfs=[]),
            Component(id="eka", name="Kernel Architecture", bldinfs=[])
        ]
        kernelhwsrv_colls = [
            Collection(id="brdbootldr", name="Board Boot Loader", components=kernelhwsrv_comps),
            Collection(id="dummy", name="Dummy", components=[])
        ]
        os_packages = [
            Package(id="kernelhwsrv", name="Kernel and Hardware Services", collections=kernelhwsrv_colls)
        ]
        mw_packages = [
            Package(id="classicui", name="Classic UI", collections=[])
        ]
        self.layers = [
            Layer(id="os", name="OS", packages=os_packages), 
            Layer(id="mw", name="Middleware", packages=mw_packages)
        ]
    
    def get_packages(self):
        return (
            Package(id="graphics", name="Graphics", 
                    components=(Component("classicui_pub","Classic UI Public Interfaces",["W:/sf/mw/classicui/classicui_pub/group/bld.inf"]),
                                Component("classicui_plat","Classic UI Platform Interfaces",["W:/sf/mw/classicui/classicui_plat/group/bld.inf"]) 
                                )
            ),
            Package(id="classicui", name="Classic UI", 
                    components=(Component("aknglobalui","Avkon Global UI",["W:/sf/mw/classicui/uifw/aknglobalui/group/bld.inf"]),
                                Component("commonui","Common UI",["W:/sf/mw/classicui/commonuis/commonui/group/bld.inf"])
                                )
            )
        )
    
    def get_components(self, package_id):
        component_classicui_pub = Component("classicui_pub","Classic UI Public Interfaces",["W:/sf/mw/classicui/classicui_pub/group/bld.inf"])
        component_classicui_plat = Component("classicui_plat","Classic UI Platform Interfaces",["W:/sf/mw/classicui/classicui_plat/group/bld.inf"])        
        component_aknglobalui = Component("aknglobalui","Avkon Global UI",["W:/sf/mw/classicui/uifw/aknglobalui/group/bld.inf"])
        component_commonui = Component("commonui","Common UI",["W:/sf/mw/classicui/commonuis/commonui/group/bld.inf"])
        
        if package_id == "classicui":
            return [component_classicui_pub, component_classicui_plat, component_aknglobalui, component_commonui]
        if package_id == "graphics":
            return ["commongraphicsheaders"]
        
    def get_sbs_output_dir(self, component_id):
        if component_id == "classicui_pub":   
            return "classicui_pub"
        elif component_id == "classicui_plat": 
            return "classicui_plat"
        elif component_id == "commongraphicsheaders":   
            return "commongraphicsheaders"
        elif component_id == "aknglobalui":
            return "aknglobalui"
        elif component_id == "commonui":
            return "commonui" 
        else:
            raise Exception("component id '%s' is not defined in stub"%component_id)

    def get_bldinfs(self, pacakge_id):
        return ["W:/sf/mw/classicui/classicui_pub/group/bld.inf"]        


        
class StubBldInfExportsMap(object):
    set1 = set([('W:/epoc32/include/platform/graphics/displayconfiguration.h','W:/sf/os/graphics/graphicsutils/commongraphicsheaders/inc/displayconfiguration.h'),
                       ('W:/epoc32/include/platform/graphics/extensioncontainer.h','W:/sf/os/graphics/graphicsutils/commongraphicsheaders/inc/extensioncontainer.h'),
                       ('W:/epoc32/include/mw/foo/not_in_a_this_component.h','W:/sf/mw/foo/not_in_a_this_component.h')])
    set_pub = set([("W:/epoc32/include/mw/aknSoundinfo.h", "W:/sf/mw/classicui/classicui_pub/sounds_api/inc/aknSoundInfo.h"),
			          ("W:/epoc32/include/mw/AiwServiceHandler.h", "W:/sf/mw/classicui/classicui_pub/aiw_service_handler_api/inc/AiwServiceHandler.h"),
                      ('W:/epoc32/include/mw/bar/in_a_this_component.h','W:/sf/mw/bar/in_a_this_component.h')])
    set_plat = set([("W:/epoc32/include/platform/mw/mpslnfwappthemeobserver.h", "W:/sf/mw/classicui/classicui_plat/personalisation_framework_api/inc/MPslnFWAppThemeObserver.h"),
                       ("W:/epoc32/include/platform/mw/pslnfwappthemehandler.h", "W:/sf/mw/classicui/classicui_plat/personalisation_framework_api/inc/PslnFWAppThemeHandler.h")])                     
    set_internal = set([('W:/sf/os/graphics/displayconfiguration.h','W:/sf/os/graphics/displayconfiguration.h'),
                       ('W:/sf/os/graphics/extensioncontainer.h','W:/sf/os/graphics/extensioncontainer.h')])    
    set_all = set1.union(set_pub).union(set_plat).union(set_internal)
    
    def get_exports(self, bld_inf_path):
        if bld_inf_path == "W:/sf/os/graphics/graphicsutils/commongraphicsheaders/group/bld.inf":
            return self.set1
        elif bld_inf_path == "W:/sf/mw/classicui/classicui_pub/group/bld.inf":
			return self.set_pub	
        elif bld_inf_path == "W:/sf/mw/classicui/classicui_plat/group/bld.inf":
            return self.set_plat
        else: 
            return None    
            
    def is_public(self, header):
        if header in ["W:/epoc32/include/mw/aknSoundinfo.h", "W:/epoc32/include/mw/AiwServiceHandler.h", 
                        "W:/epoc32/include/mw/aknSoundinfo.h", "W:/epoc32/include/mw/foo/not_in_a_this_component.h",
                        "W:/epoc32/include/mw/bar/in_a_this_component.h"]:
            return True
        elif header in ["W:/epoc32/include/platform/mw/pslnfwappthemehandler.h", "W:/epoc32/include/platform/graphics/extensioncontainer.h", 
                        "W:/epoc32/include/platform/mw/mpslnfwappthemeobserver.h", "W:/sf/os/graphics/displayconfiguration.h"]:
            return False
        else:
            raise Exception("Header '%s' is not defined in is_public"%str(header)) 
            # % header
        #return not(self.is_platform(header)) and not(self.is_internal(header))    
        
class StubPackageLevelMapCreator(object):
    
    def __init__(self, sysdef, build_dir):
        self.sysdef = sysdef
        self.build_dir = build_dir
    
    def get_package_level_map(self, package_id):
        if package_id == "ClassicUI":
            return etree.fromstring(ditamap_classicui)
        else:
            return etree.fromstring(ditamap)#ditamap is a target level map

    
class TestComponentMapCreator(unittest.TestCase):
    
    def setUp(self):
        plmcreator = StubPackageLevelMapCreator(StubSysdef(),"")
        hrefloader = HrefLoaderStub(".")
        bldinfexportsmap = StubBldInfExportsMap()
        self.cmc = ComponentMapCreator(plmcreator, hrefloader, "", bldinfexportsmap)
        self.test_dir = abspath(join("TestComponentMapCreator_test"))
        self._create_test_dir()
        
    def _create_test_dir(self):
        os.makedirs(self.test_dir)        
        
    def tearDown(self):
        self._clean_test_dir()        
        
    def _clean_test_dir(self):
        shutil.rmtree(self.test_dir)
        
    def test_i_remove_links_to_api_items_not_exported_by_a_component(self):
        hrefloader = HrefLoaderStub(".")
        package = 'inputmethods'
        stub_sysdef = StubSysdef()
        plmcreator = StubPackageLevelMapCreator(StubSysdef(), "")
        plm = plmcreator.get_package_level_map(package)
        clmcreator = ComponentMapCreator(plmcreator, hrefloader, "", StubBldInfExportsMap())
        components = stub_sysdef.get_components("classicui")
        clm = clmcreator.get_component_level_map(components[0], plm)
        self.assertEquals(expected_clm, etree.tostring(clm))
    
    def test_get_new_map_filters_out_pdk_headers_in_an_sdk_build(self):
        hrefloader = HrefLoaderStub(".")
        package = 'inputmethods'
        stub_sysdef = StubSysdef()
        plmcreator = StubPackageLevelMapCreator(StubSysdef(),"")
        plm = plmcreator.get_package_level_map(package)
        clmcreator = ComponentMapCreator(plmcreator,hrefloader, "", StubBldInfExportsMap(), sdk_build=True)
        components = stub_sysdef.get_components("classicui")
        export_headers = StubBldInfExportsMap.set_all
        clm = clmcreator.get_new_map(export_headers, plm, components[0])
        self.assertEquals(expected_sdk_clm, etree.tostring(clm))        
        
    def test_i_can_write_a_component_map_to_the_file_system(self):        
        map = etree.fromstring(expected_clm)
        self.cmc.output_dir = self.test_dir
        self.cmc._write(map)
        map_path = join(self.test_dir, "cmp_classicui_pub.ditamap") # map names should be cmp_ + mapid
        self.assertTrue(exists(map_path))
        content = open(map_path, "r").read()
        self.assertTrue(content.find("<?xml") == 0) # it has a doctype declaration
        self.assertTrue(content.find("<!DOCTYPE cxxAPIMap") != -1) # it has doctype decl
        self.assertTrue(content.find('<cxxAPIMap id="cmp_classicui_pub"') != -1) # it has the map
        
    def test_i_dont_write_out_an_empty_component_map_to_the_file_system(self):        
        map = etree.fromstring(empty_clm)
        self.cmc.output_dir = self.test_dir
        self.cmc._write(map)
        map_path = join(self.test_dir, "cmp_classicui_pub.ditamap") # map names should be cmp_ + mapid
        self.assertFalse(exists(map_path)) # Shouldnt have been written out as map was empty        
        
        
class TestPackageLevelMapCreator(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath("filter_orb_test_dir"+os.sep+"TestPackageLevelMapCreator_test_dir")
        self.build_dir = self.test_dir+os.sep+"build"
        self.plmc = PackageLevelMapCreator(StubSysdef(), self.build_dir)
        self._create_test_dir()
        
    def _create_test_dir(self):
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
        self._clean_test_dir()
        
    def _clean_test_dir(self):
        shutil.rmtree(self.test_dir)        
        
    def _remove_newlines(self, string):
        return string.replace("\n", "")
                   
    def test_i_can_return_targetmap_paths_for_a_component(self):
        targetmaps = self.plmc._get_targetmap_paths_for_component("aknglobalui")
        self.assertEquals(targetmaps, [self.akncapserver_ditamap_path])
                
    def test_i_gracefully_handle_a_badly_formed_target_map(self):
        root = self.plmc._get_targetmap(self.badly_formed_ditamap_path)
        self.assertEquals(root, None)
        
    def test_i_can_return_a_componentmap_for_a_component_id(self):
        component_map = self.plmc._get_componentmap("aknglobalui")
        self.assertEquals(etree.tostring(component_map), aknglobalui)

    def test_i_can_filter_duplicates_from_a_package_level_map(self):
        root = etree.fromstring(classicui_plm_dup)
        self.assertEquals(self._remove_newlines(etree.tostring(self.plmc._filter_duplicates(root))), self._remove_newlines(classicui_plm))
        
    def test_i_can_filter_grandchild_duplicates_from_a_package_level_map(self):
        root = etree.fromstring(classicui_plm_grandchild_dup)
        self.assertEquals(self._remove_newlines(etree.tostring(self.plmc._filter_duplicates(root))), self._remove_newlines(classicui_plm_grandchild))        
                
    def test_i_can_return_a_package_level_map_for_a_package(self):
        plm = self.plmc.get_package_level_map("classicui")
        self.assertEquals(self._remove_newlines(etree.tostring(plm)), self._remove_newlines(classicui_plm))
        

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
        except Exception, e:
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


class EtreeStub(object):    
    def parse(self, file):
        return etree.parse(StringIO(class_c_always_online))


class EtreeStubComponentMap(object):    
    def parse(self, file):
        return etree.parse(StringIO(class_classic_ui))        


class InvalidEtreeStub(object):    
    def parse(self, file):
        return etree.parse(StringIO("<foo><bar"))

        
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


class TestHrefLoader(unittest.TestCase):
    def test_i_return_a_header_when_passed_a_href(self):
        refloader = HrefLoader(".", parser=EtreeStub())
        self.assertTrue("D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h" == 
                        refloader.get("class_c_always_online_e_com_interface.xml#class_c_always_online_e_com_interface"))
            
    def test_i_continue_if_a_file_is_invalid(self):
        try:
            hl = HrefLoader(".", parser=InvalidEtreeStub())
            hl.get("")
        except Exception:
            self.fail("Shouldnt have raised an exception")

    def test_i_return_an_empty_string_when_passed_a_href_that_doesnt_exist(self):
        refloader = HrefLoader(".", parser=EtreeStub())
        self.assertTrue("" == refloader.get("class_c_always_online_e_com_interface.xml#foo_bar"))

    def test_i_return_an_empty_string_when_asked_for_a_file__that_doesnt_exist(self):
        refloader = HrefLoader(".")
        self.assertTrue("" == refloader.get("class_c_always_online_e_com_interface.xml#foo_bar"))


expected_clm = """<cxxAPIMap id="cmp_classicui_pub" title="Classic UI Public Interfaces">
    <cxxStructRef href="struct___array_util.xml#struct___array_util" navtitle="struct___array_util" />
    <cxxClassRef href="class_c_active_scheduler.xml#class_c_active_scheduler" navtitle="class_c_active_scheduler">
        <cxxClassRef href="class_c_active_scheduler_1_1_t_cleanup_bundle.xml#class_c_active_scheduler_1_1_t_cleanup_bundle" navtitle="class_c_active_scheduler_1_1_t_cleanup_bundle" />
    </cxxClassRef>
    <cxxClassRef href="class_c_always_online_e_com_interface.xml#class_c_always_online_e_com_interface" navtitle="class_c_always_online_e_com_interface">
        </cxxClassRef>
    </cxxAPIMap>"""

expected_sdk_clm = """<cxxAPIMap id="cmp_classicui_pub" title="Classic UI Public Interfaces">
    <cxxStructRef href="struct___array_util.xml#struct___array_util" navtitle="struct___array_util" />
    <cxxClassRef href="class_c_active_scheduler.xml#class_c_active_scheduler" navtitle="class_c_active_scheduler">
        <cxxClassRef href="class_c_active_scheduler_1_1_t_cleanup_bundle.xml#class_c_active_scheduler_1_1_t_cleanup_bundle" navtitle="class_c_active_scheduler_1_1_t_cleanup_bundle" />
    </cxxClassRef>
    <cxxClassRef href="class_c_always_online_e_com_interface.xml#class_c_always_online_e_com_interface" navtitle="class_c_always_online_e_com_interface">
        <cxxStructRef href="nested_and_removed.xml" />
    </cxxClassRef>
    </cxxAPIMap>"""

    
empty_clm = """<cxxAPIMap id="cmp_classicui_pub" title="Classic UI Public Interfaces"></cxxAPIMap>"""        


## Package Level Maps
# Package map for classicui package 
classicui_plm = """\
<cxxAPIMap id="classicui" title="classicui">
<cxxClassRef href="class_c_akn_sound_info.xml#class_c_akn_sound_info" navtitle="CAknSoundInfo" />
<cxxClassRef href="class_c_aiw_service_handler.xml#class_c_aiw_service_handler" navtitle="CAiwServiceHandler" />
</cxxAPIMap>"""

# Package map for classicui package 
classicui_plm_grandchild = """\
<cxxAPIMap id="classicui" title="classicui">
<cxxClassRef href="class_c_akn_sound_info.xml#class_c_akn_sound_info" navtitle="CAknSoundInfo" />
<cxxClassRef href="class_c_aiw_service_handler.xml#class_c_aiw_service_handler" navtitle="CAiwServiceHandler">
</cxxClassRef>
</cxxAPIMap>"""

# Package map for classicui package that contains duplicates that need filtering out 
classicui_plm_dup = """\
<cxxAPIMap id="classicui" title="classicui">
<cxxClassRef href="class_c_akn_sound_info.xml#class_c_akn_sound_info" navtitle="CAknSoundInfo" />
<cxxClassRef href="class_c_akn_sound_info.xml#class_c_akn_sound_info" navtitle="CAknSoundInfo" />
<cxxClassRef href="class_c_aiw_service_handler.xml#class_c_aiw_service_handler" navtitle="CAiwServiceHandler" />
</cxxAPIMap>"""

# Package map for classicui package that contains duplicates that need filtering out 
classicui_plm_grandchild_dup = """\
<cxxAPIMap id="classicui" title="classicui">
<cxxClassRef href="class_c_akn_sound_info.xml#class_c_akn_sound_info" navtitle="CAknSoundInfo" />
<cxxClassRef href="class_c_akn_sound_info.xml#class_c_akn_sound_info" navtitle="CAknSoundInfo" />
    <cxxClassRef href="class_c_aiw_service_handler.xml#class_c_aiw_service_handler" navtitle="CAiwServiceHandler">
</cxxClassRef>
</cxxAPIMap>"""

## Component Level Maps

# Component map in classicui package
aknglobalui = """\
<cxxAPIMap id="aknglobalui" title="aknglobalui">\
<cxxClassRef href="class_c_akn_sound_info.xml#class_c_akn_sound_info" navtitle="CAknSoundInfo" />
</cxxAPIMap>"""

# Component map in classicui package
commonui = """\
<cxxAPIMap id="commonui" title="commonui">
<cxxClassRef href="class_c_aiw_service_handler.xml#class_c_aiw_service_handler" navtitle="CAiwServiceHandler" />
</cxxAPIMap>
"""

## Target Level Maps   

# Target map in aknglobalui component 
akncapserver_ditamap = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="akncapserver" title="akncapserver">
    <cxxClassRef href="class_c_akn_sound_info.xml#class_c_akn_sound_info" navtitle="CAknSoundInfo" />
</cxxAPIMap>"""

# Target map in commonui component 
commonui_ditamap = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="CommonUI" title="CommonUI">
    <cxxClassRef href="class_c_aiw_service_handler.xml#class_c_aiw_service_handler" navtitle="CAiwServiceHandler" />
</cxxAPIMap>"""     

# Badly formed 
badly_formed_ditamap = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="BadlyFormed" title="BadlyFormed">
    <cxxClassRef href="class_c_aiw_service_handler.xml#class_c_aiw_service_handler" navtitle="CAiwServiceHandler" />
</cxxAPIMap"""  

example_what = """<whatlog bldinf='C:/hydra/sf/os/commsfw/datacommsserver/esockserver/group/bld.inf' mmp='' config=''><export destination='C:/epoc32/include/comms-infras/ss_esockstates.h' source='C:/hydra/sf/os/commsfw/datacommsserver/esockserver/core_states/ss_esockstates.h'/><export destination='C:/epoc32/include/comms-infras/ss_esockactivities.h' source='C:/hydra/sf/os/commsfw/datacommsserver/esockserver/core_states/ss_esockactivities.h'/></whatlog>"""


example_what_lines = [
    "<whatlog bldinf='C:/hydra/sf/os/commsfw/datacommsserver/esockserver/group/bld.inf' mmp='' config=''>",
    "<export destination='C:/epoc32/include/comms-infras/ss_esockstates.h' source='C:/hydra/sf/os/commsfw/datacommsserver/esockserver/core_states/ss_esockstates.h'/>",
    "<export destination='C:/epoc32/include/comms-infras/ss_esockactivities.h' source='C:/hydra/sf/os/commsfw/datacommsserver/esockserver/core_states/ss_esockactivities.h'/>",
    "</whatlog>"
]


build_info = """<info>sbs: version 2.10.0 [2009-10-05 sf release]
</info>
<info>SBS_HOME C:/APPS/sbs</info>
<info>Set-up C:/APPS/sbs/sbs_init.xml</info>
<info>Command-line-arguments -c doxygen -s os\deviceplatformrelease\foundation_system\system_model\system_definition_schema2.xml -k -j 12</info>
<info>Current working directory W:\sf</info>
<info>Environment EPOCROOT=\</info>
<info>Buildable configuration 'doxygen'</info>
<info>System Definition file os/deviceplatformrelease/foundation_system/system_model/system_definition_schema2.xml</info>"""


sysdefv1_unsupported = """<?xml version="1.0" encoding="UTF-8"?>
<SystemDefinition schema="1.4" name="Symbian^3"></SystemDefinition>"""

sysdefv2_unsupported = """<?xml version="1.0" encoding="UTF-8"?>
<SystemDefinition schema="2.1.0" name="Symbian^3"></SystemDefinition>"""

sysdefv3_unsupported = """<?xml version="1.0" encoding="UTF-8"?>
<SystemDefinition schema="2.1.0" name="Symbian^3"></SystemDefinition>"""

sysdefv2 = """<?xml version="1.0" encoding="UTF-8"?>
<SystemDefinition schema="2.0.1" name="Symbian^3">
    <systemModel>
        <layer name="os" long-name="OS" levels="hw services">
            <block name="kernelhwsrv" level="hw" long-name="Kernel and Hardware Services" levels="hw-if adaptation framework test">
                <collection name="brdbootldr" long-name="Board Boot Loader" level="hw-if">
                    <component name="ubootldr" long-name="Boot Loader" introduced="9.2" purpose="optional">
                        <unit mrp="brdbootldr/ubootldr/base_ubootldr.mrp"/>
                    </component>
                </collection>
                <collection id="bsptemplate" long-name="Board Support Package Template" level="hw-if">
                    <component name="asspandvariant" long-name="Template ASSP and Variant" introduced="6.0" purpose="development">
                        <unit bldFile="os/kernelhwsrv/bsptemplate/asspandvariant/template_variant" mrp="bsptemplate/asspandvariant/base_template.mrp"/>
                    </component>
                </collection>
                <collection name="kernel" long-name="Kernel Architecture" level="adaptation">
                    <component name="eka" long-name="Kernel Architecture" introduced="8.0" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/kernel/eka" mrp="kernel/eka/base_e32.mrp"/>
                    </component>
                </collection>
                <collection name="kerneltest" long-name="Kernel Test" level="hw-if">
                    <component name="e32utils" long-name="E32 Utilities" purpose="development">
                        <unit bldFile="os/kernelhwsrv/kerneltest/e32utils/group" mrp="kerneltest/e32utils/group/base_e32utils.mrp"/>
                    </component>
                    <component name="e32test" long-name="E32 Tests" purpose="development">
                        <unit bldFile="os/kernelhwsrv/kerneltest/e32test/group" mrp="kerneltest/e32test/group/base_e32test.mrp"/>
                    </component>
                    <component name="f32test" long-name="File Server Tests" purpose="development">
                        <unit bldFile="os/kernelhwsrv/kerneltest/f32test/group" mrp="kerneltest/f32test/group/base_f32test.mrp"/>
                    </component>
                </collection>
                <collection name="ldds" long-name="Logical Device Drivers" level="adaptation">
                    <component name="ethernetldd" long-name="Ethernet Drivers" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/ethernet" mrp="kernel/eka/drivers/ethernet/base_e32_drivers_ethernet.mrp"/>
                    </component>
                    <component name="audioldd" long-name="Audio Drivers" introduced="8.1b" purpose="optional">     
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/soundsc" mrp="kernel/eka/drivers/soundsc/base_e32_drivers_sound.mrp"/>       
                    </component>
                    <component name="serialldd" long-name="Serial Port Drivers" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/ecomm" mrp="kernel/eka/drivers/ecomm/base_e32_drivers_ecomm.mrp"/>
                    </component>
                    <component name="legacydrivers" long-name="Legacy Drivers" purpose="optional">
                        <unit mrp="kernel/eka/drivers/adc/base_e32_drivers_adc.mrp"/>
                    </component>
                    <component name="locmedia" long-name="Local Media Subsystem" introduced="8.1b" purpose="mandatory">
                        <!-- these are LDDs for storage media-->
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/locmedia" mrp="kernel/eka/drivers/locmedia/base_e32_drivers_locmedia.mrp"/>
                    </component>
                    <component name="runmodedebugger" long-name="Run Mode Debugger" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/debug/group" mrp="kernel/eka/drivers/debug/group/base_e32_drivers_debug.mrp"/>        
                    </component>
                    <component name="btrace" long-name="Kernel Trace Tool" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/trace" mrp="kernel/eka/drivers/trace/base_e32_drivers_trace.mrp"/>
                    </component>
                    <component name="cameraldd" long-name="Camera Drivers" introduced="^3" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/camerasc" mrp="kernel/eka/drivers/camerasc/base_drivers_camerasc.mrp"/>
                    </component>
                    <component name="displayldd" long-name="Display Drivers" introduced="^3" purpose="optional">
                        <!-- owned and maintained by graphics package. To be moved there as soon as technical limitations are resolved -->
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/display" mrp="kernel/eka/drivers/display/base_e32_drivers_display.mrp"/>
                    </component>
                    <component name="usbclientdrivers" long-name="USB Client Drivers" introduced="8.1b" purpose="optional">
                        <!-- owned and maintained by usb package. To be moved there as soon as technical limitations are resolved -->
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/usbc" mrp="kernel/eka/drivers/usbc/base_e32_drivers_usbcli.mrp"/>
                    </component>
                </collection>
                <collection name="driversupport" long-name="Generic Driver Support" level="hw-if">
                    <component name="mediadrivers" long-name="Media Drivers" purpose="optional">
                        <!-- these are for storage media-->
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/media" mrp="kernel/eka/drivers/media/base_e32_drivers_media.mrp"/>
                    </component>
                    <component name="genericboardsupport" long-name="Generic Board Support" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/bsp" mrp="kernel/eka/drivers/bsp/base_e32_drivers_bsp.mrp"/>
                    </component>
                </collection>
                <collection name="userlibandfileserver" long-name="User Library and File Server" level="framework">
                    <component name="euser" long-name="User Library" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/euser" mrp="kernel/eka/euser/base_e32_euser.mrp"/>
                    </component>
                    <component name="compsupp" long-name="Compiler Runtime Support" filter="gt" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/compsupp" mrp="kernel/eka/compsupp/base_e32_compsupp.mrp"/>
                    </component>
                    <component name="fileserver" long-name="File Server" filter="gt" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/group" mrp="userlibandfileserver/fileserver/group/base_f32.mrp"/>
                    </component>
                    <component name="estart" long-name="Base Starter" filter="gt" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/estart" mrp="userlibandfileserver/fileserver/estart/base_f32_estart.mrp"/>
                    </component>
                    <component name="domainmgr" long-name="Domain Manager" introduced="8.1b" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/domainmgr/group" mrp="userlibandfileserver/domainmgr/group/base_domain.mrp"/>
                    </component>
                </collection>
                <collection name="filesystems" long-name="File Systems" level="framework">
                    <component name="romfs" long-name="ROM File System" filter="gt" purpose="optional" class="plugin">
                        <unit mrp="userlibandfileserver/fileserver/srom/base_f32_srom.mrp"/>
                    </component>
                    <component name="rofs" long-name="ROFS" filter="gt" purpose="optional" class="plugin">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/srofs" mrp="userlibandfileserver/fileserver/srofs/base_f32_srofs.mrp"/>
                    </component>
                    <component name="usbmsfs" long-name="USB Mass Storage File System" filter="gt" purpose="optional" class="plugin">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/smassstorage" mrp="userlibandfileserver/fileserver/smassstorage/base_f32_smassstorage.mrp"/>
                    </component>
                    <component name="usbhostmssrv" long-name="USB Host Mass Storage Server" filter="gt" introduced="^3" purpose="optional" class="plugin">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/shostmassstorage" mrp="userlibandfileserver/fileserver/shostmassstorage/base_f32_shostmassstorage.mrp"/>
                    </component>
                    <component name="fat32fs" long-name="FAT32 File System" filter="gt" purpose="optional" class="plugin">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/sfat32" mrp="userlibandfileserver/fileserver/sfat32/base_f32_sfat32.mrp"/>
                    </component>
                    <component name="fatfs" long-name="FAT File System" filter="gt" purpose="optional" class="plugin">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/sfat" mrp="userlibandfileserver/fileserver/sfat/base_f32_sfat.mrp"/>
                    </component>
                    <component name="compfs" long-name="Composite File System" filter="gt" purpose="optional" class="plugin">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/scomp" mrp="userlibandfileserver/fileserver/scomp/base_f32_scomp.mrp"/>
                    </component>
                </collection>
                <collection name="halservices" long-name="HAL Services" level="framework">
                    <component name="hal" long-name="User-Side Hardware Abstraction" introduced="6.0" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/halservices/hal" mrp="halservices/hal/base_hal.mrp"/>
                    </component>
                </collection>
                <collection name="textmodeshell" long-name="Text Mode Shell" level="test">
                    <component name="e32wsrv" long-name="Text Window Server" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/ewsrv" mrp="kernel/eka/ewsrv/base_e32_ewsrv.mrp"/>
                    </component>
                    <component name="textshell" long-name="Text Shell" filter="gt" purpose="development">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/etshell" mrp="userlibandfileserver/fileserver/etshell/base_f32_eshell.mrp"/>
                    </component>
                </collection>
                <collection name="baseapitest" long-name="Base API Tests" level="test">
                    <component name="basesvs" long-name="Base Verification Suite" introduced="^2" purpose="development" filter="test">
                        <unit mrp="baseapitest/basesvs/group/basesvs.mrp" bldFile="baseapitest/basesvs/group"/>
                    </component>
                </collection>
                <collection name="kernelhwsrv_info" long-name="Kernel and Hardware Services Info" level="test">
                    <component name="kernelhwsrv_metadata" long-name="Kernel and Hardware Services Metadata" class="config" introduced="^2" purpose="development" target="desktop">
                        <unit mrp="kernelhwsrv_info/kernelhwsrv_metadata/kernelhwsrv_metadata.mrp"/>
                    </component>
                </collection>
            </block>
        </layer>
        <layer name="mw" long-name="Middleware" levels="generic specific">
            <block name="classicui" level="generic" long-name="Classic UI" levels="base support server generic specific">
                <collection name="psln" long-name="Personalization" level="specific">
                    <component filter="s60" long-name="Personalization Engine" class="placeholder">
                        <!-- <unit bldFile="psln/pslnengine/group"/> -->
                    </component>
                    <component name="pslnframework" filter="s60" long-name="Personalization Framework" class="placeholder">
                        <!-- <unit bldFile="psln/pslnframework"/> -->
                    </component>
                    <component name="pslnlibraryloaders" filter="s60" long-name="Personalization Library Loaders" class="placeholder">
                        <!-- no bld.inf, need to create one or remove component -->
                    </component>
                    <component name="pslnslidesetdialog" filter="s60" long-name="Personalization Slideset Dialog" plugin="Y" class="placeholder">
                        <!-- <unit bldFile="psln/pslnslidesetdialog/group"/> -->
                    </component>
                    <component name="pslngsplugin" filter="s60" long-name="Personalization GS Plugin" plugin="Y">
                        <unit bldFile="mw/classicui/psln/pslngsplugin/Group"/>
                    </component>
                    <component name="psln_help" filter="s60" long-name="Personalization Help">
                        <unit bldFile="mw/classicui/psln/help/group"/>
                    </component>
                    <component name="psln_build" filter="s60" long-name="Personalization Build">
                        <!-- the Psln group bld.inf should be distributed into the individual components, or they should be collapsed in a single component -->
                        <unit bldFile="mw/classicui/psln/group"/>
                    </component>
                </collection>
                <collection name="applicationinterworkingfw" long-name="Application Interworking Framework" level="generic">
                    <component name="aifwservicehandler" filter="s60" long-name="Application Interworking Service Handle">
                        <unit bldFile="mw/classicui/applicationinterworkingfw/servicehandler/group"/>
                    </component>
                </collection>
                <collection name="commonuis" long-name="Common UIs" level="specific">
                    <component name="commonui" filter="s60" long-name="Common UI">
                        <unit bldFile="mw/classicui/commonuis/commonui/group"/>
                    </component>
                    <component name="commondialogs" filter="s60" long-name="Common Dialogs">
                        <unit bldFile="mw/classicui/commonuis/commondialogs/group"/>
                        <!-- <unit bldFile="commonuis/commondialogs/group_test"/> -->
                    </component>
                </collection>
                <collection name="uifw" long-name="UI Framework" level="server">
                    <component name="uiklaf" filter="s60" long-name="Uikon Look-and-Feel">
                        <unit bldFile=""/>
                    </component>
                    <component name="eikctl" filter="s60" long-name="Eikon Controls">
                        <unit bldFile="mw/classicui/uifw/eikctl/group"/>
                    </component>
                    <component name="avkon" filter="s60" long-name="Avkon">
                        <unit bldFile="mw/classicui/uifw/avkon/aknphysics/group"/>
                        <unit bldFile="mw/classicui/uifw/avkon/group"/>
                        <unit bldFile="mw/classicui/uifw/avkon/odeconf/group"/>
                        <!-- <unit bldFile="uifw/avkon/aknhlist/group"/> -->
                        <!-- <unit bldFile="uifw/avkon/aknkeyrotator/group"/> -->
                        <!-- <unit bldFile="uifw/avkon/prebuilder"/> -->
                        <!-- <unit bldFile="uifw/avkon/tsrc/bc/s60_sdkmcl/bctestmixmcl/group"/> -->
                    </component>
                    <component name="eikstd" filter="s60" long-name="Eikon Standard">
                        <unit bldFile="mw/classicui/uifw/eikstd/group"/>
                    </component>
                    <component name="aknglobalui" filter="s60" long-name="Avkon Global UI">
                        <unit bldFile="mw/classicui/uifw/aknglobalui/group"/>
                    </component>
                    <component name="ganes" filter="s60" long-name="Ganes">
                        <unit bldFile="mw/classicui/uifw/ganes/group"/>
                    </component>
                    <component name="uifw_test" filter="s60" long-name="UI Framework Test" purpose="development" class="placeholder">
                        <!-- <unit bldFile="uifw/tsrc/group"/> -->
                    </component>
                </collection>
                <collection name="commonadapter" long-name="Common Adapter" level="support">
                    <component name="commonadapter_build" filter="s60" long-name="Common Adapter Build">
                        <unit bldFile="mw/classicui/commonadapter/group"/>
                    </component>
                </collection>
                <collection name="ode" long-name="Open Dynamics Engine" level="support">
                    <component name="ode_build" filter="s60" long-name="ODE">
                        <unit bldFile="mw/classicui/ode/group"/>
                    </component>
                </collection>
                <collection name="commonuisupport" long-name="Common UI Support" level="support">
                    <component name="uikon" long-name="Uikon" introduced="6.0" purpose="mandatory">
                        <unit bldFile="mw/classicui/commonuisupport/uikon/group" mrp="mw/classicui/commonuisupport/uikon/group/app-framework_uikon.mrp"/>
                    </component>
                    <component name="errorresolverdata" long-name="Error Resolver Data" purpose="mandatory">
                        <unit bldFile="mw/classicui/commonuisupport/errorresolverdata/group" mrp="mw/classicui/commonuisupport/errorresolverdata/group/app-framework_errorresgt.mrp"/>
                    </component>
                    <component name="uilaf" long-name="UI Look and Feel" introduced="6.0" purpose="mandatory">
                        <unit bldFile="mw/classicui/commonuisupport/uilaf/GROUP" mrp="mw/classicui/commonuisupport/uilaf/GROUP/app-framework_uiklafgt.mrp"/>
                    </component>
                    <component name="grid" long-name="Grid" purpose="optional">
                        <unit bldFile="mw/classicui/commonuisupport/grid/group" mrp="mw/classicui/commonuisupport/grid/group/app-framework_grid.mrp"/>
                    </component>
                    <component name="uifwsdocs" long-name="UI Frameworks Documentation" purpose="development" class="doc">
                        <unit mrp="mw/classicui/commonuisupport/uifwsdocs/app-framework_documentation.mrp"/>
                    </component>
                </collection>
                <collection name="lafagnosticuifoundation" long-name="Look-and-Feel Agnostic UI Foundation" level="base">
                    <component name="cone" long-name="Control Environment" purpose="mandatory">
                        <unit bldFile="mw/classicui/lafagnosticuifoundation/cone/group" mrp="mw/classicui/lafagnosticuifoundation/cone/group/app-framework_cone.mrp"/>
                    </component>
                    <component name="graphicseffects" long-name="Graphics Effects" introduced="9.2" purpose="optional">
                        <unit bldFile="mw/classicui/lafagnosticuifoundation/graphicseffects/group" mrp="mw/classicui/lafagnosticuifoundation/graphicseffects/group/app-framework_gfxtranseffect.mrp"/>
                    </component>
                    <component name="uigraphicsutils" long-name="UI Graphics Utilities" purpose="mandatory">
                        <unit bldFile="mw/classicui/lafagnosticuifoundation/uigraphicsutils/group" mrp="mw/classicui/lafagnosticuifoundation/uigraphicsutils/group/app-framework_egul.mrp"/>
                    </component>
                    <component name="clockanim" long-name="Clock" purpose="optional" plugin="Y">
                        <unit bldFile="mw/classicui/lafagnosticuifoundation/clockanim/group" mrp="mw/classicui/lafagnosticuifoundation/clockanim/group/app-framework_clock.mrp"/>
                    </component>
                    <component name="bmpanimation" long-name="BMP Animation" introduced="6.0" purpose="optional">
                        <unit bldFile="mw/classicui/lafagnosticuifoundation/bmpanimation/group" mrp="mw/classicui/lafagnosticuifoundation/bmpanimation/group/app-framework_bmpanim.mrp"/>
                    </component>
                    <component name="animation" long-name="Animation" introduced="9.1" purpose="optional">
                        <unit bldFile="mw/classicui/lafagnosticuifoundation/animation/group" mrp="mw/classicui/lafagnosticuifoundation/animation/group/app-framework_animation.mrp"/>
                    </component>
                </collection>
                <collection name="classicui_info" long-name="Classic UI Info" level="specific">
                    <!-- the multiple units in the API components need to be resolved -->
                    <component name="classicui_pub" filter="s60" long-name="Classic UI Public Interfaces" class="api">
                        <unit bldFile="mw/classicui/classicui_pub/group"/>
                    </component>
                    <component name="classicui_plat" filter="s60" long-name="Classic UI Platform Interfaces" class="api">
                        <unit bldFile="mw/classicui/classicui_plat/group"/>
                    </component>
                    <component name="classicui_test" filter="s60" long-name="Classic UI Tests" purpose="development">
                        <unit bldFile="mw/classicui/classicui_plat/tsrc/group"/>
                        <unit bldFile="mw/classicui/classicui_pub/document_handler_api/tsrc/group"/>
                        <unit bldFile="mw/classicui/classicui_pub/server_application_api/tsrc/group"/>
                        <!-- <unit bldFile="classicui_pub/tsrc/bc/apps/bctesttemplate/group"/> -->
                        <!-- <unit bldFile="classicui_pub/tsrc/bc/apps/s60_sdk3.0/group"/> -->
                        <!-- <unit bldFile="classicui_pub/tsrc/bc/apps/s60_sdk3.1/group"/> -->
                        <!-- <unit bldFile="classicui_pub/tsrc/bc/apps/s60_sdk3.2/group"/> -->
                        <!-- <unit bldFile="classicui_pub/tsrc/bc/apps/s60_sdk5.0/bctestpane/group"/> -->
                        <!-- <unit bldFile="classicui_pub/tsrc/bc/apps/s60_sdk5.0/group"/> -->
                        <!-- <unit bldFile="classicui_pub/tsrc/bc/group"/> -->
                        <!-- <unit bldFile="classicui_plat/avkon_testability_api/tsrc/group"/> -->
                        <!-- <unit bldFile="classicui_plat/extended_sounds_api/tsrc/group"/> -->
                        <unit bldFile="mw/classicui/classicui_plat/ganes_api/tsrc/group"/>
                        <unit bldFile="mw/classicui/classicui_plat/physics_api/tsrc/group"/>
                    </component>
                    <component name="classicui_metadata" long-name="Classic UI Metadata" introduced="^2" purpose="development" class="config PC">
                        <unit mrp="mw/classicui/classicui_info/classicui_metadata/classicui_metadata.mrp"/>
                    </component>
                </collection>
            </block>
        </layer>
    </systemModel>
</SystemDefinition>"""


sysdefv3_nondistributed = """<?xml version="1.0" encoding="UTF-8"?>
<SystemDefinition schema="3.0.0">
    <systemModel name="Symbian^3">
        <layer id="os" name="OS" levels="hw services">
            <package id="kernelhwsrv" name="Kernel and Hardware Services" levels="hw-if adaptation framework test">
                <collection id="brdbootldr" name="Board Boot Loader" level="hw-if">
                    <component id="ubootldr" name="Boot Loader" introduced="9.2" purpose="optional">
                        <unit mrp="brdbootldr/ubootldr/base_ubootldr.mrp"/>
                    </component>
                </collection>
                <collection id="bsptemplate" name="Board Support Package Template" level="hw-if">
                    <component id="asspandvariant" name="Template ASSP and Variant" introduced="6.0" purpose="development">
                        <unit bldFile="os/kernelhwsrv/bsptemplate/asspandvariant/template_variant" mrp="bsptemplate/asspandvariant/base_template.mrp"/>
                    </component>
                </collection>
                <collection id="kernel" name="Kernel Architecture" level="adaptation">
                    <component id="eka" name="Kernel Architecture" introduced="8.0" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/kernel/eka" mrp="kernel/eka/base_e32.mrp"/>
                    </component>
                </collection>
                <collection id="kerneltest" name="Kernel Test" level="hw-if">
                    <component id="e32utils" name="E32 Utilities" purpose="development">
                        <unit bldFile="os/kernelhwsrv/kerneltest/e32utils/group" mrp="kerneltest/e32utils/group/base_e32utils.mrp"/>
                    </component>
                    <component id="e32test" name="E32 Tests" purpose="development">
                        <unit bldFile="os/kernelhwsrv/kerneltest/e32test/group" mrp="kerneltest/e32test/group/base_e32test.mrp"/>
                    </component>
                    <component id="f32test" name="File Server Tests" purpose="development">
                        <unit bldFile="os/kernelhwsrv/kerneltest/f32test/group" mrp="kerneltest/f32test/group/base_f32test.mrp"/>
                    </component>
                </collection>
                <collection id="ldds" name="Logical Device Drivers" level="adaptation">
                    <component id="ethernetldd" name="Ethernet Drivers" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/ethernet" mrp="kernel/eka/drivers/ethernet/base_e32_drivers_ethernet.mrp"/>
                    </component>
                    <component id="audioldd" name="Audio Drivers" introduced="8.1b" purpose="optional">     
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/soundsc" mrp="kernel/eka/drivers/soundsc/base_e32_drivers_sound.mrp"/>       
                    </component>
                    <component id="serialldd" name="Serial Port Drivers" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/ecomm" mrp="kernel/eka/drivers/ecomm/base_e32_drivers_ecomm.mrp"/>
                    </component>
                    <component id="legacydrivers" name="Legacy Drivers" purpose="optional">
                        <unit mrp="kernel/eka/drivers/adc/base_e32_drivers_adc.mrp"/>
                    </component>
                    <component id="locmedia" name="Local Media Subsystem" introduced="8.1b" purpose="mandatory">
                        <!-- these are LDDs for storage media-->
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/locmedia" mrp="kernel/eka/drivers/locmedia/base_e32_drivers_locmedia.mrp"/>
                    </component>
                    <component id="runmodedebugger" name="Run Mode Debugger" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/debug/group" mrp="kernel/eka/drivers/debug/group/base_e32_drivers_debug.mrp"/>        
                    </component>
                    <component id="btrace" name="Kernel Trace Tool" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/trace" mrp="kernel/eka/drivers/trace/base_e32_drivers_trace.mrp"/>
                    </component>
                    <component id="cameraldd" name="Camera Drivers" introduced="^3" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/camerasc" mrp="kernel/eka/drivers/camerasc/base_drivers_camerasc.mrp"/>
                    </component>
                    <component id="displayldd" name="Display Drivers" introduced="^3" purpose="optional">
                        <!-- owned and maintained by graphics package. To be moved there as soon as technical limitations are resolved -->
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/display" mrp="kernel/eka/drivers/display/base_e32_drivers_display.mrp"/>
                    </component>
                    <component id="usbclientdrivers" name="USB Client Drivers" introduced="8.1b" purpose="optional">
                        <!-- owned and maintained by usb package. To be moved there as soon as technical limitations are resolved -->
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/usbc" mrp="kernel/eka/drivers/usbc/base_e32_drivers_usbcli.mrp"/>
                    </component>
                </collection>
                <collection id="driversupport" name="Generic Driver Support" level="hw-if">
                    <component id="mediadrivers" name="Media Drivers" purpose="optional">
                        <!-- these are for storage media-->
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/media" mrp="kernel/eka/drivers/media/base_e32_drivers_media.mrp"/>
                    </component>
                    <component id="genericboardsupport" name="Generic Board Support" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/drivers/bsp" mrp="kernel/eka/drivers/bsp/base_e32_drivers_bsp.mrp"/>
                    </component>
                </collection>
                <collection id="userlibandfileserver" name="User Library and File Server" level="framework">
                    <component id="euser" name="User Library" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/euser" mrp="kernel/eka/euser/base_e32_euser.mrp"/>
                    </component>
                    <component id="compsupp" name="Compiler Runtime Support" filter="gt" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/compsupp" mrp="kernel/eka/compsupp/base_e32_compsupp.mrp"/>
                    </component>
                    <component id="fileserver" name="File Server" filter="gt" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/group" mrp="userlibandfileserver/fileserver/group/base_f32.mrp"/>
                    </component>
                    <component id="estart" name="Base Starter" filter="gt" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/estart" mrp="userlibandfileserver/fileserver/estart/base_f32_estart.mrp"/>
                    </component>
                    <component id="domainmgr" name="Domain Manager" introduced="8.1b" purpose="mandatory">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/domainmgr/group" mrp="userlibandfileserver/domainmgr/group/base_domain.mrp"/>
                    </component>
                </collection>
                <collection id="filesystems" name="File Systems" level="framework">
                    <component id="romfs" name="ROM File System" filter="gt" purpose="optional" class="plugin">
                        <unit mrp="userlibandfileserver/fileserver/srom/base_f32_srom.mrp"/>
                    </component>
                    <component id="rofs" name="ROFS" filter="gt" purpose="optional" class="plugin">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/srofs" mrp="userlibandfileserver/fileserver/srofs/base_f32_srofs.mrp"/>
                    </component>
                    <component id="usbmsfs" name="USB Mass Storage File System" filter="gt" purpose="optional" class="plugin">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/smassstorage" mrp="userlibandfileserver/fileserver/smassstorage/base_f32_smassstorage.mrp"/>
                    </component>
                    <component id="usbhostmssrv" name="USB Host Mass Storage Server" filter="gt" introduced="^3" purpose="optional" class="plugin">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/shostmassstorage" mrp="userlibandfileserver/fileserver/shostmassstorage/base_f32_shostmassstorage.mrp"/>
                    </component>
                    <component id="fat32fs" name="FAT32 File System" filter="gt" purpose="optional" class="plugin">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/sfat32" mrp="userlibandfileserver/fileserver/sfat32/base_f32_sfat32.mrp"/>
                    </component>
                    <component id="fatfs" name="FAT File System" filter="gt" purpose="optional" class="plugin">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/sfat" mrp="userlibandfileserver/fileserver/sfat/base_f32_sfat.mrp"/>
                    </component>
                    <component id="compfs" name="Composite File System" filter="gt" purpose="optional" class="plugin">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/scomp" mrp="userlibandfileserver/fileserver/scomp/base_f32_scomp.mrp"/>
                    </component>
                </collection>
                <collection id="halservices" name="HAL Services" level="framework">
                    <component id="hal" name="User-Side Hardware Abstraction" introduced="6.0" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/halservices/hal" mrp="halservices/hal/base_hal.mrp"/>
                    </component>
                </collection>
                <collection id="textmodeshell" name="Text Mode Shell" level="test">
                    <component id="e32wsrv" name="Text Window Server" purpose="optional">
                        <unit bldFile="os/kernelhwsrv/kernel/eka/ewsrv" mrp="kernel/eka/ewsrv/base_e32_ewsrv.mrp"/>
                    </component>
                    <component id="textshell" name="Text Shell" filter="gt" purpose="development">
                        <unit bldFile="os/kernelhwsrv/userlibandfileserver/fileserver/etshell" mrp="userlibandfileserver/fileserver/etshell/base_f32_eshell.mrp"/>
                    </component>
                </collection>
                <collection id="baseapitest" name="Base API Tests" level="test">
                    <component id="basesvs" name="Base Verification Suite" introduced="^2" purpose="development" filter="test">
                        <unit mrp="baseapitest/basesvs/group/basesvs.mrp" bldFile="baseapitest/basesvs/group"/>
                    </component>
                </collection>
                <collection id="kernelhwsrv_info" name="Kernel and Hardware Services Info" level="test">
                    <component id="kernelhwsrv_metadata" name="Kernel and Hardware Services Metadata" class="config" introduced="^2" purpose="development" target="desktop">
                        <unit mrp="kernelhwsrv_info/kernelhwsrv_metadata/kernelhwsrv_metadata.mrp"/>
                    </component>
                </collection>
            </package>
        </layer>
        <layer id="mw" name="Middleware" levels="generic specific">
            <package id="classicui" name="Classic UI" levels="base support server generic specific">
                <collection id="psln" name="Personalization" level="specific">
                    <component id="pslnengine" filter="s60" name="Personalization Engine">
                        <!-- <unit bldFile="mw/classicui/psln/pslnengine/group"/> -->
                    </component>
                    <component id="pslnframework" filter="s60" name="Personalization Framework">
                        <!-- <unit bldFile="mw/classicui/psln/pslnframework"/> -->
                    </component>
                    <component id="pslnlibraryloaders" filter="s60" name="Personalization Library Loaders">
                        <!-- no bld.inf, need to create one or remove component -->
                    </component>
                    <component id="pslnslidesetdialog" filter="s60" name="Personalization Slideset Dialog" class="plugin">
                        <!-- <unit bldFile="mw/classicui/psln/pslnslidesetdialog/group"/> -->
                    </component>
                    <component id="pslngsplugin" filter="s60" name="Personalization GS Plugin" class="plugin">
                        <unit bldFile="mw/classicui/psln/pslngsplugin/Group"/>
                    </component>
                    <component id="psln_help" filter="s60" name="Personalization Help">
                        <unit bldFile="mw/classicui/psln/help/group"/>
                    </component>
                    <component id="psln_build" filter="s60" name="Personalization Build">
                        <!-- the Psln group bld.inf should be distributed into the individual components, or they should be collapsed in a single component -->
                        <unit bldFile="mw/classicui/psln/group"/>
                    </component>
                </collection>
                <collection id="applicationinterworkingfw" name="Application Interworking Framework" level="generic">
                    <component id="aifwservicehandler" filter="s60" name="Application Interworking Service Handle">
                        <unit bldFile="mw/classicui/applicationinterworkingfw/servicehandler/group"/>
                    </component>
                </collection>
                <collection id="commonuis" name="Common UIs" level="specific">
                    <component id="commonui" filter="s60" name="Common UI">
                        <unit bldFile="mw/classicui/commonuis/commonui/group"/>
                    </component>
                    <component id="commondialogs" filter="s60" name="Common Dialogs">
                        <unit bldFile="mw/classicui/commonuis/commondialogs/group"/>
                        <!-- <unit bldFile="mw/classicui/commonuis/commondialogs/group_test"/> -->
                    </component>
                </collection>
                <collection id="uifw" name="UI Framework" level="server">
                    <component id="uiklaf" filter="s60" name="Uikon Look-and-Feel">
                        <unit bldFile=""/>
                    </component>
                    <component id="eikctl" filter="s60" name="Eikon Controls">
                        <unit bldFile="mw/classicui/uifw/eikctl/group"/>
                    </component>
                    <component id="avkon" filter="s60" name="Avkon">
                        <unit bldFile="mw/classicui/uifw/avkon/aknphysics/group"/>
                        <unit bldFile="mw/classicui/uifw/avkon/group"/>
                        <unit bldFile="mw/classicui/uifw/avkon/odeconf/group"/>
                        <!-- <unit bldFile="mw/classicui/uifw/avkon/aknhlist/group"/> -->
                        <!-- <unit bldFile="mw/classicui/uifw/avkon/aknkeyrotator/group"/> -->
                        <!-- <unit bldFile="mw/classicui/uifw/avkon/prebuilder"/> -->
                        <!-- <unit bldFile="mw/classicui/uifw/avkon/tsrc/bc/s60_sdkmcl/bctestmixmcl/group"/> -->
                    </component>
                    <component id="eikstd" filter="s60" name="Eikon Standard">
                        <unit bldFile="mw/classicui/uifw/eikstd/group"/>
                    </component>
                    <component id="aknglobalui" filter="s60" name="Avkon Global UI">
                        <unit bldFile="mw/classicui/uifw/aknglobalui/group"/>
                    </component>
                    <component id="ganes" filter="s60" name="Ganes">
                        <unit bldFile="mw/classicui/uifw/ganes/group"/>
                    </component>
                    <component id="uifw_test" filter="s60" name="UI Framework Test" purpose="development">
                        <!-- <unit bldFile="mw/classicui/uifw/tsrc/group"/> -->
                    </component>
                </collection>
                <collection id="commonadapter" name="Common Adapter" level="support">
                    <component id="commonadapter_build" filter="s60" name="Common Adapter Build">
                        <unit bldFile="mw/classicui/commonadapter/group"/>
                    </component>
                </collection>
                <collection id="ode" name="Open Dynamics Engine" level="support">
                    <component id="ode_build" filter="s60" name="ODE">
                        <unit bldFile="mw/classicui/ode/group"/>
                    </component>
                </collection>
                <collection id="commonuisupport" name="Common UI Support" level="support">
                    <component id="uikon" name="Uikon" introduced="6.0" purpose="mandatory">
                        <unit bldFile="mw/classicui/commonuisupport/uikon/group" mrp="commonuisupport/uikon/group/app-framework_uikon.mrp"/>
                    </component>
                    <component id="errorresolverdata" name="Error Resolver Data" purpose="mandatory">
                        <unit bldFile="mw/classicui/commonuisupport/errorresolverdata/group" mrp="commonuisupport/errorresolverdata/group/app-framework_errorresgt.mrp"/>
                    </component>
                    <component id="uilaf" name="UI Look and Feel" introduced="6.0" purpose="mandatory">
                        <unit bldFile="mw/classicui/commonuisupport/uilaf/GROUP" mrp="commonuisupport/uilaf/GROUP/app-framework_uiklafgt.mrp"/>
                    </component>
                    <component id="grid" name="Grid" purpose="optional">
                        <unit bldFile="mw/classicui/commonuisupport/grid/group" mrp="commonuisupport/grid/group/app-framework_grid.mrp"/>
                    </component>
                    <component id="uifwsdocs" name="UI Frameworks Documentation" purpose="development" class="doc">
                        <unit mrp="commonuisupport/uifwsdocs/app-framework_documentation.mrp"/>
                    </component>
                </collection>
                <collection id="lafagnosticuifoundation" name="Look-and-Feel Agnostic UI Foundation" level="base">
                    <component id="cone" name="Control Environment" purpose="mandatory">
                        <unit bldFile="mw/classicui/lafagnosticuifoundation/cone/group" mrp="lafagnosticuifoundation/cone/group/app-framework_cone.mrp"/>
                    </component>
                    <component id="graphicseffects" name="Graphics Effects" introduced="9.2" purpose="optional">
                        <unit bldFile="mw/classicui/lafagnosticuifoundation/graphicseffects/group" mrp="lafagnosticuifoundation/graphicseffects/group/app-framework_gfxtranseffect.mrp"/>
                    </component>
                    <component id="uigraphicsutils" name="UI Graphics Utilities" purpose="mandatory">
                        <unit bldFile="mw/classicui/lafagnosticuifoundation/uigraphicsutils/group" mrp="lafagnosticuifoundation/uigraphicsutils/group/app-framework_egul.mrp"/>
                    </component>
                    <component id="clockanim" name="Clock" purpose="optional" class="plugin">
                        <unit bldFile="mw/classicui/lafagnosticuifoundation/clockanim/group" mrp="lafagnosticuifoundation/clockanim/group/app-framework_clock.mrp"/>
                    </component>
                    <component id="bmpanimation" name="BMP Animation" introduced="6.0" purpose="optional">
                        <unit bldFile="mw/classicui/lafagnosticuifoundation/bmpanimation/group" mrp="lafagnosticuifoundation/bmpanimation/group/app-framework_bmpanim.mrp"/>
                    </component>
                    <component id="animation" name="Animation" introduced="9.1" purpose="optional">
                        <unit bldFile="mw/classicui/lafagnosticuifoundation/animation/group" mrp="lafagnosticuifoundation/animation/group/app-framework_animation.mrp"/>
                    </component>
                </collection>
                <collection id="classicui_info" name="Classic UI Info" level="specific">
                    <!-- the multiple units in the API components need to be resolved -->
                    <component id="classicui_pub" filter="s60" name="Classic UI Public Interfaces" class="api">
                        <unit bldFile="mw/classicui/classicui_pub/group"/>
                    </component>
                    <component id="classicui_plat" filter="s60" name="Classic UI Platform Interfaces" class="api">
                        <unit bldFile="mw/classicui/classicui_plat/group"/>
                    </component>
                    <component id="classicui_test" filter="s60" name="Classic UI Tests" purpose="development">
                        <unit bldFile="mw/classicui/classicui_plat/tsrc/group"/>
                        <unit bldFile="mw/classicui/classicui_pub/document_handler_api/tsrc/group"/>
                        <unit bldFile="mw/classicui/classicui_pub/server_application_api/tsrc/group"/>
                        <!-- <unit bldFile="mw/classicui/classicui_pub/tsrc/bc/apps/bctesttemplate/group"/> -->
                        <!-- <unit bldFile="mw/classicui/classicui_pub/tsrc/bc/apps/s60_sdk3.0/group"/> -->
                        <!-- <unit bldFile="mw/classicui/classicui_pub/tsrc/bc/apps/s60_sdk3.1/group"/> -->
                        <!-- <unit bldFile="mw/classicui/classicui_pub/tsrc/bc/apps/s60_sdk3.2/group"/> -->
                        <!-- <unit bldFile="mw/classicui/classicui_pub/tsrc/bc/apps/s60_sdk5.0/bctestpane/group"/> -->
                        <!-- <unit bldFile="mw/classicui/classicui_pub/tsrc/bc/apps/s60_sdk5.0/group"/> -->
                        <!-- <unit bldFile="mw/classicui/classicui_pub/tsrc/bc/group"/> -->
                        <!-- <unit bldFile="mw/classicui/classicui_plat/avkon_testability_api/tsrc/group"/> -->
                        <!-- <unit bldFile="mw/classicui/classicui_plat/extended_sounds_api/tsrc/group"/> -->
                        <unit bldFile="mw/classicui/classicui_plat/ganes_api/tsrc/group"/>
                        <unit bldFile="mw/classicui/classicui_plat/physics_api/tsrc/group"/>
                    </component>
                    <component id="classicui_metadata" name="Classic UI Metadata" class="config" introduced="^2" purpose="development" target="desktop">
                        <unit mrp="classicui_info/classicui_metadata/classicui_metadata.mrp"/>
                    </component>
                </collection>
            </package>
        </layer>
    </systemModel>
</SystemDefinition>"""

sysdefv3_distributed = """<?xml version="1.0" encoding="UTF-8"?>
<SystemDefinition schema="3.0.0">
    <systemModel name="Symbian^3">
        <layer id="os" name="OS" levels="hw services">
          <package id="kernelhwsrv" level="hw" tech-domain="hb" href="../../../../os/kernelhwsrv/package_definition.xml"/>
        </layer>
        <layer id="mw" name="Middleware" levels="generic specific">
          <package id="classicui" level="generic" tech-domain="ui" href="../../../../mw/classicui/package_definition.xml"/>
        </layer>
  </systemModel>
</SystemDefinition>"""

sysdefv3_distributed_invalid_href = """<?xml version="1.0" encoding="UTF-8"?>
<SystemDefinition schema="3.0.0">
    <systemModel name="Symbian^3">
        <layer id="os" name="OS" levels="hw services">
          <package id="kernelhwsrv" level="hw" tech-domain="hb" href="xml"/>
        </layer>
        <layer id="mw" name="Middleware" levels="generic specific">
          <package id="classicui" level="generic" tech-domain="ui" href="../../../../mw/classicui/package_definition.xml"/>
        </layer>
  </systemModel>
</SystemDefinition>"""

kernelhwsrv_pkg_def = """<?xml version="1.0" encoding="UTF-8"?>
<SystemDefinition schema="3.0.0">
  <package id="kernelhwsrv" name="Kernel and Hardware Services" levels="hw-if adaptation framework test">
    <collection id="brdbootldr" name="Board Boot Loader" level="hw-if">
      <component id="ubootldr" name="Boot Loader" introduced="9.2" purpose="optional">
        <unit mrp="brdbootldr/ubootldr/base_ubootldr.mrp"/>
      </component>
    </collection>
    <collection id="bsptemplate" name="Board Support Package Template" level="hw-if">
      <component id="asspandvariant" name="Template ASSP and Variant" introduced="6.0" purpose="development">
        <unit bldFile="bsptemplate/asspandvariant/template_variant" mrp="bsptemplate/asspandvariant/base_template.mrp"/>
      </component>
    </collection>
    <collection id="kernel" name="Kernel Architecture" level="adaptation">
      <component id="eka" name="Kernel Architecture" introduced="8.0" purpose="mandatory">
        <unit bldFile="kernel/eka" mrp="kernel/eka/base_e32.mrp"/>
      </component>
    </collection>
    <collection id="kerneltest" name="Kernel Test" level="hw-if">
      <component id="e32utils" name="E32 Utilities" purpose="development">
      <unit bldFile="kerneltest/e32utils/group" mrp="kerneltest/e32utils/group/base_e32utils.mrp"/>
      </component>
      <component id="e32test" name="E32 Tests" purpose="development">
        <unit bldFile="kerneltest/e32test/group" mrp="kerneltest/e32test/group/base_e32test.mrp"/>
      </component>
      <component id="f32test" name="File Server Tests" purpose="development">
        <unit bldFile="kerneltest/f32test/group" mrp="kerneltest/f32test/group/base_f32test.mrp"/>
      </component>
    </collection>
    <collection id="ldds" name="Logical Device Drivers" level="adaptation">
      <component id="ethernetldd" name="Ethernet Drivers" purpose="optional">
        <unit bldFile="kernel/eka/drivers/ethernet" mrp="kernel/eka/drivers/ethernet/base_e32_drivers_ethernet.mrp"/>
      </component>
      <component id="audioldd" name="Audio Drivers" introduced="8.1b" purpose="optional">     
        <unit bldFile="kernel/eka/drivers/soundsc" mrp="kernel/eka/drivers/soundsc/base_e32_drivers_sound.mrp"/>       
      </component>
      <component id="serialldd" name="Serial Port Drivers" purpose="optional">
        <unit bldFile="kernel/eka/drivers/ecomm" mrp="kernel/eka/drivers/ecomm/base_e32_drivers_ecomm.mrp"/>
      </component>
      <component id="legacydrivers" name="Legacy Drivers" purpose="optional">
        <unit mrp="kernel/eka/drivers/adc/base_e32_drivers_adc.mrp"/>
      </component>
      <component id="locmedia" name="Local Media Subsystem" introduced="8.1b" purpose="mandatory">
        <!-- these are LDDs for storage media-->
        <unit bldFile="kernel/eka/drivers/locmedia" mrp="kernel/eka/drivers/locmedia/base_e32_drivers_locmedia.mrp"/>
      </component>
      <component id="runmodedebugger" name="Run Mode Debugger" purpose="mandatory">
        <unit bldFile="kernel/eka/drivers/debug/group" mrp="kernel/eka/drivers/debug/group/base_e32_drivers_debug.mrp"/>        
      </component>
      <component id="btrace" name="Kernel Trace Tool" purpose="mandatory">
        <unit bldFile="kernel/eka/drivers/trace" mrp="kernel/eka/drivers/trace/base_e32_drivers_trace.mrp"/>
      </component>
      <component id="cameraldd" name="Camera Drivers" introduced="^3" purpose="optional">
        <unit bldFile="kernel/eka/drivers/camerasc" mrp="kernel/eka/drivers/camerasc/base_drivers_camerasc.mrp"/>
      </component>
      <component id="displayldd" name="Display Drivers" introduced="^3" purpose="optional">
        <!-- owned and maintained by graphics package. To be moved there as soon as technical limitations are resolved -->
        <unit bldFile="kernel/eka/drivers/display" mrp="kernel/eka/drivers/display/base_e32_drivers_display.mrp"/>
      </component>
      <component id="usbclientdrivers" name="USB Client Drivers" introduced="8.1b" purpose="optional">
        <!-- owned and maintained by usb package. To be moved there as soon as technical limitations are resolved -->
        <unit bldFile="kernel/eka/drivers/usbc" mrp="kernel/eka/drivers/usbc/base_e32_drivers_usbcli.mrp"/>
      </component>
    </collection>
    <collection id="driversupport" name="Generic Driver Support" level="hw-if">
      <component id="mediadrivers" name="Media Drivers" purpose="optional">
        <!-- these are for storage media-->
        <unit bldFile="kernel/eka/drivers/media" mrp="kernel/eka/drivers/media/base_e32_drivers_media.mrp"/>
      </component>
      <component id="genericboardsupport" name="Generic Board Support" purpose="optional">
        <unit bldFile="kernel/eka/drivers/bsp" mrp="kernel/eka/drivers/bsp/base_e32_drivers_bsp.mrp"/>
      </component>
    </collection>
    <collection id="userlibandfileserver" name="User Library and File Server" level="framework">
      <component id="euser" name="User Library" purpose="mandatory">
        <unit bldFile="kernel/eka/euser" mrp="kernel/eka/euser/base_e32_euser.mrp"/>
      </component>
      <component id="compsupp" name="Compiler Runtime Support" filter="gt" purpose="mandatory">
        <unit bldFile="kernel/eka/compsupp" mrp="kernel/eka/compsupp/base_e32_compsupp.mrp"/>
      </component>
      <component id="fileserver" name="File Server" filter="gt" purpose="mandatory">
        <unit bldFile="userlibandfileserver/fileserver/group" mrp="userlibandfileserver/fileserver/group/base_f32.mrp"/>
      </component>
      <component id="estart" name="Base Starter" filter="gt" purpose="optional">
        <unit bldFile="userlibandfileserver/fileserver/estart" mrp="userlibandfileserver/fileserver/estart/base_f32_estart.mrp"/>
      </component>
      <component id="domainmgr" name="Domain Manager" introduced="8.1b" purpose="mandatory">
        <unit bldFile="userlibandfileserver/domainmgr/group" mrp="userlibandfileserver/domainmgr/group/base_domain.mrp"/>
      </component>
    </collection>
    <collection id="filesystems" name="File Systems" level="framework">
      <component id="romfs" name="ROM File System" filter="gt" purpose="optional" class="plugin">
        <unit mrp="userlibandfileserver/fileserver/srom/base_f32_srom.mrp"/>
      </component>
      <component id="rofs" name="ROFS" filter="gt" purpose="optional" class="plugin">
        <unit bldFile="userlibandfileserver/fileserver/srofs" mrp="userlibandfileserver/fileserver/srofs/base_f32_srofs.mrp"/>
      </component>
      <component id="usbmsfs" name="USB Mass Storage File System" filter="gt" purpose="optional" class="plugin">
        <unit bldFile="userlibandfileserver/fileserver/smassstorage" mrp="userlibandfileserver/fileserver/smassstorage/base_f32_smassstorage.mrp"/>
      </component>
      <component id="usbhostmssrv" name="USB Host Mass Storage Server" filter="gt" introduced="^3" purpose="optional" class="plugin">
        <unit bldFile="userlibandfileserver/fileserver/shostmassstorage" mrp="userlibandfileserver/fileserver/shostmassstorage/base_f32_shostmassstorage.mrp"/>
      </component>
      <component id="fat32fs" name="FAT32 File System" filter="gt" purpose="optional" class="plugin">
        <unit bldFile="userlibandfileserver/fileserver/sfat32" mrp="userlibandfileserver/fileserver/sfat32/base_f32_sfat32.mrp"/>
      </component>
      <component id="fatfs" name="FAT File System" filter="gt" purpose="optional" class="plugin">
        <unit bldFile="userlibandfileserver/fileserver/sfat" mrp="userlibandfileserver/fileserver/sfat/base_f32_sfat.mrp"/>
      </component>
      <component id="compfs" name="Composite File System" filter="gt" purpose="optional" class="plugin">
        <unit bldFile="userlibandfileserver/fileserver/scomp" mrp="userlibandfileserver/fileserver/scomp/base_f32_scomp.mrp"/>
      </component>
    </collection>
    <collection id="halservices" name="HAL Services" level="framework">
      <component id="hal" name="User-Side Hardware Abstraction" introduced="6.0" purpose="optional">
        <unit bldFile="halservices/hal" mrp="halservices/hal/base_hal.mrp"/>
      </component>
    </collection>
    <collection id="textmodeshell" name="Text Mode Shell" level="test">
      <component id="e32wsrv" name="Text Window Server" purpose="optional">
        <unit bldFile="kernel/eka/ewsrv" mrp="kernel/eka/ewsrv/base_e32_ewsrv.mrp"/>
      </component>
      <component id="textshell" name="Text Shell" filter="gt" purpose="development">
        <unit bldFile="userlibandfileserver/fileserver/etshell" mrp="userlibandfileserver/fileserver/etshell/base_f32_eshell.mrp"/>
      </component>
    </collection>
    <collection id="baseapitest" name="Base API Tests" level="test">
      <component id="basesvs" name="Base Verification Suite" introduced="^2" purpose="development" filter="test">
        <unit mrp="baseapitest/basesvs/group/basesvs.mrp" bldFile="baseapitest/basesvs/group"/>
      </component>
    </collection>
    <collection id="kernelhwsrv_info" name="Kernel and Hardware Services Info" level="test">
      <component id="kernelhwsrv_metadata" name="Kernel and Hardware Services Metadata" class="config" introduced="^2" purpose="development" target="desktop">
        <unit mrp="kernelhwsrv_info/kernelhwsrv_metadata/kernelhwsrv_metadata.mrp"/>
      </component>
    </collection>
  </package>
</SystemDefinition>"""

classicui_pkg_def = """<?xml version="1.0" encoding="UTF-8"?>
<SystemDefinition schema="3.0.0">
  <package id="classicui" name="Classic UI" levels="base support server generic specific">
    <collection id="psln" name="Personalization" level="specific">
      <component id="pslnengine" filter="s60" name="Personalization Engine">
        <!-- <unit bldFile="psln/pslnengine/group"/> -->
      </component>
      <component id="pslnframework" filter="s60" name="Personalization Framework">
        <!-- <unit bldFile="psln/pslnframework"/> -->
      </component>
      <component id="pslnlibraryloaders" filter="s60" name="Personalization Library Loaders">
          <!-- no bld.inf, need to create one or remove component -->
      </component>
      <component id="pslnslidesetdialog" filter="s60" name="Personalization Slideset Dialog" class="plugin">
        <!-- <unit bldFile="psln/pslnslidesetdialog/group"/> -->
      </component>
      <component id="pslngsplugin" filter="s60" name="Personalization GS Plugin" class="plugin">
        <unit bldFile="psln/pslngsplugin/Group"/>
      </component>
      <component id="psln_help" filter="s60" name="Personalization Help">
        <unit bldFile="psln/help/group"/>
      </component>
      <component id="psln_build" filter="s60" name="Personalization Build">
             <!-- the Psln group bld.inf should be distributed into the individual components, or they should be collapsed in a single component -->
        <unit bldFile="psln/group"/>
      </component>
    </collection>
    <collection id="applicationinterworkingfw" name="Application Interworking Framework" level="generic">
      <component id="aifwservicehandler" filter="s60" name="Application Interworking Service Handle">
        <unit bldFile="applicationinterworkingfw/servicehandler/group"/>
      </component>
    </collection>
    <collection id="commonuis" name="Common UIs" level="specific">
      <component id="commonui" filter="s60" name="Common UI">
        <unit bldFile="commonuis/commonui/group"/>
      </component>
      <component id="commondialogs" filter="s60" name="Common Dialogs">
        <unit bldFile="commonuis/commondialogs/group"/>
        <!-- <unit bldFile="commonuis/commondialogs/group_test"/> -->
      </component>
    </collection>
    <collection id="uifw" name="UI Framework" level="server">
      <component id="uiklaf" filter="s60" name="Uikon Look-and-Feel">
        <unit bldFile=""/>
      </component>
      <component id="eikctl" filter="s60" name="Eikon Controls">
        <unit bldFile="uifw/eikctl/group"/>
      </component>
      <component id="avkon" filter="s60" name="Avkon">
        <unit bldFile="uifw/avkon/aknphysics/group"/>
        <unit bldFile="uifw/avkon/group"/>
        <unit bldFile="uifw/avkon/odeconf/group"/>
        <!-- <unit bldFile="uifw/avkon/aknhlist/group"/> -->
        <!-- <unit bldFile="uifw/avkon/aknkeyrotator/group"/> -->
        <!-- <unit bldFile="uifw/avkon/prebuilder"/> -->
        <!-- <unit bldFile="uifw/avkon/tsrc/bc/s60_sdkmcl/bctestmixmcl/group"/> -->
      </component>
      <component id="eikstd" filter="s60" name="Eikon Standard">
        <unit bldFile="uifw/eikstd/group"/>
      </component>
      <component id="aknglobalui" filter="s60" name="Avkon Global UI">
        <unit bldFile="uifw/aknglobalui/group"/>
      </component>
      <component id="ganes" filter="s60" name="Ganes">
        <unit bldFile="uifw/ganes/group"/>
      </component>
      <component id="uifw_test" filter="s60" name="UI Framework Test" purpose="development">
        <!-- <unit bldFile="uifw/tsrc/group"/> -->
      </component>
    </collection>
    <collection id="commonadapter" name="Common Adapter" level="support">
      <component id="commonadapter_build" filter="s60" name="Common Adapter Build">
        <unit bldFile="commonadapter/group"/>
      </component>
    </collection>
    <collection id="ode" name="Open Dynamics Engine" level="support">
      <component id="ode_build" filter="s60" name="ODE">
        <unit bldFile="ode/group"/>
      </component>
    </collection>
    <collection id="commonuisupport" name="Common UI Support" level="support">
      <component id="uikon" name="Uikon" introduced="6.0" purpose="mandatory">
        <unit bldFile="commonuisupport/uikon/group" mrp="commonuisupport/uikon/group/app-framework_uikon.mrp"/>
      </component>
      <component id="errorresolverdata" name="Error Resolver Data" purpose="mandatory">
        <unit bldFile="commonuisupport/errorresolverdata/group" mrp="commonuisupport/errorresolverdata/group/app-framework_errorresgt.mrp"/>
      </component>
      <component id="uilaf" name="UI Look and Feel" introduced="6.0" purpose="mandatory">
        <unit bldFile="commonuisupport/uilaf/GROUP" mrp="commonuisupport/uilaf/GROUP/app-framework_uiklafgt.mrp"/>
      </component>
      <component id="grid" name="Grid" purpose="optional">
        <unit bldFile="commonuisupport/grid/group" mrp="commonuisupport/grid/group/app-framework_grid.mrp"/>
      </component>
      <component id="uifwsdocs" name="UI Frameworks Documentation" purpose="development" class="doc">
        <unit mrp="commonuisupport/uifwsdocs/app-framework_documentation.mrp"/>
      </component>
    </collection>
    <collection id="lafagnosticuifoundation" name="Look-and-Feel Agnostic UI Foundation" level="base">
      <component id="cone" name="Control Environment" purpose="mandatory">
        <unit bldFile="lafagnosticuifoundation/cone/group" mrp="lafagnosticuifoundation/cone/group/app-framework_cone.mrp"/>
      </component>
      <component id="graphicseffects" name="Graphics Effects" introduced="9.2" purpose="optional">
        <unit bldFile="lafagnosticuifoundation/graphicseffects/group" mrp="lafagnosticuifoundation/graphicseffects/group/app-framework_gfxtranseffect.mrp"/>
      </component>
      <component id="uigraphicsutils" name="UI Graphics Utilities" purpose="mandatory">
        <unit bldFile="lafagnosticuifoundation/uigraphicsutils/group" mrp="lafagnosticuifoundation/uigraphicsutils/group/app-framework_egul.mrp"/>
      </component>
      <component id="clockanim" name="Clock" purpose="optional" class="plugin">
        <unit bldFile="lafagnosticuifoundation/clockanim/group" mrp="lafagnosticuifoundation/clockanim/group/app-framework_clock.mrp"/>
      </component>
      <component id="bmpanimation" name="BMP Animation" introduced="6.0" purpose="optional">
        <unit bldFile="lafagnosticuifoundation/bmpanimation/group" mrp="lafagnosticuifoundation/bmpanimation/group/app-framework_bmpanim.mrp"/>
      </component>
      <component id="animation" name="Animation" introduced="9.1" purpose="optional">
        <unit bldFile="lafagnosticuifoundation/animation/group" mrp="lafagnosticuifoundation/animation/group/app-framework_animation.mrp"/>
      </component>
    </collection>
    <collection id="classicui_info" name="Classic UI Info" level="specific">
       <!-- the multiple units in the API components need to be resolved -->
      <component id="classicui_pub" filter="s60" name="Classic UI Public Interfaces" class="api">
        <unit bldFile="classicui_pub/group"/>
      </component>
      <component id="classicui_plat" filter="s60" name="Classic UI Platform Interfaces" class="api">
        <unit bldFile="classicui_plat/group"/>
      </component>
      <component id="classicui_test" filter="s60" name="Classic UI Tests" purpose="development">
        <unit bldFile="classicui_plat/tsrc/group"/>
        <unit bldFile="classicui_pub/document_handler_api/tsrc/group"/>
        <unit bldFile="classicui_pub/server_application_api/tsrc/group"/>
        <!-- <unit bldFile="classicui_pub/tsrc/bc/apps/bctesttemplate/group"/> -->
        <!-- <unit bldFile="classicui_pub/tsrc/bc/apps/s60_sdk3.0/group"/> -->
        <!-- <unit bldFile="classicui_pub/tsrc/bc/apps/s60_sdk3.1/group"/> -->
        <!-- <unit bldFile="classicui_pub/tsrc/bc/apps/s60_sdk3.2/group"/> -->
        <!-- <unit bldFile="classicui_pub/tsrc/bc/apps/s60_sdk5.0/bctestpane/group"/> -->
        <!-- <unit bldFile="classicui_pub/tsrc/bc/apps/s60_sdk5.0/group"/> -->
        <!-- <unit bldFile="classicui_pub/tsrc/bc/group"/> -->
        <!-- <unit bldFile="classicui_plat/avkon_testability_api/tsrc/group"/> -->
        <!-- <unit bldFile="classicui_plat/extended_sounds_api/tsrc/group"/> -->
        <unit bldFile="classicui_plat/ganes_api/tsrc/group"/>
        <unit bldFile="classicui_plat/physics_api/tsrc/group"/>
      </component>
      <component id="classicui_metadata" name="Classic UI Metadata" class="config" introduced="^2" purpose="development" target="desktop">
        <unit mrp="classicui_info/classicui_metadata/classicui_metadata.mrp"/>
      </component>
    </collection>
  </package>
</SystemDefinition>"""

class_classic_ui = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.5.0//EN" "dtd/cxxClass.dtd" >
<cxxClass id="class_c_always_online_e_com_interface">
    <apiName>classicui</apiName>
    <shortdesc/>
    <cxxClassDetail>
        <cxxClassDefinition>
            <cxxClassAccessSpecifier value="public"/>
            <cxxClassAbstract/>
            <cxxClassDerivations>
                <cxxClassDerivation>
                    <cxxClassDerivationAccessSpecifier value="public"/>
                    <cxxClassBaseClass keyref="class_c_base">CBase</cxxClassBaseClass>
                </cxxClassDerivation>
            </cxxClassDerivations>
            <cxxClassAPIItemLocation>
                <cxxClassDeclarationFile name="filePath" value="W:/sf/mw/classicui/classicui_pub/aiw_service_handler_api/inc/AiwServiceHandler.h"/>
                <cxxClassDeclarationFileLine name="lineNumber" value="43"/>
                <cxxClassDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                <cxxClassDefinitionFileLineStart name="lineNumber" value="42"/>
                <cxxClassDefinitionFileLineEnd name="lineNumber" value="95"/>
            </cxxClassAPIItemLocation>
        </cxxClassDefinition>
        <apiDesc>
            <p>7.0  <xref href="class_r_e_com_session">REComSession</xref>, <xref href="class_c_active">CActive</xref> An AlwaysOnlineManager abstract class being representative of the concrete class which the client wishes to use. It acts as a base, for a real class to provide all the functionality that a client requires. It supplies instantiation &amp; destruction by using the ECom framework, and functional services by using the methods of the actual class. </p>
        </apiDesc>
    </cxxClassDetail>
</cxxClass>"""
    
class_c_always_online = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.5.0//EN" "dtd/cxxClass.dtd" >
<cxxClass id="class_c_always_online_e_com_interface">
    <apiName>CAlwaysOnlineEComInterface</apiName>
    <shortdesc/>
    <cxxClassDetail>
        <cxxClassDefinition>
            <cxxClassAccessSpecifier value="public"/>
            <cxxClassAbstract/>
            <cxxClassDerivations>
                <cxxClassDerivation>
                    <cxxClassDerivationAccessSpecifier value="public"/>
                    <cxxClassBaseClass keyref="class_c_base">CBase</cxxClassBaseClass>
                </cxxClassDerivation>
            </cxxClassDerivations>
            <cxxClassAPIItemLocation>
                <cxxClassDeclarationFile name="filePath" value="D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h"/>
                <cxxClassDeclarationFileLine name="lineNumber" value="43"/>
                <cxxClassDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                <cxxClassDefinitionFileLineStart name="lineNumber" value="42"/>
                <cxxClassDefinitionFileLineEnd name="lineNumber" value="95"/>
            </cxxClassAPIItemLocation>
        </cxxClassDefinition>
        <apiDesc>
            <p>7.0  <xref href="class_r_e_com_session">REComSession</xref>, <xref href="class_c_active">CActive</xref> An AlwaysOnlineManager abstract class being representative of the concrete class which the client wishes to use. It acts as a base, for a real class to provide all the functionality that a client requires. It supplies instantiation &amp; destruction by using the ECom framework, and functional services by using the methods of the actual class. </p>
        </apiDesc>
    </cxxClassDetail>
    <cxxClassNestedStruct keyref="class_c_always_online_e_com_interface">CAlwaysOnlineEComInterface</cxxClassNestedStruct>
    <cxxTypedef id="class_c_always_online_e_com_interface_1a73319f9960b3243e25a8a4c5ab41e3ca">
        <apiName>TAlwaysOnlineManagerInterfaceInitParams</apiName>
        <shortdesc/>
        <cxxTypedefDetail>
            <cxxTypedefDefinition>
                <cxxTypedefAccessSpecifier value="public"/>
                <cxxTypedefDeclaredType>struct <apiRelation keyref="struct_c_always_online_e_com_interface_1_1___c_e_com_interface_init_params">CAlwaysOnlineEComInterface::_CEComInterfaceInitParams</apiRelation>
                </cxxTypedefDeclaredType>
                <cxxTypedefScopedName>CAlwaysOnlineEComInterface</cxxTypedefScopedName>
                <cxxTypedefPrototype>struct CAlwaysOnlineEComInterface::_CEComInterfaceInitParams TAlwaysOnlineManagerInterfaceInitParams</cxxTypedefPrototype>
                <cxxTypedefNameLookup>CAlwaysOnlineEComInterface::TAlwaysOnlineManagerInterfaceInitParams</cxxTypedefNameLookup>
                <cxxTypedefAPIItemLocation>
                    <cxxTypedefDeclarationFile name="filePath" value="D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h"/>
                    <cxxTypedefDeclarationFileLine name="lineNumber" value="51"/>
                </cxxTypedefAPIItemLocation>
            </cxxTypedefDefinition>
            <apiDesc/>
        </cxxTypedefDetail>
    </cxxTypedef>
    <cxxFunction id="class_c_always_online_e_com_interface_1ad1417c7daef14ddd8cfbdfd87145b3f7">
        <apiName>NewL</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionInline/>
                <cxxFunctionDeclaredType>
                    <apiRelation keyref="class_c_always_online_e_com_interface">CAlwaysOnlineEComInterface</apiRelation> *</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CAlwaysOnlineEComInterface</cxxFunctionScopedName>
                <cxxFunctionPrototype>inline static CAlwaysOnlineEComInterface * NewL(TUid aId)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CAlwaysOnlineEComInterface::NewL(TUid)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>
                            <apiRelation keyref="class_t_uid">TUid</apiRelation>
                        </cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>aId</cxxFunctionParameterDeclarationName>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="55"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="38"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="42"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="class_c_always_online_e_com_interface_1a696eafb2803d687b3349c619ecfaeb75">
        <apiName>NewL</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionInline/>
                <cxxFunctionDeclaredType>
                    <apiRelation keyref="class_c_always_online_e_com_interface">CAlwaysOnlineEComInterface</apiRelation> *</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CAlwaysOnlineEComInterface</cxxFunctionScopedName>
                <cxxFunctionPrototype>inline static CAlwaysOnlineEComInterface * NewL(const TDesC8 &amp;aMatchString)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CAlwaysOnlineEComInterface::NewL(const TDesC8 &amp;)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>const <apiRelation keyref="class_t_des_c8">TDesC8</apiRelation> &amp;</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>aMatchString</cxxFunctionParameterDeclarationName>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="60"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="44"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="63"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="class_c_always_online_e_com_interface_1a2993500e22cbb8d55978a7ea36140e95">
        <apiName>~CAlwaysOnlineEComInterface</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionInline/>
                <cxxFunctionVirtual/>
                <cxxFunctionDestructor/>
                <cxxFunctionDeclaredType/>
                <cxxFunctionScopedName>CAlwaysOnlineEComInterface</cxxFunctionScopedName>
                <cxxFunctionPrototype>inline virtual ~CAlwaysOnlineEComInterface()</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CAlwaysOnlineEComInterface::~CAlwaysOnlineEComInterface()</cxxFunctionNameLookup>
                <cxxFunctionParameters/>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="63"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="30"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="36"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="class_c_always_online_e_com_interface_1a50f6b3a4ffb0d3751b7d81ccad3a1094">
        <apiName>ListImplementationsL</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionInline/>
                <cxxFunctionDeclaredType>void</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CAlwaysOnlineEComInterface</cxxFunctionScopedName>
                <cxxFunctionPrototype>inline static void ListImplementationsL(RImplInfoPtrArray &amp;aImplInfoArray)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CAlwaysOnlineEComInterface::ListImplementationsL(RImplInfoPtrArray &amp;)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>
                            <apiRelation keyref="class_r_pointer_array">RImplInfoPtrArray</apiRelation> &amp;</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>aImplInfoArray</cxxFunctionParameterDeclarationName>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="67"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="65"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="77"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="class_c_always_online_e_com_interface_1af9f8a32b8a8b46d6cc10cd49b674522e">
        <apiName>ListAllImplementationsL</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionInline/>
                <cxxFunctionDeclaredType>void</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CAlwaysOnlineEComInterface</cxxFunctionScopedName>
                <cxxFunctionPrototype>inline static void ListAllImplementationsL(RImplInfoPtrArray &amp;aImplInfoArray)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CAlwaysOnlineEComInterface::ListAllImplementationsL(RImplInfoPtrArray &amp;)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>
                            <apiRelation keyref="class_r_pointer_array">RImplInfoPtrArray</apiRelation> &amp;</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>aImplInfoArray</cxxFunctionParameterDeclarationName>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="68"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="79"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="82"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="class_c_always_online_e_com_interface_1a2d1bca910400ce5629c8ec39d5d58f10">
        <apiName>HandleServerCommandL</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionInline/>
                <cxxFunctionPureVirtual/>
                <cxxFunctionDeclaredType>
                    <apiRelation keyref="_always_online_manager_client_8cpp_1af7aafba448a6eaa6ce8801f88dcb5b90">TAny</apiRelation> *</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CAlwaysOnlineEComInterface</cxxFunctionScopedName>
                <cxxFunctionPrototype>inline virtual TAny * HandleServerCommandL(TInt aCommand, TDesC8 *aParameters=NULL)=0</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CAlwaysOnlineEComInterface::HandleServerCommandL(TInt,TDesC8 *)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>
                            <apiRelation keyref="_always_online_manager_client_8cpp_1abb88f5378e8305d934297176fe5fa298">TInt</apiRelation>
                        </cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>aCommand</cxxFunctionParameterDeclarationName>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>
                            <apiRelation keyref="class_t_des_c8">TDesC8</apiRelation> *</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>aParameters</cxxFunctionParameterDeclarationName>
                        <cxxFunctionParameterDefaultValue>NULL</cxxFunctionParameterDefaultValue>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="74"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="85"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="88"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="class_c_always_online_e_com_interface_1ac99836f705a34c72e7c26211f0d28523">
        <apiName>SetStatusQueryObject</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionInline/>
                <cxxFunctionDeclaredType>void</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CAlwaysOnlineEComInterface</cxxFunctionScopedName>
                <cxxFunctionPrototype>inline void SetStatusQueryObject(MAlwaysOnlineStatusQueryInterface *aStatusQueryObject)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CAlwaysOnlineEComInterface::SetStatusQueryObject(MAlwaysOnlineStatusQueryInterface *)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>
                            <apiRelation keyref="class_m_always_online_status_query_interface">MAlwaysOnlineStatusQueryInterface</apiRelation> *</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>aStatusQueryObject</cxxFunctionParameterDeclarationName>
                        <apiDefNote/>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="76"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="90"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="93"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="class_c_always_online_e_com_interface_1a143fe336b9c5a2c2a9b93b8ae971ba15">
        <apiName>InstanceUid</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionInline/>
                <cxxFunctionDeclaredType>
                    <apiRelation keyref="class_t_uid">TUid</apiRelation>
                </cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CAlwaysOnlineEComInterface</cxxFunctionScopedName>
                <cxxFunctionPrototype>inline TUid InstanceUid()</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CAlwaysOnlineEComInterface::InstanceUid()</cxxFunctionNameLookup>
                <cxxFunctionParameters/>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="78"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="95"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="98"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="class_c_always_online_e_com_interface_1a96b2319cd9cbabda8be3612d2592e7aa">
        <apiName>CAlwaysOnlineEComInterface</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="protected"/>
                <cxxFunctionInline/>
                <cxxFunctionConstructor/>
                <cxxFunctionDeclaredType/>
                <cxxFunctionScopedName>CAlwaysOnlineEComInterface</cxxFunctionScopedName>
                <cxxFunctionPrototype>inline CAlwaysOnlineEComInterface()</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CAlwaysOnlineEComInterface::CAlwaysOnlineEComInterface()</cxxFunctionNameLookup>
                <cxxFunctionParameters/>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="82"/>
                    <cxxFunctionDefinitionFile name="filePath" value="D:/EPOC/master/sf/mw/messagingmw/messagingfw/alwaysonline/AlwaysOnlineManager/src/AlwaysOnlineManagerClient.cpp"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="25"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="28"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc/>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxVariable id="class_c_always_online_e_com_interface_1a4daeab4bc33a838f0935854a7a2d7b29">
        <apiName>iDtor_ID_Key</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="private"/>
                <cxxVariableDeclaredType>
                    <apiRelation keyref="class_t_uid">TUid</apiRelation>
                </cxxVariableDeclaredType>
                <cxxVariableScopedName>CAlwaysOnlineEComInterface</cxxVariableScopedName>
                <cxxVariablePrototype>TUid iDtor_ID_Key</cxxVariablePrototype>
                <cxxVariableNameLookup>CAlwaysOnlineEComInterface::iDtor_ID_Key</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="86"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc/>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="class_c_always_online_e_com_interface_1a561dc71e162a5f2754d8758a56e5145f">
        <apiName>iStatusQueryObject</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="protected"/>
                <cxxVariableDeclaredType>
                    <apiRelation keyref="class_m_always_online_status_query_interface">MAlwaysOnlineStatusQueryInterface</apiRelation> *</cxxVariableDeclaredType>
                <cxxVariableScopedName>CAlwaysOnlineEComInterface</cxxVariableScopedName>
                <cxxVariablePrototype>MAlwaysOnlineStatusQueryInterface * iStatusQueryObject</cxxVariablePrototype>
                <cxxVariableNameLookup>CAlwaysOnlineEComInterface::iStatusQueryObject</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="D:/epoc32/include/platform/mw/AlwaysOnlineEComInterface.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="90"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc/>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxClassInherits>
        <cxxClassFunctionInherited keyref="class_c_base_1a240de7932690a4e987d75690b0b6f82b">CBase::CBase()</cxxClassFunctionInherited>
        <cxxClassFunctionInherited keyref="class_c_base_1ac0a06aeab68b3e01be81f9dd79e011c6">CBase::Delete(CBase *)</cxxClassFunctionInherited>
        <cxxClassFunctionInherited keyref="class_c_base_1aae681a54d9c9b10c7d42e7e32ff109d5">CBase::Extension_(TUint,TAny *&amp;,TAny *)</cxxClassFunctionInherited>
        <cxxClassFunctionInherited keyref="class_c_base_1af4c4965092a763b0856ccbfa3cf99eaf">CBase::operator new(TUint)</cxxClassFunctionInherited>
        <cxxClassFunctionInherited keyref="class_c_base_1ab9e5f557dea4db22886189926687ddc1">CBase::operator new(TUint,TAny *)</cxxClassFunctionInherited>
        <cxxClassFunctionInherited keyref="class_c_base_1aa464dd21494443ac109084ed03b81f28">CBase::operator new(TUint,TLeave)</cxxClassFunctionInherited>
        <cxxClassFunctionInherited keyref="class_c_base_1af8429815362d4df6fecd47179e0c5dfe">CBase::operator new(TUint,TLeave,TUint)</cxxClassFunctionInherited>
        <cxxClassFunctionInherited keyref="class_c_base_1a80505bdf8b1b20a2ed102307a78eeeeb">CBase::operator new(TUint,TUint)</cxxClassFunctionInherited>
        <cxxClassFunctionInherited keyref="class_c_base_1a1390361b94424be22bb2b1020eb400ea">CBase::~CBase()</cxxClassFunctionInherited>
    </cxxClassInherits>
</cxxClass>"""

ditamap = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="AlwaysOnlineManagerClient" title="AlwaysOnlineManagerClient">
    <cxxStructRef href="struct___array_util.xml#struct___array_util" navtitle="struct___array_util"/>
    <cxxClassRef href="class_b_trace.xml#class_b_trace" navtitle="class_b_trace">
        <cxxStructRef href="struct_b_trace_1_1_s_exec_extension.xml#struct_b_trace_1_1_s_exec_extension" navtitle="struct_b_trace_1_1_s_exec_extension"/>
    </cxxClassRef>
    <cxxClassRef href="class_c_active.xml#class_c_active" navtitle="class_c_active"/>
    <cxxClassRef href="class_c_active_scheduler.xml#class_c_active_scheduler" navtitle="class_c_active_scheduler">
        <cxxClassRef href="class_c_active_scheduler_1_1_t_cleanup_bundle.xml#class_c_active_scheduler_1_1_t_cleanup_bundle" navtitle="class_c_active_scheduler_1_1_t_cleanup_bundle"/>
    </cxxClassRef>
    <cxxClassRef href="class_c_active_scheduler_wait.xml#class_c_active_scheduler_wait" navtitle="class_c_active_scheduler_wait"/>
    <cxxClassRef href="class_c_always_online_disk_space_observer.xml#class_c_always_online_disk_space_observer" navtitle="class_c_always_online_disk_space_observer"/>
    <cxxClassRef href="class_c_always_online_e_com_interface.xml#class_c_always_online_e_com_interface" navtitle="class_c_always_online_e_com_interface">
        <cxxStructRef href="struct_c_always_online_e_com_interface_1_1___c_e_com_interface_init_params.xml#struct_c_always_online_e_com_interface_1_1___c_e_com_interface_init_params" navtitle="struct_c_always_online_e_com_interface_1_1___c_e_com_interface_init_params"/>
        <cxxStructRef href="nested_and_removed.xml"/>
    </cxxClassRef>
    <cxxClassRef href="class_c_always_online_manager.xml#class_c_always_online_manager" navtitle="class_c_always_online_manager"/>
    <cxxClassRef href="class_c_always_online_manager_server.xml#class_c_always_online_manager_server" navtitle="class_c_always_online_manager_server"/>
    <cxxClassRef href="test_class_defined_in_src_path.xml#test_class_defined_in_src_path" navtitle="test_class_defined_in_src_path"/>
</cxxAPIMap>"""

ditamap_classicui = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxAPIMap PUBLIC "-//NOKIA//DTD DITA C++ API Map Reference Type v0.5.0//EN" "dtd/cxxAPIMap.dtd" >
<cxxAPIMap id="ClassicUI" title="ClassicUI">
    <cxxClassRef href="class_c_always_online_e_com_interface" navtitle="test_class_defined_in_src_path"/>
    <cxxClassRef href="classicui_2.xml#test_class_defined_in_src_path" navtitle="test_class_defined_in_src_path"/>    
</cxxAPIMap>"""
