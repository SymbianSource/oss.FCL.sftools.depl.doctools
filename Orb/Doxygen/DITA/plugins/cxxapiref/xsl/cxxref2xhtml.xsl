<?xml version="1.0" encoding="UTF-8" ?>
<!--
  Copyright (c) 2009 Nokia Corporation and/or its subsidiary(-ies).
  All rights reserved.
-->

<xsl:stylesheet
    version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>

<xsl:output method="xml"
            encoding="utf-8"
            indent="no"
/>

<xsl:param name="CXXAPICSS" select="'nokiacxxref.css'"/>
<xsl:param name="CXXAPICSSRTL" select="'nokiacxxrefrtl.css'"/>

<xsl:param name="WORKDIR" select="'./'"/>


<xsl:template name="cxxGetString">
  <xsl:param name="stringName"/>
  <xsl:call-template name="getString">
    <xsl:with-param name="stringName" select="$stringName"/>
    <xsl:with-param name="stringFileList">cxxapistrings.xml</xsl:with-param>
  </xsl:call-template>
</xsl:template>

<!-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   - Suppressed processing
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->
<!-- always process definitions in a mode for a specific purpose -->
<xsl:template match="*[contains(@class,' apiRef/apiDef ')]"/>

<!-- process the package, class, and interface name as part of the
     body processing -->
<xsl:template match="*[contains(@class,' cxxPackage/cxxPackage ') or
        contains(@class,' cxxClass/cxxClass ') or
        contains(@class,' cxxInterface/cxxInterface ')] /
    *[contains(@class,' apiRef/apiName ')]"/>

<!-- process the members as part of the body processing -->
<xsl:template match="*[contains(@class,' cxxClass/cxxClass ') or
        contains(@class,' cxxInterface/cxxInterface ')] /
    *[contains(@class,' cxxMethod/cxxMethod ') or
        contains(@class,' cxxField/cxxField ')]"/>

<!-- process the parent package for a class or interface
     as part of the body processing -->
<xsl:template match="*[contains(@class,' topic/link ') and
    @type='cxxPackage' and @role='parent']" priority="3"/>

<!-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   - Alternatives to base processing
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->
<xsl:template match="*[
        contains(@class,' cxxPackage/cxxPackage '    ) or
        contains(@class,' cxxClass/cxxClass '        ) or
        contains(@class,' cxxInterface/cxxInterface ') or
        contains(@class,' cxxField/cxxField '        ) or
        contains(@class,' cxxMethod/cxxMethod '      )] /
    *[contains(@class,' apiRef/apiName ')]" mode="default">
  <xsl:apply-imports/>
</xsl:template>

<xsl:template match="/*[
        contains(@class,' cxxPackage/cxxPackage '    ) or
        contains(@class,' cxxClass/cxxClass '        ) or
        contains(@class,' cxxInterface/cxxInterface ')]">
  <xsl:call-template name="cxxapi-chapter-setup"/>
</xsl:template>

<xsl:template name="cxxapi-chapter-setup">
  <html>
    <xsl:call-template name="setTopicLanguage"/>
    <xsl:value-of select="$newline"/>
    <xsl:call-template name="cxxapiChapterHead"/>
    <xsl:call-template name="cxxapiChapterBody"/>
  </html>
</xsl:template>

<xsl:template name="cxxapiChapterHead">
  <head><xsl:value-of select="$newline"/>
    <!-- initial meta information -->
    <xsl:call-template name="generateCharset"/>   <!-- Set the character set to UTF-8 -->
    <xsl:call-template name="generateDefaultCopyright"/> <!-- Generate a default copyright, if needed -->
    <xsl:call-template name="generateDefaultMeta"/> <!-- Standard meta for security, robots, etc -->
    <xsl:call-template name="getMeta"/>           <!-- Process metadata from topic prolog -->
    <xsl:call-template name="generateCssLinks"/>  <!-- Generate links to defaultCSS files -->
    <xsl:call-template name="cxxapiGenerateCssLinks"/>  <!-- Generate links to CSS files -->
    <xsl:call-template name="generateChapterTitle"/> <!-- Generate the <title> element -->
    <xsl:call-template name="cxxapi-gen-user-head" />    <!-- include user's XSL HEAD processing here -->
    <xsl:call-template name="cxxapi-gen-user-scripts" /> <!-- include user's XSL cxxscripts here -->
    <xsl:call-template name="cxxapi-gen-user-styles" />  <!-- include user's XSL style element and content here -->
    <xsl:call-template name="processHDF"/>        <!-- Add user HDF file, if specified -->
  </head>
  <xsl:value-of select="$newline"/>
</xsl:template>

<xsl:template name="cxxapiGenerateCssLinks">
  <xsl:variable name="childlang"><xsl:call-template name="getLowerCaseLang"/></xsl:variable>
  <xsl:variable name="urltest">
    <xsl:call-template name="url-string">
      <xsl:with-param name="urltext" select="$CSSPATH"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:choose>
    <xsl:when test="($childlang='ar-eg' or $childlang='ar' or $childlang='he' or $childlang='he-il') and ($urltest='url')">
      <link rel="stylesheet" type="text/css" href="{$CSSPATH}{$CXXAPICSSRTL}" />
    </xsl:when>
    <xsl:when test="($childlang='ar-eg' or $childlang='ar' or $childlang='he' or $childlang='he-il') and ($urltest='')">
      <link rel="stylesheet" type="text/css" href="{$PATH2PROJ}{$CSSPATH}{$CXXAPICSSRTL}" />
    </xsl:when>
    <xsl:when test="not($childlang='ar-eg' or $childlang='ar' or $childlang='he' or $childlang='he-il') and ($urltest='url')">
      <link rel="stylesheet" type="text/css" href="{$CSSPATH}{$CXXAPICSS}" />
    </xsl:when>
    <xsl:otherwise>
      <link rel="stylesheet" type="text/css" href="{$PATH2PROJ}{$CSSPATH}{$CXXAPICSS}" />
    </xsl:otherwise>
  </xsl:choose>
  <xsl:value-of select="$newline"/>
</xsl:template>

<xsl:template name="cxxapiChapterBody">
  <body>
    <!-- Already put xml:lang on <html>; do not copy to body with commonattributes -->
    <xsl:call-template name="setidaname"/>
    <xsl:value-of select="$newline"/>
    <xsl:call-template name="flagit"/>
    <xsl:call-template name="start-revflag"/>
    <!-- xsl:call-template name="generateBreadcrumbs"/ -->
    <xsl:call-template name="cxxapi-gen-user-header"/>  <!-- include user's XSL running header here -->
    <xsl:call-template name="processHDR"/>
    <!-- Include a user's XSL call here to generate a toc based on what's a child of topic -->
    <xsl:call-template name="cxxapi-gen-user-sidetoc"/>
    <xsl:apply-templates/> <!-- this will include all things within topic; therefore, -->
                           <!-- title content will appear here by fall-through -->
                           <!-- followed by prolog (but no fall-through is permitted for it) -->
                           <!-- followed by body content, again by fall-through in document order -->
                           <!-- followed by related links -->
                           <!-- followed by child topics by fall-through -->

    <xsl:call-template name="gen-endnotes"/>    <!-- include footnote-endnotes -->
    <xsl:call-template name="cxxapi-gen-user-footer"/> <!-- include user's XSL running footer here -->
    <xsl:call-template name="processFTR"/>      <!-- Include XHTML footer, if specified -->
    <xsl:call-template name="end-revflag"/>
  </body>
  <xsl:value-of select="$newline"/>
</xsl:template>


<!-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   - Hooks
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->
<xsl:template name="cxxapi-gen-user-head">
  <!-- by default, execute the default user head -->
  <xsl:call-template name="gen-user-head"/>
</xsl:template>

<xsl:template name="cxxapi-gen-user-scripts">
  <!-- by default, execute the default user scripts -->
  <xsl:call-template name="gen-user-scripts"/>
</xsl:template>

<xsl:template name="cxxapi-gen-user-styles">
  <!-- by default, execute the default user styles -->
  <xsl:call-template name="gen-user-styles"/>
</xsl:template>

<xsl:template name="cxxapi-gen-user-header">
  <!-- by default, execute the default user header -->
  <xsl:call-template name="gen-user-header"/>
</xsl:template>

<xsl:template name="cxxapi-gen-user-sidetoc">
  <!-- by default, execute the default user sidetoc -->
  <xsl:call-template name="gen-user-sidetoc"/>
</xsl:template>

<xsl:template name="cxxapi-gen-user-footer">
  <!-- by default, execute the default user footer -->
  <xsl:call-template name="gen-user-footer"/>
</xsl:template>


<!-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   - Package processing
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->
<!-- BASED ON topic/body PROCESSING IN dit2htm -->
<xsl:template match="*[contains(@class,' cxxPackage/cxxPackageDetail ')]">
<div>
  <xsl:call-template name="commonattributes"/>
  <xsl:call-template name="setidaname"/>
  <xsl:call-template name="flagit"/>
  <xsl:call-template name="start-revflag"/>

  <xsl:apply-templates select=".." mode="nameheader"/>

  <xsl:apply-templates
      select="preceding-sibling::*[contains(@class,' topic/shortdesc ')]"
      mode="outofline"/>

  <xsl:apply-templates select="../*[contains(@class,' topic/related-links ')]"
      mode="cxxpackage"/>

  <h3 class="packageDescriptionHead">
    <xsl:apply-templates select=".." mode="nametype"/>
    <xsl:text> </xsl:text>
    <xsl:apply-templates
        select="preceding-sibling::*[contains(@class,' apiRef/apiName ')]"
        mode="default"/>
    <xsl:text> </xsl:text>
    <xsl:call-template name="getString">
      <xsl:with-param name="stringName" select="'Description'"/>
    </xsl:call-template>
  </h3>
  <xsl:apply-templates/>

  <xsl:call-template name="end-revflag"/>
