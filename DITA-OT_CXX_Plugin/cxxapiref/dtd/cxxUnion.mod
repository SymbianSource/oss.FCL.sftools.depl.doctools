<!-- ================================================================= -->
<!--                    HEADER                                         -->
<!-- ================================================================= -->
<!--  MODULE:    C++ Union DTD                                         -->
<!--  VERSION:   0.5.0                                                 -->
<!--  DATE:      February 2009                                          -->
<!--                                                                   -->
<!-- ================================================================= -->

<!-- ================================================================= -->
<!--                    PUBLIC DOCUMENT TYPE DEFINITION                -->
<!--                    TYPICAL INVOCATION                             -->
<!--                                                                   -->
<!--  Refer to this file by the following public identifier or an 
      appropriate system identifier 
PUBLIC "-//NOKIA//DTD DITA C++ API Union Reference Type v0.5.0//EN"
      Delivered as file "cxxUnion.dtd"                                 -->
 
<!-- ================================================================= -->
<!-- SYSTEM:     Darwin Information Typing Architecture (DITA)         -->
<!--                                                                   -->
<!-- PURPOSE:    C++ API Reference for Unions                          -->
<!--                                                                   -->
<!-- ORIGINAL CREATION DATE:                                           -->
<!--             November 2009                                         -->
<!--                                                                   -->
<!-- Copyright (c) 2009 Nokia Corporation and/or its subsidiary(-ies). -->
<!-- All rights reserved.                                              -->
<!--                                                                   -->
<!--  Change History (latest at top):                                  -->
<!--  +++++++++++++++++++++++++++++++                                  -->
<!--  2010-02-16 VOG: Updated.                                         -->
<!--  2010-02-10 PaulRoss: Updated.                                   -->
<!--  2009-11-16 PaulRoss: Initial design.                             -->
<!--                                                                   -->
<!-- ================================================================= -->

<!--
Copyright (c) 2009 Nokia Corporation and/or its subsidiary(-ies).
All rights reserved.
-->

<!-- ============ Hooks for domain extension ============ -->
<!ENTITY % cxxUnion                             "cxxUnion">
<!ENTITY % cxxUnionDetail                       "cxxUnionDetail">
<!ENTITY % cxxUnionDefinition                   "cxxUnionDefinition">
<!ENTITY % cxxUnionAbstract                     "cxxUnionAbstract">
<!ENTITY % cxxUnionAccessSpecifier              "cxxUnionAccessSpecifier">
<!-- union has no inheritance  
<!ENTITY % cxxUnionDerivations                  "cxxUnionDerivations">
<!ENTITY % cxxUnionDerivation                   "cxxUnionDerivation">
-->
<!ENTITY % cxxUnionTemplateParamList            "cxxUnionTemplateParamList">
<!ENTITY % cxxUnionTemplateParameter            "cxxUnionTemplateParameter">
<!ENTITY % cxxUnionTemplateParamType            "cxxUnionTemplateParamType">
<!ENTITY % cxxUnionTemplateParamDeclarationName "cxxUnionTemplateParamDeclarationName">
<!ENTITY % cxxUnionTemplateParamDefinitionName  "cxxUnionTemplateParamDefinitionName">

<!-- Derivation -->
<!-- union has no inheritance  
<!ENTITY % cxxUnionDerivationAccessSpecifier    "cxxUnionDerivationAccessSpecifier">
<!ENTITY % cxxUnionDerivationVirtual            "cxxUnionDerivationVirtual">
<!ENTITY % cxxUnionBaseClass                    "cxxUnionBaseClass">
<!ENTITY % cxxUnionBaseStruct                   "cxxUnionBaseStruct">
<!ENTITY % cxxUnionBaseUnion                    "cxxUnionBaseUnion">
<!ENTITY % cxxUnionInherits                     "cxxUnionInherits">
<!ENTITY % cxxUnionInheritsDetail               "cxxUnionInheritsDetail">

<!ENTITY % cxxUnionFunctionInherited            "cxxUnionFunctionInherited">
<!ENTITY % cxxUnionVariableInherited            "cxxUnionVariableInherited">
<!ENTITY % cxxUnionEnumerationInherited         "cxxUnionEnumerationInherited">
-->
<!-- Nested members -->
<!ENTITY % cxxUnionNested                       "cxxUnionNested">
<!ENTITY % cxxUnionNestedDetail                 "cxxUnionNestedDetail">
<!ENTITY % cxxUnionNestedClass                  "cxxUnionNestedClass">
<!ENTITY % cxxUnionNestedStruct                 "cxxUnionNestedStruct">
<!ENTITY % cxxUnionNestedUnion                  "cxxUnionNestedUnion">

