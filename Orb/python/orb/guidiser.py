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
import uuid
import os
import stat
import sys
import shutil
import xml
import logging
from optparse import OptionParser
try:
    from xml.etree import cElementTree as etree
except ImportError:
    from xml.etree import ElementTree as etree
import xml.etree.ElementTree
from cStringIO import StringIO
from lib import scan, xml_decl, doctype_identifier, XmlParser
from doxyidredirect import DoxyIdRedirect, ExceptionDoxyIdRedirectLookup


__version__ = "0.1"


logger = logging.getLogger('orb.guidiser')


class Guidiser(object):
    """
    A simple class that parses an xml file and converts the values of all
    id, href and keyref attributes to a 'GUID'.
    
    >>> guid = Guidiser()
    >>> root = guid.guidise(StringIO(cxxclass))
    >>> oldroot = etree.parse(StringIO(cxxclass)).getroot()
    >>> oldroot.attrib['id']
    'class_test'
    >>> root.attrib['id']
    'GUID-7D44FAFC-2C6A-3B1D-8EEA-558968414CCE'
    """
    # Publishing targets
    PT_MODE = 0
    PT_DITAOT = 1
    PUBLISHING_TARGETS = (PT_MODE, PT_DITAOT)
    
    def __init__(self, namespace='www.nokia.com', publishing_target=0, xmlparser=XmlParser(), doxyidredirect=DoxyIdRedirect(None)):
        self.namespace = self._get_namespace(namespace)
        self.set_publishing_target(publishing_target)
        self.xmlparser = xmlparser
        self.doxyidredirect = doxyidredirect
        
    def set_publishing_target(self, target):
        if not target in self.PUBLISHING_TARGETS:
            raise Exception('Invalid Publishing Target \"%s\"' % target)
        self._publishing_target = target
        
    def get_publishing_target(self):
        return self._publishing_target
        
    def _get_namespace(self, namespace, LEN_BYTES=16):
        if len(namespace) < LEN_BYTES:
            namespace = namespace + (' ' * (LEN_BYTES - len(namespace)))
        return uuid.UUID(bytes=namespace[:LEN_BYTES])
    
    def _get_guid(self, fqn):
        return ('GUID-%s' % (uuid.uuid3(self.namespace, fqn))).upper()
                        
    def _guidise_href(self, href, tag):
        if tag == "xref":
            return self._guidise_xref_href(href)
        else:
            # Tag is a topicref or topicref descended element
            return self._guidise_topicref_href(href)
    
    def _guidise_topicref_href(self, href):
        # Guidise an href that points to a ditamap
        # NOTE: the id of the map is assumed to be the same as the filename
        # (minus the ".ditamap" extension)
        if href.endswith(".ditamap"):
            guid = self._get_guid(href[:-len(".ditamap")])
            if self.get_publishing_target() == self.PT_DITAOT:
                guid += ".ditamap"
            return guid
        
        # Guidise an href that points to a topic
        # NOTE: Doxygen currently outputs "filepath#topicid" for topicref hrefs
        # the "#topicid" is redundant (as topicrefs can't reference below the topic level)
        # so will probably be removed from doxygen output at some point.
        filename = href.split('#')[0]
        id = os.path.splitext(filename)[0]
        fqn = None
        if not(id.lower() in ("test", "deprecated", "todo") or id.lower().find("namespace_") != -1):                
            try:
                filename, fqn = self.doxyidredirect.lookupId(id)
            except ExceptionDoxyIdRedirectLookup:
                logger.error("Could not lookup Fully Qualified APIName for id '%s' in href '%s'" % (id, href))
        #if the id was not found just guidise the id
        #this is just to make the id unique for mode
        guid = self._get_guid(fqn) if fqn else self._get_guid(id)
        if self.get_publishing_target() == self.PT_DITAOT:
            guid+=".xml"
        return guid
    
    def _guidise_xref_href(self, href):
        # Don't guidise references without hashes. Assume they are filepaths
        # to files other than ditatopics
        if href.find('#') == -1:
            return href
        # Doxygen currently outputs hrefs in the format autolink_8cpp.xml#autolink_8cpp_1ae0e289308b6d2cbb5c86e753741981dc
        # The right side of the # is not enough to extract the fully qualified name of the function because it is md5ed
        # Send the right side to doxyidredirect to get the fqn of the function			
        filename, id = href.split('#')
        fqn = None                
        if not(id.lower() in ("test", "deprecated", "todo") or id.lower().find("namespace_") != -1):                        
            try:
                fqn = self.doxyidredirect.lookupId(id)[1]
            except ExceptionDoxyIdRedirectLookup:
                logger.error("No API name for element id %s, guidising id instead" % id)
        guid = self._get_guid(fqn) if fqn else self._get_guid(id)
        basename, ext = os.path.splitext(filename)
        try:
            base_guid = self._get_guid(self.doxyidredirect.lookupId(basename)[1])
        except ExceptionDoxyIdRedirectLookup:
            base_guid = self._get_guid(basename)
            
        if self.get_publishing_target() == self.PT_DITAOT:
            return base_guid + ext + "#" + guid
        else:
            return guid
    
    def _guidise_id(self, id):
        try:
            _, fqn = self.doxyidredirect.lookupId(id)
            return self._get_guid(fqn)
        except ExceptionDoxyIdRedirectLookup:
            logger.debug("Didn't find a Fully Qualified APIName for id '%s'" % id)
            return self._get_guid(id)
    
    def guidise(self, xmlfile):
        #WORKAROUND: ElementTree provides no function to set prefixes and makes up its own if they are not set (ns0, ns1, ns2)
        xml.etree.ElementTree._namespace_map.update({ "http://dita.oasis-open.org/architecture/2005/": 'ditaarch' })
        try:
            root = etree.parse(xmlfile).getroot()
        except Exception, e:
            logger.error("%s could not be parsed: %s\n" % (xmlfile, str(e)))
            return None
        for child in root.getiterator():
            for key in [key for key in ('id', 'href', 'keyref') if key in child.attrib]:
                if key == 'id':
                    child.attrib['id'] = self._guidise_id(child.attrib['id'])
                elif key == 'href':
                    if 'format' in child.attrib and child.attrib['format'] == 'html':
                        continue
                    else:
                        #base_dir = os.path.dirname(xmlfile) if isinstance(xmlfile, str) else ""
                        child.attrib['href'] = self._guidise_href(child.attrib['href'], child.tag)
                elif key == 'keyref':
                    child.attrib['keyref'] = self._get_guid(child.attrib['keyref'])                    

        return root
    

