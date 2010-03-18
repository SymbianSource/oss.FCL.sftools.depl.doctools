<?xml version="1.0"?>
<!--
Copyright (c) 2010 Nokia Corporation and/or its subsidiary(-ies).
All rights reserved.-->
 <xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:key name="id" match="*[@name]" use="@name"/>
	<xsl:param name="td"/>
	
<xsl:template match="/*">
	<xsl:message>Cannot process this document</xsl:message>
</xsl:template>

<xsl:template match="/SystemDefinition[@schema='2.0.1']">
<xsl:call-template name="DTD"/>
<SystemDefinition schema="3.0.0">
	<systemModel name="{@name}">
		<xsl:apply-templates select="systemModel/layer"/>
	</systemModel>
</SystemDefinition>
</xsl:template>

<xsl:template match="@*"/>

<xsl:template match="@name"> 
	<!-- throw an error if there are duplicate IDs -->
	<xsl:if test="count(key('id',.))!=1">
		<xsl:message>Duplicate ID, cannot transform: <xsl:value-of select="."/></xsl:message>
	</xsl:if>
	<xsl:attribute name="id"><xsl:value-of select="."/></xsl:attribute>
</xsl:template>

<xsl:template match="@long-name">
	<xsl:attribute name="name"><xsl:value-of select="."/></xsl:attribute>
</xsl:template>



<xsl:template match="layer|collection">
	<xsl:copy>
		<xsl:apply-templates select="@*"/>
		<xsl:apply-templates select="*|comment()"/>
	</xsl:copy>
</xsl:template>


<xsl:template match="block|subblock">
	<package>
		<xsl:apply-templates select="@name|@long-name|@level|@span|@levels|@tech_domain"/>
		<xsl:if test="$td!=''">
			<xsl:for-each select="document($td)//block[@name=current()/@name]">
				<xsl:attribute name="tech-domain"><xsl:value-of select="@tech_domain"/></xsl:attribute>
			</xsl:for-each>
		</xsl:if>
		<xsl:apply-templates select="*|comment()"/>
	</package>
</xsl:template>


<xsl:template match="component">
	<xsl:copy>
		<xsl:apply-templates select="@name|@long-name|@deprecated|@introduced|@filter|@purpose"/>
		<xsl:call-template name="class">
			<xsl:with-param name="remove">placeholder PC test</xsl:with-param>
			<xsl:with-param name="add">
				<xsl:if test="@plugin='Y'">plugin</xsl:if>
			</xsl:with-param>
		</xsl:call-template>
		<xsl:if test="contains(concat(' ',@class,' '),' PC ')">
			<xsl:attribute name="target">desktop</xsl:attribute>
		</xsl:if>
		<xsl:apply-templates select="*|comment()"/>		
	</xsl:copy>
</xsl:template>

<xsl:template match="unit">
	<xsl:copy>
		<xsl:apply-templates select="@*"/>
	</xsl:copy>
</xsl:template>

<xsl:template match="@levels|@level|@span|@deprecated|@introduced|@filter|unit/@*|comment()|@purpose">
	<xsl:copy-of select="."/>
</xsl:template>

<xsl:template match="unit/@mrp|unit/@bldFile">
	<xsl:attribute name="{name()}"><xsl:if test="not(starts-with(.,'/'))">/</xsl:if><xsl:value-of select="."/></xsl:attribute>
</xsl:template>

<xsl:template name="class"><xsl:param name="remove"/><xsl:param name="add"/>
	<xsl:param name="class" select="normalize-space(@class)"/>
	<xsl:variable name="r">
		<xsl:text> </xsl:text>
		<xsl:choose>
			<xsl:when test="contains($remove,' ')"><xsl:value-of select="substring-before($remove,' ')"/></xsl:when>
			<xsl:otherwise><xsl:value-of select="$remove"/></xsl:otherwise>
		</xsl:choose>
		<xsl:text> </xsl:text>
	</xsl:variable>
	<xsl:variable name="c">
		<xsl:choose>
			<xsl:when test="contains(concat(' ',$class,' '),$r)">
				<xsl:value-of select="substring-before(concat(' ',$class,' '),$r)"/>
				<xsl:text> </xsl:text>
				<xsl:value-of select="substring-after(concat(' ',$class,' '),$r)"/>
			</xsl:when>
			<xsl:otherwise><xsl:value-of select="$class"/></xsl:otherwise>
		</xsl:choose>
		<xsl:if test="normalize-space($add)!=''"><xsl:value-of select="concat(' ',normalize-space($add))"/></xsl:if>
	</xsl:variable>
	<xsl:choose>
		<xsl:when test="contains($remove,' ')">
			<xsl:call-template name="class">
				<xsl:with-param name="remove" select="substring-after($remove,' ')"/>
				<xsl:with-param name="class" select="$c"/>
			</xsl:call-template>
		</xsl:when>
		<xsl:when test="normalize-space($c)!=''">
			<xsl:attribute name="class">
				<xsl:value-of select="normalize-space($c)"/>
			</xsl:attribute>
		</xsl:when>
	</xsl:choose>
</xsl:template>

<xsl:template match="@tech_domain" priority="5">
	<xsl:attribute name="tech-domain"><xsl:value-of select="."/></xsl:attribute>
</xsl:template>

<xsl:template name="DTD">
<xsl:text disable-output-escaping="yes"><![CDATA[]]></xsl:text>
</xsl:template>

</xsl:stylesheet>
