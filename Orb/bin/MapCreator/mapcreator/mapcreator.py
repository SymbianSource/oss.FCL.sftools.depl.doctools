from lxml import etree
from optparse import OptionParser
import logging
import sys
import os
import re


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
    
    
class ComponentMapLoader(object):
    def __init__(self, cmp_map_dir):
        self.cmp_map_dir = cmp_map_dir
        
    def load(self, cmp_map_name):
        cmp_map_path = self.cmp_map_dir+os.sep+cmp_map_name
        return cmp_map_path if os.path.exists(cmp_map_path) else None
        

class MapCreator(object):
    def __init__(self, sysdef, cmp_map_dir, pkgloader=PackageLoader, cmpmaploader=ComponentMapLoader):
        self.sysdef = sysdef        
        self.cmp_map_dir = cmp_map_dir
        self.pkgloader = pkgloader(self.sysdef)
        self.cmpmaploader = cmpmaploader(self.cmp_map_dir)
        self._tree = etree.parse(self.sysdef)
        self._create_root()
        
    def _log_debug_msg(self, element):
        logging.debug('Parsing %s: %s' % (element.tag, element.attrib.get('id', 'No id in %s' % element.tag)))

    def _create_root(self):
        sysmod = self._tree.find('/systemModel')
        if sysmod is None:
            raise InvalidSystemDefintionError("System definition does not have a 'systemModel' element")
        self.root = etree.Element("map", title=sysmod.attrib['name'], id=sysmod.attrib['name'])
        
    def _create_topichead(self, element):
        name = element.attrib['id'] if 'name' not in element.attrib else element.attrib['name']             
        return etree.Element("topichead", id=element.attrib['id'], navtitle=name)        

    def _load_definition(self):
        for layer in self._tree.findall('//layer'):
            topicref = self._parse_layer(layer)
            self.root.append(topicref)
    
    def _parse_layer(self, layer):
        self._log_debug_msg(layer)
        topichead = self._create_topichead(layer)            
        for package in layer.findall('package'):
            try:
                pkgtree = etree.parse(self.pkgloader.load(package.attrib['href']))  # Package is defined in a 
                package = pkgtree.getroot().find('package')                         # package definition file
            except KeyError:    # OK - Package is defined within layer
                pass                
            except PackageDefinionNotFoundError, e: # Package is defined in a package definition file 
                logging.error(e)                    # that doesn't exist; Ignore this package and continue
                continue                
            except etree.XMLSyntaxError, e:                                # Invalid package definition.
                logging.error('Invalid package definition \"%s\": %s' %         # Ignore this package and continue
                              (package.attrib.get('id', 'No id in package'), e))
                continue                    
            topichead.append(self._parse_package(package))
        return topichead
    
    def _parse_package(self, package):
        self._log_debug_msg(package)
        topichead = self._create_topichead(package)
        for collection in package.findall('collection'):
            topichead.append(self._parse_collection(collection))
        return topichead
            
    def _parse_collection(self, collection):
        self._log_debug_msg(collection)
        topichead = self._create_topichead(collection)
        for component in collection.findall('component'):
            topichead.append(self._parse_component(component))
        return topichead        

    def _parse_component(self, component):
        self._log_debug_msg(component)
        topichead = self._create_topichead(component)
        for unit in component.findall('unit'):
            topicref = self._parse_unit(unit)
            if topicref is not None:
                topichead.append(topicref)
        return topichead 

    def _parse_unit(self, unit):
        # Create link to component level map. This is a map that is named after an output directory
        # in the SBS build dir. The output dir name is taken from the bld.inf directory by SBS.
        if not 'bldFile' in unit.attrib:
            logging.info('No bldFile attribute in unit, assuming no bld dir maps to link to')
            return 
        
        search = re.search(r".*/(.*)/group", unit.attrib['bldFile'])
        if not search:
            search = re.search(r".*/(.*)", unit.attrib['bldFile'])
            if not search:
                logging.error('Could not determine bldFile dir name from unit bldFile attribute: \"%s\"'
                              % unit.attrib['bldFile'])
                return 
        
        bldfile_dir_name = search.group(1)
        component_map_name = 'cmp_'+bldfile_dir_name+'.ditamap'   
        if self.cmpmaploader.load(component_map_name) is not None:  # If the component map that matches the                             
            return etree.Element('topicref',                        # name exists then create link to it,
                                  href=component_map_name,          # (otherwise don't create link to non-existant maps)
                                  navtitle=bldfile_dir_name,
                                  format='ditamap')
        else:
            return None
        
    def getmap(self):
        self._load_definition()
        return self.root        


def runmapcreator(sysdefpath, component_map_dir, output):
    mc = MapCreator(sysdefpath, component_map_dir)
    map = mc.getmap()
    if output is None:
        print etree.tostring(map, pretty_print=True)
    else:
        f = open(output, 'w')
        f.write("""<?xml version="1.0" encoding="UTF-8"?>"""+'\n')
        f.write("""<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">"""+'\n')
        f.write(etree.tostring(map, pretty_print=True))
        f.close()


def main():
    usage = "usage: %prog [options] [path to system definition] [component_map_dir]"
    parser = OptionParser(usage, version='%prog ' + __version__)
    parser.add_option("-l", type="int", dest="loglevel", default=logging.WARNING, 
                      help="Level of logging required")
    parser.add_option("-o", type="string", dest="output", default=None, 
                      help="Where to write the ditamap (defaults to stdout)")    
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.print_help()
        parser.error("Argument missing")
    logging.basicConfig(level=options.loglevel, format='%(asctime)s %(levelname)-8s %(message)s', stream=sys.stdout)
    sysdefpath = os.path.abspath(args[0])
    component_map_dir = os.path.abspath(args[1])
    if not os.path.exists(sysdefpath):
        parser.error('System definition file: "%s" does not exist' % sysdefpath)
    if not os.path.exists(component_map_dir):
        parser.error('Component map dir: "%s" does not exist' % component_map_dir)        
    runmapcreator(sysdefpath, component_map_dir, options.output)


if __name__ == '__main__':
    sys.exit(main())
    
    
    