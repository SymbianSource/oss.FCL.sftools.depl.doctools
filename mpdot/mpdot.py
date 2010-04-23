"""
Created on Feb 25, 2010

@author: p2ross


Take as inmput the toc. Read for
<topicref format="ditamap" href="GUID-F59DFBA0-B60B-334A-9B18-4B4E1E756DFA.ditamap" navtitle="camera" />

Create in output dir 

out/dot_comp/camera_GUID-F59DFBA0-B60B-334A-9B18-4B4E1E756DFA/

As the DOT target.
Run DOT as a sub-process.
Then copy all of the contents except the index.html into:

out/dot_src/

Els stuff with ditamaps to dot_src/...

Then run DOT on input:
out/dot_src/<toc>.ditamap

Output:
out/dot_tgt/
"""

import os
import sys
from optparse import OptionParser, check_choice
import subprocess
import multiprocessing
try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree

import logging
#import pprint
import random
import time
import shutil
import unittest
#import xml
from cStringIO import StringIO

__version__ = '0.1.3'

"""
Nokia XHTML conversion:
$> ant ... -Dtranstype=xhtml.nokia -Dargs.input=INPUT_DITAMAP
Nokia Eclipse Help conversion:
$> ant ... -Dtranstype=eclipsehelp.nokia -Dargs.eclipse.version=VERSION -Dargs.eclipse.provider="Nokia Corporation" -Dargs.input=INPUT_DITAMAP
"""


CMD_BASE            = "ant -logger org.dita.dost.log.DITAOTBuildLogger -Doutercontrol=quiet"
CMD_PREFIX_INPUT    = "-Dargs.input="
CMD_PREFIX_OUTPUT   = "-Doutput.dir="
CMD_PREFIX_TEMP     = "-Ddita.temp.dir="
CMD_PREFIX_NERVOUS  = "echo"
#CMD_PREFIX_XSL      = "/xsl:plugins/cxxapiref/xsl/dita2xhtml.nokia.xsl "

DIR_DOT_COMPONENT   = 'dot_comp'
DIR_DOT_SOURCE      = 'dot_src'
DIR_TOC_TMP         = 'dot_toc_tmp'
DIR_DOT_TOC         = 'dot_toc'


def invokeDot(theDitaMapPath, theDirOut, argList, isNervous):
    myCmdList = []
    if isNervous:
        myCmdList.append(CMD_PREFIX_NERVOUS)
        time.sleep(0.25 * random.random())
    # Randomise the start time so that DOT does not create
    # duplicate temp directories (0.001 sec name resolution).
    time.sleep(1.0 * random.random())
    myCmdList.append(CMD_BASE)
    myCmdList.append('%s"%s"' % (CMD_PREFIX_INPUT, theDitaMapPath))
    myCmdList.append('%s"%s"' % (CMD_PREFIX_OUTPUT, theDirOut))
    myCmdList.append('%s"%s"' % (CMD_PREFIX_TEMP, 'temp/%s' % os.path.basename(theDirOut)))
    myCmdList.extend(['-D%s' % a for a in argList])
    myCmd = ' '.join(myCmdList).replace('\\', '/')
    if not os.path.exists(theDirOut):
        os.makedirs(theDirOut)
    print 'invokeDot: "%s"' % myCmd
    p = subprocess.Popen(
        myCmd,
        shell=True,
        bufsize=-1,
        # Direct stdout/stderr to a PIPE then forget them
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        #close_fds=True,
        )
    (stdOut, stdErr) = p.communicate()
    if len(stdErr) > 0:
        print 'stdErr for: %s -> %s' % (theDitaMapPath, theDirOut)
        print stdErr
    return p.returncode, theDirOut

def genCompMapNames(theToc):
    for ev, el in etree.iterparse(theToc):
        if el.tag == 'topicref':
            myRef = el.get('href', None)
            if myRef is not None and myRef.endswith('.ditamap'):
                logging.debug('genCompMapNames(): %s -> %s' % (myRef, el.get('navtitle')))
                yield myRef, el.get('navtitle')