</div>
<xsl:value-of select="$newline"/>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxPackage/cxxPackage ')] /
      *[contains(@class,' topic/related-links ')]"/>

<xsl:template match="*[contains(@class,' cxxPackage/cxxPackage ')] /
      *[contains(@class,' topic/related-links ')]" mode="cxxpackage">
  <xsl:variable name="subPackageNodes" select="
      *[contains(@class,' topic/linkpool ')] /
      *[contains(@class,' topic/linkpool ')] /
      *[contains(@class,' topic/link ') and
          contains(@mapclass,' cxxAPIMap/cxxPackageRef ') and
          @role='child']"/>
  <xsl:variable name="interfaceNodes" select="
      *[contains(@class,' topic/linkpool ')] /
      *[contains(@class,' topic/linkpool ')] /
      *[contains(@class,' topic/link ') and
          contains(@mapclass,' cxxAPIMap/cxxInterfaceRef ') and
          @role='child']"/>
  <xsl:variable name="classNodes" select="
      *[contains(@class,' topic/linkpool ')] /
      *[contains(@class,' topic/linkpool ')] /
      *[contains(@class,' topic/link ') and
          contains(@mapclass,' cxxAPIMap/cxxClassRef ') and
          @role='child']"/>
  <xsl:variable name="exceptionNodes" select="
      *[contains(@class,' topic/linkpool ')] /
      *[contains(@class,' topic/linkpool ')] /
      *[contains(@class,' topic/link ') and
          contains(@mapclass,' cxxAPIMap/cxxExceptionClassRef ') and
          @role='child']"/>
  <xsl:variable name="errorNodes" select="
      *[contains(@class,' topic/linkpool ')] /
      *[contains(@class,' topic/linkpool ')] /
      *[contains(@class,' topic/link ') and
          contains(@mapclass,' cxxAPIMap/cxxErrorClassRef ') and
          @role='child']"/>
  <xsl:if test="$subPackageNodes">
    <table class="packageSubpackageSummary">
      <tr>
        <th align="left" valign="top" colspan="2" class="apiSummaryHead">
          <xsl:call-template name="cxxGetString">
            <xsl:with-param name="stringName" select="'cxxPackageHead'"/>
          </xsl:call-template>
        </th>
      </tr>
      <xsl:apply-templates select="$subPackageNodes" mode="packageSummary"/>
    </table>
  </xsl:if>
  <xsl:if test="$interfaceNodes">
    <table class="packageInterfaceSummary">
      <tr>
        <th align="left" valign="top" colspan="2" class="apiSummaryHead">
          <xsl:call-template name="cxxGetString">
            <xsl:with-param name="stringName" select="'cxxInterfaceHead'"/>
          </xsl:call-template>
        </th>
      </tr>
      <xsl:apply-templates select="$interfaceNodes" mode="packageSummary"/>
    </table>
  </xsl:if>
  <xsl:if test="$classNodes">
    <table class="packageClassSummary">
      <tr>
        <th align="left" valign="top" colspan="2" class="apiSummaryHead">
          <xsl:call-template name="cxxGetString">
            <xsl:with-param name="stringName" select="'cxxClassHead'"/>
          </xsl:call-template>
        </th>
      </tr>
      <xsl:apply-templates select="$classNodes" mode="packageSummary"/>
    </table>
  </xsl:if>
  <xsl:if test="$exceptionNodes">
    <table class="packageClassSummary">
      <tr>
        <th align="left" valign="top" colspan="2" class="apiSummaryHead">
          <xsl:call-template name="cxxGetString">
            <xsl:with-param name="stringName" select="'cxxExceptionHead'"/>
          </xsl:call-template>
        </th>
      </tr>
      <xsl:apply-templates select="$exceptionNodes" mode="packageSummary"/>
    </table>
  </xsl:if>
  <xsl:if test="$errorNodes">
    <table class="packageClassSummary">
      <tr>
        <th align="left" valign="top" colspan="2" class="apiSummaryHead">
          <xsl:call-template name="cxxGetString">
            <xsl:with-param name="stringName" select="'cxxErrorHead'"/>
          </xsl:call-template>
        </th>
      </tr>
      <xsl:apply-templates select="$errorNodes" mode="packageSummary"/>
    </table>
  </xsl:if>
</xsl:template>

<xsl:template match="*[contains(@class,' topic/link ') and @role='child']"
      mode="packageSummary">
  <xsl:variable name="file">
    <xsl:call-template name="getTopicFile"/>
  </xsl:variable>
  <xsl:variable name="topicid">
    <xsl:call-template name="getTopicID"/>
  </xsl:variable>
  <xsl:variable name="fileDocument" select="document($file,/)"/>
  <xsl:variable name="topicNode"
    select="($fileDocument[$topicid = '#none#']//*[contains(@class, ' topic/topic ')])[1] |
        $fileDocument[$topicid != '#none#']//*[contains(@class, ' topic/topic ')][@id=$topicid]"/>
  <xsl:variable name="topicTitleNode"
    select="$topicNode/*[contains(@class, ' topic/title ')]"/>
  <xsl:variable name="topicShortDescNode"
    select="$topicNode/*[contains(@class, ' topic/shortdesc ')]"/>
  <xsl:if test="not($topicNode)">
    <xsl:message>
      <xsl:text>$file=</xsl:text>
      <xsl:value-of select="$file"/>
      <xsl:text>, $topicid=</xsl:text>
      <xsl:value-of select="$topicid"/>
      <xsl:text>, $fileDocument is</xsl:text>
      <xsl:value-of select="boolean($fileDocument)"/>
      <xsl:text>, $topicNode is</xsl:text>
      <xsl:value-of select="boolean($topicNode)"/>
      <xsl:text>, $topicTitleNode=</xsl:text>
      <xsl:value-of select="$topicTitleNode"/>
      <xsl:text>, $topicShortDescNode=</xsl:text>
      <xsl:value-of select="$topicShortDescNode"/>
    </xsl:message>
  </xsl:if>
  <tr>
    <td valign="top" class="apiPackageListName">
      <a>
        <xsl:attribute name="href">
          <xsl:call-template name="href"/>
        </xsl:attribute>
	    <xsl:apply-templates select="$topicTitleNode/node()" mode="default"/>
      </a>
    </td>
    <td valign="top" class="apiPackageListDesc">
      <xsl:choose>
      <xsl:when test="$topicShortDescNode">
	    <xsl:apply-templates
            select="$topicShortDescNode/*|$topicShortDescNode/text()"/>
      </xsl:when>
      <xsl:otherwise>
	    <xsl:apply-templates select="$topicTitleNode/node()" mode="default"/>
      </xsl:otherwise>
      </xsl:choose>
    </td>
  </tr>
</xsl:template>


<!-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   - Class and interface prodcessing
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->
<xsl:template match="*[contains(@class,' cxxClass/cxxClassDetail ') or
      contains(@class,' cxxInterface/cxxInterfaceDetail ')]">
  <xsl:apply-templates select=".." mode="checkClass">
    <xsl:with-param name="classDetail" select="."/>
  </xsl:apply-templates>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxClass/cxxClass ')]"
      mode="checkClass">
  <xsl:param name="classDetail"/>
  <xsl:param name="baseClasses"/>
  <xsl:param name="baseRefs"/>
  <xsl:param name="isFirstBase" select="true()"/>
  <xsl:variable name="baseRef" select="
        *[contains(@class,' cxxClass/cxxClassDetail ')] /
        *[contains(@class,' cxxClass/cxxClassDef ')] /
        *[contains(@class,' cxxClass/cxxBaseClass ')]"/>
  <xsl:call-template name="getBaseClass">
    <xsl:with-param name="classDetail" select="$classDetail"/>
    <xsl:with-param name="baseClasses" select="$baseClasses"/>
    <xsl:with-param name="baseRefs"    select="$baseRefs"/>
    <xsl:with-param name="baseRef"     select="$baseRef"/>
    <xsl:with-param name="isFirstBase" select="$isFirstBase"/>
  </xsl:call-template>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxInterface/cxxInterface ')]"
      mode="checkClass">
  <xsl:param name="classDetail"/>
  <xsl:param name="baseClasses"/>
  <xsl:param name="baseRefs"/>
  <xsl:param name="isFirstBase" select="true()"/>
  <xsl:variable name="baseRef" select="
        *[contains(@class,' cxxInterface/cxxInterfaceDetail ')] /
        *[contains(@class,' cxxInterface/cxxInterfaceDef ')] /
        *[contains(@class,' cxxInterface/cxxBaseInterface ')]"/>
  <xsl:call-template name="getBaseClass">
    <xsl:with-param name="classDetail" select="$classDetail"/>
    <xsl:with-param name="baseClasses" select="$baseClasses"/>
    <xsl:with-param name="baseRefs"    select="$baseRefs"/>
    <xsl:with-param name="baseRef"     select="$baseRef"/>
    <xsl:with-param name="isFirstBase" select="$isFirstBase"/>
  </xsl:call-template>
