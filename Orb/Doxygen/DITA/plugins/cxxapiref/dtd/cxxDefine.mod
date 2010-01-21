<!-- ================================================================= -->
<!--                    HEADER                                         -->
<!-- ================================================================= -->
<!--  MODULE:    C++ Define DTD                                      -->
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
PUBLIC "-//NOKIA//DTD DITA C++ API Define Reference Type v0.1.0//EN"
      Delivered as file "cxxDefine.dtd"                              -->
 
<!-- ================================================================= -->
<!-- SYSTEM:     Darwin Information Typing Architecture (DITA)         -->
<!--                                                                   -->
<!-- PURPOSE:    C++ API Reference for Defines                       -->
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
<!ENTITY % cxxDefine                                  "cxxDefine">
<!ENTITY % cxxDefineDetail                            "cxxDefineDetail">
<!ENTITY % cxxDefineDefinition                        "cxxDefineDefinition">

<!ENTITY % cxxDefineDeclaredType                      "cxxDefineDeclaredType">
<!ENTITY % cxxDefineReturnType                        "cxxDefineReturnType">
<!ENTITY % cxxDefineScopedName                        "cxxDefineScopedName">
<!ENTITY % cxxDefinePrototype                         "cxxDefinePrototype">
<!ENTITY % cxxDefineNameLookup                        "cxxDefineNameLookup">
<!ENTITY % cxxDefineReimplemented                     "cxxDefineReimplemented">

<!-- Parameters -->
<!ENTITY % cxxDefineParameters                        "cxxDefineParameters">
<!ENTITY % cxxDefineParameter                         "cxxDefineParameter">
<!ENTITY % cxxDefineParameterDeclaredType             "cxxDefineParameterDeclaredType">
<!ENTITY % cxxDefineParameterType                     "cxxDefineParameterType">
<!ENTITY % cxxDefineParameterDeclarationName          "cxxDefineParameterDeclarationName">
<!ENTITY % cxxDefineParameterDefinitionName           "cxxDefineParameterDefinitionName">
<!ENTITY % cxxDefineParameterDefaultValue             "cxxDefineParameterDefaultValue">

<!-- Type information -->
<!ENTITY % cxxDefineFundementalType                   "cxxDefineFundementalType">
<!ENTITY % cxxDefineClassType                         "cxxDefineClassType">
<!ENTITY % cxxDefineStructType                        "cxxDefineStructType">
<!ENTITY % cxxDefineUnionType                         "cxxDefineUnionType">
<!ENTITY % cxxDefineArrayType                         "cxxDefineArrayType">
<!ENTITY % cxxDefineVoidType                          "cxxDefineVoidType">

<!-- Storage class specifiers and other qualifiers. -->
<!ENTITY % cxxDefineAccessSpecifier                   "cxxDefineAccessSpecifier">
<!ENTITY % cxxDefineStorageClassSpecifierExtern       "cxxDefineStorageClassSpecifierExtern">
<!ENTITY % cxxDefineStorageClassSpecifierStatic       "cxxDefineStorageClassSpecifierStatic">
<!ENTITY % cxxDefineStorageClassSpecifierMutable      "cxxDefineStorageClassSpecifierMutable">
<!ENTITY % cxxDefineConst                             "cxxDefineConst">
<!ENTITY % cxxDefineExplicit                          "cxxDefineExplicit">
<!ENTITY % cxxDefineInline                            "cxxDefineInline">
<!ENTITY % cxxDefineVirtual                           "cxxDefineVirtual">
<!ENTITY % cxxDefinePureVirtual                       "cxxDefinePureVirtual">
<!ENTITY % cxxDefineConstructor                       "cxxDefineConstructor">
<!ENTITY % cxxDefineDestructor                        "cxxDefineDestructor">

<!-- Location information -->
<!ENTITY % cxxDefineAPIItemLocation                   "cxxDefineAPIItemLocation">
<!ENTITY % cxxDefineDeclarationFile                   "cxxDefineDeclarationFile">
<!ENTITY % cxxDefineDeclarationFileLine               "cxxDefineDeclarationFileLine">
<!ENTITY % cxxDefineDefinitionFile                    "cxxDefineDefinitionFile">
<!ENTITY % cxxDefineDefinitionFileLineStart           "cxxDefineDefinitionFileLineStart">
<!ENTITY % cxxDefineDefinitionFileLineEnd             "cxxDefineDefinitionFileLineEnd">