def _copyDir(s, d, depth=0):
    """Recursive copy of all but the top level index.html."""
    assert(os.path.isdir(s))
    assert(os.path.isdir(d))
    for n in os.listdir(s):
        pS = os.path.join(s, n)
        pD = os.path.join(d, n)
        if os.path.isfile(pS) \
        and (depth > 1 or n.lower() != 'index.html'):
            try:
                shutil.copy(pS, pD)
            except (WindowsError, IOError), err:
                logging.error('_copyDirs(): %s' % err)
        elif os.path.isdir(pS):
            if not os.path.exists(pD):
                os.makedirs(pD)
            _copyDir(pS, pD, depth=depth+1)

def copyDirs(theResults, theOutDir):
    if not os.path.exists(theOutDir):
        os.makedirs(theOutDir)
    for c, d in theResults:
        if c == 0:
            print 'copyDirs(): "%s" to "%s"' % (os.path.basename(d), theOutDir)
            if not os.path.isdir(d):
                logging.error('copyDirs(): not a directory: %s' % d)
            elif not os.path.isdir(theOutDir):
                logging.error('copyDirs(): not a directory: %s' % theOutDir)
            else:
                _copyDir(d, theOutDir)
        else:
            logging.error('Not copying. Results code %d directory: %s' % (c, d))

def execute(inToc, outDir, argList, numJobs=0, nervous=False):
    inDir = os.path.dirname(inToc)
    outDirCmpDot = os.path.join(outDir, DIR_DOT_COMPONENT)
    if not os.path.exists(outDirCmpDot):
        os.makedirs(outDirCmpDot)
    if numJobs >= 1:
        myPool = multiprocessing.Pool(processes=numJobs)
    else:
        logging.info('Setting jobs to %d' % multiprocessing.cpu_count())
        myPool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    myTaskS = [
        (
            os.path.join(inDir, t[0]),
            os.path.join(outDirCmpDot, '%s_%s' % (t[1], t[0])),
            argList,
            nervous,
        )
        for t in genCompMapNames(inToc)
    ]
    myResults = [r.get() for r in [myPool.apply_async(invokeDot, t) for t in myTaskS]]
    copyDirs(myResults, os.path.join(outDir, DIR_DOT_SOURCE))
    return myResults

class DitamapLinkConverterError(Exception):
    """ Raised if an invalid toc is input """

class DitamapLinkConverter():
    
    def __init__(self, toc_path, out_dir):
        self.out_dir = os.path.abspath(out_dir)
        self.toc_path = os.path.abspath(toc_path)
        self.toc_dir = os.path.dirname(self.toc_path)
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
            
    def _convert_link_to_html(self, link):
        if link.attrib["href"].endswith(".xml"):
            link.attrib["href"] = link.attrib["href"].replace(".xml", ".html")
            link.attrib["scope"] = "peer"
            link.attrib["format"] = "html"
        return link
    
    def _convert_links(self, tree):
        for element in tree.getiterator():
            if element.attrib.get("href") != None:
                element = self._convert_link_to_html(element)
        return tree
    
    def _handle_map(self, ditamap):
        try:
            root = etree.parse(ditamap).getroot()
        except IOError, e:
            logging.error("Component map \"%s\" does not exist" % ditamap)
            return
        except Exception, e:
            logging.error("%s could not be parsed: %s\n" % (ditamap, str(e)))
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
        except Exception, e:
            raise DitamapLinkConverterError("%s could not be parsed: %s\n" % (self.toc_path, str(e)))
        component_maps = self._get_component_map_paths(tree)
        for component_map in component_maps:
            self._handle_map(component_map)
        shutil.copyfile(self.toc_path, self.out_dir+os.sep+os.path.basename(self.toc_path))

