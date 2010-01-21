<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" xmlns:data="urn:some.urn" exclude-result-prefixes="data">
<!-- Copyright (c) 2007-2010 Nokia Corporation and/or its subsidiary(-ies) All rights reserved. -->
<!-- This component and the accompanying materials are made available under the terms of the License 
"Eclipse Public License v1.0" which accompanies this distribution, 
and is available at the URL "http://www.eclipse.org/legal/epl-v10.html". -->
<!-- Initial Contributors:
	Nokia Corporation - initial contribution.
Contributors: 
-->
    <!--topic_xref pr-d_xref api-d_apipackage-->
    <xsl:template name="isParentReference">
        <xsl:choose>
            <xsl:when test="name(..)='cxxClassInherits' or name(..)='cxxTypedef' or name(..)='cxxVariable' or name(..)='cxxEnumeration' or name(..)='cxxEnumerator' or name(..)='cxxFile' or name(..)='cxxGlobals' or name(..)='cxxPackage' or name(..)='cxxDefine' or name(..)='cxxFunction' or name(..)='cxxClass' or name(..)='cxxStruct' or name(..)='cxxUnion'">
                <xsl:value-of select="'true'"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="'false'"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!--topic_xref pr-d_xref api-d_apipackage-->
    <xsl:template match="cxxbitfield|cxxclass|cxxdefine|cxxenumerator|cxxfile|cxxfunction|cxxnamespace|cxxparameter|cxxprogram|cxxstruct|cxxtypedef|cxxunion|cxxvariable">
        <xsl:variable name="isInReference">
            <xsl:call-template name="isParentReference"/>
        </xsl:variable>
        <xsl:choose>
        <!-- DEFECT xref was output inside reference this is not allowed in dita reference-->
            <xsl:when test="$isInReference='true'">
                <xsl:comment>A specialisation of reference had a child that cannot be inside reference</xsl:comment>            
                <xsl:call-template name="wrapInRequiredCleanup"/>
            </xsl:when>
            <xsl:otherwise>
                <xref>
                    <xsl:apply-templates select="@*"/>
                    <xsl:apply-templates/>
                </xref>
            </xsl:otherwise>
        </xsl:choose>        
        <xref>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </xref>
    </xsl:template>

    <!-- map_map apiMap_apiMap-->
    <xsl:template match="cxxAPIMap">
        <map>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </map>
    </xsl:template>

    <!--map_topicref apiMap_apiItemRef-->
    <xsl:template match="cxxClassRef|cxxDefineRef|cxxEnumerationRef|cxxFileRef|cxxFunctionRef|cxxNamespaceRef|cxxProgramRef|cxxStructRef|cxxTypedefRef|cxxUnionRef|cxxVariableRef">
        <topicref>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </topicref>
    </xsl:template>

    <!--topic_body reference_refbody apiRef_apiDetail apiClassifier_apiClassifierDetail-->
    <xsl:template match="cxxClassDetail|cxxStructDetail|cxxUnionDetail|cxxEnumerationDetail|cxxEnumeratorDetail|cxxFileDetail">
        <refbody>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </refbody>
    </xsl:template>

    <!--topic_body reference_refbody apiRef_apiDetail apiOperation_apiOperationDetail-->
    <xsl:template match="cxxDefineDetail|cxxFunctionDetail">
        <refbody>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </refbody>
    </xsl:template>

    <!--topic_body reference_refbody apiRef_apiDetail apiPackage_apiDetail-->
    <xsl:template match="cxxPackageDetail">
        <refbody>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </refbody>
    </xsl:template>

    <!--topic_body reference_refbody apiRef_apiDetail apiValue_apiValueDetail-->
    <xsl:template match="cxxTypedefDetail|cxxVariableDetail">
        <refbody>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </refbody>
    </xsl:template>

    <!--topic_ph reference_ph apiRef_apiDefItem-->
    <xsl:template match="cxxClassAPIItemLocation|cxxClassDerivation|cxxClassDerivations|cxxTemplateParamList|cxxDefineAPIItemLocation|cxxFunctionAPIItemLocation|cxxStructAPIItemLocation|cxxStructDerivation|cxxStructDerivations|cxxStructTemplateParamList|cxxStructTemplateParameter|cxxUnionAPIItemLocation|cxxUnionDerivation|cxxUnionDerivations|cxxClassTemplateParameter|cxxClassTemplateParamList|cxxEnumerationAPIItemLocation|cxxEnumeratorAPIItemLocation|cxxFileAPIItemLocation|cxxTypedefAPIItemLocation|cxxUnionTemplateParamList|cxxVariableAPIItemLocation|cxxFunctionDeclaredType|cxxFunctionNameLookup|cxxFunctionParameters|cxxFunctionParameter|cxxFunctionParameterDeclaredType|cxxFunctionParameterDeclarationName|cxxFunctionParameterDefaultValue|cxxFunctionParameterDefinitionName|cxxFunctionParameterType|cxxFunctionPrototype|cxxFunctionReturnType|cxxFunctionScopedName">

        <xsl:variable name="isInReference">
            <xsl:call-template name="isParentReference"/>
        </xsl:variable>
        <xsl:choose>
        <!-- DEFECT ph was output inside reference this is not allowed in dita reference-->
            <xsl:when test="$isInReference='true'">
                <xsl:comment>A specialisation of reference had a child that cannot be inside reference</xsl:comment>            
                <xsl:call-template name="wrapInRequiredCleanup"/>
            </xsl:when>
            <xsl:otherwise>
                <ph>
                    <xsl:apply-templates select="@*"/>
                    <xsl:apply-templates/>
                </ph>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!--topic_section reference_section apiRef_apiDef apiClassifier_apiClassifierDef-->
    <xsl:template match="cxxClassDefinition|cxxStructDefinition|cxxUnionDefinition|cxxEnumerationDefinition|cxxEnumeratorDefinition">
        <section>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </section>
    </xsl:template>

    <!--topic_section reference_section apiRef_apiDef apiOperation_apiOperationDef-->
    <xsl:template match="cxxDefineDefinition|cxxFunctionDefinition">
        <section>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </section>
    </xsl:template>

    <!--topic_section reference_section apiRef_apiDef apiValue_apiValueDef-->
    <xsl:template match="cxxTypedefDefinition|cxxVariableDefinition">
        <section>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </section>
    </xsl:template>

    <!--topic_state reference_state apiRef_apiArray apiOperation_apiArray-->
    <xsl:template match="cxxDefineArrayType|cxxFunctionArrayType|cxxTypedefArrayType|cxxVariableArrayType">
		<!--
        <state>        
            <xsl:call-template name="addMissingStateAttribs"/>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </state>
		-->
    </xsl:template>

    <!--topic_state reference_state apiRef_apiQualifier apiClassifier_apiQualifier-->
    <xsl:template match="cxxClassAbstract|cxxClassAccessSpecifier|cxxClassDeclarationFile|cxxClassDeclarationFileLine|cxxClassDefinitionFile|cxxClassDefinitionFileLineEnd|cxxClassDefinitionFileLineStart|cxxClassDerivationVirtual|cxxDefineDeclarationFile|cxxDefineDeclarationFileLine|cxxDefineDefinitionFile|cxxDefineDefinitionFileLineEnd|cxxDefineDefinitionFileLineStart|cxxFunctionDeclarationFile|cxxFunctionDeclarationFileLine|cxxFunctionDefinitionFile|cxxFunctionDefinitionFileLineEnd|cxxFunctionDefinitionFileLineStart|cxxStructAbstract|cxxStructAccessSpecifier|cxxStructDeclarationFile|cxxStructDeclarationFileLine|cxxStructDefinitionFile|cxxStructDefinitionFileLineEnd|cxxStructDefinitionFileLineStart|cxxStructDerivationAccessSpecifier|cxxStructDerivationVirtual|cxxUnionAbstract|cxxUnionAccessSpecifier|cxxUnionDeclarationFile|cxxUnionDeclarationFileLine|cxxUnionDefinitionFile|cxxUnionDefinitionFileLineEnd|cxxUnionDefinitionFileLineStart|cxxUnionDerivationAccessSpecifier|cxxUnionDerivationVirtual|cxxDefineAccessSpecifier|cxxEnumerationAccessSpecifier|cxxEnumerationDeclarationFile|cxxEnumerationDeclarationFileLine|cxxEnumerationDefinitionFile|cxxEnumerationDefinitionFileLineEnd|cxxEnumerationDefinitionFileLineStart|cxxEnumeratorAccessSpecifier|cxxEnumeratorDeclarationFile|cxxEnumeratorDeclarationFileLine|cxxFileDeclarationFile|cxxFunctionAccessSpecifier">
        <!--
        <state>
            <xsl:call-template name="addMissingStateAttribs"/>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </state>
		-->
    </xsl:template>

    <!--topic_state reference_state apiRef_apiQualifier apiOperation_apiQualifier-->
    <xsl:template match="cxxDefineConst|cxxDefineConstructor|cxxDefineDestructor|cxxDefineExplicit|cxxDefineInline|cxxDefinePureVirtual|cxxDefineStorageClassSpecifierExtern|cxxDefineStorageClassSpecifierMutable|cxxDefineStorageClassSpecifierStatic|cxxDefineVirtual|cxxDefineVoidType|cxxFunctionConst|cxxFunctionConstructor|cxxFunctionDestructor|cxxFunctionExplicit|cxxFunctionInline|cxxFunctionPureVirtual|cxxFunctionStorageClassSpecifierExtern|cxxFunctionStorageClassSpecifierMutable|cxxFunctionStorageClassSpecifierStatic|cxxFunctionVirtual|cxxFunctionFundementalType|cxxFunctionVoidType|cxxTypedefVoidType|cxxVariableConst|cxxVariableStorageClassSpecifierExtern|cxxVariableStorageClassSpecifierMutable|cxxVariableStorageClassSpecifierStatic|cxxVariableVoidType">
		<!--
        <state>
            <xsl:call-template name="addMissingStateAttribs"/>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </state>
		-->
    </xsl:template>
    
    <xsl:template name="addMissingStateAttribs">
        <xsl:if test="not(@name)">
            <xsl:attribute name="name">name</xsl:attribute>
        </xsl:if>
        <xsl:if test="not(@value)">
            <xsl:attribute name="value">value</xsl:attribute>           
        </xsl:if>        
    </xsl:template>
    <!--topic_state reference_state apiRef_apiDetail-->
    <xsl:template match="cxxClassInheritsDetail|cxxStructInheritsDetail">
        <refbody>
			<section>
				<ph>
					<xsl:apply-templates select="@*"/>
					<xsl:apply-templates/>
				</ph>
			</section>
        </refbody>
    </xsl:template>

    <!--topic_topic reference_refbody apiRef_apiRef apiClassifier_apiClassifier-->
    <xsl:template match="cxxClass|cxxStruct|cxxUnion">
        <reference>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </reference>
    </xsl:template>

    <!--topic_topic reference_reference apiRef_apiRef apiOperation_apiOperation-->
    <xsl:template match="cxxDefine|cxxFunction">
        <reference>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </reference>
    </xsl:template>

    <!--topic_topic reference_reference apiRef_apiRef apiPackage_apiPackage-->
    <xsl:template match="cxxFile|cxxGlobals|cxxPackage">
        <reference>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </reference>
    </xsl:template>

    <!--topic_topic reference_reference apiRef_apiRef apiValue_apiValue-->
    <xsl:template match="cxxTypedef|cxxVariable|cxxEnumeration|cxxEnumerator">
        <reference>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </reference>
    </xsl:template>

    <!--topic_topic reference_reference apiRef_apiRef-->
    <xsl:template match="cxxClassInherits|cxxStructInherits">
        <reference id="{generate-id(.)}">
            <title>Class Inheritance</title>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </reference>
    </xsl:template>

    <!--topic_xref reference_xref apiRef_apiRelation apiClassifier_apiBaseClassifier-->
    <xsl:template match="cxxClassBaseClass|cxxClassBaseStruct|cxxClassBaseUnion|cxxStructBaseClass|cxxStructBaseStruct|cxxStructBaseUnion|cxxUnionBaseClass|cxxUnionBaseStruct|cxxUnionBaseUnion">
        <xsl:variable name="isInReference">
            <xsl:call-template name="isParentReference"/>
        </xsl:variable>
        <xsl:choose>
        <!-- DEFECT xref was output inside reference this is not allowed in dita reference-->
            <xsl:when test="$isInReference='true'">
                <xsl:comment>A specialisation of reference had a child that cannot be inside reference</xsl:comment>            
                <xsl:call-template name="wrapInRequiredCleanup"/>
            </xsl:when>
            <xsl:otherwise>
                <xref>
                    <xsl:apply-templates select="@*"/>
                    <xsl:apply-templates/>
                </xref>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!--topic_xref reference_xref apiRef_apiRelation apiOperation_apiOperationClassifier-->
    <xsl:template match="cxxDefineClassType|cxxDefineStructType|cxxDefineUnionType|cxxFunctionClassType|cxxFunctionStructType|cxxFunctionUnionType|cxxTypedefClassType|cxxTypedefStructType|cxxTypedefUnionType|cxxVariableClassType|cxxVariableStructType|cxxVariableUnionType">
        <xsl:variable name="isInReference">
            <xsl:call-template name="isParentReference"/>
        </xsl:variable>
        <xsl:choose>
        <!-- DEFECT xref was output inside reference this is not allowed in dita reference-->
            <xsl:when test="$isInReference='true'">
                <xsl:comment>A specialisation of reference had a child that cannot be inside reference</xsl:comment>            
                <xsl:call-template name="wrapInRequiredCleanup"/>
            </xsl:when>
            <xsl:otherwise>
                <xref>
                    <xsl:apply-templates select="@*"/>
                    <xsl:apply-templates/>
                </xref>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!--topic_xref reference_xref apiRef_apiRelation-->
    <xsl:template match="cxxClassNestedClass|cxxClassNestedStruct|cxxClassNestedUnion|cxxStructNestedClass|cxxStructNestedStruct|cxxStructNestedUnion|cxxUnionNestedClass|cxxUnionNestedStruct|cxxUnionNestedUnion|cxxClassEnumerationInherited|cxxClassEnumeratorInherited|cxxClassFunctionInherited|cxxClassVariableInherited|cxxStructEnumerationInherited|cxxStructEnumeratorInherited|cxxStructFunctionInherited|cxxStructVariableInherited|cxxFunctionReimplemented">
        <xsl:variable name="isInReference">
            <xsl:call-template name="isParentReference"/>
        </xsl:variable>
        <xsl:choose>
        <!-- DEFECT xref was output inside reference this is not allowed in dita reference-->
            <xsl:when test="$isInReference='true'">
                <xsl:comment>A specialisation of reference had a child that cannot be inside reference</xsl:comment>
                <xsl:call-template name="wrapInRequiredCleanup"/>
            </xsl:when>
            <xsl:otherwise>
                <xref>
                    <xsl:apply-templates select="@*"/>
                    <xsl:apply-templates/>
                </xref>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>