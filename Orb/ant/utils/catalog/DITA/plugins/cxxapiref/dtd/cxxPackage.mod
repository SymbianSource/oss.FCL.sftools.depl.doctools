<!--
Copyright (c) 2009 Nokia Corporation and/or its subsidiary(-ies).
All rights reserved.
-->

<!-- ============ Hooks for domain extension ============ -->
<!ENTITY % cxxPackage           "cxxPackage">
<!ENTITY % cxxPackageDetail     "cxxPackageDetail">


<!-- ============ Hooks for shell DTD ============ -->
<!ENTITY % cxxPackage-types-default  "no-topic-nesting">
<!ENTITY % cxxPackage-info-types     "%cxxPackage-types-default;">

<!ENTITY included-domains "">


<!-- ============ Topic specializations ============ -->
<!ELEMENT cxxPackage     ((%apiSyntax;)?, (%apiName;), (%shortdesc;), (%prolog;)?, (%cxxPackageDetail;), (%related-links;)?, (%cxxPackage-info-types;)*)>
<!ATTLIST cxxPackage     id ID #REQUIRED
                          conref CDATA #IMPLIED
                          outputclass CDATA #IMPLIED
                          xml:lang NMTOKEN #IMPLIED
                          %arch-atts;
                          domains CDATA "&included-domains;"
>

<!ELEMENT cxxPackageDetail      ((%apiDesc;)?, (%example;|%section;|%apiImpl;)*)>
<!ATTLIST cxxPackageDetail  %id-atts;
                          translate (yes|no) #IMPLIED
                          xml:lang NMTOKEN #IMPLIED
                          outputclass CDATA #IMPLIED>


<!-- ============ Class attributes for type ancestry ============ -->
<!ATTLIST cxxPackage   %global-atts;
    class  CDATA "- topic/topic reference/reference apiRef/apiRef apiPackage/apiPackage cxxPackage/cxxPackage ">
<!ATTLIST cxxPackageDetail   %global-atts;
    class  CDATA "- topic/body reference/refbody apiRef/apiDetail apiPackage/apiDetail cxxPackage/cxxPackageDetail ">
