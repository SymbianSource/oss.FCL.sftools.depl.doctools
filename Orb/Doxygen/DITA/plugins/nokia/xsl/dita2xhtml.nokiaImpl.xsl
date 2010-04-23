<?xml version="1.0" encoding="UTF-8" ?>
<!--
 (C) Copyright Nokia Corporation and/or its subsidiary(-ies) 2009  - 2010. All rights reserved.
-->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:dita2html="http://dita-ot.sourceforge.net/ns/200801/dita2html"
                xmlns:related-links="http://dita-ot.sourceforge.net/ns/200709/related-links"
                version="1.0"
                exclude-result-prefixes="dita2html related-links">

  <!-- Add wrapper div elements -->
  <xsl:template match="*[contains(@class, ' topic/topic ')]" mode="chapterBody">
    <xsl:variable name="flagrules">
      <xsl:call-template name="getrules"/>
    </xsl:variable>
    <body>
      <!-- Already put xml:lang on <html>; do not copy to body with commonattributes -->
      <xsl:call-template name="gen-style">
        <xsl:with-param name="flagrules" select="$flagrules"/>
      </xsl:call-template>
      <!--output parent or first "topic" tag's outputclass as class -->
      <xsl:if test="@outputclass">
        <xsl:attribute name="class">
          <xsl:value-of select="@outputclass"/>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="self::dita">
        <xsl:if test="*[contains(@class,' topic/topic ')][1]/@outputclass">
          <xsl:attribute name="class">
            <xsl:value-of select="*[contains(@class,' topic/topic ')][1]/@outputclass"/>
          </xsl:attribute>
        </xsl:if>
      </xsl:if>
      <xsl:apply-templates select="." mode="addAttributesToBody"/>
      <xsl:call-template name="setidaname"/>
      <xsl:call-template name="start-flagit">
        <xsl:with-param name="flagrules" select="$flagrules"/>
      </xsl:call-template>
      <xsl:call-template name="start-revflag">
        <xsl:with-param name="flagrules" select="$flagrules"/>
      </xsl:call-template>
      <div class="body">
        <div class="contentLeft prTxt">
          <xsl:call-template name="generateBreadcrumbs"/>
          <xsl:call-template name="gen-user-header"/><!-- include user's XSL running header here -->
          <xsl:call-template name="processHDR"/>
          <xsl:call-template name="gen-user-sidetoc"/><!-- Include a user's XSL call here to generate a toc based on what's a child of topic -->
          <xsl:apply-templates/>
          <!-- this will include all things within topic; therefore, -->
          <!-- title content will appear here by fall-through -->
          <!-- followed by prolog (but no fall-through is permitted for it) -->
          <!-- followed by body content, again by fall-through in document order -->
          <!-- followed by related links -->
          <!-- followed by child topics by fall-through -->
          <!--
          <xsl:apply-templates select="*[contains(@class, ' topic/title ')] |
                                       *[contains(@class, ' topic/shortdesc ')] |
                                       *[contains(@class, ' topic/abstract ')] |
                                       *[contains(@class, ' topic/prolog ')] |
                                       *[contains(@class, ' topic/body ')] |
                                       *[contains(@class, ' topic/related-links ')]"/>
          -->
          <xsl:call-template name="gen-endnotes"/><!-- include footnote-endnotes -->
        </div>
      </div>        
      <xsl:call-template name="gen-user-footer"/><!-- include user's XSL running footer here -->
      <xsl:call-template name="processFTR"/><!-- Include XHTML footer, if specified -->
      <xsl:call-template name="end-revflag">
        <xsl:with-param name="flagrules" select="$flagrules"/>
      </xsl:call-template>
      <xsl:call-template name="end-flagit">
        <xsl:with-param name="flagrules" select="$flagrules"/>
      </xsl:call-template>
    </body>
  </xsl:template>
  
  <xsl:template match="*[contains(@class,' topic/topic ')]/*[contains(@class,' topic/title ')]" mode="get-output-class">
    <!-- NWG -->
    <xsl:text>pageHeading </xsl:text>
    <!-- OT -->
    <xsl:text>topictitle</xsl:text>
    <xsl:choose>
      <xsl:when test="count(ancestor::*[contains(@class,' topic/topic ')]) > 6">6</xsl:when>
      <xsl:otherwise><xsl:value-of select="count(ancestor::*[contains(@class,' topic/topic ')])"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- Nokia Web Guidelines -->
  <xsl:template name="gen-user-styles">
    <xsl:apply-templates select="." mode="gen-user-styles"/>
    <link href="{$PATH2PROJ}{$CSSPATH}html.css" rel="stylesheet" type="text/css"/>    
    <link href="{$PATH2PROJ}{$CSSPATH}style.css" rel="stylesheet" type="text/css"/>
    <link href="{$PATH2PROJ}{$CSSPATH}nwg.css" rel="stylesheet" type="text/css"/>
    <link href="{$PATH2PROJ}{$CSSPATH}eclipse.css" rel="stylesheet" type="text/css"/>
  </xsl:template>

  <!-- Nokia footer -->
  <xsl:template name="gen-user-footer">
    <div class="footer">
      <hr/>
      <div class="copy">
        <xsl:text>© Nokia </xsl:text>
        <xsl:value-of select="$YEAR"/>
        <xsl:text>.</xsl:text>
      </div>
      <xsl:apply-templates select="." mode="gen-user-footer"/>
    </div>
  </xsl:template>
  
  <!-- Disable empty shortdesc -->
  <xsl:template match="*[contains(@class, ' topic/shortdesc ')][not(node())]"/>

  <!-- rel-links.xsl -->
  
  <!-- Change heading markup, titles, and contents into a list -->
  <xsl:template match="*[contains(@class, ' topic/link ')]" mode="related-links:result-group"><!--name="related-links:group-result."-->
    <xsl:param name="links"/>
    <div class="section relinfo">
      <h2 class="sectiontitle">
        <xsl:call-template name="getString">
          <xsl:with-param name="stringName">
            <xsl:choose>
              <xsl:when test="@type = 'concept'">Related concepts</xsl:when>
              <xsl:when test="@type = 'task'">Related tasks</xsl:when>
              <xsl:when test="@type = 'reference'">Related reference</xsl:when>
              <xsl:when test="@type = 'apiRef'">Related API reference</xsl:when>
              <xsl:otherwise>Related information</xsl:otherwise>             
            </xsl:choose>
         </xsl:with-param>
        </xsl:call-template>
      </h2>
      <div>
        <xsl:copy-of select="$links"/>
      </div>
    </div>
  </xsl:template>
  
  <!-- Generate list items -->
  <!--
  <xsl:template match="*[contains(@class, ' topic/link ')]" name="topic.link">
    <xsl:choose>
      <!- - Linklist links put out <br/> in "processlinklist" - ->
      <xsl:when test="ancestor::*[contains(@class,' topic/linklist ')]">
        <xsl:call-template name="makelink"/>
      </xsl:when>
      <!- - Ancestor links go in the breadcrumb trail, and should not get a <br/> - ->
      <xsl:when test="@role='ancestor'">
        <xsl:call-template name="makelink"/>
      </xsl:when>
      <!- - Items with these roles should always go to output, and are not included in the hideduplicates key. - ->
      <xsl:when test="@role and not(@role='cousin' or @role='external' or @role='friend' or @role='other' or @role='sample' or @role='sibling')">
        <li class="a">
          <xsl:call-template name="makelink"/>
        </li>
      </xsl:when>
      <!- - If roles do not match, but nearly everything else does, skip the link. - ->
      <xsl:when test="(key('hideduplicates', concat(ancestor::*[contains(@class, ' topic/related-links ')]/parent::*[contains(@class, ' topic/topic ')]/@id, ' ',@href,@scope,@audience,@platform,@product,@otherprops,@rev,@type,normalize-space(child::*))))[2]">
        <xsl:choose>
          <xsl:when test="generate-id(.)=generate-id((key('hideduplicates', concat(ancestor::*[contains(@class, ' topic/related-links ')]/parent::*[contains(@class, ' topic/topic ')]/@id, ' ',@href,@scope,@audience,@platform,@product,@otherprops,@rev,@type,normalize-space(child::*))))[1])">
            <li class="b">
              <xsl:call-template name="makelink"/>
            </li>
          </xsl:when>
          <!- - If this is filtered out, we may need the duplicate link message anyway. - ->
          <xsl:otherwise>
            <xsl:call-template name="linkdupinfo"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:otherwise>
        <li class="c">
          <xsl:call-template name="makelink"/>
        </li>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  -->

  <!-- Disable parent-child links -->
  <!--
  <xsl:template name="parentlink" match="*[contains(@class, ' topic/link ')][@role='parent']" priority="2000"/>
  <xsl:template match="*[contains(@class, ' topic/link ')][@role='child' or @role='descendant']" priority="2000" name="topic.link_child"/>
  -->

</xsl:stylesheet>