<!-- Location elements -->
<!ENTITY % cxxUnionAPIItemLocation              "cxxUnionAPIItemLocation">
<!ENTITY % cxxUnionDeclarationFile              "cxxUnionDeclarationFile">
<!ENTITY % cxxUnionDeclarationFileLine          "cxxUnionDeclarationFileLine">
<!ENTITY % cxxUnionDefinitionFile               "cxxUnionDefinitionFile">
<!ENTITY % cxxUnionDefinitionFileLineStart      "cxxUnionDefinitionFileLineStart">
<!ENTITY % cxxUnionDefinitionFileLineEnd        "cxxUnionDefinitionFileLineEnd">

<!-- ============ Hooks for shell DTD ============ -->

<!ENTITY % cxxUnion-types-default
    "cxxUnionNested | cxxFunction | cxxDefine | cxxVariable | cxxEnumeration | cxxTypedef">
<!ENTITY % cxxUnion-info-types  "%cxxUnion-types-default;">

<!ENTITY % cxxUnionNested-types-default "no-topic-nesting">
<!ENTITY % cxxUnionNested-info-types  "%cxxUnionNested-types-default;">

<!ENTITY included-domains "">

<!-- ============ Topic specializations ============ -->

<!ELEMENT cxxUnion   (
                        (%apiName;),
                        (%shortdesc;)?,
                        (%prolog;)?,
                        (%cxxUnionDetail;),
                        (%related-links;)?,
                        (%cxxUnion-info-types;)*
                      )
>
<!-- union has no inheritance    (%cxxUnionInherits;)*  -->
<!ATTLIST cxxUnion       id ID #REQUIRED
                          conref CDATA #IMPLIED
                          outputclass CDATA #IMPLIED
                          xml:lang NMTOKEN #IMPLIED
                          %arch-atts;
                          domains CDATA "&included-domains;"
>

<!ELEMENT cxxUnionDetail  ((%cxxUnionDefinition;)?, (%apiDesc;)?, (%example; | %section; | %apiImpl;)*)>
<!ATTLIST cxxUnionDetail  %id-atts;
                          translate (yes|no) #IMPLIED
                          xml:lang NMTOKEN #IMPLIED
                          outputclass CDATA #IMPLIED>

<!ELEMENT cxxUnionDefinition   (
                                    (%cxxUnionAccessSpecifier;)?,
                                    (%cxxUnionAbstract;)?,
                                    (%cxxUnionTemplateParamList;)?,
                                    (%cxxUnionAPIItemLocation;)
                               )
>
<!-- union has no inheritance       (%cxxUnionDerivations;)?,   -->
<!ATTLIST cxxUnionDefinition    spectitle CDATA #IMPLIED
                                  %univ-atts;
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionAccessSpecifier  EMPTY>
<!ATTLIST cxxUnionAccessSpecifier  name CDATA #FIXED "access"
                          value (public|protected|private) "public"
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionAbstract  EMPTY>
<!ATTLIST cxxUnionAbstract  name CDATA #FIXED "abstract"
                            value CDATA #FIXED "abstract"
                            %univ-atts;
                            outputclass CDATA #IMPLIED
>

<!-- union has no inheritance  
<!ELEMENT cxxUnionDerivations   (%cxxUnionDerivation; | %cxxStructDerivation;)+ >
<!ATTLIST cxxUnionDerivations    %univ-atts;
                                outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionDerivation   (
                                    %cxxUnionDerivationAccessSpecifier;,
                                    (%cxxUnionDerivationVirtual;)*,
                                    (
                                        %cxxUnionBaseClass;
                                        | %cxxUnionBaseStruct;
                                        | %cxxUnionBaseUnion;
                                     )
                               )
>
<!ATTLIST cxxUnionDerivation    %univ-atts;
                                outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionInherits   (
                                %cxxUnionInheritsDetail;
                              )
>

<!ATTLIST cxxUnionInherits    %univ-atts;
                                outputclass CDATA #IMPLIED
                                domains CDATA "&included-domains;"
>

<!ELEMENT cxxUnionInheritsDetail   (
                                (
                                    %cxxUnionFunctionInherited;
                                    | %cxxUnionVariableInherited;
                                    | %cxxUnionEnumerationInherited;
                                    | %cxxUnionEnumeratorInherited;
                                )+
                              )
>

