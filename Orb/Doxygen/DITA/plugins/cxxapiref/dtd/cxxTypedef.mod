<!-- ================================================================= -->
<!--                    HEADER                                         -->
<!-- ================================================================= -->
<!--  MODULE:    C++ Typedefs DTD                                      -->
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
PUBLIC "-//NOKIA//DTD DITA C++ API Typedef Reference Type v0.1.0//EN"
      Delivered as file "cxxTypedef.dtd"                               -->
 
<!-- ================================================================= -->
<!-- SYSTEM:     Darwin Information Typing Architecture (DITA)         -->
<!--                                                                   -->
<!-- PURPOSE:    C++ API Reference for Typedefs                        -->
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
<!ENTITY % cxxTypedef                                  "cxxTypedef">
<!ENTITY % cxxTypedefDetail                            "cxxTypedefDetail">
<!ENTITY % cxxTypedefDefinition                        "cxxTypedefDefinition">
<!ENTITY % cxxTypedefAccessSpecifier                   "cxxTypedefAccessSpecifier">

<!ENTITY % cxxTypedefDeclaredType                      "cxxTypedefDeclaredType">
<!ENTITY % cxxTypedefType                              "cxxTypedefType">
<!ENTITY % cxxTypedefScopedName                        "cxxTypedefScopedName">
<!ENTITY % cxxTypedefPrototype                         "cxxTypedefPrototype">
<!ENTITY % cxxTypedefNameLookup                        "cxxTypedefNameLookup">

<!-- Type information -->
<!ENTITY % cxxTypedefFundementalType                   "cxxTypedefFundementalType">
<!ENTITY % cxxTypedefClassType                         "cxxTypedefClassType">
<!ENTITY % cxxTypedefStructType                        "cxxTypedefStructType">
<!ENTITY % cxxTypedefUnionType                         "cxxTypedefUnionType">
<!ENTITY % cxxTypedefArrayType                         "cxxTypedefArrayType">
<!ENTITY % cxxTypedefVoidType                          "cxxTypedefVoidType">

<!-- Storage class specifiers and other qualifiers. -->
<!ENTITY % cxxTypedefAccessSpecifier                   "cxxTypedefAccessSpecifier">

<!-- Location information -->
<!ENTITY % cxxTypedefAPIItemLocation                   "cxxTypedefAPIItemLocation">
<!ENTITY % cxxTypedefDeclarationFile                   "cxxTypedefDeclarationFile">
<!ENTITY % cxxTypedefDeclarationFileLine               "cxxTypedefDeclarationFileLine">


<!-- ============ Hooks for shell DTD ============ -->
<!ENTITY % cxxTypedef-types-default  "no-topic-nesting">
<!ENTITY % cxxTypedef-info-types     "%cxxTypedef-types-default;">

<!ENTITY included-domains "">


<!-- ============ Topic specializations ============ -->
<!ELEMENT cxxTypedef       ( (%apiName;), (%shortdesc;), (%prolog;)?, (%cxxTypedefDetail;), (%related-links;)?, ( %cxxTypedef-info-types;)* )>
<!ATTLIST cxxTypedef    id ID #REQUIRED
                          conref CDATA #IMPLIED
                          outputclass CDATA #IMPLIED
                          xml:lang NMTOKEN #IMPLIED
                          %arch-atts;
                          domains CDATA "&included-domains;"
>

<!ELEMENT cxxTypedefDetail  ((%cxxTypedefDefinition;), (%apiDesc;)?, (%example;|%section;|%apiImpl;)*)>
<!ATTLIST cxxTypedefDetail  %id-atts;
                          translate (yes|no) #IMPLIED
                          xml:lang NMTOKEN #IMPLIED
                          outputclass CDATA #IMPLIED>

