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
import xml
import os
import logging


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
        #except xml.parsers.expat.ExpatError, e:
        except Exception, e:
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


################################################################
# Unit test code
################################################################
import unittest
from cStringIO import StringIO


class EtreeStub(object):    
    def parse(self, file):
        return etree.parse(StringIO(class_c_always_online))


class InvalidEtreeStub(object):    
    def parse(self, file):
        return etree.parse(StringIO("<foo><bar"))


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