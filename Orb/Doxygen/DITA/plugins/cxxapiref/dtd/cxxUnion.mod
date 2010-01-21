<!-- ================================================================= -->
<!--                    HEADER                                         -->
<!-- ================================================================= -->
<!--  MODULE:    C++ Union DTD                                         -->
<!--  VERSION:   0.1.0                                                 -->
<!--  DATE:      November 2009                                         -->
<!--                                                                   -->
<!-- ================================================================= -->

<!-- ================================================================= -->
<!--                    PUBLIC DOCUMENT TYPE DEFINITION                -->
<!--                    TYPICAL INVOCATION                             -->
<!--                                                                   -->
<!--  Refer to this file by the following public identifier or an 
      appropriate system identifier 
PUBLIC "-//NOKIA//DTD DITA C++ API Union Reference Type v0.1.0//EN"
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
<!ENTITY % cxxUnionDerivations                  "cxxUnionDerivations">
<!ENTITY % cxxUnionDerivation                   "cxxUnionDerivation">
<!ENTITY % cxxUnionTemplateParamList            "cxxUnionTemplateParamList">
<!ENTITY % cxxUnionTemplateParameter            "cxxUnionTemplateParameter">

<!-- Derivation -->
<!ENTITY % cxxUnionDerivationAccessSpecifier    "cxxUnionDerivationAccessSpecifier">
<!ENTITY % cxxUnionDerivationVirtual            "cxxUnionDerivationVirtual">
<!ENTITY % cxxUnionBaseClass                    "cxxUnionBaseClass">
<!ENTITY % cxxUnionBaseStruct                   "cxxUnionBaseStruct">
<!ENTITY % cxxUnionBaseUnion                    "cxxUnionBaseUnion">
<!ENTITY % cxxUnionInherits                     "cxxUnionInherits">

<!ENTITY % cxxUnionFunctionInherited            "cxxUnionFunctionInherited">
<!ENTITY % cxxUnionVariableInherited            "cxxUnionVariableInherited">
<!ENTITY % cxxUnionEnumerationInherited         "cxxUnionEnumerationInherited">
<!ENTITY % cxxUnionEnumeratorInherited          "cxxUnionEnumeratorInherited">

<!-- Nested members -->
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
    "%cxxUnionNestedClass; | %cxxUnionNestedStruct; | %cxxUnionNestedUnion; | cxxFunction | cxxDefine | cxxVariable | cxxEnumeration | cxxTypedef">
<!ENTITY % cxxUnion-info-types  "%cxxUnion-types-default;">

<!ENTITY included-domains "">

<!-- ============ Topic specializations ============ -->
                        <!-- (%cxxUnion-info-types;)* -->

<!ELEMENT cxxUnion   (
                        (%apiName;),
                        (%shortdesc;),
                        (%prolog;)?,
                        (%cxxUnionDetail;),
                        (%related-links;)?,
                        (%cxxUnion-info-types;)*,
                        (%cxxUnionInherits;)*
                      )
>
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
                                    (%cxxUnionDerivations;)?,
                                    (%cxxUnionTemplateParamList;)?,
                                    (%cxxUnionAPIItemLocation;)
                               )
>
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

<!ELEMENT cxxUnionDerivations   (%cxxUnionDerivation;)+ >
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
                                (
                                    %cxxUnionFunctionInherited;
                                    | %cxxUnionVariableInherited;
                                    | %cxxUnionEnumerationInherited;
                                    | %cxxUnionEnumeratorInherited;
                                )+
                              )
>
<!ATTLIST cxxUnionInherits    %univ-atts;
                                outputclass CDATA #IMPLIED
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

<!ELEMENT cxxUnionEnumeratorInherited  (#PCDATA)*>
<!ATTLIST cxxUnionEnumeratorInherited   href CDATA #IMPLIED
                                          keyref CDATA #IMPLIED
                                          type   CDATA  #IMPLIED
                                          %univ-atts;
                                          format        CDATA   #IMPLIED
                                          scope (local | peer | external) #IMPLIED
                                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionDerivationAccessSpecifier  EMPTY>
<!ATTLIST cxxUnionDerivationAccessSpecifier  name CDATA #FIXED "access"
                                            value (public) #FIXED "public"
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


<!ELEMENT cxxUnionTemplateParamList   (%cxxUnionTemplateParameter;)+ >
<!ATTLIST cxxUnionTemplateParamList    %univ-atts;
                                        outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionTemplateParameter   (#PCDATA)*>
<!ATTLIST cxxUnionTemplateParameter    %univ-atts;
                                        outputclass CDATA #IMPLIED
>

<!ELEMENT cxxUnionAPIItemLocation   (
                                        %cxxUnionDeclarationFile;,
                                        %cxxUnionDeclarationFileLine;,
                                        %cxxUnionDefinitionFile;,
                                        %cxxUnionDefinitionFileLineStart;,
                                        %cxxUnionDefinitionFileLineEnd;
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

<!-- Nested records e.g. <cxxUnionNestedClass keyref="class_two_1_1_nested">Two::Nested</cxxUnionNestedClass> -->
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
<!ATTLIST cxxAbstractClass   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxUnion/cxxUnionAbstract ">

<!-- Representing inheritance -->
<!ATTLIST cxxUnionDerivations   %global-atts;
    class  CDATA "- topic/ph reference/ph apiRef/apiDefItem cxxUnion/cxxUnionDerivations ">
<!ATTLIST cxxUnionDerivation   %global-atts;
    class  CDATA "- topic/ph reference/ph apiRef/apiDefItem cxxUnion/cxxUnionDerivation ">
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

<!-- Templates -->
<!ATTLIST cxxTemplateParamList   %global-atts;
    class  CDATA "- topic/ph reference/ph apiRef/apiDefItem cxxUnion/cxxUnionTemplateParamList ">

<!-- Nested records -->
<!ATTLIST cxxUnionNestedClass   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation cxxUnion/cxxUnionNestedClass ">
<!ATTLIST cxxUnionNestedStruct   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation cxxUnion/cxxUnionNestedStruct ">
<!ATTLIST cxxUnionNestedUnion   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation cxxUnion/cxxUnionNestedUnion ">

<!-- Location elements -->
<!ATTLIST cxxUnionAPIItemLocation   %global-atts;
    class  CDATA "- topic/ph reference/ph apiRef/apiDefItem cxxUnion/cxxUnionAPIItemLocation ">
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


