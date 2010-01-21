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
from xml.etree import ElementTree as etree
from cStringIO import StringIO
from lib import scan, main, xml_decl, doctype_identifier


__version__ = "0.1"


class Guidiser(object):
    """
    A simple class that parses an xml file and converts the values of all
    id, href and keyref attributes to a 'GUID'.
    
    >>> guid = Guidiser()
    >>> root = guid.guidise(StringIO(cxxclass))
    >>> oldroot = etree.parse(StringIO(cxxclass)).getroot()
    >>> oldroot.attrib['id']
    'CP_class'
    >>> root.attrib['id']
    'GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E'
    """
    def __init__(self, namespace='www.nokia.com'):
        self.namespace = self._get_namespace(namespace)
    
    def _get_namespace(self, namespace, LEN_BYTES=16):
        if len(namespace) < LEN_BYTES:
            namespace = namespace + (' ' * (LEN_BYTES - len(namespace)))
        return uuid.UUID(bytes=namespace[:LEN_BYTES])
    
    def _get_guid(self, id):
        # Sometimes need to remove filepath and hash if id is an href
        id = id.split('#')[-1]
        # If id is an href and points to a ditamap, then the id of the map is filename minus ".ditamap"
        if id.endswith(".ditamap"):
            id = id[:-8]
        return ('GUID-%s' % (uuid.uuid3(self.namespace, id))).upper()
    
    def guidise(self, xmlfile):
        def _update_attrib(el, key):
            child.attrib[key] = self._get_guid(child.attrib[key])
        try:
            root = etree.parse(xmlfile).getroot()
        except xml.parsers.expat.ExpatError, e:
            sys.stderr.write("ERROR: %s could not be parser: %s\n" % (xmlfile, str(e)))
            return None
        for child in root.getiterator():
            for key in [key for key in ('id', 'href', 'keyref') if key in child.attrib]:
                _update_attrib(child, key) 
        return root


def updatefiles(xmldir):
    guidiser = Guidiser()
    for filepath in scan(xmldir):
        root = guidiser.guidise(filepath)
        if root is not None:
            os.chmod(filepath, stat.S_IWRITE)
            with open(filepath, 'w') as f:
                f.write(xml_decl()+'\n')
                f.write(doctype_identifier(root.tag)+'\n')
                f.write(etree.tostring(root))        


if __name__ == '__main__':
    sys.exit(main(updatefiles, __version__))
    
######################################
# Test code
######################################

class TestGuidiser(unittest.TestCase):
    def setUp(self):
        self.guidiser = Guidiser()
        
    def test_i_update_root_elements_id(self):        
        root = self.guidiser.guidise(StringIO(cxxclass))
        self.assertTrue(root.attrib['id'] == "GUID-25825EC4-341F-3EA4-94AA-7DCE380E6D2E")

    def test_i_continue_if_passed_an_invalid_file(self):
        try:
            self.guidiser.guidise(StringIO("<cxxclass><argh</cxxclass>"))
        except Exception:
            self.fail("I shouldnt have raised an exception")

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
        
    def test_based_toplevel_class_jarnos_output(self):
        self.assertTrue(self.guidiser._get_guid("RConnection") ==
                         "GUID-01926597-E8A1-35E5-A221-B4530CF1783F"
                         )
        
    def test_target_id(self):
        self.assertTrue(self.guidiser._get_guid("ESock::TAddrUpdate") ==
                         "GUID-E72084E6-C1CE-3388-93F7-5B7A3F506C3B"
                         )
        
    def test_map_href(self):
        self.assertTrue(self.guidiser._get_guid("ESock::struct_e_sock_1_1_t_addr_update.xml#ESock::TAddrUpdate") ==
                 "GUID-E72084E6-C1CE-3388-93F7-5B7A3F506C3B"
                 )
                
    def test_map_href_to_another_map(self):
        self.assertTrue(self.guidiser._get_guid("ziplib.ditamap") ==
                 "GUID-7C7A889C-AE2B-31FC-A5DA-A87019E1251D"
                 )
        
        
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
        f.write(reference)
        f.close()
        updatefiles(self.test_dir)
        self.assertEquals(reference_file_handle("r").read(), guidised_reference)
        
        
        
