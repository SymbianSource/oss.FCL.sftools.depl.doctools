License
=======
Copyright (c) 2007-2010 Nokia Corporation and/or its subsidiary(-ies) All rights reserved.
This component and the accompanying materials are made available under the terms of the License 
"Eclipse Public License v1.0" which accompanies this distribution, 
and is available at the URL "http://www.eclipse.org/legal/epl-v10.html".

Orb Files
=========
Directory tree          Description
--------------          -----------
+---bin                 Preexisisting symbian build system directory. doxygen.exe is copied here and the batch script to transform output to DITA reference and produce ditamaps.
|   \---MapCreator      A tool for creating ditamaps from system definition files.
+---doc_pub             Additional documentation about converting output to DITA reference dtd and how to generate and use a system definition file with Orb.
+---lib                 Preexisisting symbian build system directory. Orb adds a doxygen configuration to the Symbian Build System so that it can run Doxygen.
\---python              Preexisisting symbian build system directory.
    \---doxygen         Python scripts that are used by the map creation and transform scripts.
+---utils				Contains the sysdefupgrade.xsl tool.

Installation
============
For installation instructions please read INSTALL.txt

Prerequisites
=============
* %EPOCROOT% environment variable is set to the parent of the epoc32 directory
  including a last \. If the directory is c:\foo\bar\epoc32 then this must be c:\foo\bar\
  if this is C:\epoc32 then %EPOCROOT% must be just \.
* %SBS_HOME% environment variable must be set to the Symbian Build System install directory.
  (usually C:\Apps\sbs)
* A version 3 system definition file and all of the package definition files it links to with relative paths OR
  A version 2 system definition file upgraded to 3 using the provided xslt (see below)
* An EPOC source directory (containing all packages prior to export) contains all required
  system_definition.xml and package_definition.xml files  
  
  
How to create html output from C++ source code  
==============================================

1. Run Orb on your project. 
	This creates the cxx specialised output from source.
2. Run the postprocessor on your project 
	This creates the top level maps and   the documents for convertion into html with DITA Open Toolkit.
3. Run DOT on the output to create html.
	For small sets of xml use DITA Open Toolkit version 1.5.1 with the cxx specialisation plugin.
	We recommend the use of the MPDOT tool on large amounts of documents. 
	The MPDOT tool is supplied with the specialised cxx DITA Open Toolkit plugin.
	
	
1. Run Orb on your project
==========================
Once Orb is installed, open a console, change directory to the folder containing the bld.inf and mrp file for your project and run

sbs -c doxygen

You can also run it with a .dox extension to your existing configuration. e.g.
sbs -c arm.v7.rvct4_0.dox
sbs -c rvct3_0.dox
sbs -c armv5_urel.dox

The documentation for your project will be created in the \epoc32\build\release on your system. 

If you need to run Orb on a complete OS see doc_pub\sysdefv3_guide.txt
The above command builds all of the source. Build an SDK release with this command:

sbs -c doxygen-sdk

Output
======
Orb builds output to the epoc32 directory under the location indicated by the EPOCROOT environment variable.
The two locations are epoc32\build and epoc32\release\doxygen\dita. The build directory contains the temporary 
output that doxygen produces as it runs on all the targets of the Symbian OS. There is one directory per component
and each component directory contains the doxygen output for the documentation for each dll or executable 
target being built. The release directory contains the output of every target copied to a single directory
to remove duplicates.
The output directory epoc32\release\doxygen\dita is required by the script that converts the cxx DITA output from doxygen to DITA reference.
See doc_pub\converting_to_reference.txt for guidance.


Running the postprocessor
=========================
Now you must run the postprocessing step to create top level maps and ready your output so that it can be built into html using DITA Open Toolkit.

Introduction
============
The postprocessing script runs several scripts on Doxygen output.
This includes:
-A script that creates a DITA map from a Symbian build system compatible 
system definition version 3 XML file.
-A script that creates a map for each component.
-A script that replaces all id attribute values and all links to ids (e.g in xrefs) 
to a global unique id (GUID)
-A script that renames each file to a GUID value.

Creating a table of contents from a system definition version 2 file
====================================================================
The map creator in this package is only compatible with system definition version 3 files
If the symbian build system is run using a system definition version 2 file it must be converted to version 3
before the convertion can be run.
To do this please do the following:
Set up the prerequisites as described in sysdefv3_guide.txt (this is to set up the Apache Xalan transformer for use on the command line)
From the console run:

java org.apache.xalan.xslt.Process -in C:\path_to_system_definition\canonical_system_definition_GT_tb92sf.xml -xsl %SBS_HOME%\utils\sysdefupgrade.xsl -out c:\output_path\new_system_definition.xml

You can use one of the examples in the "Running the batch script" section below on this new system defintion version 3 file to produce correct maps for this documentation build.  

Running the batch script
========================
The batch file is in %SBS_HOME%\bin\orb_process_cxx.bat
If the symbian build system version 2 has been installed using an installer the %SBS_HOME% environment 
variable will be set and be on the system path which means it can be invoked from anywhere.
If it is not set then please set it.

The usage is as follows:
orb_proces_cxx.bat SYSTEM_DEFINITION_PATH [PUBLISHING_TARGET]

SYSTEM_DEFINITION_PATH	EPOC source tree os the directory containing v3 system definition and package definitions
PUBLISHING_TARGET	    [mode], ditaot

PUBLISHING_TARGET is an optional argument that determines how the output of the tool is prepared for the intended publishing environment.
"mode" is the default publishing target and will be used if no option is given.

Examples:
orb_process_cxx.bat C:\EPOC\master\sf\os\deviceplatformrelease\foundation_system\system_model\system_definition.xml

orb_process_cxx.bat C:\EPOC\master\sf\os\deviceplatformrelease\foundation_system\system_model\system_definition.xml mode

orb_process_cxx.bat C:\EPOC\master\sf\os\deviceplatformrelease\foundation_system\system_model\system_definition.xml ditaot

Output
======
The output DITA maps go into %EPOCROOT%epoc32\release\doxygen\dita. 
This directory now contains:
* the main table of contents named GUID-445218BA-A6BF-334B-9337-5DCBD993AEB3.ditamap. 
* the component level maps. 
* all of the reference cxx XML files.

All of these files are renamed with a GUID. The maps all end with .ditamap and all the reference documents end in .xml.

The main table of contents links to the component level maps and they in turn link to each target's ditamap generated by doxygen 
There is no log capture automatically performed by this script. Capture the stdout if you wish to review this.


Running DITA Open Toolkit to create html
========================================
For smaller sets of documents it is possible to use DITA Open Toolkit version 1.5.1 with the cxxapiref plugin to build your documentation. 
It is recommended that the supplied DITA Open Toolkit is used, as supplied with it is a utility that allows each component to be built 
concurrently. This saves time and reduces the likelihood of java out of memory errors.


Additional documentation
========================
Some additional documents have been included in the directory named documentation
For a guide on generating and using a system definition version 3 with Orb please see
sysdefv3_guide.txt
For doxygen documentation please see DoxygenDITAEditionUserGuide.chm