</xsl:template>

<xsl:template name="getBaseClass">
  <xsl:param name="classDetail"/>
  <xsl:param name="baseClasses"/>
  <xsl:param name="baseRefs"/>
  <xsl:param name="baseRef"/>
  <xsl:param name="isFirstBase"/>
  <xsl:choose>
  <xsl:when test="$baseRef and $baseRef/@href and
        (not($baseRef/@format) or $baseRef/@format='dita')">
    <xsl:variable name="href" select="$baseRef/@href"/>
    <xsl:variable name="file">
      <xsl:call-template name="getTopicFile">
        <xsl:with-param name="href" select="$href"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="topicID">
      <xsl:call-template name="getTopicID">
          <xsl:with-param name="href" select="$href"/>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="baseDocument" select="document($file, /)"/>
    <xsl:variable name="baseClass" select="
        ($baseDocument[$topicID = '#none#'] //
            *[contains(@class, ' topic/topic ')])[1] |
        $baseDocument[$topicID != '#none#'] //
            *[contains(@class, ' topic/topic ')][@id=$topicID]"/>
    <xsl:choose>
    <xsl:when test="$baseClass">
      <xsl:choose>
      <xsl:when test="$isFirstBase">
        <xsl:apply-templates select="$baseClass" mode="checkClass">
          <xsl:with-param name="classDetail" select="$classDetail"/>
          <xsl:with-param name="baseClasses" select="$baseClass"/>
          <xsl:with-param name="baseRefs"    select="$baseRef"/>
          <xsl:with-param name="isFirstBase" select="false()"/>
        </xsl:apply-templates>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="$baseClass" mode="checkClass">
          <xsl:with-param name="classDetail" select="$classDetail"/>
          <xsl:with-param name="baseClasses" select="$baseClass|$baseClasses"/>
          <xsl:with-param name="baseRefs"    select="$baseRef|$baseRefs"/>
          <xsl:with-param name="isFirstBase" select="false()"/>
        </xsl:apply-templates>
      </xsl:otherwise>
      </xsl:choose>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="formatClass">
        <xsl:with-param name="classDetail" select="$classDetail"/>
        <xsl:with-param name="baseClasses" select="$baseClasses"/>
        <xsl:with-param name="baseRefs"    select="$baseRefs"/>
        <xsl:with-param name="hasBase"     select="not($isFirstBase)"/>
      </xsl:call-template>
    </xsl:otherwise>
    </xsl:choose>
  </xsl:when>
  <xsl:otherwise>
    <xsl:call-template name="formatClass">
      <xsl:with-param name="classDetail" select="$classDetail"/>
      <xsl:with-param name="baseClasses" select="$baseClasses"/>
      <xsl:with-param name="baseRefs"    select="$baseRefs"/>
      <xsl:with-param name="hasBase"     select="not($isFirstBase)"/>
    </xsl:call-template>
  </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="formatClass">
  <xsl:param name="classDetail"/>
  <xsl:param name="baseClasses"/>
  <xsl:param name="baseRefs"/>
  <xsl:param name="hasBase"/>
  <xsl:apply-templates select="$classDetail" mode="formatClass">
    <xsl:with-param name="baseClasses" select="$baseClasses"/>
    <xsl:with-param name="baseRefs"    select="$baseRefs"/>
    <xsl:with-param name="hasBase"     select="$hasBase"/>
  </xsl:apply-templates>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxClass/cxxClassDetail ') or
          contains(@class,' cxxInterface/cxxInterfaceDetail ')]"
      mode="formatClass">
  <xsl:param name="baseClasses"/>
  <xsl:param name="baseRefs"/>
  <xsl:param name="hasBase"/>
  <xsl:variable name="constructorNodes" select="
      following-sibling::*[contains(@class,' cxxMethod/cxxMethod ') and
          *[contains(@class,' cxxMethod/cxxMethodDetail ') and
              *[contains(@class,' cxxMethod/cxxConstructorDef ') and
                  *[contains(@class,' cxxMethod/cxxMethodAccess ') and
                      @value='public'] ] ] ]"/>
  <xsl:variable name="fieldNodes" select="
      following-sibling::*[contains(@class,' cxxField/cxxField ') and
          *[contains(@class,' cxxField/cxxFieldDetail ') and
              *[contains(@class,' cxxField/cxxFieldDef ') and
                  *[contains(@class,' cxxField/cxxFieldAccess ') and
                      @value='public'] ] ] ]"/>
  <xsl:variable name="methodNodes" select="
      following-sibling::*[contains(@class,' cxxMethod/cxxMethod ') and
          *[contains(@class,' cxxMethod/cxxMethodDetail ') and
              *[contains(@class,' cxxMethod/cxxMethodDef ') and
                  *[contains(@class,' cxxMethod/cxxMethodAccess ') and
                      @value='public'] ] ] ]"/>

<div>
  <xsl:call-template name="commonattributes"/>
  <xsl:call-template name="setidaname"/>
  <xsl:call-template name="flagit"/>
  <xsl:call-template name="start-revflag"/>

  <xsl:comment>name header</xsl:comment>
  <xsl:apply-templates select=".." mode="nameheader"/>

  <xsl:comment>ancestry header</xsl:comment>
  <xsl:apply-templates select=".." mode="formatAncestry">
    <xsl:with-param name="baseClasses" select="$baseClasses"/>
    <xsl:with-param name="baseRefs"    select="$baseRefs"/>
    <xsl:with-param name="hasBase"     select="$hasBase"/>
  </xsl:apply-templates>

  <hr/>

  <xsl:comment>signature summary</xsl:comment>
  <xsl:apply-templates select=".." mode="signatureSummary"/>

  <xsl:comment>description</xsl:comment>
  <xsl:apply-templates
      select="preceding-sibling::*[contains(@class,' topic/shortdesc ')]"
      mode="outofline"/>
  <xsl:apply-templates/>

  <xsl:comment>see also</xsl:comment>
  <xsl:apply-templates
      select="following-sibling::*[contains(@class,' topic/related-links ')]"/>

  <hr/>

  <xsl:comment>member summary</xsl:comment>

  <xsl:if test="$fieldNodes">
    <table class="fieldSummary">
      <tr>
        <th align="left" valign="top" colspan="2" class="apiSummaryHead">
          <xsl:call-template name="cxxGetString">
            <xsl:with-param name="stringName" select="'cxxFieldHead'"/>
          </xsl:call-template>
        </th>
      </tr>
      <xsl:apply-templates select="$fieldNodes" mode="memberSummary"/>
    </table>
  </xsl:if>

  <xsl:if test="$hasBase">
    <xsl:call-template name="listBaseFields">
      <xsl:with-param name="baseClasses" select="$baseClasses"/>
      <xsl:with-param name="baseRefs"    select="$baseRefs"/>
    </xsl:call-template>
  </xsl:if>

  <xsl:if test="$constructorNodes">
    <table class="constructorSummary">
      <tr>
        <th align="left" valign="top" class="apiSummaryHead">
          <xsl:call-template name="cxxGetString">
            <xsl:with-param name="stringName" select="'cxxConstructorHead'"/>
          </xsl:call-template>
        </th>
      </tr>
      <xsl:apply-templates select="$constructorNodes"
          mode="signatureSummary"/>
    </table>
  </xsl:if>

  <xsl:if test="$methodNodes">
    <table class="methodSummary">
      <tr>
        <th align="left" valign="top" colspan="2" class="apiSummaryHead">
          <xsl:call-template name="cxxGetString">
            <xsl:with-param name="stringName" select="'cxxMethodHead'"/>
          </xsl:call-template>
        </th>
      </tr>
      <xsl:apply-templates select="$methodNodes" mode="memberSummary"/>
    </table>
  </xsl:if>

  <xsl:if test="$hasBase">
    <xsl:call-template name="listBaseMethods">
      <xsl:with-param name="baseClasses" select="$baseClasses"/>
      <xsl:with-param name="baseRefs"    select="$baseRefs"/>
    </xsl:call-template>
  </xsl:if>

  <xsl:comment>member detail</xsl:comment>

  <xsl:if test="$constructorNodes">
    <p class="cxxConstructorDetail">
      <xsl:call-template name="cxxGetString">
        <xsl:with-param name="stringName" select="'cxxConstructorDetail'"/>
      </xsl:call-template>
    </p>
    <xsl:apply-templates select="$constructorNodes" mode="memberDetail"/>
  </xsl:if>

  <xsl:if test="$methodNodes">
    <p class="cxxMethodDetail">
      <xsl:call-template name="cxxGetString">
        <xsl:with-param name="stringName" select="'cxxMethodDetail'"/>
      </xsl:call-template>
    </p>
    <xsl:apply-templates select="$methodNodes" mode="memberDetail"/>
  </xsl:if>

  <xsl:call-template name="end-revflag"/>
</div>
<xsl:value-of select="$newline"/>
</xsl:template>