reference = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">
<reference id="CActiveScheduler::TCleanupBundle">
    <title>CActiveScheduler::TCleanupBundle</title>
    <shortdesc/>
    <refbody>
        <section>
            <ph>
            </ph>
        </section>
        <section/>
    </refbody>
    <reference id="CActiveScheduler::TCleanupBundle::iCleanupPtr">
        <title>iCleanupPtr</title>
        <shortdesc/>
        <refbody>
            <section>
                <ph>
                </ph>
            </section>
            <section/>
        </refbody>
    </reference>
    <reference id="CActiveScheduler::TCleanupBundle::iDummyInt">
        <title>iDummyInt</title>
        <shortdesc/>
        <refbody>
            <section>
            </section>
            <section/>
        </refbody>
    </reference>
</reference>
"""

guidised_reference = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">
<reference id="GUID-83FD90ED-B2F7-3ED5-ABC5-83ED6A3F1C2F">
    <title>CActiveScheduler::TCleanupBundle</title>
    <shortdesc />
    <refbody>
        <section>
            <ph>
            </ph>
        </section>
        <section />
    </refbody>
    <reference id="GUID-903F7E6D-EFFE-3A37-9348-B9FE3A27AF4A">
        <title>iCleanupPtr</title>
        <shortdesc />
        <refbody>
            <section>
                <ph>
                </ph>
            </section>
            <section />
        </refbody>
    </reference>
    <reference id="GUID-DA4580F4-EBCC-3FA2-A856-810EAFC82236">
        <title>iDummyInt</title>
        <shortdesc />
        <refbody>
            <section>
            </section>
            <section />
        </refbody>
    </reference>
</reference>"""
        