def updatefiles(xmldir, publishing_target="ditaot"):
    publishing_target = Guidiser.PT_MODE if (publishing_target == "mode") else Guidiser.PT_DITAOT
    guidiser = Guidiser(publishing_target=publishing_target, doxyidredirect=DoxyIdRedirect(xmldir))
    for filepath in scan(xmldir):
        logger.debug('Guidising file \"%s\"' % filepath)
        root = guidiser.guidise(filepath)
        if root is not None:
            try:
                os.chmod(filepath, stat.S_IWRITE)
            except Exception, e:
                logger.error("Could not make file \"%s\" writable, error was \"%s\"" % (filepath, e))
                continue            
            with open(filepath, 'w') as f:
                f.write(xml_decl()+'\n')
                try:
                    doc_id = doctype_identifier(root.tag)
                except Exception, e:
                    logger.error("Could not write doctype identifier for file \"%s\", error was \"%s\""
                                  %(filepath, e))
                else:
                    f.write(doc_id+'\n')
                f.write(etree.tostring(root))        
                f.close()
                
def main():
    usage = "usage: %prog [options] <Path to the XML content>"
    parser = OptionParser(usage, version='%prog ' + __version__)
    parser.add_option("-p", dest="publishing_target", type="choice", choices=["mode", "ditaot"], default="mode", 
                      help="Publishing Target: mode|ditaot, [default: %default]")
    parser.add_option("-l", "--loglevel", type="int", default=30, help="Log Level (debug=10, info=20, warning=30, [error=40], critical=50)")      
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        parser.error("Please supply the path to the XML content")
    if options.loglevel:
        logging.basicConfig(level=options.loglevel)  
    updatefiles(args[0], options.publishing_target)


if __name__ == '__main__':
    sys.exit(main())

    
######################################
# Test code
######################################