<!-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   - Base listing
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->
<xsl:template name="listBaseFields">
  <xsl:param name="baseClasses"/>
  <xsl:param name="baseRefs"/>
  <xsl:param name="baseCount" select="count($baseClasses)"/>
  <xsl:param name="currBase"  select="$baseCount"/>
  <xsl:if test="$currBase &gt; 0">
    <xsl:apply-templates select="$baseClasses[$currBase]"
        mode="baseFieldListing">
      <xsl:with-param name="baseRef" select="$baseRefs[$currBase]"/>
    </xsl:apply-templates>
    <xsl:call-template name="listBaseFields">
      <xsl:with-param name="baseClasses" select="$baseClasses"/>
      <xsl:with-param name="baseRefs"    select="$baseRefs"/>
      <xsl:with-param name="baseCount"   select="$baseCount"/>
      <xsl:with-param name="currBase"    select="$currBase - 1"/>
    </xsl:call-template>
  </xsl:if>
</xsl:template>

<xsl:template name="listBaseMethods">
  <xsl:param name="baseClasses"/>
  <xsl:param name="baseRefs"/>
  <xsl:param name="baseCount" select="count($baseClasses)"/>
  <xsl:param name="currBase"  select="$baseCount"/>
  <xsl:if test="$currBase &gt; 0">
    <xsl:apply-templates select="$baseClasses[$currBase]"
        mode="baseMethodListing">
      <xsl:with-param name="baseRef" select="$baseRefs[$currBase]"/>
    </xsl:apply-templates>
    <xsl:call-template name="listBaseMethods">
      <xsl:with-param name="baseClasses" select="$baseClasses"/>
      <xsl:with-param name="baseRefs"    select="$baseRefs"/>
      <xsl:with-param name="baseCount"   select="$baseCount"/>
      <xsl:with-param name="currBase"    select="$currBase - 1"/>
    </xsl:call-template>
  </xsl:if>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxClass/cxxClass ') or
          contains(@class,' cxxInterface/cxxInterface ')]"
      mode="baseFieldListing">
  <xsl:param name="baseRef"/>
  <xsl:variable name="fieldNodes" select="
      *[contains(@class,' cxxField/cxxField ') and
          *[contains(@class,' cxxField/cxxFieldDetail ') and
              *[contains(@class,' cxxField/cxxFieldDef ') and
                  *[contains(@class,' cxxField/cxxFieldAccess ') and
                      @value='public'] ] ] ]"/>
  <xsl:apply-templates select="." mode="baseMemberListing">
    <xsl:with-param name="baseRef"    select="$baseRef"/>
    <xsl:with-param name="memberType" select="'cxxBaseFieldHead'"/>
    <xsl:with-param name="members"    select="$fieldNodes"/>
  </xsl:apply-templates>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxClass/cxxClass ') or
          contains(@class,' cxxInterface/cxxInterface ')]"
      mode="baseMethodListing">
  <xsl:param name="baseRef"/>
  <xsl:variable name="methodNodes" select="
      *[contains(@class,' cxxMethod/cxxMethod ') and
          *[contains(@class,' cxxMethod/cxxMethodDetail ') and
              *[contains(@class,' cxxMethod/cxxMethodDef ') and
                  *[contains(@class,' cxxMethod/cxxMethodAccess ') and
                      @value='public'] ] ] ]"/>
  <xsl:apply-templates select="." mode="baseMemberListing">
    <xsl:with-param name="baseRef"    select="$baseRef"/>
    <xsl:with-param name="memberType" select="'cxxBaseMethodHead'"/>
    <xsl:with-param name="members"    select="$methodNodes"/>
  </xsl:apply-templates>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxClass/cxxClass ') or
          contains(@class,' cxxInterface/cxxInterface ')]"
      mode="baseMemberListing">
  <xsl:param name="baseRef"/>
  <xsl:param name="memberType"/>
  <xsl:param name="members"/>
  <xsl:if test="$members">
    <xsl:variable name="baseFile">
      <xsl:call-template name="getOutputFile">
        <xsl:with-param name="href" select="$baseRef/@href"/>
      </xsl:call-template>
    </xsl:variable>
    <table class="baseSummary">
      <tr>
        <th align="left" valign="top" colspan="2" class="apiSummaryHead">
          <xsl:call-template name="cxxGetString">
            <xsl:with-param name="stringName" select="$memberType"/>
          </xsl:call-template>
          <xsl:text> </xsl:text>
          <a class="baseHeader" href="{$baseFile}">
            <xsl:apply-templates
                select="*[contains(@class, ' apiRef/apiName ')]"
                mode="default"/>
          </a>
        </th>
      </tr>
      <tr>
        <td valign="top">
	      <xsl:for-each select="$members">
            <xsl:apply-templates select="." mode="baseListing">
              <xsl:with-param name="baseFile" select="$baseFile"/>
              <xsl:with-param name="topicID"  select="@id"/>
            </xsl:apply-templates>
            <xsl:if test="position()&lt;last()">
              <xsl:text>, </xsl:text>
            </xsl:if>
    	  </xsl:for-each>
        </td>
      </tr>
    </table>
  </xsl:if>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxClass/cxxClass ') or
          contains(@class,' cxxInterface/cxxInterface ')]"
      mode="formatAncestry">
  <xsl:param name="baseClasses"/>
  <xsl:param name="baseRefs"/>
  <xsl:param name="hasBase"/>
  <xsl:variable name="currClass" select="."/>
  <pre>
    <xsl:choose>
    <xsl:when test="$hasBase">
      <xsl:apply-templates select="$baseClasses[1]" mode="formatTopBase">
        <xsl:with-param name="baseClasses" select="$baseClasses"/>
        <xsl:with-param name="baseRefs"    select="$baseRefs"/>
        <xsl:with-param name="hasBase"     select="$hasBase"/>
        <xsl:with-param name="currClass"   select="$currClass"/>
      </xsl:apply-templates>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates select="$currClass" mode="formatTopBase">
        <xsl:with-param name="hasBase"     select="$hasBase"/>
        <xsl:with-param name="currClass"   select="$currClass"/>
      </xsl:apply-templates>
    </xsl:otherwise>
    </xsl:choose>
  </pre>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxInterface/cxxInterface ')]"
      mode="formatTopBase">
  <xsl:param name="baseClasses"/>
  <xsl:param name="baseRefs"/>
  <xsl:param name="hasBase"/>
  <xsl:param name="currClass"/>
  <xsl:variable name="topBase" select="
          *[contains(@class,' cxxInterface/cxxInterfaceDetail ')] /
          *[contains(@class,' cxxInterface/cxxInterfaceDef ')] /
          *[contains(@class,' cxxInterface/cxxBaseInterface ')]"/>
  <xsl:call-template name="formatTopBase">
    <xsl:with-param name="baseClasses" select="$baseClasses"/>
    <xsl:with-param name="baseRefs"    select="$baseRefs"/>
    <xsl:with-param name="hasBase"     select="$hasBase"/>
    <xsl:with-param name="currClass"   select="$currClass"/>
    <xsl:with-param name="topBase"     select="$topBase"/>
  </xsl:call-template>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxClass/cxxClass ')]"
      mode="formatTopBase">
  <xsl:param name="baseClasses"/>
  <xsl:param name="baseRefs"/>
  <xsl:param name="hasBase"/>
  <xsl:param name="currClass"/>
  <xsl:variable name="topBase" select="
          *[contains(@class,' cxxClass/cxxClassDetail ')] /
          *[contains(@class,' cxxClass/cxxClassDef ')] /
          *[contains(@class,' cxxClass/cxxBaseClass ')]"/>
  <xsl:call-template name="formatTopBase">
    <xsl:with-param name="baseClasses" select="$baseClasses"/>
    <xsl:with-param name="baseRefs"    select="$baseRefs"/>
    <xsl:with-param name="hasBase"     select="$hasBase"/>
    <xsl:with-param name="currClass"   select="$currClass"/>
    <xsl:with-param name="topBase"     select="$topBase"/>
  </xsl:call-template>
</xsl:template>

