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
try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree
import os
import logging
import weakref
import re
import xml


logger = logging.getLogger('orb.sysdef')


"""
When time to test with 2.6
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


class SystemDefinitionParserException(Exception):
    "Raised if a System defintion file is invalid"


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
        #except xml.parsers.expat.ExpatError, e:
        except Exception, e:
            raise SystemDefinitionParserException(str(e))
        root = tree.getroot()
        if "schema" not in root.attrib:
            raise SystemDefinitionParserException("Unknown XML file found, root node does not have a schema attribute")
        schema = root.attrib["schema"]
        if schema.startswith("2.0"):
            logger.debug("Creating a version 2 system definition parser, schema was: " + schema)
            self._parser = SystemDefinitionV2Parser(sysdeffile, pkgloader, tree)
        elif schema.startswith("3.0"):
            logger.debug("Creating a version 3 system definition parser, schema was: " + schema)
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
            logger.error("Package definition not found: %s" % str(e))
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
            logger.debug("Found bldFile: %s" % unit.attrib["bldFile"])        
        return bldinfs
            
    def _get_components(self, pkgel, bldFile_prefix):
        components = []
        for component in pkgel.findall(self._component):
            id, name = self._get_name_and_id(component)
            logger.debug("Adding component to components list: %s" % id)
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
            logger.debug("Adding collection to collections list: %s" % id)
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
                logger.debug("Adding package to packages list: %s" % pkg.attrib[self._id])
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


class SystemDefinition(object):
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
            logger.error("Package with package_id: %s, was not found" % package_id)
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
            logger.error("Component with an id of: %s, was not found" % component_id)
            return None
        if len(component.bldinfs) == 0:
            logger.info('No bldFiles found for: %s' % component_id)
            return None
        # Otherwise take the first one?
        bldinf = component.bldinfs[0]
        search = re.search(r".*/(.*)/group", bldinf, re.IGNORECASE)
        if not search:
            search = re.search(r".*/(.*)", bldinf)
            if not search:
                logger.error('Could not determine bldFile dir name from unit bldFile attribute: "%s"' % bldinf)
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
            logger.error("Component with id: '%s' not found" % component_id)
        else:
            for bf in component.bldinfs:
                logger.debug("Found bldFile (or directory): %s" % bf) 
                bf = bf.replace("\\","/")
                if bf.startswith(".."):
                    bf = bf.replace("..","")    
                if bf.startswith("/"):
                    bf = bf[1:]                   
                if bf.startswith("sf"):
                    bf = "%s/%s" % (os.path.splitdrive(self.cwd)[0], bf)
                else:
                    bf = "%s/sf/%s" % (os.path.splitdrive(self.cwd)[0], bf)  
                if not bf.endswith("bld.inf"):
                    bf = "%s/%s" % (bf, "bld.inf") 
                bf = os.path.normpath(bf)
                bf = bf.replace("\\","/")
                logger.debug("Saving bldFile as: %s" % bf)
                bldfiles.append(bf)       
        return bldfiles


################################################################
# Unit test code
################################################################
import unittest
from cStringIO import StringIO


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
            SystemDefinitionParser(StringIO("<boo><foo/>"))
            self.fail("An exception should have been raised")
        except SystemDefinitionParserException:
            pass # Expected

    def test_i_raise_an_exception_if_given_an_unkown_xml_file(self):
        try:
            SystemDefinitionParser(StringIO("<SystemDefinition></SystemDefinition>"))
            self.fail("An exception should have been raised")
        except SystemDefinitionParserException:
            pass # Expected

    def test_i_raise_an_exception_if_given_an_unsupported_SystemDefinition_version(self):
        for name, sysdef in self.unsupported_sysdefs.items():
            try:
                SystemDefinitionParser(StringIO(sysdef))
                self.fail("Should have raised a SystemDefinitionParserException as I do not support %s" % name)
            except SystemDefinitionParserException:
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
            "sysdefv2":         SystemDefinition(StringIO(sysdefv2), "y:\\"),
            "sysdefv3_dist":    SystemDefinition(StringIO(sysdefv3_distributed), "y:\\", pkgloader=MockPackageDefinitionLoader),
            "sysdefv3_nondist": SystemDefinition(StringIO(sysdefv3_nondistributed), "y:\\")
        }
        
    def test_i_return_the_list_of_packages(self):
        for name, sysdef in self.sysdefs.items():
            packages = sysdef.get_packages()
            self.assertEquals(len(packages), 2, msg="Correct number of packages were not found, using %s" % name)
            self.assertEquals(packages[0].id, "kernelhwsrv", msg="Incorrect package id found, using %s" % name)
            self.assertEquals(packages[1].id, "classicui", msg="Incorrect package id found, using %s" % name)

    def test_i_can_handle_invalid_href_urls(self):
        sysdefv3 = SystemDefinition(StringIO(sysdefv3_distributed_invalid_href), "y:\\", pkgloader=MockPackageDefinitionLoader)
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
            bldinf_path = "y:/sf/mw/classicui/psln/pslngsplugin/Group/bld.inf"
            self.assertEquals(bldfiles[0], bldinf_path, msg="%s != %s. using %s" % (bldfiles[0], bldinf_path, name))

    def test_i_can_handle_additional_dots_in_the_bldfile_path(self):
        for name, sysdef in self.sysdefs.items():
            bldfiles = sysdef.get_bldinfs("animation") # paths start with ../
            self.assertEquals(len(bldfiles), 1, msg="Incorrect number of bldfiles returned, using %s" % name)
            self.assertTrue(bldfiles[0].endswith("bld.inf"))
            bldinf_path = "y:/sf/mw/classicui/lafagnosticuifoundation/animation/group/bld.inf"
            self.assertEquals(bldfiles[0], bldinf_path, msg="%s != %s. using %s" % (bldfiles[0], bldinf_path, name))   

    def test_i_can_handle_a_slash_at_the_start_in_the_bldfile_path(self):
        for name, sysdef in self.sysdefs.items():
            bldfiles = sysdef.get_bldinfs("bmpanimation") # paths start with /
            self.assertEquals(len(bldfiles), 1, msg="Incorrect number of bldfiles returned, using %s" % name)
            self.assertTrue(bldfiles[0].endswith("bld.inf"))
            bldinf_path = "y:/sf/mw/classicui/lafagnosticuifoundation/bmpanimation/group/bld.inf"
            self.assertEquals(bldfiles[0], bldinf_path, msg="%s != %s. using %s" % (bldfiles[0], bldinf_path, name)) 
        
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
                        <unit bldFile="/mw/classicui/lafagnosticuifoundation/bmpanimation/group" mrp="mw/classicui/lafagnosticuifoundation/bmpanimation/group/app-framework_bmpanim.mrp"/>
                    </component>
                    <component name="animation" long-name="Animation" introduced="9.1" purpose="optional">
                        <unit bldFile="../mw/classicui/lafagnosticuifoundation/animation/group" mrp="mw/classicui/lafagnosticuifoundation/animation/group/app-framework_animation.mrp"/>
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
                        <unit bldFile="/mw/classicui/lafagnosticuifoundation/bmpanimation/group" mrp="lafagnosticuifoundation/bmpanimation/group/app-framework_bmpanim.mrp"/>
                    </component>
                    <component id="animation" name="Animation" introduced="9.1" purpose="optional">
                        <unit bldFile="../mw/classicui/lafagnosticuifoundation/animation/group" mrp="lafagnosticuifoundation/animation/group/app-framework_animation.mrp"/>
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
        <unit bldFile="/lafagnosticuifoundation/bmpanimation/group" mrp="lafagnosticuifoundation/bmpanimation/group/app-framework_bmpanim.mrp"/>
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