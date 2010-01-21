<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
<!-- Copyright (c) 2007-2010 Nokia Corporation and/or its subsidiary(-ies) All rights reserved. -->
<!-- This component and the accompanying materials are made available under the terms of the License 
"Eclipse Public License v1.0" which accompanies this distribution, 
and is available at the URL "http://www.eclipse.org/legal/epl-v10.html". -->
<!-- Initial Contributors:
	Nokia Corporation - initial contribution.
Contributors: 
-->    
    <!--topic_xref pr-d_xref-->
	<xsl:template match="apiclassifier|apioperation|apipackage|apivalue">
        <xref>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </xref>
    </xsl:template>

    <!--map_map-->
	<xsl:template match="apiMap">
        <map>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </map>
    </xsl:template>

    <!--map_topicref-->
	<xsl:template match="apiItemRef">
        <topicref>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </topicref>
    </xsl:template>

    <!--topic_body reference_refbody apiRef_apiDetail-->
	<xsl:template match="apiClassifierDetail|apiOperationDetail|apiValueDetail">
        <refbody>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </refbody>
    </xsl:template>

    <!--topic_keyword reference_keyword-->
	<xsl:template match="apiItemName">
        <keyword>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </keyword>
    </xsl:template>
    
    <!--topic_p reference_p-->
	<xsl:template match="apiSyntaxItem">
        <p>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </p>
    </xsl:template>    

    <!--topic_ph reference_ph apiRef_apiData-->
	<xsl:template match="apiData|apiDefItem|apiDefNote">
        <ph>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </ph>
    </xsl:template>

    <!--topic_ph reference_ph apiRef_apiDefItem-->
	<xsl:template match="apiClassifierMember|apiEvent|apiOperationDefItem|apiParam|apiReturn|apiValueMember">
        <ph>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </ph>
    </xsl:template>

    <!--topic_pre reference_pre-->
	<xsl:template match="apiSyntaxText">
        <pre>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </pre>
    </xsl:template>
    
    <!--topic_section reference_refsyn-->
	<xsl:template match="apiSyntax">
        <refsyn>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </refsyn>
    </xsl:template>

    <!--topic_section reference_section-->
	<xsl:template match="apiDef|apiDesc|apiImpl">
        <section>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </section>
    </xsl:template>
    
    <!--topic_section reference_section apiRef_apiDef-->
	<xsl:template match="apiClassifierDef|apiConstructorDef|apiOperationDef|apiValueDef">
        <section>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </section>
    </xsl:template>

    <!--topic_state reference_state-->
	<xsl:template match="apiArray|apiQualifier|apiType">
        <state>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </state>
    </xsl:template>

    <!--topic_title reference_title-->
	<xsl:template match="apiName">
        <title>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </title>
    </xsl:template>

    <!--topic_topic reference_reference-->
	<xsl:template match="apiRef">
        <reference>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </reference>
    </xsl:template>
    
    <!--topic_topic reference_reference apiRef_apiRef-->
	<xsl:template match="apiClassifier|apiOperation|apiPackage|apiValue">
        <reference>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </reference>
    </xsl:template>

    <!--topic_xref reference_xref-->
	<xsl:template match="apiRelation">
        <xref>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </xref>
    </xsl:template>

    <!--topic_xref reference_xref apiRef_apiRelation-->
	<xsl:template match="apiBaseClassifier|apiOtherClassifier|apiOperationClassifier|apiValueClassifier">
        <xref>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </xref>
    </xsl:template>    
</xsl:stylesheet>