<!-- ============ Hooks for shell DTD ============ -->
<!ENTITY % cxxDefine-types-default  "no-topic-nesting">
<!ENTITY % cxxDefine-info-types     "%cxxDefine-types-default;">

<!ENTITY included-domains "">


<!-- ============ Topic specializations ============ -->
<!ELEMENT cxxDefine   ( (%apiName;), (%shortdesc;), (%prolog;)?, (%cxxDefineDetail;), (%related-links;)?, (%cxxDefine-info-types;)* )>
<!ATTLIST cxxDefine      id ID #REQUIRED
                          conref CDATA #IMPLIED
                          outputclass CDATA #IMPLIED
                          xml:lang NMTOKEN #IMPLIED
                          %arch-atts;
                          domains CDATA "&included-domains;"
>

<!ELEMENT cxxDefineDetail  (%cxxDefineDefinition;, (%apiDesc;)?, (%example; | %section; | %apiImpl;)*)>
<!ATTLIST cxxDefineDetail  %id-atts;
                              translate (yes|no) #IMPLIED
                              xml:lang NMTOKEN #IMPLIED
                              outputclass CDATA #IMPLIED>

<!ELEMENT cxxDefineDefinition   (
                                    (%cxxDefineAccessSpecifier;)?,
                                    (%cxxDefineStorageClassSpecifierExtern;)?,
                                    (%cxxDefineStorageClassSpecifierStatic;)?,
                                    (%cxxDefineStorageClassSpecifierMutable;)?,
                                    (%cxxDefineConst;)?,
                                    (%cxxDefineExplicit;)?,
                                    (%cxxDefineInline;)?,
                                    (%cxxDefineVirtual;)?,
                                    (%cxxDefinePureVirtual;)?,
                                    (%cxxDefineConstructor;)?,
                                    (%cxxDefineDestructor;)?,

                                    (%cxxDefineDeclaredType;)?,
                                    (%cxxDefineReturnType;)?,

                                    (%cxxDefineScopedName;)?,
                                    (%cxxDefinePrototype;)?,
                                    (%cxxDefineNameLookup;)?,

                                    (%cxxDefineReimplemented;)?,

                                    (%cxxDefineParameters;)?,

                                    (%cxxDefineAPIItemLocation;)?
                                   )
>
<!ATTLIST cxxDefineDefinition    spectitle CDATA #IMPLIED
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineAccessSpecifier  EMPTY>
<!ATTLIST cxxDefineAccessSpecifier  name CDATA #FIXED "access"
                                             value (public|protected|private) "public"
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineDeclaredType   (
                                        #PCDATA
                                        | %apiRelation;
                                     )*
>
<!ATTLIST cxxDefineDeclaredType    %univ-atts;
                                        outputclass CDATA #IMPLIED
>