<!ELEMENT cxxTypedefDefinition   (
                                    (%cxxTypedefAccessSpecifier;)?,

                                    (%cxxTypedefDeclaredType;)?,
                                    (%cxxTypedefType;)?,

                                    (%cxxTypedefScopedName;)?,
                                    (%cxxTypedefPrototype;)?,
                                    (%cxxTypedefNameLookup;)?,
                                   
                                    (%cxxTypedefAPIItemLocation;)?
                                   )
>
<!ATTLIST cxxTypedefDefinition    spectitle CDATA #IMPLIED
                                  %univ-atts;
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxTypedefAccessSpecifier  EMPTY>
<!ATTLIST cxxTypedefAccessSpecifier  name CDATA #FIXED "access"
                                             value (public | protected | private) "public"
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxTypedefDeclaredType  (
                                        #PCDATA
                                        | %apiRelation;
                                    )*
>
<!ATTLIST cxxTypedefDeclaredType    %univ-atts;
                                        outputclass CDATA #IMPLIED
>

<!-- cxxTypedefScopedName need keyrefs and it can refer to other types (if not a fundemental type) -->
<!ELEMENT cxxTypedefScopedName   (#PCDATA)*>
<!ATTLIST cxxTypedefScopedName     href CDATA #IMPLIED
                                    keyref CDATA #IMPLIED
                                    type   CDATA  #IMPLIED
                                    %univ-atts;
                                    outputclass CDATA #IMPLIED
>

<!ELEMENT cxxTypedefPrototype   (#PCDATA)*>
<!ATTLIST cxxTypedefPrototype    %univ-atts;
                                    outputclass CDATA #IMPLIED
>

<!ELEMENT cxxTypedefNameLookup   (#PCDATA)*>
<!ATTLIST cxxTypedefNameLookup    %univ-atts;
                                    outputclass CDATA #IMPLIED
>

<!ELEMENT cxxTypedefType     (
                                        (
                                        %cxxTypedefFundementalType;
                                        | %cxxTypedefClassType;
                                        | %cxxTypedefStructType;
                                        | %cxxTypedefUnionType;
                                        | %cxxTypedefVoidType;
                                        ),
                                     (%cxxTypedefArrayType;)*,
                                     (%apiDefNote;)?
                                    )
>
<!ATTLIST cxxTypedefType      keyref CDATA #IMPLIED
                                      %univ-atts;
                                      outputclass CDATA #IMPLIED
>

<!-- Type information -->
<!-- Note: void is handled by a special element, not cxxTypedefFundementalType -->
<!-- Note; Enumerated attributes must be NMTOKENS so no ws. See XML 1.0 section 3.3.1 Attribute Types -->
<!ELEMENT cxxTypedefFundementalType  EMPTY>
<!ATTLIST cxxTypedefFundementalType  name CDATA #FIXED "type"
                                      value (
                                            char
                                            | signed_char
                                            | unsigned_char
                                            | short_int
                                            | int
                                            | long_int
                                            | unsigned_short_int
                                            | unsigned
                                            | unsigned_int
                                            | unsigned_long_int
                                            | wchar_t
                                            | bool
                                            | float
                                            | double
                                            | long_double
                                      ) #REQUIRED
                                      %univ-atts;
                                      outputclass CDATA #IMPLIED
>

<!ELEMENT cxxTypedefClassType  (#PCDATA)*>
<!ATTLIST cxxTypedefClassType  href CDATA #IMPLIED
                                  keyref CDATA #IMPLIED
                                  type   CDATA  #IMPLIED
                                  %univ-atts;
                                  format        CDATA   #IMPLIED
                                  scope (local | peer | external) #IMPLIED
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxTypedefStructType  (#PCDATA)*>
<!ATTLIST cxxTypedefStructType  href CDATA #IMPLIED
                                  keyref CDATA #IMPLIED
                                  type   CDATA  #IMPLIED
                                  %univ-atts;
                                  format        CDATA   #IMPLIED
                                  scope (local | peer | external) #IMPLIED
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxTypedefUnionType  (#PCDATA)*>
<!ATTLIST cxxTypedefUnionType  href CDATA #IMPLIED
                                  keyref CDATA #IMPLIED
                                  type   CDATA  #IMPLIED
                                  %univ-atts;
                                  format        CDATA   #IMPLIED
                                  scope (local | peer | external) #IMPLIED
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxTypedefVoidType  EMPTY>
<!ATTLIST cxxTypedefVoidType  name CDATA #FIXED "void"
                                  value CDATA #FIXED "void"
                                  %univ-atts;
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxTypedefArrayType  EMPTY>
<!ATTLIST cxxTypedefArrayType  name CDATA "arraysize"
                          value CDATA ""
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!-- Storage class specifiers and other qualifiers. -->

<!-- Location information -->
<!ELEMENT cxxTypedefAPIItemLocation   (
                                            %cxxTypedefDeclarationFile;,
                                            %cxxTypedefDeclarationFileLine;
                                        )
>
<!ATTLIST cxxTypedefAPIItemLocation    %univ-atts;
                                        outputclass CDATA #IMPLIED
>

<!ELEMENT cxxTypedefDeclarationFile  EMPTY>
<!ATTLIST cxxTypedefDeclarationFile  name CDATA #FIXED "filePath"
                                        value CDATA #REQUIRED
                                        %univ-atts;
                                        outputclass CDATA #IMPLIED
>

<!ELEMENT cxxTypedefDeclarationFileLine  EMPTY>
<!ATTLIST cxxTypedefDeclarationFileLine   name CDATA #FIXED "lineNumber"
                                            value CDATA #REQUIRED
                                            %univ-atts;
                                            outputclass CDATA #IMPLIED
>

<!-- ============ Class attributes for type ancestry ============ -->
<!-- TODO: Complete this for  all elements -->

<!ATTLIST cxxTypedef   %global-atts;
    class  CDATA "- topic/topic reference/reference apiRef/apiRef apiValue/apiValue cxxTypedef/cxxTypedef ">
<!ATTLIST cxxTypedefDetail   %global-atts;
    class  CDATA "- topic/body reference/refbody apiRef/apiDetail apiValue/apiValueDetail cxxTypedef/cxxTypedefDetail ">
<!ATTLIST cxxTypedefDefinition   %global-atts;
    class  CDATA "- topic/section reference/section apiRef/apiDef apiValue/apiValueDef cxxTypedef/cxxTypedefDefinition ">
<!ATTLIST cxxTypedefAPIItemLocation   %global-atts;
    class  CDATA "- topic/ph reference/ph apiRef/apiDefItem cxxTypedef/cxxTypedefAPIItemLocation">    
<!ATTLIST cxxTypedefAccessSpecifier   %global-atts;                                                      
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxTypedef/cxxTypedefAccessSpecifier "> 
<!ATTLIST cxxTypedefArrayType   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiArray apiOperation/apiArray cxxTypedef/cxxTypedefArrayType "> 
<!ATTLIST cxxTypedefClassType   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiOperation/apiOperationClassifier cxxTypedef/cxxTypedefClassType "> 
<!ATTLIST cxxTypedefDeclarationFile   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxTypedef/cxxTypedefDeclarationFile ">
<!ATTLIST cxxTypedefDeclarationFileLine   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxTypedef/cxxTypedefDeclarationFileLine ">
    <!--cxxTypedefDeclaredType 
cxxTypedefFundementalType 
cxxTypedefNameLookup  
cxxTypedefPrototype  
cxxTypedefScopedName
cxxTypedefType-->
<!ATTLIST cxxTypedefStructType   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiOperation/apiOperationClassifier cxxTypedef/cxxTypedefStructType ">
<!ATTLIST cxxTypedefUnionType   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiOperation/apiOperationClassifier cxxTypedef/cxxTypedefUnionType ">
 <!ATTLIST cxxTypedefVoidType   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiOperation/apiQualifier cxxTypedef/cxxTypedefVoidType ">