<xsl:template name="formatTopBase">
  <xsl:param name="baseClasses"/>
  <xsl:param name="baseRefs"/>
  <xsl:param name="hasBase"/>
  <xsl:param name="currClass"/>
  <xsl:param name="topBase"/>
  <xsl:choose>
  <xsl:when test="$topBase">
    <xsl:text>+-- </xsl:text>
    <xsl:choose>
    <xsl:when test="$topBase/@href">
      <a class="ancestrylink" href="{$topBase/@href}">
        <xsl:value-of select="$topBase"/>
      </a>
    </xsl:when>
    <xsl:otherwise>
      <span class="ancestrybase">
        <xsl:value-of select="$topBase"/>
      </span>
    </xsl:otherwise>
    </xsl:choose>
    <xsl:value-of select="$newline"/>
    <xsl:call-template name="completeBaseSummary">
      <xsl:with-param name="baseClasses" select="$baseClasses"/>
      <xsl:with-param name="baseRefs"    select="$baseRefs"/>
      <xsl:with-param name="hasBase"     select="$hasBase"/>
      <xsl:with-param name="currClass"   select="$currClass"/>
      <xsl:with-param name="indent"      select="'      '"/>
    </xsl:call-template>
  </xsl:when>
  <xsl:otherwise>
    <xsl:call-template name="completeBaseSummary">
      <xsl:with-param name="baseClasses" select="$baseClasses"/>
      <xsl:with-param name="baseRefs"    select="$baseRefs"/>
      <xsl:with-param name="hasBase"     select="$hasBase"/>
      <xsl:with-param name="currClass"   select="$currClass"/>
    </xsl:call-template>
  </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="completeBaseSummary">
  <xsl:param name="baseClasses"/>
  <xsl:param name="baseRefs"/>
  <xsl:param name="hasBase"/>
  <xsl:param name="currClass"/>
  <xsl:param name="indent" select="''"/>
  <xsl:choose>
  <xsl:when test="$hasBase">
    <xsl:call-template name="baseSummary">
      <xsl:with-param name="baseClasses" select="$baseClasses"/>
      <xsl:with-param name="baseRefs"    select="$baseRefs"/>
      <xsl:with-param name="currClass"   select="$currClass"/>
      <xsl:with-param name="indent"      select="$indent"/>
    </xsl:call-template>
  </xsl:when>
  <xsl:otherwise>
    <xsl:call-template name="currClassSummary">
      <xsl:with-param name="currClass" select="$currClass"/>
      <xsl:with-param name="indent"    select="$indent"/>
    </xsl:call-template>
  </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="baseSummary">
  <xsl:param name="baseClasses"/>
  <xsl:param name="baseRefs"/>
  <xsl:param name="currClass"/>
  <xsl:param name="currBase"  select="1"/>
  <xsl:param name="baseCount" select="count($baseClasses)"/>
  <xsl:param name="indent"    select="''"/>
  <xsl:choose>
  <xsl:when test="$currBase &lt;= $baseCount">
    <xsl:variable name="filename">
      <xsl:call-template name="getOutputFile">
        <xsl:with-param name="href" select="$baseRefs[$currBase]/@href"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:value-of select="$indent"/>
    <xsl:text>+-- </xsl:text>
    <a class="ancestrylink" href="{$filename}">
      <xsl:value-of select="$baseClasses[$currBase] /
          *[contains(@class,' apiRef/apiName ')]"/>
    </a>
    <xsl:value-of select="$newline"/>
    <xsl:call-template name="baseSummary">
      <xsl:with-param name="baseClasses" select="$baseClasses"/>
      <xsl:with-param name="baseRefs"    select="$baseRefs"/>
      <xsl:with-param name="currClass"   select="$currClass"/>
      <xsl:with-param name="currBase"    select="$currBase+1"/>
      <xsl:with-param name="baseCount"   select="$baseCount"/>
      <xsl:with-param name="indent"      select="concat($indent,'      ')"/>
    </xsl:call-template>
  </xsl:when>
  <xsl:otherwise>
    <xsl:call-template name="currClassSummary">
      <xsl:with-param name="currClass" select="$currClass"/>
      <xsl:with-param name="indent"    select="$indent"/>
    </xsl:call-template>
  </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="currClassSummary">
  <xsl:param name="currClass"/>
  <xsl:param name="indent" select="''"/>
  <xsl:value-of select="$indent"/>
  <xsl:text>+-- </xsl:text>
  <span class="ancestryself">
    <xsl:value-of select="$currClass/*[contains(@class,' apiRef/apiName ')]"/>
  </span>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxPackage/cxxPackage ')]"
      mode="nameheader">
  <h2 class="topHead">
    <xsl:apply-templates select="." mode="nametype"/>
    <xsl:text> </xsl:text>
    <xsl:apply-templates select="*[contains(@class,' apiRef/apiName ')]"
        mode="default"/>
  </h2>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxClass/cxxClass ') or
          contains(@class,' cxxInterface/cxxInterface ')]"
      mode="nameheader">
  <xsl:apply-templates select="
          *[contains(@class,' topic/related-links ')] /
          *[contains(@class,' topic/linkpool ')] /
          *[contains(@class,' topic/link ') and
              @type='cxxPackage' and @role='parent']"
      mode="header"/>
  <h2 class="topHead">
    <xsl:apply-templates select="." mode="nametype"/>
    <xsl:text> </xsl:text>
    <xsl:apply-templates select="*[contains(@class,' apiRef/apiName ')]"
        mode="default"/>
  </h2>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxPackage/cxxPackage ')]"
      mode="nametype">
  <xsl:call-template name="cxxGetString">
    <xsl:with-param name="stringName" select="'cxxPackage'"/>
  </xsl:call-template>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxClass/cxxClass ')]"
      mode="nametype">
  <xsl:call-template name="cxxGetString">
    <xsl:with-param name="stringName" select="'cxxClass'"/>
  </xsl:call-template>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxInterface/cxxInterface ')]"
      mode="nametype">
  <xsl:call-template name="cxxGetString">
    <xsl:with-param name="stringName" select="'cxxInterface'"/>
  </xsl:call-template>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxField/cxxField ') or
          contains(@class,' cxxMethod/cxxMethod ')]"
      mode="baseListing">
  <xsl:param name="baseFile"/>
  <xsl:param name="topicID"/>
  <a href="{$baseFile}#{@id}" class="baselink">
    <xsl:apply-templates select="*[contains(@class,' apiRef/apiName ')]"
        mode="apiSignature"/>
  </a>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxClass/cxxClass ') or
          contains(@class,' cxxInterface/cxxInterface ')]"
      mode="baseListing">
  <xsl:param name="baseFile"/>
  <xsl:param name="topicID"/>
  <xsl:param name="isFirstListing"/>
  <xsl:variable name="methodNodes" select="
      *[contains(@class,' cxxMethod/cxxMethod ') and
          *[contains(@class,' cxxMethod/cxxMethodDetail ') and
              *[contains(@class,' cxxMethod/cxxMethodDef ') and
                  *[contains(@class,' cxxMethod/cxxMethodAccess ') and
                      @value='public'] ] ] ]"/>
  <xsl:choose>
  <xsl:when test="$methodNodes">
      <xsl:call-template name="baseListingRows">
        <xsl:with-param name="baseFile"    select="$baseFile"/>
        <xsl:with-param name="topicID"     select="$topicID"/>
        <xsl:with-param name="methodNodes" select="$methodNodes"/>
      </xsl:call-template>
    <xsl:apply-templates select="." mode="checkBase">
      <xsl:with-param name="isFirstListing" select="false()"/>
    </xsl:apply-templates>
  </xsl:when>
  <xsl:otherwise>
    <xsl:apply-templates select="." mode="checkBase">
      <xsl:with-param name="isFirstListing" select="$isFirstListing"/>
    </xsl:apply-templates>
  </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="baseListingRows">
  <xsl:param name="baseFile"/>
  <xsl:param name="topicID"/>
  <xsl:param name="methodNodes"/>
  <tr>
    <th align="left" valign="top" colspan="2" class="apiSummaryHead">
      <xsl:call-template name="cxxGetString">
        <xsl:with-param name="stringName" select="'cxxBaseHead'"/>
      </xsl:call-template>
      <xsl:text> </xsl:text>
      <xsl:apply-templates select="*[contains(@class, ' topic/title ')]"
          mode="default"/>
    </th>
  </tr>
  <tr>
    <td valign="top">
	  <xsl:for-each select="$methodNodes">
        <xsl:apply-templates select="." mode="baseListing">
          <xsl:with-param name="baseFile" select="$baseFile"/>
          <xsl:with-param name="topicID"  select="$topicID"/>
        </xsl:apply-templates>
        <xsl:if test="position()&lt;last()">
          <xsl:text>, </xsl:text>
        </xsl:if>
	  </xsl:for-each>
    </td>
  </tr>
</xsl:template>

<xsl:template match="*[contains(@class,' topic/link ') and
        @type='cxxPackage' and @role='parent']" mode="header">
  <p>
    <a class="headPackage">
      <xsl:attribute name="href">
        <xsl:call-template name="href"/>
      </xsl:attribute>
      <xsl:apply-templates select="*[contains(@class,' topic/linktext ')]"/>
    </a>
  </p>
</xsl:template>