<!-- cxxDefineScopedName need keyrefs and it can refer to other types (if not a fundemental type) -->
<!ELEMENT cxxDefineScopedName   (#PCDATA)*>
<!ATTLIST cxxDefineScopedName     href CDATA #IMPLIED
                                    keyref CDATA #IMPLIED
                                    type   CDATA  #IMPLIED
                                    %univ-atts;
                                    outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefinePrototype   (#PCDATA)*>
<!ATTLIST cxxDefinePrototype    %univ-atts;
                                    outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineNameLookup   (#PCDATA)*>
<!ATTLIST cxxDefineNameLookup    %univ-atts;
                                    outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineReimplemented  (#PCDATA)*>
<!ATTLIST cxxDefineReimplemented href CDATA #IMPLIED
                                      keyref CDATA #IMPLIED
                                      type   CDATA  #IMPLIED
                                      %univ-atts;
                                      format        CDATA   #IMPLIED
                                      scope (local | peer | external) #IMPLIED
                                      outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineParameters   (%cxxDefineParameter;)* >
<!ATTLIST cxxDefineParameters    %univ-atts;
                                    outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineParameter  (
                                    (%cxxDefineParameterDeclaredType;)?,
                                    (%cxxDefineParameterType;)?,
                                    (%cxxDefineParameterDeclarationName;)?,
                                    (%cxxDefineParameterDefinitionName;)?,
                                    (%cxxDefineParameterDefaultValue;)?,
                                    (%apiDefNote;)?
                                )
>
<!ATTLIST cxxDefineParameter  %univ-atts;
                                outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineParameterDeclaredType  (
                                                #PCDATA
                                                | %apiRelation;
                                            )*
>
<!ATTLIST cxxDefineParameterDeclaredType  %univ-atts;
                                            outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineParameterDeclarationName  (#PCDATA)*>
<!ATTLIST cxxDefineParameterDeclarationName  %univ-atts;
                                                outputclass CDATA #IMPLIED
>


<!ELEMENT cxxDefineParameterDefinitionName  (#PCDATA)*>
<!ATTLIST cxxDefineParameterDefinitionName  %univ-atts;
                                                outputclass CDATA #IMPLIED
>

<!-- TODO: This encloses PCDATA but linkifyTextDITA() is called. -->
<!ELEMENT cxxDefineParameterDefaultValue  (
                                                #PCDATA
                                                | %apiRelation;
                                            )*
>
<!ATTLIST cxxDefineParameterDefaultValue  %univ-atts;
                                            outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineParameterType     (
                                        (
                                        %cxxDefineFundementalType;
                                        | %cxxDefineClassType;
                                        | %cxxDefineStructType;
                                        | %cxxDefineUnionType;
                                        | %cxxDefineVoidType;
                                        ),
                                     (%cxxDefineArrayType;)*,
                                     (%apiDefNote;)?
                                    )
>
<!ATTLIST cxxDefineParameterType      keyref CDATA #IMPLIED
                                      %univ-atts;
                                      outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineReturnType     (
                                        (
                                        %cxxDefineFundementalType;
                                        | %cxxDefineClassType;
                                        | %cxxDefineStructType;
                                        | %cxxDefineUnionType;
                                        | %cxxDefineVoidType;
                                        ),
                                     (%cxxDefineArrayType;)*,
                                     (%apiDefNote;)?
                                    )
>
<!ATTLIST cxxDefineReturnType      keyref CDATA #IMPLIED
                                      %univ-atts;
                                      outputclass CDATA #IMPLIED
>



<!-- Type information -->
<!-- Note: void is handled by a special element, not cxxDefineFundementalType -->
<!-- Note; Enumerated attributes must be NMTOKENS so no ws. See XML 1.0 section 3.3.1 Attribute Types -->
<!ELEMENT cxxDefineFundementalType  EMPTY>
<!ATTLIST cxxDefineFundementalType  name CDATA #FIXED "type"
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

<!ELEMENT cxxDefineClassType  (#PCDATA)*>
<!ATTLIST cxxDefineClassType  href CDATA #IMPLIED
                                  keyref CDATA #IMPLIED
                                  type   CDATA  #IMPLIED
                                  %univ-atts;
                                  format        CDATA   #IMPLIED
                                  scope (local | peer | external) #IMPLIED
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineStructType  (#PCDATA)*>
<!ATTLIST cxxDefineStructType  href CDATA #IMPLIED
                                  keyref CDATA #IMPLIED
                                  type   CDATA  #IMPLIED
                                  %univ-atts;
                                  format        CDATA   #IMPLIED
                                  scope (local | peer | external) #IMPLIED
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineUnionType  (#PCDATA)*>
<!ATTLIST cxxDefineUnionType  href CDATA #IMPLIED
                                  keyref CDATA #IMPLIED
                                  type   CDATA  #IMPLIED
                                  %univ-atts;
                                  format        CDATA   #IMPLIED
                                  scope (local | peer | external) #IMPLIED
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineVoidType  EMPTY>
<!ATTLIST cxxDefineVoidType  name CDATA #FIXED "void"
                                  value CDATA #FIXED "void"
                                  %univ-atts;
                                  outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineArrayType  EMPTY>
<!ATTLIST cxxDefineArrayType  name CDATA "arraysize"
                          value CDATA ""
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!-- Storage class specifiers and other qualifiers. -->
<!ELEMENT cxxDefineStorageClassSpecifierExtern  EMPTY>
<!ATTLIST cxxDefineStorageClassSpecifierExtern  name CDATA #FIXED "extern"
                          value CDATA #FIXED "extern"
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineStorageClassSpecifierStatic  EMPTY>
<!ATTLIST cxxDefineStorageClassSpecifierStatic  name CDATA #FIXED "static"
                          value CDATA #FIXED "static"
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineStorageClassSpecifierMutable  EMPTY>
<!ATTLIST cxxDefineStorageClassSpecifierMutable  name CDATA #FIXED "mutable"
                          value CDATA #FIXED "mutable"
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineConst  EMPTY>
<!ATTLIST cxxDefineConst  name CDATA #FIXED "const"
                          value CDATA #FIXED "const"
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineExplicit  EMPTY>
<!ATTLIST cxxDefineExplicit  name CDATA #FIXED "Explicit"
                          value CDATA #FIXED "Explicit"
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineInline  EMPTY>
<!ATTLIST cxxDefineInline  name CDATA #FIXED "Inline"
                          value CDATA #FIXED "Inline"
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineConstructor  EMPTY>
<!ATTLIST cxxDefineConstructor  name CDATA #FIXED "Constructor"
                          value CDATA #FIXED "Constructor"
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineDestructor  EMPTY>
<!ATTLIST cxxDefineDestructor  name CDATA #FIXED "Destructor"
                          value CDATA #FIXED "Destructor"
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineVirtual  EMPTY>
<!ATTLIST cxxDefineVirtual  name CDATA #FIXED "Virtual"
                          value CDATA #FIXED "Virtual"
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefinePureVirtual  EMPTY>
<!ATTLIST cxxDefinePureVirtual  name CDATA #FIXED "PureVirtual"
                          value CDATA #FIXED "PureVirtual"
                          %univ-atts;
                          outputclass CDATA #IMPLIED
>

<!-- Location information -->
<!ELEMENT cxxDefineAPIItemLocation   (
                                            %cxxDefineDeclarationFile;,
                                            %cxxDefineDeclarationFileLine;,
                                            (%cxxDefineDefinitionFile;)?,
                                            (%cxxDefineDefinitionFileLineStart;)?,
                                            (%cxxDefineDefinitionFileLineEnd;)?
                                        )
>
<!ATTLIST cxxDefineAPIItemLocation    %univ-atts;
                                        outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineDeclarationFile  EMPTY>
<!ATTLIST cxxDefineDeclarationFile  name CDATA #FIXED "filePath"
                                      value CDATA #REQUIRED
                                      %univ-atts;
                                      outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineDeclarationFileLine  EMPTY>
<!ATTLIST cxxDefineDeclarationFileLine   name CDATA #FIXED "lineNumber"
                                            value CDATA #REQUIRED
                                            %univ-atts;
                                            outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineDefinitionFile  EMPTY>
<!ATTLIST cxxDefineDefinitionFile  name CDATA #FIXED "filePath"
                                      value CDATA #REQUIRED
                                      %univ-atts;
                                      outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineDefinitionFileLineStart  EMPTY>
<!ATTLIST cxxDefineDefinitionFileLineStart  name CDATA #FIXED "lineNumber"
                                                value CDATA #REQUIRED
                                                %univ-atts;
                                                outputclass CDATA #IMPLIED
>

<!ELEMENT cxxDefineDefinitionFileLineEnd  EMPTY>
<!ATTLIST cxxDefineDefinitionFileLineEnd  name CDATA #FIXED "lineNumber"
                                            value CDATA #REQUIRED
                                            %univ-atts;
                                            outputclass CDATA #IMPLIED
>



<!-- ============ Class attributes for type ancestry ============ -->
<!-- TODO: Complete this for  all elements -->

<!ATTLIST cxxDefine   %global-atts;
    class  CDATA "- topic/topic reference/reference apiRef/apiRef apiOperation/apiOperation cxxDefine/cxxDefine ">
<!ATTLIST cxxDefineDetail   %global-atts;
    class  CDATA "- topic/body reference/refbody apiRef/apiDetail apiOperation/apiOperationDetail cxxDefine/cxxDefineDetail ">
<!ATTLIST cxxDefineDefinition   %global-atts;
    class  CDATA "- topic/section reference/section apiRef/apiDef apiOperation/apiOperationDef cxxDefine/cxxDefineDefinition ">

<!-- Type information -->
<!ATTLIST cxxDefineFundementalType   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiType apiOperation/apiType cxxDefine/cxxDefineFundementalType ">
<!ATTLIST cxxDefineClassType   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiOperation/apiOperationClassifier cxxDefine/cxxDefineClassType ">
<!ATTLIST cxxDefineStructType   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiOperation/apiOperationClassifier cxxDefine/cxxDefineStructType ">
<!ATTLIST cxxDefineUnionType   %global-atts;
    class  CDATA "- topic/xref reference/xref apiRef/apiRelation apiOperation/apiOperationClassifier cxxDefine/cxxDefineUnionType ">
<!ATTLIST cxxDefineArrayType   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiArray apiOperation/apiArray cxxDefine/cxxDefineArrayType ">
<!ATTLIST cxxDefineVoidType   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiOperation/apiQualifier cxxDefine/cxxDefineVoidType ">


<!-- Operation qualifiers specialised form topic/state reference/state apiRef/apiQualifier apiOperation/apiQualifier -->
<!ATTLIST cxxDefineStorageClassSpecifierExtern   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiOperation/apiQualifier  cxxDefine/cxxDefineStorageClassSpecifierExtern ">
<!ATTLIST cxxDefineStorageClassSpecifierStatic   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiOperation/apiQualifier cxxDefine/cxxDefineStorageClassSpecifierStatic ">
<!ATTLIST cxxDefineStorageClassSpecifierMutable   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiOperation/apiQualifier cxxDefine/cxxDefineStorageClassSpecifierMutable ">
<!ATTLIST cxxDefineConst   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiOperation/apiQualifier cxxDefine/cxxDefineConst ">
<!ATTLIST cxxDefineExplicit   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiOperation/apiQualifier cxxDefine/cxxDefineExplicit ">
<!ATTLIST cxxDefineInline   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiOperation/apiQualifier cxxDefine/cxxDefineInline ">
<!ATTLIST cxxDefineConstructor   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiOperation/apiQualifier cxxDefine/cxxDefineConstructor ">
<!ATTLIST cxxDefineDestructor   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiOperation/apiQualifier cxxDefine/cxxDefineDestructor ">
<!ATTLIST cxxDefineVirtual   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiOperation/apiQualifier cxxDefine/cxxDefineVirtual ">
<!ATTLIST cxxDefinePureVirtual   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiOperation/apiQualifier cxxDefine/cxxDefinePureVirtual ">

<!-- Location elements -->
<!ATTLIST cxxDefineAPIItemLocation   %global-atts;
    class  CDATA "- topic/ph reference/ph apiRef/apiDefItem cxxDefine/cxxDefineAPIItemLocation ">
<!ATTLIST cxxDefineDeclarationFile   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxDefine/cxxDefineDeclarationFile ">
<!ATTLIST cxxDefineDeclarationFileLine   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxDefine/cxxDefineDeclarationFileLine ">
<!ATTLIST cxxDefineDefinitionFile   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxDefine/cxxDefineDefinitionFile ">
<!ATTLIST cxxDefineDefinitionFileLineStart   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxDefine/cxxDefineDefinitionFileLineStart ">
<!ATTLIST cxxDefineDefinitionFileLineEnd   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxDefine/cxxDefineDefinitionFileLineEnd ">

<!ATTLIST cxxDefineAccessSpecifier   %global-atts;
    class  CDATA "- topic/state reference/state apiRef/apiQualifier apiClassifier/apiQualifier cxxDefine/cxxDefineAccessSpecifier ">
<!-- 
cxxDefineDeclaredType  
cxxDefineNameLookup  
cxxDefineParameter 
cxxDefineParameterDeclarationName 
cxxDefineParameterDeclaredType 
cxxDefineParameterDefaultValue 
cxxDefineParameterDefinitionName 
cxxDefineParameters  
cxxDefineParameterType    
cxxDefinePrototype  
cxxDefineReimplemented 
cxxDefineReturnType    
cxxDefineScopedName     
 -->