<!ATTLIST cxxUnionInheritsDetail    %univ-atts;
                                outputclass CDATA #IMPLIED
                                domains CDATA "&included-domains;"
>

<!ELEMENT cxxUnionFunctionInherited  (#PCDATA)*>
<!ATTLIST cxxUnionFunctionInherited   href CDATA #IMPLIED
                                      keyref CDATA #IMPLIED
                                      type   CDATA  #IMPLIED
                                      %univ-atts;
                                      format        CDATA   #IMPLIED
                                      scope (local | peer | external) #IMPLIED
                                      outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionVariableInherited  (#PCDATA)*>
<!ATTLIST cxxUnionVariableInherited   href CDATA #IMPLIED
                                      keyref CDATA #IMPLIED
                                      type   CDATA  #IMPLIED
                                      %univ-atts;
                                      format        CDATA   #IMPLIED
                                      scope (local | peer | external) #IMPLIED
                                      outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionEnumerationInherited  (#PCDATA)*>
<!ATTLIST cxxUnionEnumerationInherited   href CDATA #IMPLIED
                                          keyref CDATA #IMPLIED
                                          type   CDATA  #IMPLIED
                                          %univ-atts;
                                          format        CDATA   #IMPLIED
                                          scope (local | peer | external) #IMPLIED
                                          outputclass CDATA #IMPLIED
>


<!ELEMENT cxxUnionDerivationAccessSpecifier  EMPTY>
<!ATTLIST cxxUnionDerivationAccessSpecifier  name CDATA #FIXED "access"
                                             value (public | protected | private) "public"
                                            %univ-atts;
                                            outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionDerivationVirtual  EMPTY>
<!ATTLIST cxxUnionDerivationVirtual  name CDATA #FIXED "virtual"
                                      value CDATA #FIXED "true"
                                      %univ-atts;
                                      outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionBaseClass  (#PCDATA)*>
<!ATTLIST cxxUnionBaseClass   href CDATA #IMPLIED
                              keyref CDATA #IMPLIED
                              type   CDATA  #IMPLIED
                              %univ-atts;
                              format        CDATA   #IMPLIED
                              scope (local | peer | external) #IMPLIED
                              outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionBaseStruct  (#PCDATA)*>
<!ATTLIST cxxUnionBaseStruct   href CDATA #IMPLIED
                              keyref CDATA #IMPLIED
                              type   CDATA  #IMPLIED
                              %univ-atts;
                              format        CDATA   #IMPLIED
                              scope (local | peer | external) #IMPLIED
                              outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionBaseUnion  (#PCDATA)*>
<!ATTLIST cxxUnionBaseUnion   href CDATA #IMPLIED
                              keyref CDATA #IMPLIED
                              type   CDATA  #IMPLIED
                              %univ-atts;
                              format        CDATA   #IMPLIED
                              scope (local | peer | external) #IMPLIED
                              outputclass CDATA #IMPLIED
>
-->

<!ELEMENT cxxUnionTemplateParamList   (%cxxUnionTemplateParameter;)+ >
<!ATTLIST cxxUnionTemplateParamList    %univ-atts;
                                  outputclass CDATA #IMPLIED
>
<!ELEMENT cxxUnionTemplateParameter   ( %cxxUnionTemplateParamType;,
                                       (%cxxUnionTemplateParamDeclarationName;)?,
                                       (%cxxUnionTemplateParamDefinitionName;)? 
																			)
>
<!ATTLIST cxxUnionTemplateParameter    %univ-atts;
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionTemplateParamType   (#PCDATA)*>
<!ATTLIST cxxUnionTemplateParamType    %univ-atts;
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionTemplateParamDeclarationName   (#PCDATA)*>
<!ATTLIST cxxUnionTemplateParamDeclarationName    %univ-atts;
                                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionTemplateParamDefinitionName   (#PCDATA)*>
<!ATTLIST cxxUnionTemplateParamDefinitionName    %univ-atts;
                                                 outputclass CDATA #IMPLIED
>
<!ELEMENT cxxUnionAPIItemLocation   (
                                        %cxxUnionDeclarationFile;,
                                        %cxxUnionDeclarationFileLine;,
                                        %cxxUnionDefinitionFile;?,
                                        %cxxUnionDefinitionFileLineStart;?,
                                        %cxxUnionDefinitionFileLineEnd;?
                                     )
>
<!ATTLIST cxxUnionAPIItemLocation    %univ-atts;
                                    outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionDeclarationFile  EMPTY>
<!ATTLIST cxxUnionDeclarationFile  name CDATA #FIXED "filePath"
                                  value CDATA #REQUIRED
                                  %univ-atts;
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionDeclarationFileLine  EMPTY>
<!ATTLIST cxxUnionDeclarationFileLine   name CDATA #FIXED "lineNumber"
                                        value CDATA #REQUIRED
                                        %univ-atts;
                                        outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionDefinitionFile  EMPTY>
<!ATTLIST cxxUnionDefinitionFile  name CDATA #FIXED "filePath"
                                  value CDATA #REQUIRED
                                  %univ-atts;
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionDefinitionFileLineStart  EMPTY>
<!ATTLIST cxxUnionDefinitionFileLineStart  name CDATA #FIXED "lineNumber"
                                            value CDATA #REQUIRED
                                            %univ-atts;
                                            outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionDefinitionFileLineEnd  EMPTY>
<!ATTLIST cxxUnionDefinitionFileLineEnd  name CDATA #FIXED "lineNumber"
                                            value CDATA #REQUIRED
                                            %univ-atts;
                                            outputclass CDATA #IMPLIED
>

<!-- Nested members -->
<!ELEMENT cxxUnionNested (
                        (%cxxUnionNestedDetail;),
                        (%cxxUnionNested-info-types;)*
                         )
>
<!ATTLIST cxxUnionNested  conref CDATA #IMPLIED
                          outputclass CDATA #IMPLIED
                          xml:lang NMTOKEN #IMPLIED
                          %arch-atts;
                          domains CDATA "&included-domains;"
>

<!ELEMENT cxxUnionNestedDetail  ( (%cxxUnionNestedClass;) | (%cxxUnionNestedStruct;) | (%cxxUnionNestedUnion;) )+>
<!ATTLIST cxxUnionNestedDetail  %id-atts;
                          translate (yes|no) #IMPLIED
                          xml:lang NMTOKEN #IMPLIED
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionNestedClass  (#PCDATA)*>
<!ATTLIST cxxUnionNestedClass  href CDATA #IMPLIED
                              keyref CDATA #IMPLIED
                              type   CDATA  #IMPLIED
                              %univ-atts;
                              format        CDATA   #IMPLIED
                              scope (local | peer | external) #IMPLIED
                              outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionNestedStruct  (#PCDATA)*>
<!ATTLIST cxxUnionNestedStruct  href CDATA #IMPLIED
                              keyref CDATA #IMPLIED
                              type   CDATA  #IMPLIED
                              %univ-atts;
                              format        CDATA   #IMPLIED
                              scope (local | peer | external) #IMPLIED
                              outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionNestedUnion  (#PCDATA)*>
<!ATTLIST cxxUnionNestedUnion  href CDATA #IMPLIED
                              keyref CDATA #IMPLIED
                              type   CDATA  #IMPLIED
                              %univ-atts;
                              format        CDATA   #IMPLIED
                              scope (local | peer | external) #IMPLIED
                              outputclass CDATA #IMPLIED
>


<!-- ============ Class attributes for type ancestry ============ -->
<!ATTLIST cxxUnion   %global-atts;
    class  CDATA "- topic/topic reference/reference apiRef/apiRef apiClassifier/apiClassifier cxxUnion/cxxUnion ">
<!ATTLIST cxxUnionDetail   %global-atts;
    class  CDATA "- topic/body reference/refbody apiRef/apiDetail apiClassifier/apiClassifierDetail cxxUnion/cxxUnionDetail ">
<!ATTLIST cxxUnionDefinition   %global-atts;
    class  CDATA "- topic/section reference/section apiRef/apiDef apiClassifier/apiClassifierDef cxxUnion/cxxUnionDefinition ">
<!ATTLIST cxxUnionAccessSpecifier   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxUnion/cxxUnionAccessSpecifier ">
<!ATTLIST cxxUnionAbstract   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxUnion/cxxUnionAbstract ">

<!-- Representing inheritance -->
<!-- union has no inheritance  
<!ATTLIST cxxUnionDerivations   %global-atts;
    class  CDATA "- topic/ph reference/ph apiRef/apiDefItem apiClassifier/apiDefItem cxxUnion/cxxUnionDerivations ">
<!ATTLIST cxxUnionDerivation   %global-atts;
    class  CDATA "- topic/ph reference/ph apiRef/apiDefItem apiClassifier/apiDefItem cxxUnion/cxxUnionDerivation ">
<!ATTLIST cxxUnionDerivationAccessSpecifier   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxUnion/cxxUnionDerivationAccessSpecifier ">
<!ATTLIST cxxUnionDerivationVirtual   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxUnion/cxxUnionDerivationVirtual ">
<!ATTLIST cxxUnionBaseClass   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiClassifier/apiBaseClassifier cxxUnion/cxxUnionBaseClass ">
<!ATTLIST cxxUnionBaseStruct   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiClassifier/apiBaseClassifier cxxUnion/cxxUnionBaseStruct ">
<!ATTLIST cxxUnionBaseUnion   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiClassifier/apiBaseClassifier cxxUnion/cxxUnionBaseUnion ">
-->

<!-- Templates -->
<!ATTLIST cxxUnionTemplateParamList   %global-atts;
    class  CDATA "- topic/ph reference/ph apiRef/apiDefItem apiClassifier/apiDefItem cxxUnion/cxxUnionTemplateParamList ">
<!ATTLIST cxxUnionTemplateParameter   %global-atts;
    class  CDATA "- topic/ph reference/ph apiRef/apiDefItem apiClassifier/apiDefItem cxxUnion/cxxUnionTemplateParameter ">
<!ATTLIST cxxUnionTemplateParamType   %global-atts;
    class  CDATA "- topic/ph reference/ph apiRef/apiDefItem apiClassifier/apiDefItem cxxUnion/cxxUnionTemplateParamType ">
<!ATTLIST cxxUnionTemplateParamDeclarationName   %global-atts;
    class  CDATA "- topic/keyword reference/keyword apiRef/apiItemName apiClassifier/apiItemName cxxUnion/cxxUnionTemplateParamDeclarationName ">    
<!ATTLIST cxxUnionTemplateParamDefinitionName   %global-atts;
    class  CDATA "- topic/keyword reference/keyword apiRef/apiItemName apiClassifier/apiItemName cxxUnion/cxxUnionTemplateParamDefinitionName ">
    
<!-- Nested records -->
<!ATTLIST cxxUnionNested   %global-atts;
    class  CDATA "- topic/topic reference/reference apiRef/apiRef apiClassifier/apiClassifier cxxUnion/cxxUnionNested ">
<!ATTLIST cxxUnionNestedDetail   %global-atts;
    class  CDATA "- topic/body reference/refbody apiRef/apiDetail apiClassifier/apiDetail cxxUnion/cxxUnionNestedDetail ">    
<!ATTLIST cxxUnionNestedClass   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiClassifier/apiRelation cxxUnion/cxxUnionNestedClass ">
<!ATTLIST cxxUnionNestedStruct   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiClassifier/apiRelation cxxUnion/cxxUnionNestedStruct ">
<!ATTLIST cxxUnionNestedUnion   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiClassifier/apiRelation cxxUnion/cxxUnionNestedUnion ">

<!-- Location elements -->
<!ATTLIST cxxUnionAPIItemLocation   %global-atts;
    class  CDATA "- topic/ph reference/ph apiRef/apiDefItem apiClassifier/apiDefItem cxxUnion/cxxUnionAPIItemLocation ">
<!ATTLIST cxxUnionDeclarationFile   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxUnion/cxxUnionDeclarationFile ">
<!ATTLIST cxxUnionDeclarationFileLine   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxUnion/cxxUnionDeclarationFileLine ">
<!ATTLIST cxxUnionDefinitionFile   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxUnion/cxxUnionDefinitionFile ">
<!ATTLIST cxxUnionDefinitionFileLineStart   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxUnion/cxxUnionDefinitionFileLineStart ">
<!ATTLIST cxxUnionDefinitionFileLineEnd   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxUnion/cxxUnionDefinitionFileLineEnd ">

<!-- union has no inheritance  
<!ATTLIST cxxUnionInherits   %global-atts;
    class  CDATA "- topic/topic reference/reference apiRef/apiRef apiClassifier/apiClassifier cxxUnion/cxxUnionInherits ">  
<!ATTLIST cxxUnionInheritsDetail   %global-atts;
    class  CDATA "- topic/body reference/refbody apiRef/apiDetail apiClassifier/apiDetail cxxUnion/cxxUnionInheritsDetail ">    
<!ATTLIST cxxUnionEnumerationInherited   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiClassifier/apiRelation cxxUnion/cxxUnionEnumerationInherited ">
<!ATTLIST cxxUnionFunctionInherited    %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiClassifier/apiRelation cxxUnion/cxxUnionFunctionInherited  ">
<!ATTLIST cxxUnionVariableInherited   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiClassifier/apiRelation cxxUnion/cxxUnionVariableInherited ">  
-->