<!-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   - Member summary
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->
<xsl:template match="*[contains(@class,' cxxMethod/cxxMethodDef ') or
            contains(@class,' cxxMethod/cxxConstructorDef ')]"
      mode="memberSummary">
  <xsl:variable name="paramNodes"
          select="*[contains(@class,' cxxMethod/cxxParam ')]"/>
  <xsl:variable name="returnNode"
          select="*[contains(@class,' cxxMethod/cxxReturn ') and
              *[contains(@class,' apiRef/apiDefNote ')]]"/>
  <xsl:variable name="exceptionNodes"
      select="*[contains(@class,' cxxMethod/cxxException ')]"/>
  <xsl:if test="$paramNodes">
    <p class="cxxMethodDetailHeader">
      <xsl:call-template name="cxxGetString">
        <xsl:with-param name="stringName" select="'cxxParameterHead'"/>
      </xsl:call-template>
      <xsl:call-template name="getString">
        <xsl:with-param name="stringName" select="'ColonSymbol'"/>
      </xsl:call-template>
    </p>
    <table class="methodParameters">
      <xsl:apply-templates select="$paramNodes" mode="memberSummary"/>
    </table>
  </xsl:if>
  <xsl:if test="$returnNode">
    <p class="cxxMethodDetailHeader">
      <xsl:call-template name="cxxGetString">
        <xsl:with-param name="stringName" select="'cxxReturnHead'"/>
      </xsl:call-template>
      <xsl:call-template name="getString">
        <xsl:with-param name="stringName" select="'ColonSymbol'"/>
      </xsl:call-template>
    </p>
    <table class="methodReturns">
      <xsl:apply-templates select="$returnNode" mode="memberSummary"/>
    </table>
  </xsl:if>
  <xsl:if test="$exceptionNodes">
    <p class="cxxMethodDetailHeader">
      <xsl:call-template name="cxxGetString">
        <xsl:with-param name="stringName" select="'cxxThrowHead'"/>
      </xsl:call-template>
      <xsl:call-template name="getString">
        <xsl:with-param name="stringName" select="'ColonSymbol'"/>
      </xsl:call-template>
    </p>
    <table class="methodExceptions">
      <xsl:apply-templates select="$exceptionNodes" mode="memberSummary"/>
    </table>
  </xsl:if>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxVoid ')]"
      mode="memberSummary">
  <tr>
    <td valign="top">
      <xsl:apply-templates select="."/>
    </td>
  </tr>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxReturn ')]"
      mode="memberSummary">
  <tr>
    <td valign="top">
      <!-- should supply shortdesc for target if no contextual note -->
      <xsl:apply-templates select="*[contains(@class,' apiRef/apiDefNote ')]"/>
    </td>
  </tr>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxException ')]"
      mode="memberSummary">
  <tr>
    <td valign="top" class="exceptionListing">
      <xsl:apply-templates
          select="*[contains(@class,' cxxMethod/cxxMethodClass ')]"/>
    </td>
    <td valign="top">
      <xsl:apply-templates select="*[contains(@class,' apiRef/apiDefNote ')]">
        <xsl:with-param name="insertText" select="' - '"/>
      </xsl:apply-templates>
    </td>
  </tr>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxParam ')]"
      mode="memberSummary">
  <tr>
    <td valign="top" class="paramListing">
      <xsl:apply-templates
          select="*[contains(@class,' apiRef/apiItemName ')]"/>
    </td>
    <td valign="top">
      <!-- should supply shortdesc for target if no contextual note -->
      <xsl:apply-templates
          select="*[contains(@class,' apiRef/apiDefNote ')]">
        <xsl:with-param name="insertText" select="' - '"/>
      </xsl:apply-templates>
    </td>
  </tr>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxClass/cxxClass ') or
          contains(@class,' cxxInterface/cxxInterface ')] /
      *[contains(@class,' apiRef/apiRef ' )]"
      mode="memberSummary">
  <tr>
    <td valign="top" class="apiDatatype">
      <xsl:apply-templates select="." mode="apiDatatype"/>
    </td>
    <td valign="top">
      <xsl:apply-templates select="." mode="apiSignature"/>
    </td>
  </tr>
</xsl:template>


<!-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   - Signature
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->
<xsl:template match="*[contains(@class,' cxxClass/cxxClass ')]"
      mode="signatureSummary">
  <xsl:variable name="baseNode" select="
          *[contains(@class,' cxxClass/cxxClassDetail ')] /
            *[contains(@class,' cxxClass/cxxClassDef ')] /
            *[contains(@class,' cxxClass/cxxBaseClass ')]"/>
  <xsl:variable name="implementedInterfaceNodes" select="
          *[contains(@class,' cxxClass/cxxClassDetail ')] /
            *[contains(@class,' cxxClass/cxxClassDef ')] /
            *[contains(@class,' cxxClass/cxxImplementedInterface ')]"/>
  <xsl:variable name="qualifierNodes" select="
          *[contains(@class,' cxxClass/cxxClassDetail ')] /
            *[contains(@class,' cxxClass/cxxClassDef ')] / *[
            contains(@class,' cxxClass/cxxFinalClass '   ) or
            contains(@class,' cxxClass/cxxAbstractClass ') or
            contains(@class,' cxxClass/cxxStaticClass '  ) or
            contains(@class,' cxxClass/cxxClassAccess '  )]"/>
  <p class="signatureSummary">
    <xsl:if test="$qualifierNodes">
      <xsl:apply-templates select="$qualifierNodes"/>
      <xsl:text> </xsl:text>
    </xsl:if>
    <xsl:call-template name="cxxGetString">
      <xsl:with-param name="stringName" select="'cxxClass'"/>
    </xsl:call-template>
    <xsl:text> </xsl:text>
    <xsl:apply-templates select="*[contains(@class,' apiRef/apiName ')]"
          mode="apiSignature">
      <xsl:with-param name="spanClass" select="'cxxClassName'"/>
    </xsl:apply-templates>
    <xsl:if test="$baseNode">
      <br />
      <xsl:call-template name="cxxGetString">
        <xsl:with-param name="stringName" select="'cxxBaseClass'"/>
      </xsl:call-template>
      <xsl:text> </xsl:text>
      <xsl:apply-templates select="$baseNode"/>
    </xsl:if>
    <xsl:if test="$implementedInterfaceNodes">
      <br />
      <xsl:call-template name="cxxGetString">
        <xsl:with-param name="stringName" select="'cxxImplementedInterface'"/>
      </xsl:call-template>
      <xsl:text> </xsl:text>
	  <xsl:for-each select="$implementedInterfaceNodes">
        <xsl:apply-templates select="."/>
        <xsl:if test="position()&lt;last()">
          <xsl:text>, </xsl:text>
        </xsl:if>
	  </xsl:for-each>
    </xsl:if>
  </p>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxInterface/cxxInterface ')]"
      mode="signatureSummary">
  <xsl:variable name="baseNode" select="
          *[contains(@class,' cxxInterface/cxxInterfaceDetail ')] /
            *[contains(@class,' cxxInterface/cxxInterfaceDef ')] /
            *[contains(@class,' cxxInterface/cxxBaseInterface ')]"/>
  <xsl:variable name="qualifierNodes" select="
          *[contains(@class,' cxxInterface/cxxInterfaceDetail ')] /
            *[contains(@class,' cxxInterface/cxxInterfaceDef ')] /
            *[contains(@class,' cxxInterface/cxxInterfaceAccess '  )]"/>
  <p class="{@class}">
    <xsl:if test="$qualifierNodes">
      <xsl:apply-templates select="$qualifierNodes"/>
      <xsl:text> </xsl:text>
    </xsl:if>
    <xsl:call-template name="cxxGetString">
      <xsl:with-param name="stringName" select="'cxxInterface'"/>
    </xsl:call-template>
    <xsl:text> </xsl:text>
    <xsl:apply-templates select="*[contains(@class,' apiRef/apiName ')]"
          mode="apiSignature">
      <xsl:with-param name="spanClass" select="'cxxInterfaceName'"/>
    </xsl:apply-templates>
    <xsl:if test="$baseNode">
      <br />
      <xsl:call-template name="cxxGetString">
        <xsl:with-param name="stringName" select="'cxxBaseClass'"/>
      </xsl:call-template>
      <xsl:text> </xsl:text>
      <xsl:apply-templates select="$baseNode"/>
    </xsl:if>
  </p>
</xsl:template>

<xsl:template match="*[contains(@class,' topic/title ')]" mode="apiSignature">
  <xsl:param name="spanClass" select="local-name(.)"/>
  <span class="{$spanClass}">
    <xsl:apply-templates mode="default"/>
  </span>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxClass/cxxClass ') or
          contains(@class,' cxxInterface/cxxInterface ')] /
      *[contains(@class,' cxxMethod/cxxMethod ' )]"
      mode="signatureSummary">
  <tr>
    <td valign="top">
      <xsl:apply-templates select="." mode="apiSignature"/>
    </td>
  </tr>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxField/cxxField ')]"
      mode="apiSignature">
  <a name="{@id}"></a>
  <span class="signatureSummary">
    <xsl:apply-templates select="*[contains(@class,' topic/title ')]"
        mode="apiSignature"/>
  </span>
  <br />
  <xsl:apply-templates select="*[contains(@class,' topic/shortdesc ')]"
      mode="apiSignature"/>
</xsl:template>

<xsl:template match="*[contains(@class,' topic/shortdesc ')]"
      mode="apiSignature">
  <p class="apiSignature">
    <xsl:apply-templates/>
  </p>
  <xsl:value-of select="$newline"/>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxMethod ')]"
      mode="apiSignature">
  <span class="signatureSummary">
    <a href="#{@id}" class="summarylink">
      <xsl:apply-templates select="*[contains(@class,' topic/title ')]"
          mode="apiSignature"/>
    </a>
    <xsl:text>(</xsl:text>
    <xsl:apply-templates
        select="*[contains(@class,' cxxMethod/cxxMethodDetail ')] /
            *[contains(@class,' cxxMethod/cxxMethodDef '       ) or
              contains(@class,' cxxMethod/cxxConstructorDef '  )] /
            *[contains(@class,' cxxMethod/cxxParam '           )]"
        mode="apiSignature"/>
    <xsl:text>)</xsl:text>
  </span>
  <br />
  <xsl:apply-templates select="*[contains(@class,' topic/shortdesc ')]"
      mode="apiSignature"/>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxParam ')]"
      mode="apiSignature">
  <xsl:if test="preceding-sibling::*[1][
      contains(@class,' cxxMethod/cxxParam ')]">
    <xsl:text>, </xsl:text>
  </xsl:if>
  <xsl:apply-templates select="*[
      contains(@class,' cxxMethod/cxxMethodClass '     ) or
      contains(@class,' cxxMethod/cxxMethodInterface ' ) or
      contains(@class,' cxxMethod/cxxMethodPrimitive ' ) or
      contains(@class,' cxxMethod/cxxMethodArray '     )]"
      mode="apiSignature"/>
  <xsl:text> </xsl:text>
  <xsl:apply-templates select="*[contains(@class,' apiRef/apiItemName ')]"
      mode="apiSignature"/>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxMethodClass ' ) or
      contains(@class,' cxxMethod/cxxMethodInterface ' ) or
      contains(@class,' cxxMethod/cxxMethodPrimitive ' ) or
      contains(@class,' cxxMethod/cxxMethodArray '     )]"
      mode="apiSignature">
  <xsl:apply-templates select="."/>
