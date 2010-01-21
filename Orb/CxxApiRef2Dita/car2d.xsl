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
    <xsl:param name="datetime"/>
    <xsl:param name="sourceFile"/>
    <xsl:param name="sourceDir"/>

    <xsl:output method="xml" indent="no"/>
    <xsl:include href="apiref.xsl"/>
    <xsl:include href="cxx.xsl"/>    
    <!-- Start required cleanup stuff-->
    <xsl:template match="*" name="wrapInRequiredCleanup" priority="-1">
        <xsl:comment>
            <xsl:text/>&lt;required-cleanup class="fail" remap="<xsl:value-of select="name()"/>"<xsl:apply-templates select="@*" mode="serialize"/>&gt;<xsl:text/>
            <xsl:apply-templates mode="serialize"/>
            <xsl:text/>&lt;/required-cleanup<xsl:text/>
        </xsl:comment>
    </xsl:template>
    <xsl:template match="text()" name="serialize-text" mode="serialize">
        <xsl:param name="text" select="."/>
        <xsl:choose>
            <xsl:when test="contains($text, '--')">
                <xsl:value-of select="substring-before($text, '--')"/>
                <xsl:text>- -</xsl:text>
                <xsl:call-template name="serialize-text">
                    <xsl:with-param name="text" select="substring-after($text, '--')"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$text"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>    
    <xsl:template match="*" mode="serialize">
        <xsl:text>&lt;</xsl:text>
        <xsl:value-of select="name()"/>
        <xsl:apply-templates select="@*" mode="serialize"/>
        <xsl:text>&gt;</xsl:text>
        <xsl:apply-templates select="node()" mode="serialize"/>
        <xsl:text>&lt;/</xsl:text>
        <xsl:value-of select="name()"/>
        <xsl:text>&gt;</xsl:text>
    </xsl:template>
    <xsl:template match="@*" mode="serialize">
        <xsl:text/>
        <xsl:value-of select="name()"/>
        <xsl:text>="</xsl:text>
        <xsl:call-template name="serialize-text"/>
        <xsl:text>"</xsl:text>
    </xsl:template>     
    <!-- End required cleanup stuff-->   

    <!-- Start Doctype--> 
    <xsl:template name="outputDoctype">
        <xsl:param name="topicType"/>
        <xsl:choose>
            <xsl:when test="normalize-space($topicType) = 'map'">
                <xsl:text disable-output-escaping="yes">
                    <![CDATA[<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">]]>
                </xsl:text>
            </xsl:when>        
            <xsl:when test="normalize-space($topicType) = 'topic'">
                <xsl:text disable-output-escaping="yes">
                    <![CDATA[<!DOCTYPE topic PUBLIC "-//OASIS//DTD DITA Topic//EN" "topic.dtd">]]>
                </xsl:text>
            </xsl:when>
            <xsl:when test="normalize-space($topicType) = 'concept'">
                <xsl:text disable-output-escaping="yes">
                    <![CDATA[<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">]]>
                </xsl:text>
            </xsl:when>
            <xsl:when test="normalize-space($topicType) = 'reference'">
                <xsl:text disable-output-escaping="yes">
                    <![CDATA[<!DOCTYPE reference PUBLIC "-//OASIS//DTD DITA Reference//EN" "reference.dtd">]]>
                </xsl:text>					
            </xsl:when>
            <xsl:when test="normalize-space($topicType) = 'task'">
                <xsl:text disable-output-escaping="yes">
                    <![CDATA[<!DOCTYPE task PUBLIC "-//OASIS//DTD DITA Task//EN" "task.dtd">]]>
                </xsl:text>					
            </xsl:when>
            <xsl:otherwise>
                <xsl:text disable-output-escaping="yes">
                    <![CDATA[<!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd">]]>
                </xsl:text>
            </xsl:otherwise>				
        </xsl:choose>
    </xsl:template>
    <xsl:template match="/">
        <xsl:choose>        
            <xsl:when test="name(/*)='topic'">
                <xsl:call-template name="outputDoctype">
                    <xsl:with-param name="topicType" select="'topic'"/> 
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="name(/*)='cxxAPIMap'">
                <xsl:call-template name="outputDoctype">
                    <xsl:with-param name="topicType" select="'map'"/> 
                </xsl:call-template>
            </xsl:when>            
            <xsl:otherwise>
                <xsl:call-template name="outputDoctype">
                    <xsl:with-param name="topicType" select="'reference'"/> 
                </xsl:call-template>             
            </xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="@*">
        <xsl:copy-of select="."/>
    </xsl:template>
    
    <xsl:template match="@id">
        <xsl:variable name="thisId" select="."/>
        <xsl:choose>
            <xsl:when test="count(//*[@id=$thisId]) &gt; 1">
                <xsl:attribute name="id"><xsl:value-of select="generate-id(.)"/></xsl:attribute>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy-of select="."/>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>
    
    <xsl:template match="*" priority="-0.75">
        <!-- If this element begins with cxx wrap it in a required cleanup 
        if no its probably standard dita-->
        <xsl:choose>
            <xsl:when test="starts-with(name(.),'cxx')">
                <xsl:comment>An element was found that does not yet have a lineage DITA defined</xsl:comment>
                <xsl:call-template name="wrapInRequiredCleanup"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy-of select="."/>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>    

</xsl:stylesheet>