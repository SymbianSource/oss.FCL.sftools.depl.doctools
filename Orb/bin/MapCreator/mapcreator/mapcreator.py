from lxml import etree
from optparse import OptionParser
import logging
import sys
import os
import re

# TODO - functions to be replaced by equivalent funcs in orb lib module
# when mapcreator is integrated into main orb codeline
def xml_decl():
    return """<?xml version="1.0" encoding="UTF-8"?>"""
    
def doctype_identifier(doctype):
    """
    Return a doctype declaration string for a given doctype.
    """
    # DITA Doctypes Identifiers (no specific version number in identifier means latest DITA DTD version)
    if doctype == "map":
        return """<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">"""
    # TODO implement doctype identifiers for other doctypes
    else:
        return ""


__version__ = '0.1'


class PackageDefinionNotFoundError(Exception):
    "Raised if a package definition file could not be found"


class InvalidSystemDefintionError(Exception):
    "Raised if the System definition file is not valid"


class PackageLoader(object):
    def __init__(self, sysdefpath):
        self.sysdefpath = os.path.abspath(os.path.dirname(sysdefpath))
    
    def _get_pkgdef_path(self, pkgpath):
        return os.path.abspath(os.path.join(self.sysdefpath, pkgpath))
    
    def load(self, pkgpath):
        fullpkgpath = self._get_pkgdef_path(pkgpath)
        if not os.path.exists(fullpkgpath):
            raise PackageDefinionNotFoundError(
             '''Package definition "%s" was not found. 
                System definition directory is: "%s".
                Relative path in System definition was "%s"''' % (fullpkgpath, self.sysdefpath, pkgpath))
        return fullpkgpath


class MapCreator(object):
    def __init__(self, sysdef, pkgloader=PackageLoader):
        self.sysdef = sysdef        
        self.pkgloader = pkgloader(self.sysdef)
        self._tree = etree.parse(self.sysdef)
        self._create_root()

    def _create_root(self):
        sysmod = self._tree.find('/systemModel')
        if sysmod is None:
            raise InvalidSystemDefintionError("System definition does not have a 'systemModel' element")
        self.root = etree.Element("map", title=sysmod.attrib['name'], id=sysmod.attrib['name'])

    def getmap(self):
        self._load_definition()
        return self.root

    def _load_definition(self):
        for layer in self._tree.findall('//layer'):
            topicref = self._parse_layer(layer)
            self.root.append(topicref)
    
    def _parse_layer(self, layer):
        topicref = self._create_topichead(layer)
        for package in (p for p in layer.findall('package') if 'href' in p.attrib):
            pkgfile = etree.parse(self.pkgloader.load(package.attrib['href']))
            topicref.append(self._parse_package(pkgfile))
        return topicref

    def _parse_package(self, pkgtree):
        root = pkgtree.getroot().find('package')
        topichead = self._create_topichead(root)
        for collection in pkgtree.findall('//collection'):
            topichead.append(self._parse_collection(collection))
        return topichead
            
    def _parse_collection(self, collection):
        topichead = self._create_topichead(collection)
        for component in collection.findall('component'):
            topichead.append(self._parse_component(component))
        return topichead        

    def _parse_component(self, component):
        topichead = self._create_topichead(component)
        topichead.append(etree.Element(
                                      'topicref', 
                                      href="cmp_"+component.attrib['id']+'.ditamap',
                                      navtitle=component.attrib['id'],
                                      format='ditamap'
        ))

# Code for generating topicrefs from units currently not used        
#        for unit in component.findall('unit'):
#            href, title = self._get_component_info(unit)
#            topicref.append(etree.Element(
#                    'topicref', 
#                    href=href,
#                    navtitle=title,
#                    format='ditamap'
#            ))
        return topichead 

    def _create_topichead(self, element):
        name = element.attrib['id'] if 'name' not in element.attrib else element.attrib['name']             
        return etree.Element("topichead", id='_'+element.attrib['id'], navtitle=name)

# Code for generating topicrefs from units currently not used
#    def _get_component_info(self, unit):
#        def component_name(regex, attribname):
#            mrpname = re.search(regex, unit.attrib[attribname])
#            return mrpname.group(1) if mrpname else ""
#        if 'bldFile' in unit.attrib:
#            mrp = component_name(r".*/(.*)/group", 'bldFile')                        
#        else:
#            mrp = ""
#        title = mrp.replace("_", " ").capitalize()
#        return (mrp+".ditamap", title)


def runmapcreator(sysdefpath, output):
    mc = MapCreator(sysdefpath)
    map = mc.getmap()
    if output is None:
        print etree.tostring(map, pretty_print=True)
    else:
        f = open(output, 'w')
        f.write(xml_decl()+'\n')
        f.write(doctype_identifier("map")+'\n')
        f.write(etree.tostring(map, pretty_print=True))
        f.close()


def main():
    usage = "usage: %prog [options] [path to system definition]"
    parser = OptionParser(usage, version='%prog ' + __version__)
    parser.add_option("-l", type="int", dest="loglevel", default=logging.WARNING, 
                      help="Level of logging required")
    parser.add_option("-o", type="string", dest="output", default=None, 
                      help="Where to write the ditamap (defaults to stdout)")    
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        parser.error("Please supply a path to system definition")
    logging.basicConfig(level=options.loglevel, format='%(asctime)s %(levelname)-8s %(message)s', stream=sys.stdout)
    sysdefpath = os.path.abspath(args[0])
    if not os.path.exists(sysdefpath):
        parser.error('System definition file: "%s" does not exist' % sysdefpath)
    runmapcreator(sysdefpath, options.output)


if __name__ == '__main__':
    sys.exit(main())
    
    
    