</xsl:template>

<xsl:template match="*[contains(@class,' apiRef/apiItemName ' )]"
      mode="apiSignature">
  <xsl:apply-templates select="."/>
</xsl:template>


<!-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   - Datatype
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->
<xsl:template match="*[contains(@class,' cxxMethod/cxxMethodDef ')]"
      mode="apiDatatype">
  <xsl:apply-templates select="*[contains(@class,' cxxMethod/cxxReturn ') or
          contains(@class,' cxxMethod/cxxVoid ' )]"
      mode="apiDatatype"/>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxReturn ')]"
      mode="apiDatatype">
    <xsl:apply-templates select="*[
        contains(@class,' cxxMethod/cxxMethodClass '     ) or
        contains(@class,' cxxMethod/cxxMethodInterface ' ) or
        contains(@class,' cxxMethod/cxxMethodPrimitive ' ) or
        contains(@class,' cxxMethod/cxxMethodArray '     )]"/>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxVoid ')]"
      mode="apiDatatype">
  <xsl:value-of select="@value"/>
</xsl:template>

<xsl:template match="*[contains(@class,' apiRef/apiRef ')]"
      mode="apiDatatype">
  <xsl:apply-templates select="*[contains(@class,' apiRef/apiDetail ')]"
      mode="apiDatatype"/>
</xsl:template>

<xsl:template match="*[contains(@class,' apiRef/apiDetail ')]"
      mode="apiDatatype">
  <xsl:apply-templates select="*[contains(@class,' apiRef/apiDef ')]"
      mode="apiDatatype"/>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxField/cxxFieldDef ')]"
      mode="apiDatatype">
  <xsl:variable name="fieldQualifierNodes" select="*[
      contains(@class,' cxxField/cxxFieldAccess '         ) or
      contains(@class,' cxxField/cxxFinalField '          ) or
      contains(@class,' cxxField/cxxStaticField '         ) or
      contains(@class,' cxxField/cxxTransientField '      ) or
      contains(@class,' cxxField/cxxVolatileField '       )]"/>
  <xsl:if test="$fieldQualifierNodes">
    <xsl:apply-templates select="$fieldQualifierNodes"/>
    <xsl:text> </xsl:text>
  </xsl:if>
  <xsl:apply-templates
      select="*[contains(@class,' cxxField/cxxFieldClass ') or
      contains(@class,' cxxField/cxxFieldInterface ') or
      contains(@class,' cxxField/cxxFieldPrimitive ') or
      contains(@class,' cxxField/cxxFieldArray '    )]"
      mode="apiDatatype"/>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxField/cxxFieldClass ') or
      contains(@class,' cxxField/cxxFieldInterface ') or
      contains(@class,' cxxField/cxxFieldPrimitive ') or
      contains(@class,' cxxField/cxxFieldArray '    )]"
      mode="apiDatatype">
  <xsl:apply-templates select="."/>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxConstructorDef ')]"
      mode="apiDatatype"/>


<!-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   - Member listings
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->
<xsl:template match="*[contains(@class,' cxxMethod/cxxMethodDetail ')]">
  <div>
    <xsl:call-template name="commonattributes"/>
    <xsl:call-template name="setidaname"/>
    <xsl:call-template name="flagit"/>
    <xsl:call-template name="start-revflag"/>
    <xsl:comment>syntax</xsl:comment>
    <xsl:apply-templates select="
          *[contains(@class,' cxxMethod/cxxMethodDef ') or
            contains(@class,' cxxMethod/cxxConstructorDef ')]"
        mode="methodSignature"/>
    <xsl:comment>description</xsl:comment>
    <div class="methodDescription">
      <xsl:apply-templates
          select="preceding-sibling::*[contains(@class,' topic/shortdesc ')]"
          mode="outofline"/>
      <xsl:apply-templates/>
    </div>
    <xsl:comment>member summary</xsl:comment>
    <xsl:apply-templates
        select="*[contains(@class,' cxxMethod/cxxMethodDef ') or
              contains(@class,' cxxMethod/cxxConstructorDef ')]"
        mode="memberSummary"/>
    <xsl:comment>see also</xsl:comment>
    <xsl:apply-templates select="following-sibling::
        *[contains(@class,' topic/related-links ')]"/>
    <hr/>
    <xsl:call-template name="end-revflag"/>
  </div>
  <xsl:value-of select="$newline"/>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxMethodDef ') or
            contains(@class,' cxxMethod/cxxConstructorDef ')]"
      mode="methodSignature">
  <xsl:variable name="returnNodes"
        select="(*[contains(@class,' cxxMethod/cxxReturn ')]/*[
            contains(@class,' cxxMethod/cxxMethodClass '     ) or
            contains(@class,' cxxMethod/cxxMethodInterface ' ) or
            contains(@class,' cxxMethod/cxxMethodPrimitive ' ) or
            contains(@class,' cxxMethod/cxxMethodArray '     )]) |
        *[contains(@class,' cxxMethod/cxxVoid '   )]"/>
  <xsl:comment>signature summary</xsl:comment>
  <p class="cxxMethodSignature">
    <xsl:apply-templates select="*[
        contains(@class,' cxxMethod/cxxMethodAccess '       ) or
        contains(@class,' cxxMethod/cxxFinalMethod '        ) or
        contains(@class,' cxxMethod/cxxAbstractMethod '     ) or
        contains(@class,' cxxMethod/cxxStaticMethod '       ) or
        contains(@class,' cxxMethod/cxxNativeMethod '       ) or
        contains(@class,' cxxMethod/cxxSynchronizedMethod ' )]"/>
    <xsl:text> </xsl:text>
    <xsl:if test="$returnNodes">
      <xsl:apply-templates select="$returnNodes"/>
      <xsl:text> </xsl:text>
    </xsl:if>
    <xsl:apply-templates
        select="ancestor::*[contains(@class,' apiRef/apiRef ')][1] /
            *[contains(@class,' topic/title ')]"
        mode="apiSignature">
      <xsl:with-param name="spanClass" select="'cxxMethodName'"/>
    </xsl:apply-templates>
    <xsl:text>(</xsl:text>
    <xsl:apply-templates
        select="*[contains(@class,' cxxMethod/cxxParam ')]"
        mode="apiSignature"/>
    <xsl:text>)</xsl:text>
  </p>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxParam ')]">
    <xsl:apply-templates select="*[
        contains(@class,' cxxMethod/cxxMethodClass '     ) or
        contains(@class,' cxxMethod/cxxMethodInterface ' ) or
        contains(@class,' cxxMethod/cxxMethodPrimitive ' ) or
        contains(@class,' cxxMethod/cxxMethodArray '     )]"/>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxException ')]">
    <xsl:apply-templates select="*[
        contains(@class,' cxxMethod/cxxMethodClass '     )]"/>
</xsl:template>

<xsl:template match="*[
      contains(@class,' cxxClass/cxxFinalClass '          ) or
      contains(@class,' cxxClass/cxxAbstractClass '       ) or
      contains(@class,' cxxClass/cxxStaticClass '         ) or
      contains(@class,' cxxClass/cxxClassAccess '         ) or
      contains(@class,' cxxInterface/cxxInterfaceAccess ' ) or
      contains(@class,' cxxMethod/cxxMethodAccess '       ) or
      contains(@class,' cxxMethod/cxxFinalMethod '        ) or
      contains(@class,' cxxMethod/cxxAbstractMethod '     ) or
      contains(@class,' cxxMethod/cxxStaticMethod '       ) or
      contains(@class,' cxxMethod/cxxNativeMethod '       ) or
      contains(@class,' cxxMethod/cxxSynchronizedMethod ' ) or
      contains(@class,' cxxMethod/cxxVoid '               ) or
      contains(@class,' cxxMethod/cxxMethodPrimitive '    ) or
      contains(@class,' cxxField/cxxFieldAccess '         ) or
      contains(@class,' cxxField/cxxFinalField '          ) or
      contains(@class,' cxxField/cxxStaticField '         ) or
      contains(@class,' cxxField/cxxTransientField '      ) or
      contains(@class,' cxxField/cxxVolatileField '       ) or
      contains(@class,' cxxField/cxxFieldPrimitive '      )]">
  <xsl:param name="spanClass" select="local-name(.)"/>
  <xsl:if test="preceding-sibling::*[
      contains(@class,' cxxClass/cxxFinalClass '          ) or
      contains(@class,' cxxClass/cxxAbstractClass '       ) or
      contains(@class,' cxxClass/cxxStaticClass '         ) or
      contains(@class,' cxxClass/cxxClassAccess '         ) or
      contains(@class,' cxxInterface/cxxInterfaceAccess ' ) or
      contains(@class,' cxxMethod/cxxMethodAccess '       ) or
      contains(@class,' cxxMethod/cxxFinalMethod '        ) or
      contains(@class,' cxxMethod/cxxAbstractMethod '     ) or
      contains(@class,' cxxMethod/cxxStaticMethod '       ) or
      contains(@class,' cxxMethod/cxxNativeMethod '       ) or
      contains(@class,' cxxMethod/cxxSynchronizedMethod ' ) or
      contains(@class,' cxxField/cxxFieldAccess '         ) or
      contains(@class,' cxxField/cxxFinalField '          ) or
      contains(@class,' cxxField/cxxStaticField '         ) or
      contains(@class,' cxxField/cxxTransientField '      ) or
      contains(@class,' cxxField/cxxVolatileField '       ) or
      contains(@class,' cxxField/cxxFieldPrimitive '      )][1]">
    <xsl:text> </xsl:text>
  </xsl:if>
  <xsl:apply-templates select="@value" mode="span">
    <xsl:with-param name="spanClass" select="concat($spanClass,'_',@name)"/>
  </xsl:apply-templates>
