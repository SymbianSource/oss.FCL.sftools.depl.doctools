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
+---ant                 Ant scripts to transform cxxApiRef dtd xml to dita reference xml.
+---bin                 Preexisisting symbian build system directory. doxygen.exe is copied here and the batch script to transform output to dita reference and produce ditamaps.
|   \---MapCreator      A tool for creating ditamaps from system definition files.
+---CxxApiRef2Dita      xslt and ant scripts to perform the cxxApiRef to dita reference conversion.
+---documentation       Additional documentation about converting output to dita reference dtd and how to generate and use a system definition file with Orb.
+---lib                 Preexisisting symbian build system directory. Orb adds a doxygen configuration to the Symbian Build System so that it can run Doxygen.
\---python              Preexisisting symbian build system directory.
    \---doxygen         Python scripts that are used by the map creation and transform scripts

Installation
============
For installation instructions please read INSTALL.txt

Running Orb on my project
=========================

Once Orb is installed, open a console, change directory to the folder containing the bld.inf and mrp file for your project and run

sbs -c doxygen

You can also run it with a .dox extension to your existing configuration. e.g.

sbs -c arm.v7.rvct4_0.dox
sbs -c rvct3_0.dox
sbs -c armv5_urel.dox

The documentation for your project will be created in the \epoc32\build\release on your system. 

The documentation will conform to the cxx DITA dtd specialisation and will need to be converted to 
to xml that conforms to standard DITA reference xml to be processed by the Dita Open Toolkit.
For more information on performing this conversion please see documentation\converting_to_reference.txt.

Output
======
Orb builds output to the epoc32 directory under the location indicated by the EPOCROOT environment variable.
The two locations are epoc32\builds and epoc32\release\dita. The builds directory contains the temporary output
that doxygen produces as it runs on all the targets of the Symbian OS. There is one directory per component
and each component directory contains the doxygen output for the documentation for each dll or executable 
target being built. The release directory contains the output of every target copied to a single directory
to remove duplicates.
The script that converts the cxx dita output from doxygen to dita reference requires the release\dita directory.
Its outputs files to epoc32\release\ditareference and epoc32\release\maps.

Additional documentation
========================
Some additional documents have been included in the directory named documentation
For a guide on converting doxygen dita output to dita reference and producing dita maps please see 
converting_to_reference.txt 
For a guide on generating and using a system definition version 3 with Orb please see
sysdefv3_guide.txt
For doxygen documentation please see DoxygenDITAEditionUserGuide.chm