def publish_toc(toc_path, out_dir, argList, nervous):
    toc_name = os.path.basename(toc_path)
    tmp_out =  os.path.join(out_dir, DIR_TOC_TMP)
    dlc = DitamapLinkConverter(toc_path, tmp_out)
    dlc.convert()
    toc_to_publish = os.path.join(tmp_out, toc_name)
    out = os.path.join(out_dir, DIR_DOT_TOC)
    invokeDot(toc_to_publish, out, argList, nervous)
    final_destination = os.path.join(out_dir, DIR_DOT_SOURCE)
    if not os.path.exists(final_destination):
        os.makedirs(final_destination)
    try:
        shutil.copy(os.path.join(out, 'index.html'), final_destination)
    except IOError, err:
        logging.error('publish_toc(): %s' % str(err))
    
def main():
    usage = "usage: %prog [options] <DITA map> <output directory> -Doptions without the -D"
    parser = OptionParser(usage, version='%prog ' + __version__)
    parser.add_option(
            "-l", "--loglevel",
            type="int",
            dest="loglevel",
            default=30,
            help="Log Level (debug=10, info=20, warning=30, [error=40], critical=50) [default: %default]"
        )      
    parser.add_option(
            "-j", "--jobs",
            type="int",
            dest="jobs",
            default=0,
            help="Max processes when multiprocessing. Zero uses number of native CPUs [default: %default]"
        )      
    parser.add_option("-n", action="store_true", dest="nervous", default=False, 
                      help="Nervous mode (do no harm). [default: %default]")
    (options, args) = parser.parse_args()
    logging.basicConfig(level=options.loglevel, stream=sys.stdout)
    if len(args) < 1 or not os.path.isfile(args[0]):
        parser.print_help()
        parser.error("I can't do much without a path to the XML TOC.")
        return 1
    if len(args) < 2:
        parser.print_help()
        parser.error("I need an output path.")
        return 1
    # Dump out timestamp
    print 'Start time: %s' % time.ctime()
    execTime = time.clock()
    myResults = execute(args[0], args[1], args[2:], options.jobs, options.nervous)
    publish_toc(args[0], args[1], args[2:], options.nervous)
    print 'Number of DITA maps processed: %d' % len(myResults)
    print 'End time: %s' % time.ctime()
    print 'Elapsed time: %8.3f (s)' % (time.clock()-execTime)
    print 'Bye, bye...'

if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.exit(main())
    
class TestDitamapLinkConverter(unittest.TestCase):
    def setUp(self):
        self._create_test_dir()
        self.dlc = DitamapLinkConverter('', self.out_dir)
        
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
        self.assertTrue(link.get("format", None) and link.attrib["format"] == "html")
        
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
        converter = DitamapLinkConverter(os.getcwd()+os.sep+'toc.ditamap', self.out_dir)
        tree = etree.parse(StringIO(toc))
        paths = converter._get_component_map_paths(tree)
        expected = [os.getcwd()+os.sep+"GUID-F59DFBA0-B60B-334A-9B18-4B4E1E756DFA.ditamap"]       
        self.assertEquals(paths, expected)
        
    def test_i_raise_an_exception_if_i_am_given_an_invalid_toc(self):        
        invalid_toc_path = self.test_dir+os.sep+"invalid_toc.xml"
        self._write_string_to_file(invalid_toc, invalid_toc_path)
        dlc = DitamapLinkConverter(invalid_toc_path, self.out_dir)
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
    <cxxStructRef format="html" href="GUID-AE25CF37-B862-306B-B7B3-4A1226B83DA2.html" navtitle="_SChannels" scope="peer" />
    <cxxFileRef format="html" href="GUID-E1984316-685F-394E-B71A-9816E1495C1F.html" navtitle="wlanerrorcodes.h" scope="peer" />
    <cxxClassRef format="html" href="GUID-F795E994-BCB6-3040-872A-90F8ADFC75E7.html" navtitle="MWlanMgmtNotifications" scope="peer" />
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