class StubDoxyIdRedirect(object):
    def __init__(self, theDir):
        self.dict = {'struct_e_sock_1_1_t_addr_update':('struct_e_sock_1_1_t_addr_update.xml', 'ESock::TAddrUpdate'),
        'class_c_active_scheduler_1_1_t_cleanup_bundle':('class_c_active_scheduler_1_1_t_cleanup_bundle.xml', 'CActiveScheduler::TCleanupBundle'),
        'class_test':('class_test.xml', 'Test'),
        'class_test_1a99f2bbfac6c95612322b0f10e607ebe5':('cxxclass.xml', 'Test')}
    
    def lookupId(self, doxy_id):
        try:
            filename, fqn = self.dict[doxy_id]
            return (filename, fqn)
        except Exception, e:
            raise ExceptionDoxyIdRedirectLookup("StubException: %s" % e)


class TestGuidiser(unittest.TestCase):
    def setUp(self):
        self.guidiser = Guidiser(publishing_target=Guidiser.PT_MODE, doxyidredirect=StubDoxyIdRedirect('adir'))
        self.test_dir = "guidiser_test_dir"
        
    def _create_test_data(self):
        f = open("struct_e_sock_1_1_t_addr_update.xml", "w")
        f.write(struct_e_sock_1_1_t_addr_update)
        f.close()
        os.mkdir(self.test_dir)
        f = open(os.path.join(self.test_dir, "struct_e_sock_1_1_t_addr_update.xml"), "w")
        f.write(struct_e_sock_1_1_t_addr_update)
        f.close()        
        
    def _cleanup_test_data(self):
        os.remove("struct_e_sock_1_1_t_addr_update.xml")
        shutil.rmtree(self.test_dir)
        
    def test_i_can_get_and_set_a_PT(self):
        self.assertEqual(self.guidiser.get_publishing_target(), Guidiser.PT_MODE)
        self.guidiser.set_publishing_target(Guidiser.PT_DITAOT)
        self.assertEqual(self.guidiser.get_publishing_target(), Guidiser.PT_DITAOT)
        
    def test_i_raise_an_exception_when_trying_to_set_an_invalid_PT(self):
        self.assertRaises(Exception, self.guidiser.set_publishing_target, 2) 
        
    def test_i_update_root_elements_id(self):        
        root = self.guidiser.guidise(StringIO(cxxclass))
        self.assertEqual(root.attrib['id'], "GUID-56866D87-2CE9-31EA-8FA7-F4275FDBCB93")

    def test_i_continue_if_passed_an_invalid_file(self):
        try:
            self.guidiser.guidise(StringIO("<cxxclass><argh</cxxclass>"))
        except Exception:
            self.fail("I shouldnt have raised an exception.")

    def _test_keys_were_converted(self, key):
        root = self.guidiser.guidise(StringIO(cxxclass))
        for child in root.getiterator():
            if key in child.attrib:
                self.assertTrue(child.attrib[key].startswith('GUID'))        

    def test_i_update_a_subelements_id(self):
        self._test_keys_were_converted('id')

    def test_i_update_all_hrefs_with_a_guid(self):
        self._test_keys_were_converted('href')

    def test_i_update_all_keyrefs_with_a_guid(self):
        self._test_keys_were_converted('keyref')
                
    def test_based_fqn_and_one_param(self):
        self.assertTrue(self.guidiser._get_guid("RConnection::EnumerateConnections(TUint&)") ==
                        "GUID-18F9018F-78DE-3A7E-8363-B7CB101E7A99" 
                       )
        
    def test_based_fqn_and_muiltiple_params(self):
        self.assertTrue(self.guidiser._get_guid("RConnection::ProgressNotification(TSubConnectionUniqueId, TNifProgressBuf&, TRequestStatus&, TUint)") ==
                        "GUID-6E7005CF-4D8E-31CE-BAEA-21965ACC9C17" 
                       )
        
    def test_based_fqn_and_muiltiple_params_ones_a_default(self):
        self.assertTrue(self.guidiser._get_guid("RConnection::Open(RSocketServ& aSocketServer, TUint aConnectionType = KConnectionTypeDefault)") ==
                        "GUID-CE8F3FE7-14F2-3FB6-B04C-8596B5F80DFC" 
                       )
                
    def test_based_fqn_and_muiltiple_params_ones_templated(self):
        self.assertTrue(self.guidiser._get_guid("RConnection::DataReceivedNotificationRequest(TSubConnectionUniqueId, TUint, TPckg<TUint>&, TRequestStatus&)") ==
                        "GUID-9E056551-22C2-3F85-8E3D-C11FA3B46F07" 
                       )
        
    def test_based_toplevel_class(self):
        self.assertTrue(self.guidiser._get_guid("RConnection") ==
                        "GUID-BED8A733-2ED7-31AD-A911-C1F4707C67FD" 
                       )
        
    def test_target_id(self):
        self.assertTrue(self.guidiser._get_guid("ESock::TAddrUpdate") ==
                         "GUID-E72084E6-C1CE-3388-93F7-5B7A3F506C3B"
                         )
        
    def test_topicref_href_to_topic_for_mode(self):
        self.assertEquals(self.guidiser._guidise_href("struct_e_sock_1_1_t_addr_update.xml#struct_e_sock_1_1_t_addr_update", "topicref"),
                 "GUID-E72084E6-C1CE-3388-93F7-5B7A3F506C3B"
                 )
        
    def test_topicref_href_to_topic_for_ditaot(self):
        self.guidiser.set_publishing_target(Guidiser.PT_DITAOT)
        self._create_test_data()
        try:
            self.assertEquals(self.guidiser._guidise_href("struct_e_sock_1_1_t_addr_update.xml#struct_e_sock_1_1_t_addr_update", "topicref"),
                              "GUID-E72084E6-C1CE-3388-93F7-5B7A3F506C3B.xml")
        finally:
            self._cleanup_test_data()

                        
    def test_topicref_href_to_map_for_mode(self):
        self.assertEquals(self.guidiser._guidise_href("ziplib.ditamap", "topicref"),
                 "GUID-7C7A889C-AE2B-31FC-A5DA-A87019E1251D"
                 )
        
    def test_topicref_href_to_map_for_ditaot(self):
        self.guidiser.set_publishing_target(Guidiser.PT_DITAOT)
        self.assertEquals(self.guidiser._guidise_href("ziplib.ditamap", "topicref"),
                 "GUID-7C7A889C-AE2B-31FC-A5DA-A87019E1251D.ditamap"
                 )
                
    def test_xref_href_to_topic_in_same_file_for_mode(self):
        self.assertEquals(self.guidiser._guidise_href("struct_e_sock_1_1_t_addr_update.xml#struct_e_sock_1_1_t_addr_update", "xref"),
                 "GUID-E72084E6-C1CE-3388-93F7-5B7A3F506C3B"
                 )

    def test_xref_href_to_topic_in_same_file_for_ditaot(self):
        self.guidiser.set_publishing_target(Guidiser.PT_DITAOT)
        self.assertEquals(self.guidiser._guidise_href("struct_e_sock_1_1_t_addr_update.xml#struct_e_sock_1_1_t_addr_update", "xref"),
                 "GUID-E72084E6-C1CE-3388-93F7-5B7A3F506C3B.xml#GUID-E72084E6-C1CE-3388-93F7-5B7A3F506C3B"
                 )

    def test_xref_href_to_some_other_file_on_file_system(self):
        self.guidiser.set_publishing_target(Guidiser.PT_DITAOT)
        self.assertEquals(self.guidiser._guidise_href("../../documentation/RFCs/rfc3580.txt", "xref"),
                 "../../documentation/RFCs/rfc3580.txt"
                 )
    
    def test_i_guidise_the_id_of_a_fully_qualified_apiname(self):
        self.assertEquals(self.guidiser._guidise_id("struct_e_sock_1_1_t_addr_update"),
         "GUID-E72084E6-C1CE-3388-93F7-5B7A3F506C3B"
         )
         
    def test_id_guidise_the_id_something_that_is_not_a_fully_qualified_apiname(self):
        self.assertEquals(self.guidiser._guidise_id("commsdataobjects"),
         "GUID-2F2463E0-6C84-3FAB-8B60-57E57315FDEB"
         )
         
    def test_i_preserve_namespaces(self):  
        xml_in = """<reference ditaarch:DITAArchVersion="1.1" xmlns:ditaarch="http://dita.oasis-open.org/architecture/2005/" />"""
        xml_expected = """<reference ditaarch:DITAArchVersion="1.1" xmlns:ditaarch="http://dita.oasis-open.org/architecture/2005/" />"""
        root = self.guidiser.guidise(StringIO(xml_in))
        print "****", etree.tostring(root)
        self.assertEqual(etree.tostring(root), xml_expected)
        