</xsl:template>

<xsl:template match="*[contains(@class,' cxxMethod/cxxMethod ')]"
      mode="memberDetail">
  <div class="nested0">
    <xsl:call-template name="gen-topic"/>
  </div>
  <xsl:value-of select="$newline"/>
</xsl:template>


<!-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   - General API processing
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->
<xsl:template match="*[contains(@class,' apiRef/apiRelation ') and 
      not(@href)]">
  <span class="{@class}">
    <xsl:apply-templates/>
  </span>
</xsl:template>

<xsl:template match="*[contains(@class,' topic/xref ') and 
      contains(@class,' cxxapi-d/') and 
      not(@href)]">
  <span class="{@class}">
    <xsl:apply-templates/>
  </span>
</xsl:template>

<xsl:template match="*[(contains(@class,' apiRef/apiQualifier ') or
      contains(@class,' apiRef/apiType ')) and not(
	  contains(@class,' cxxClass/') or
	  contains(@class,' cxxInterface/') or
	  contains(@class,' cxxMethod/') or
	  contains(@class,' cxxField/'))]">
  <xsl:param name="spanClass" select="local-name(.)"/>
  <span class="{@class}">
    <xsl:apply-templates select="@name" mode="span">
      <xsl:with-param name="spanClass"
          select="concat($spanClass,'_valuename')"/>
    </xsl:apply-templates>
    <xsl:call-template name="getString">
      <xsl:with-param name="stringName" select="'ColonSymbol'"/>
    </xsl:call-template>
    <xsl:text> </xsl:text>
    <xsl:apply-templates select="@value" mode="span">
      <xsl:with-param name="spanClass" select="concat($spanClass,'_',@name)"/>
    </xsl:apply-templates>
  </span>
</xsl:template>

<xsl:template match="*[contains(@class,' apiRef/apiArray ')]">
  <xsl:text>[</xsl:text>
    <xsl:apply-templates select="*[contains(@class,' apiRef/apiArraySize ')]"/>
  <xsl:text>]</xsl:text>
  <xsl:apply-templates select="*[contains(@class,' apiRef/apiArray ')]"/>
</xsl:template>

<xsl:template match="*[contains(@class,' apiRef/apiDesc ')]">
  <div class="apiDescription">
    <xsl:apply-templates/>
  </div>
</xsl:template>

<xsl:template match="*[contains(@class,' apiRef/apiDefNote ')]">
  <xsl:param name="insertText"/>
  <div class="{@class}">
    <xsl:if test="$insertText">
      <xsl:value-of select="$insertText"/>
    </xsl:if>
    <xsl:apply-templates/>
  </div>
</xsl:template>

<xsl:template match="*[contains(@class,' apiRef/apiSyntax ')]">
  <pre class="{@class}">
    <xsl:apply-templates/>
  </pre>
</xsl:template>

<xsl:template match="*[contains(@class,' apiRef/apiItemName ' )]">
  <xsl:apply-templates select="*|text()"/>
</xsl:template>


<!-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   - General topic rules
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->
<!-- specifics needed for precedence -->
<xsl:template match="*|*[contains(@class,' topic/title ')]" mode="div">
  <div class="{@class}">
    <xsl:apply-templates mode="default"/>
  </div>
</xsl:template>

<xsl:template match="*|*[contains(@class,' topic/title ')]" mode="span">
  <span class="{@class}">
    <xsl:apply-templates mode="default"/>
  </span>
</xsl:template>

<xsl:template match="@*" mode="span">
  <xsl:param name="spanClass"
      select="concat(local-name(..),'_',local-name(.))"/>
  <span class="{$spanClass}">
    <xsl:value-of select="."/>
  </span>
</xsl:template>

<!--<xsl:template match="node()" mode="default">
  <xsl:apply-imports/>
</xsl:template>-->


<!-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   - Filename manipulation
   - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -->
<!-- adapted from topicpull.xsl - should be shared utilities -->
<xsl:template name="getTopicFile">
  <xsl:param name="href" select="@href"/>
  <xsl:choose>
  <xsl:when test="contains($href,'://') and contains($href,'#')">
    <xsl:value-of select="substring-before($href,'#')"/>
  </xsl:when>
  <xsl:when test="contains($href,'://')">
    <xsl:value-of select="$href"/>
  </xsl:when>
  <xsl:when test="contains($href,'#')">
    <xsl:value-of select="$WORKDIR"/>
    <xsl:value-of select="substring-before($href,'#')"/>
  </xsl:when>
  <xsl:otherwise>
    <xsl:value-of select="$WORKDIR"/>
    <xsl:value-of select="$href"/>
  </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="getTopicID">
  <xsl:param name="href" select="@href"/>
  <xsl:choose>
  <xsl:when test="contains($href,'#') and contains(substring-after($href,'#'),'/')">
    <xsl:value-of select="substring-before(substring-after($href,'#'),'/')"/>
  </xsl:when>
  <xsl:when test="contains($href,'#')">
    <xsl:value-of select="substring-after($href,'#')"/>
  </xsl:when>
  <xsl:otherwise>
    <xsl:text>#none#</xsl:text>
  </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="getBaseFile">
  <xsl:param name="file"/>
  <xsl:choose>
  <xsl:when test="not($file)"/>
  <xsl:when test="contains($file,'\')">
    <xsl:call-template name="getBaseFile">
      <xsl:with-param name="file" select="substring-after($file,'\')"/>
    </xsl:call-template>
  </xsl:when>
  <xsl:when test="contains($file,'/')">
    <xsl:call-template name="getBaseFile">
      <xsl:with-param name="file" select="substring-after($file,'/')"/>
    </xsl:call-template>
  </xsl:when>
  <xsl:otherwise>
    <xsl:value-of select="$file"/>
  </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="getFileRoot">
  <xsl:param name="fileroot"/>
  <xsl:param name="file"/>
  <xsl:choose>
  <xsl:when test="$file and contains($file,'.')">
    <xsl:variable name="infix" select="substring-before($file,'.')"/>
    <xsl:variable name="newroot">
      <xsl:choose>
      <xsl:when test="$fileroot and $infix">
        <xsl:value-of select="$fileroot"/>
        <xsl:text>.</xsl:text>
        <xsl:value-of select="$infix"/>
      </xsl:when>
      <xsl:when test="$infix">
        <xsl:value-of select="$infix"/>
      </xsl:when>
      <xsl:when test="$fileroot">
        <xsl:value-of select="$fileroot"/>
      </xsl:when>
      </xsl:choose>
    </xsl:variable>
    <xsl:call-template name="getFileRoot">
      <xsl:with-param name="fileroot" select="$newroot"/>
      <xsl:with-param name="file"     select="substring-after($file,'.')"/>
    </xsl:call-template>
  </xsl:when>
  <xsl:when test="$fileroot">
    <xsl:value-of select="$fileroot"/>
  </xsl:when>
  <xsl:when test="$file">
    <xsl:value-of select="$file"/>
  </xsl:when>
  </xsl:choose>
</xsl:template>

<xsl:template name="getBaseFileRoot">
  <xsl:param name="file"/>
  <xsl:variable name="basefile">
    <xsl:call-template name="getBaseFile">
      <xsl:with-param name="file" select="$file"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:call-template name="getFileRoot">
    <xsl:with-param name="file" select="$basefile"/>
  </xsl:call-template>
</xsl:template>

<xsl:template name="getOutputFile">
  <xsl:param name="href"/>
  <xsl:choose>
  <xsl:when test="not($href) or string-length($href) &lt; 1">
    <xsl:message>
      <xsl:text>Empty href for </xsl:text>
      <xsl:value-of select="local-name()"/>
      <xsl:text> </xsl:text>
      <xsl:value-of select="@id"/>
    </xsl:message>
  </xsl:when>
  <xsl:when test="contains($href,'.dita')">
    <xsl:value-of select="substring-before($href,'.dita')"/>
  </xsl:when>
  <xsl:when test="contains($href,'.xml')">
    <xsl:value-of select="substring-before($href,'.xml')"/>
  </xsl:when>
  <xsl:otherwise>
    <xsl:message>
      <xsl:text>Extension not .dita or .xml for </xsl:text>
      <xsl:value-of select="$href"/>
    </xsl:message>
    <xsl:value-of select="$href"/>
  </xsl:otherwise>
  </xsl:choose>
  <xsl:value-of select="$OUTEXT"/>
</xsl:template>

</xsl:stylesheet>