cxxclass = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<!DOCTYPE cxxClass PUBLIC "-//NOKIA//DTD DITA C++ API Class Reference Type v0.1.0//EN" "dtd/cxxClass.dtd" >
<cxxClass id="CP_class">
    <apiName>CP_class</apiName>
    <shortdesc/>
    <cxxClassDetail>
      <cxxClassNestedStruct keyref="CB_class">CB_class</cxxClassNestedStruct>
      <cxxClassNestedUnion keyref="CB_class">CB_class</cxxClassNestedUnion>
      <cxxClassNestedClass keyref="CB_class">CB_class</cxxClassNestedClass>    
        <cxxClassDefinition>
            <cxxClassAccessSpecifier value="public"/>
            <cxxClassAPIItemLocation>
                <cxxClassDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                <cxxClassDeclarationFileLine name="lineNumber" value="25"/>
                <cxxClassDefinitionFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                <cxxClassDefinitionFileLineStart name="lineNumber" value="21"/>
                <cxxClassDefinitionFileLineEnd name="lineNumber" value="168"/>
            </cxxClassAPIItemLocation>
        </cxxClassDefinition>
        <apiDesc>
            <p>CP_class_text. A link to a method, <xref href="CP_class::CPD_function(CPD_type_1)">CP_class::CPD_function(CPD_type_1)</xref>.</p>
        </apiDesc>
    </cxxClassDetail>
    <cxxFunction id="CP_class::CPD_function(CPD_type_1)">
        <apiName>CPD_function</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="private"/>
                <cxxFunctionDeclaredType>CPD_return</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CP_class</cxxFunctionScopedName>
                <cxxFunctionPrototype>CPD_return CPD_function(CPD_type_1 CPD_param_1)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CP_class::CPD_function(CPD_type_1)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>CPD_type_1</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>CPD_param_1</cxxFunctionParameterDeclarationName>
                        <apiDefNote>CPD_param_1_text </apiDefNote>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="33"/>
                    <cxxFunctionDefinitionFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc>
                <p>CPD_function_text. CPD_return CPD_return_text </p>
            </apiDesc>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="CP_class::CPC_function(CPC_type_1)">
        <apiName>CPC_function</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="private"/>
                <cxxFunctionDeclaredType>CPC_return</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CP_class</cxxFunctionScopedName>
                <cxxFunctionPrototype>CPC_return CPC_function(CPC_type_1 CPC_param_1)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CP_class::CPC_function(CPC_type_1)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>CPC_type_1</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>CPC_param_1</cxxFunctionParameterDeclarationName>
                        <apiDefNote>CPC_param_1_text </apiDefNote>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="39"/>
                    <cxxFunctionDefinitionFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc>
                <p>CPC_function_text. CPC_return CPC_return_text </p>
            </apiDesc>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="CP_class::CPF_function(CPF_type_1)">
        <apiName>CPF_function</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="protected"/>
                <cxxFunctionDeclaredType>CPF_return</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CP_class</cxxFunctionScopedName>
                <cxxFunctionPrototype>CPF_return CPF_function(CPF_type_1 CPF_param_1)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CP_class::CPF_function(CPF_type_1)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>CPF_type_1</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>CPF_param_1</cxxFunctionParameterDeclarationName>
                        <apiDefNote>CPF_param_1_text </apiDefNote>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="46"/>
                    <cxxFunctionDefinitionFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc>
                <p>CPF_function_text. CPF_return CPF_return_text </p>
            </apiDesc>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="CP_class::CPE_function(CPE_type_1)">
        <apiName>CPE_function</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="protected"/>
                <cxxFunctionDeclaredType>CPE_return</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CP_class</cxxFunctionScopedName>
                <cxxFunctionPrototype>CPE_return CPE_function(CPE_type_1 CPE_param_1)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CP_class::CPE_function(CPE_type_1)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>CPE_type_1</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>CPE_param_1</cxxFunctionParameterDeclarationName>
                        <apiDefNote>CPE_param_1_text </apiDefNote>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="52"/>
                    <cxxFunctionDefinitionFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc>
                <p>CPE_function_text. CPE_return CPE_return_text </p>
            </apiDesc>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="CP_class::CPB_function(CPB_type_1)">
        <apiName>CPB_function</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionDeclaredType>CPB_return</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CP_class</cxxFunctionScopedName>
                <cxxFunctionPrototype>CPB_return CPB_function(CPB_type_1 CPB_param_1)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CP_class::CPB_function(CPB_type_1)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>CPB_type_1</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>CPB_param_1</cxxFunctionParameterDeclarationName>
                        <apiDefNote>CPB_param_1_text </apiDefNote>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="59"/>
                    <cxxFunctionDefinitionFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc>
                <p>CPB_function_text. CPB_return CPB_return_text </p>
            </apiDesc>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="CP_class::CPA_function(CPA_type_1)">
        <apiName>CPA_function</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionDeclaredType>CPA_return</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CP_class</cxxFunctionScopedName>
                <cxxFunctionPrototype>CPA_return CPA_function(CPA_type_1 CPA_param_1)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CP_class::CPA_function(CPA_type_1)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>CPA_type_1</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>CPA_param_1</cxxFunctionParameterDeclarationName>
                        <apiDefNote>CPA_param_1_text </apiDefNote>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="65"/>
                    <cxxFunctionDefinitionFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc>
                <p>CPA_function_text. CPA_return CPA_return_text </p>
            </apiDesc>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="CP_class::CPH_function(CPH_type_1)">
        <apiName>CPH_function</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="protected"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionDeclaredType>CPH_return</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CP_class</cxxFunctionScopedName>
                <cxxFunctionPrototype>static CPH_return CPH_function(CPH_type_1 CPH_param_1)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CP_class::CPH_function(CPH_type_1)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>CPH_type_1</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>CPH_param_1</cxxFunctionParameterDeclarationName>
                        <apiDefNote>CPH_param_1_text </apiDefNote>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="76"/>
                    <cxxFunctionDefinitionFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc>
                <p>CPH_function_text. CPH_return CPH_return_text </p>
            </apiDesc>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="CP_class::CPG_function(CPG_type_1)">
        <apiName>CPG_function</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="protected"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionDeclaredType>CPG_return</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CP_class</cxxFunctionScopedName>
                <cxxFunctionPrototype>static CPG_return CPG_function(CPG_type_1 CPG_param_1)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CP_class::CPG_function(CPG_type_1)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>CPG_type_1</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>CPG_param_1</cxxFunctionParameterDeclarationName>
                        <apiDefNote>CPG_param_1_text </apiDefNote>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="82"/>
                    <cxxFunctionDefinitionFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc>
                <p>CPG_function_text. CPG_return CPG_return_text </p>
            </apiDesc>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="CP_class::CPJ_function(CPJ_type_1)">
        <apiName>CPJ_function</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="private"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionDeclaredType>CPJ_return</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CP_class</cxxFunctionScopedName>
                <cxxFunctionPrototype>static CPJ_return CPJ_function(CPJ_type_1 CPJ_param_1)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CP_class::CPJ_function(CPJ_type_1)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>CPJ_type_1</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>CPJ_param_1</cxxFunctionParameterDeclarationName>
                        <apiDefNote>CPJ_param_1_text </apiDefNote>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="89"/>
                    <cxxFunctionDefinitionFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc>
                <p>CPJ_function_text. CPJ_return CPJ_return_text </p>
            </apiDesc>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="CP_class::CPI_function(CPI_type_1)">
        <apiName>CPI_function</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="private"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionDeclaredType>CPI_return</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CP_class</cxxFunctionScopedName>
                <cxxFunctionPrototype>static CPI_return CPI_function(CPI_type_1 CPI_param_1)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CP_class::CPI_function(CPI_type_1)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>CPI_type_1</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>CPI_param_1</cxxFunctionParameterDeclarationName>
                        <apiDefNote>CPI_param_1_text </apiDefNote>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="95"/>
                    <cxxFunctionDefinitionFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc>
                <p>CPI_function_text. CPI_return CPI_return_text </p>
            </apiDesc>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="CP_class::CPL_function(CPL_type_1)">
        <apiName>CPL_function</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionDeclaredType>CPL_return</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CP_class</cxxFunctionScopedName>
                <cxxFunctionPrototype>static CPL_return CPL_function(CPL_type_1 CPL_param_1)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CP_class::CPL_function(CPL_type_1)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>CPL_type_1</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>CPL_param_1</cxxFunctionParameterDeclarationName>
                        <apiDefNote>CPL_param_1_text </apiDefNote>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="102"/>
                    <cxxFunctionDefinitionFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc>
                <p>CPL_function_text. CPL_return CPL_return_text </p>
            </apiDesc>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxFunction id="CP_class::CPK_function(CPK_type_1)">
        <apiName>CPK_function</apiName>
        <shortdesc/>
        <cxxFunctionDetail>
            <cxxFunctionDefinition>
                <cxxFunctionAccessSpecifier value="public"/>
                <cxxFunctionStorageClassSpecifierStatic/>
                <cxxFunctionDeclaredType>CPK_return</cxxFunctionDeclaredType>
                <cxxFunctionScopedName>CP_class</cxxFunctionScopedName>
                <cxxFunctionPrototype>static CPK_return CPK_function(CPK_type_1 CPK_param_1)</cxxFunctionPrototype>
                <cxxFunctionNameLookup>CP_class::CPK_function(CPK_type_1)</cxxFunctionNameLookup>
                <cxxFunctionParameters>
                    <cxxFunctionParameter>
                        <cxxFunctionParameterDeclaredType>CPK_type_1</cxxFunctionParameterDeclaredType>
                        <cxxFunctionParameterDeclarationName>CPK_param_1</cxxFunctionParameterDeclarationName>
                        <apiDefNote>CPK_param_1_text </apiDefNote>
                    </cxxFunctionParameter>
                </cxxFunctionParameters>
                <cxxFunctionAPIItemLocation>
                    <cxxFunctionDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDeclarationFileLine name="lineNumber" value="108"/>
                    <cxxFunctionDefinitionFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxFunctionDefinitionFileLineStart name="lineNumber" value="-1"/>
                    <cxxFunctionDefinitionFileLineEnd name="lineNumber" value="-1"/>
                </cxxFunctionAPIItemLocation>
            </cxxFunctionDefinition>
            <apiDesc>
                <p>CPK_function_text. CPK_return CPK_return_text </p>
            </apiDesc>
        </cxxFunctionDetail>
    </cxxFunction>
    <cxxVariable id="CP_class::CPN_name">
        <apiName>CPN_name</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="public"/>
                <cxxVariableDeclaredType>CPN_type</cxxVariableDeclaredType>
                <cxxVariableScopedName>CP_class</cxxVariableScopedName>
                <cxxVariablePrototype>CPN_type CPN_name</cxxVariablePrototype>
                <cxxVariableNameLookup>CP_class::CPN_name</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="114"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc>
                <p>CPN_text </p>
            </apiDesc>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="CP_class::CPM_name">
        <apiName>CPM_name</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="public"/>
                <cxxVariableDeclaredType>CPM_type</cxxVariableDeclaredType>
                <cxxVariableScopedName>CP_class</cxxVariableScopedName>
                <cxxVariablePrototype>CPM_type CPM_name</cxxVariablePrototype>
                <cxxVariableNameLookup>CP_class::CPM_name</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="116"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc>
                <p>CPM_text </p>
            </apiDesc>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="CP_class::CPP_name">
        <apiName>CPP_name</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="protected"/>
                <cxxVariableDeclaredType>CPP_type</cxxVariableDeclaredType>
                <cxxVariableScopedName>CP_class</cxxVariableScopedName>
                <cxxVariablePrototype>CPP_type CPP_name</cxxVariablePrototype>
                <cxxVariableNameLookup>CP_class::CPP_name</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="119"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc>
                <p>CPP_text </p>
            </apiDesc>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="CP_class::CPO_name">
        <apiName>CPO_name</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="protected"/>
                <cxxVariableDeclaredType>CPO_type</cxxVariableDeclaredType>
                <cxxVariableScopedName>CP_class</cxxVariableScopedName>
                <cxxVariablePrototype>CPO_type CPO_name</cxxVariablePrototype>
                <cxxVariableNameLookup>CP_class::CPO_name</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="121"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc>
                <p>CPO_text </p>
            </apiDesc>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="CP_class::CPR_name">
        <apiName>CPR_name</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="private"/>
                <cxxVariableDeclaredType>CPR_type</cxxVariableDeclaredType>
                <cxxVariableScopedName>CP_class</cxxVariableScopedName>
                <cxxVariablePrototype>CPR_type CPR_name</cxxVariablePrototype>
                <cxxVariableNameLookup>CP_class::CPR_name</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="124"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc>
                <p>CPR_text </p>
            </apiDesc>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="CP_class::CPQ_name">
        <apiName>CPQ_name</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="private"/>
                <cxxVariableDeclaredType>CPQ_type</cxxVariableDeclaredType>
                <cxxVariableScopedName>CP_class</cxxVariableScopedName>
                <cxxVariablePrototype>CPQ_type CPQ_name</cxxVariablePrototype>
                <cxxVariableNameLookup>CP_class::CPQ_name</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="126"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc>
                <p>CPQ_text </p>
            </apiDesc>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="CP_class::CPX_name">
        <apiName>CPX_name</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="private"/>
                <cxxVariableStorageClassSpecifierStatic/>
                <cxxVariableDeclaredType>CPX_type</cxxVariableDeclaredType>
                <cxxVariableScopedName>CP_class</cxxVariableScopedName>
                <cxxVariablePrototype>static CPX_type CPX_name</cxxVariablePrototype>
                <cxxVariableNameLookup>CP_class::CPX_name</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="132"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc>
                <p>CPX_text </p>
            </apiDesc>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="CP_class::CPW_name">
        <apiName>CPW_name</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="private"/>
                <cxxVariableStorageClassSpecifierStatic/>
                <cxxVariableDeclaredType>CPW_type</cxxVariableDeclaredType>
                <cxxVariableScopedName>CP_class</cxxVariableScopedName>
                <cxxVariablePrototype>static CPW_type CPW_name</cxxVariablePrototype>
                <cxxVariableNameLookup>CP_class::CPW_name</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="134"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc>
                <p>CPW_text </p>
            </apiDesc>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="CP_class::CPV_name">
        <apiName>CPV_name</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="protected"/>
                <cxxVariableStorageClassSpecifierStatic/>
                <cxxVariableDeclaredType>CPV_type</cxxVariableDeclaredType>
                <cxxVariableScopedName>CP_class</cxxVariableScopedName>
                <cxxVariablePrototype>static CPV_type CPV_name</cxxVariablePrototype>
                <cxxVariableNameLookup>CP_class::CPV_name</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="137"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc>
                <p>CPV_text </p>
            </apiDesc>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="CP_class::CPU_name">
        <apiName>CPU_name</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="protected"/>
                <cxxVariableStorageClassSpecifierStatic/>
                <cxxVariableDeclaredType>CPU_type</cxxVariableDeclaredType>
                <cxxVariableScopedName>CP_class</cxxVariableScopedName>
                <cxxVariablePrototype>static CPU_type CPU_name</cxxVariablePrototype>
                <cxxVariableNameLookup>CP_class::CPU_name</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="139"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc>
                <p>CPU_text </p>
            </apiDesc>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="CP_class::CPT_name">
        <apiName>CPT_name</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="public"/>
                <cxxVariableStorageClassSpecifierStatic/>
                <cxxVariableDeclaredType>CPT_type</cxxVariableDeclaredType>
                <cxxVariableScopedName>CP_class</cxxVariableScopedName>
                <cxxVariablePrototype>static CPT_type CPT_name</cxxVariablePrototype>
                <cxxVariableNameLookup>CP_class::CPT_name</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="142"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc>
                <p>CPT_text </p>
            </apiDesc>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxVariable id="CP_class::CPS_name">
        <apiName>CPS_name</apiName>
        <shortdesc/>
        <cxxVariableDetail>
            <cxxVariableDefinition>
                <cxxVariableAccessSpecifier value="public"/>
                <cxxVariableStorageClassSpecifierStatic/>
                <cxxVariableDeclaredType>CPS_type</cxxVariableDeclaredType>
                <cxxVariableScopedName>CP_class</cxxVariableScopedName>
                <cxxVariablePrototype>static CPS_type CPS_name</cxxVariablePrototype>
                <cxxVariableNameLookup>CP_class::CPS_name</cxxVariableNameLookup>
                <cxxVariableAPIItemLocation>
                    <cxxVariableDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxVariableDeclarationFileLine name="lineNumber" value="144"/>
                </cxxVariableAPIItemLocation>
            </cxxVariableDefinition>
            <apiDesc>
                <p>CPS_text </p>
            </apiDesc>
        </cxxVariableDetail>
    </cxxVariable>
    <cxxTypedef id="CP_class::CPb_type_alias">
        <apiName>CPb_type_alias</apiName>
        <shortdesc/>
        <cxxTypedefDetail>
            <cxxTypedefDefinition>
                <cxxTypedefAccessSpecifier value="public"/>
                <cxxTypedefDeclaredType>CPb_typedef</cxxTypedefDeclaredType>
                <cxxTypedefScopedName>CP_class</cxxTypedefScopedName>
                <cxxTypedefPrototype>CPb_typedef CPb_type_alias</cxxTypedefPrototype>
                <cxxTypedefNameLookup>CP_class::CPb_type_alias</cxxTypedefNameLookup>
                <cxxTypedefAPIItemLocation>
                    <cxxTypedefDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxTypedefDeclarationFileLine name="lineNumber" value="150"/>
                </cxxTypedefAPIItemLocation>
            </cxxTypedefDefinition>
            <apiDesc>
                <p>CPb_text </p>
            </apiDesc>
        </cxxTypedefDetail>
    </cxxTypedef>
    <cxxTypedef id="CP_class::CPa_type_alias">
        <apiName>CPa_type_alias</apiName>
        <shortdesc/>
        <cxxTypedefDetail>
            <cxxTypedefDefinition>
                <cxxTypedefAccessSpecifier value="public"/>
                <cxxTypedefDeclaredType>CPa_typedef</cxxTypedefDeclaredType>
                <cxxTypedefScopedName>CP_class</cxxTypedefScopedName>
                <cxxTypedefPrototype>CPa_typedef CPa_type_alias</cxxTypedefPrototype>
                <cxxTypedefNameLookup>CP_class::CPa_type_alias</cxxTypedefNameLookup>
                <cxxTypedefAPIItemLocation>
                    <cxxTypedefDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxTypedefDeclarationFileLine name="lineNumber" value="152"/>
                </cxxTypedefAPIItemLocation>
            </cxxTypedefDefinition>
            <apiDesc>
                <p>CPa_text </p>
            </apiDesc>
        </cxxTypedefDetail>
    </cxxTypedef>
    <cxxTypedef id="CP_class::CPd_type_alias">
        <apiName>CPd_type_alias</apiName>
        <shortdesc/>
        <cxxTypedefDetail>
            <cxxTypedefDefinition>
                <cxxTypedefAccessSpecifier value="private"/>
                <cxxTypedefDeclaredType>CPd_typedef</cxxTypedefDeclaredType>
                <cxxTypedefScopedName>CP_class</cxxTypedefScopedName>
                <cxxTypedefPrototype>CPd_typedef CPd_type_alias</cxxTypedefPrototype>
                <cxxTypedefNameLookup>CP_class::CPd_type_alias</cxxTypedefNameLookup>
                <cxxTypedefAPIItemLocation>
                    <cxxTypedefDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxTypedefDeclarationFileLine name="lineNumber" value="155"/>
                </cxxTypedefAPIItemLocation>
            </cxxTypedefDefinition>
            <apiDesc>
                <p>CPd_text </p>
            </apiDesc>
        </cxxTypedefDetail>
    </cxxTypedef>
    <cxxTypedef id="CP_class::CPc_type_alias">
        <apiName>CPc_type_alias</apiName>
        <shortdesc/>
        <cxxTypedefDetail>
            <cxxTypedefDefinition>
                <cxxTypedefAccessSpecifier value="private"/>
                <cxxTypedefDeclaredType>CPc_typedef</cxxTypedefDeclaredType>
                <cxxTypedefScopedName>CP_class</cxxTypedefScopedName>
                <cxxTypedefPrototype>CPc_typedef CPc_type_alias</cxxTypedefPrototype>
                <cxxTypedefNameLookup>CP_class::CPc_type_alias</cxxTypedefNameLookup>
                <cxxTypedefAPIItemLocation>
                    <cxxTypedefDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxTypedefDeclarationFileLine name="lineNumber" value="157"/>
                </cxxTypedefAPIItemLocation>
            </cxxTypedefDefinition>
            <apiDesc>
                <p>CPc_text </p>
            </apiDesc>
        </cxxTypedefDetail>
    </cxxTypedef>
    <cxxTypedef id="CP_class::CPf_type_alias">
        <apiName>CPf_type_alias</apiName>
        <shortdesc/>
        <cxxTypedefDetail>
            <cxxTypedefDefinition>
                <cxxTypedefAccessSpecifier value="protected"/>
                <cxxTypedefDeclaredType>CPf_typedef</cxxTypedefDeclaredType>
                <cxxTypedefScopedName>CP_class</cxxTypedefScopedName>
                <cxxTypedefPrototype>CPf_typedef CPf_type_alias</cxxTypedefPrototype>
                <cxxTypedefNameLookup>CP_class::CPf_type_alias</cxxTypedefNameLookup>
                <cxxTypedefAPIItemLocation>
                    <cxxTypedefDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxTypedefDeclarationFileLine name="lineNumber" value="160"/>
                </cxxTypedefAPIItemLocation>
            </cxxTypedefDefinition>
            <apiDesc>
                <p>CPf_text </p>
            </apiDesc>
        </cxxTypedefDetail>
    </cxxTypedef>
    <cxxTypedef id="CP_class::CPe_type_alias">
        <apiName>CPe_type_alias</apiName>
        <shortdesc/>
        <cxxTypedefDetail>
            <cxxTypedefDefinition>
                <cxxTypedefAccessSpecifier value="protected"/>
                <cxxTypedefDeclaredType>CPe_typedef</cxxTypedefDeclaredType>
                <cxxTypedefScopedName>CP_class</cxxTypedefScopedName>
                <cxxTypedefPrototype>CPe_typedef CPe_type_alias</cxxTypedefPrototype>
                <cxxTypedefNameLookup>CP_class::CPe_type_alias</cxxTypedefNameLookup>
                <cxxTypedefAPIItemLocation>
                    <cxxTypedefDeclarationFile name="filePath" value="C:/p4work/EPOC/DV3/team/2005/sysdoc/tools/Doxygen/branches/DITA/test/CXX/daft/structure/classes/src/CP.h"/>
                    <cxxTypedefDeclarationFileLine name="lineNumber" value="162"/>
                </cxxTypedefAPIItemLocation>
            </cxxTypedefDefinition>
            <apiDesc>
                <p>CPe_text </p>
            </apiDesc>
        </cxxTypedefDetail>
    </cxxTypedef>
</cxxClass>""" 