class Testupdate_files(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = "guidisertestdata"
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_i_can_update_a_file_on_the_file_sys(self):
        def reference_file_handle(mode):
            return open(os.path.join(self.test_dir, "reference.dita"), mode) 
        os.mkdir(self.test_dir)
        f = reference_file_handle("w")
        f.write(filesys_cxxclass)
        f.close()
        updatefiles(self.test_dir)
        self.assertEquals(reference_file_handle("r").read(), filesys_cxxclass_guidised)
        
struct_e_sock_1_1_t_addr_update = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxStruct PUBLIC "-//NOKIA//DTD DITA C++ API Struct Reference Type v0.1.0//EN" "dtd/cxxStruct.dtd" >
<cxxStruct id="struct_coord_struct">
	<apiName>CoordStruct</apiName>
	<shortdesc/>
	<cxxStructDetail>
		<cxxStructDefinition>
			<cxxStructAccessSpecifier value="public"/>
			<cxxStructAPIItemLocation>
				<cxxStructDeclarationFile name="filePath" value="C:/wip/sysdoc/tools/Doxygen/branches/DITA/test/PaulRo/linking/src/restypedef.cpp"/>
				<cxxStructDeclarationFileLine name="lineNumber" value="10"/>
				<cxxStructDefinitionFile name="filePath" value="C:/wip/sysdoc/tools/Doxygen/branches/DITA/test/PaulRo/linking/src/restypedef.cpp"/>
				<cxxStructDefinitionFileLineStart name="lineNumber" value="9"/>
				<cxxStructDefinitionFileLineEnd name="lineNumber" value="15"/>
			</cxxStructAPIItemLocation>
		</cxxStructDefinition>
		<apiDesc>
			<p>A coordinate pair. </p>
		</apiDesc>
	</cxxStructDetail>
	<cxxVariable id="struct_coord_struct_1a183d7226fc5a8470ce9b9f04f9cb69bb">
		<apiName>x</apiName>
		<shortdesc/>
		<cxxVariableDetail>
			<cxxVariableDefinition>
				<cxxVariableAccessSpecifier value="public"/>
				<cxxVariableDeclaredType>float</cxxVariableDeclaredType>
				<cxxVariableScopedName>CoordStruct</cxxVariableScopedName>
				<cxxVariablePrototype>float x</cxxVariablePrototype>
				<cxxVariableNameLookup>CoordStruct::x</cxxVariableNameLookup>
				<cxxVariableAPIItemLocation>
					<cxxVariableDeclarationFile name="filePath" value="C:/wip/sysdoc/tools/Doxygen/branches/DITA/test/PaulRo/linking/src/restypedef.cpp"/>
					<cxxVariableDeclarationFileLine name="lineNumber" value="12"/>
				</cxxVariableAPIItemLocation>
			</cxxVariableDefinition>
			<apiDesc>
				<p>The x coordinate </p>
			</apiDesc>
		</cxxVariableDetail>
	</cxxVariable>
	<cxxVariable id="struct_coord_struct_1a1a5966a881bc3e76e9becf00639585ac">
		<apiName>y</apiName>
		<shortdesc/>
		<cxxVariableDetail>
			<cxxVariableDefinition>
				<cxxVariableAccessSpecifier value="public"/>
				<cxxVariableDeclaredType>float</cxxVariableDeclaredType>
				<cxxVariableScopedName>CoordStruct</cxxVariableScopedName>
				<cxxVariablePrototype>float y</cxxVariablePrototype>
				<cxxVariableNameLookup>CoordStruct::y</cxxVariableNameLookup>
				<cxxVariableAPIItemLocation>
					<cxxVariableDeclarationFile name="filePath" value="C:/wip/sysdoc/tools/Doxygen/branches/DITA/test/PaulRo/linking/src/restypedef.cpp"/>
					<cxxVariableDeclarationFileLine name="lineNumber" value="14"/>
				</cxxVariableAPIItemLocation>
			</cxxVariableDefinition>
			<apiDesc>
				<p>The y coordinate </p>
			</apiDesc>
		</cxxVariableDetail>
	</cxxVariable>
</cxxStruct>"""
        
filesys_cxxclass = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.1.0//EN" "dtd/cxxClass.dtd" >
<cxxClass id="class_c_active_scheduler_1_1_t_cleanup_bundle">
    <apiName>CActiveScheduler::TCleanupBundle</apiName>
    <shortdesc/>
    <cxxClassDetail>
        <cxxClassDefinition>
            <cxxClassAccessSpecifier value="private"/>
            <cxxClassAPIItemLocation>
                <cxxClassDeclarationFile name="filePath" value="K:/epoc32/include/e32base.h"/>
                <cxxClassDeclarationFileLine name="lineNumber" value="2832"/>
                <cxxClassDefinitionFile name="filePath" value="K:/sf/os/commsfw/datacommsserver/esockserver/csock/CS_CLI.CPP"/>
                <cxxClassDefinitionFileLineStart name="lineNumber" value="2831"/>
                <cxxClassDefinitionFileLineEnd name="lineNumber" value="2836"/>
            </cxxClassAPIItemLocation>
        </cxxClassDefinition>
        <apiDesc/>
    </cxxClassDetail>
    <cxxVariable id="class_c_active_scheduler_1_1_t_cleanup_bundle_1aaa7a637534aa0b9164dda2816be6fbf4">
        <apiName>iCleanupPtr</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="public"/>
                <cxxVariableDeclaredType>
                    <apiRelation keyref="class_c_cleanup">CCleanup</apiRelation> *</cxxVariableDeclaredType>
                <cxxVariableScopedName>CActiveScheduler::TCleanupBundle</cxxVariableScopedName>
                <cxxVariablePrototype>CCleanup * iCleanupPtr</cxxVariablePrototype>
                <cxxVariableNameLookup>CActiveScheduler::TCleanupBundle::iCleanupPtr</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="K:/epoc32/include/e32base.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="2834"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc/>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="class_c_active_scheduler_1_1_t_cleanup_bundle_1ad750b8dbf966def2486a52b6c3d236fc">
        <apiName>iDummyInt</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="public"/>
                <cxxVariableDeclaredType>
                    <apiRelation keyref="_c_s___c_l_i_8_c_p_p_1abb88f5378e8305d934297176fe5fa298">TInt</apiRelation>
                </cxxVariableDeclaredType>
                <cxxVariableScopedName>CActiveScheduler::TCleanupBundle</cxxVariableScopedName>
                <cxxVariablePrototype>TInt iDummyInt</cxxVariablePrototype>
                <cxxVariableNameLookup>CActiveScheduler::TCleanupBundle::iDummyInt</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="K:/epoc32/include/e32base.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="2835"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc/>
        </cxxVariableDetail>
    </cxxVariable>
</cxxClass>"""

filesys_cxxclass_guidised = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.6.0//EN" "dtd/cxxClass.dtd">
<cxxClass id="GUID-83FD90ED-B2F7-3ED5-ABC5-83ED6A3F1C2F">
    <apiName>CActiveScheduler::TCleanupBundle</apiName>
    <shortdesc />
    <cxxClassDetail>
        <cxxClassDefinition>
            <cxxClassAccessSpecifier value="private" />
            <cxxClassAPIItemLocation>
                <cxxClassDeclarationFile name="filePath" value="K:/epoc32/include/e32base.h" />
                <cxxClassDeclarationFileLine name="lineNumber" value="2832" />
                <cxxClassDefinitionFile name="filePath" value="K:/sf/os/commsfw/datacommsserver/esockserver/csock/CS_CLI.CPP" />
                <cxxClassDefinitionFileLineStart name="lineNumber" value="2831" />
                <cxxClassDefinitionFileLineEnd name="lineNumber" value="2836" />
            </cxxClassAPIItemLocation>
        </cxxClassDefinition>
        <apiDesc />
    </cxxClassDetail>
    <cxxVariable id="GUID-903F7E6D-EFFE-3A37-9348-B9FE3A27AF4A">
        <apiName>iCleanupPtr</apiName>
        <shortdesc />
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="public" />
                <cxxVariableDeclaredType>
                    <apiRelation keyref="GUID-3BB23EB1-2F65-378D-918B-1FBBD6E46C90">CCleanup</apiRelation> *</cxxVariableDeclaredType>
                <cxxVariableScopedName>CActiveScheduler::TCleanupBundle</cxxVariableScopedName>
                <cxxVariablePrototype>CCleanup * iCleanupPtr</cxxVariablePrototype>
                <cxxVariableNameLookup>CActiveScheduler::TCleanupBundle::iCleanupPtr</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="K:/epoc32/include/e32base.h" />
                    <cxxVariableDeclarationFileLine name="lineNumber" value="2834" />
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc />
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="GUID-DA4580F4-EBCC-3FA2-A856-810EAFC82236">
        <apiName>iDummyInt</apiName>
        <shortdesc />
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="public" />
                <cxxVariableDeclaredType>
                    <apiRelation keyref="GUID-1A4B29B0-5E06-39E5-A0A8-4A33E093C872">TInt</apiRelation>
                </cxxVariableDeclaredType>
                <cxxVariableScopedName>CActiveScheduler::TCleanupBundle</cxxVariableScopedName>
                <cxxVariablePrototype>TInt iDummyInt</cxxVariablePrototype>
                <cxxVariableNameLookup>CActiveScheduler::TCleanupBundle::iDummyInt</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="K:/epoc32/include/e32base.h" />
                    <cxxVariableDeclarationFileLine name="lineNumber" value="2835" />
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc />
        </cxxVariableDetail>
    </cxxVariable>
</cxxClass>"""
        
cxxclass = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.1.0//EN" "dtd/cxxClass.dtd" >
<cxxClass id="class_test">
	<apiName>Test</apiName>
	<shortdesc/>
	<cxxClassDetail>
		<cxxClassDefinition>
			<cxxClassAccessSpecifier value="public"/>
			<cxxClassAPIItemLocation>
				<cxxClassDeclarationFile name="filePath" value="C:/wip/sysdoc/tools/Doxygen/branches/DITA/test/PaulRo/linking/src/autolink.cpp"/>
				<cxxClassDeclarationFileLine name="lineNumber" value="59"/>
				<cxxClassDefinitionFile name="filePath" value="C:/wip/sysdoc/tools/Doxygen/branches/DITA/test/PaulRo/linking/src/autolink.cpp"/>
				<cxxClassDefinitionFileLineStart name="lineNumber" value="58"/>
				<cxxClassDefinitionFileLineEnd name="lineNumber" value="74"/>
			</cxxClassAPIItemLocation>
		</cxxClassDefinition>
		<apiDesc>
        <p>Points to function <xref href="class_test.xml#class_test_1a99f2bbfac6c95612322b0f10e607ebe5">Test()</xref></p>
		</apiDesc>
	</cxxClassDetail>
	<cxxFunction id="class_test_1a99f2bbfac6c95612322b0f10e607ebe5">
		<apiName>Test</apiName>
		<shortdesc/>
		<cxxFunctionDetail>
			<cxxFunctionDefinition>
				<cxxFunctionAccessSpecifier value="public"/>
				<cxxFunctionConstructor/>
				<cxxFunctionDeclaredType/>
				<cxxFunctionScopedName>Test</cxxFunctionScopedName>
				<cxxFunctionPrototype>Test()</cxxFunctionPrototype>
				<cxxFunctionNameLookup>Test::Test()</cxxFunctionNameLookup>
				<cxxFunctionParameters/>
				<cxxFunctionAPIItemLocation>
					<cxxFunctionDeclarationFile name="filePath" value="C:/wip/sysdoc/tools/Doxygen/branches/DITA/test/PaulRo/linking/src/autolink.cpp"/>
					<cxxFunctionDeclarationFileLine name="lineNumber" value="61"/>
					<cxxFunctionDefinitionFile name="filePath" value="C:/wip/sysdoc/tools/Doxygen/branches/DITA/test/PaulRo/linking/src/autolink.cpp"/>
					<cxxFunctionDefinitionFileLineStart name="lineNumber" value="77"/>
					<cxxFunctionDefinitionFileLineEnd name="lineNumber" value="77"/>
				</cxxFunctionAPIItemLocation>
			</cxxFunctionDefinition>
			<apiDesc>
				<p>details. </p>
			</apiDesc>
		</cxxFunctionDetail>
	</cxxFunction>
</cxxClass>""" 