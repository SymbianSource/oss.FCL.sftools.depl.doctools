REM Copyright (c) 2007-2010 Nokia Corporation and/or its subsidiary(-ies) All rights reserved.
REM This component and the accompanying materials are made available under the terms of the License 
REM "Eclipse Public License v1.0" which accompanies this distribution, 
REM and is available at the URL "http://www.eclipse.org/legal/epl-v10.html".
REM Initial Contributors:
	REM Nokia Corporation - initial contribution.
REM Contributors: 
echo off
set input=%1
if "%1" == "" GOTO ARGMISSING

set sys_def_path=%1

set python_home=%sbs_home%\win32\python252
set PATH=%python_home%;%PATH%

set input=%EPOCROOT%epoc32\release\doxygen\dita
set maps_output=%EPOCROOT%epoc32\release\doxygen\maps
set dita_output=%EPOCROOT%epoc32\release\doxygen\ditareference

set ANT_OPTS=-Xmx512m
set ant_home=%sbs_home%\ant
set ant_path=%ant_home%\bin\ant.bat
set build_file=%sbs_home%\CxxApiRef2Dita\build.xml

set map_creator_path=%sbs_home%\bin\MapCreator\mapcreator.exe
set component_map_creator_path=%sbs_home%\python\doxygen\component_map_creator.py
set guidiser_path=%sbs_home%\python\doxygen\guidiser.py
set filerenamer_path=%sbs_home%\python\doxygen\filerenamer.py
set index_creator_path=%sbs_home%\python\doxygen\indexcreator.py


md %maps_output%
md %dita_output%
call %map_creator_path%  %sys_def_path% -o %maps_output%\toc.ditamap
call python %component_map_creator_path% %EPOCROOT%epoc32\build %maps_output%
rem call python %index_creator_path% %input% %output%\maps\index.ditamap

call %ant_path% -f %build_file% -Dinput="%input%" -Doutput="%dita_output%"

call python %guidiser_path% %maps_output%
call python %guidiser_path% %input%
call python %guidiser_path% %dita_output%\transformed

call python %filerenamer_path% %maps_output%
call python %filerenamer_path% %input%
call python %filerenamer_path% %dita_output%\transformed


goto EOF

:ARGMISSING
echo Error Arguments missing were 1.system_defintion.xml path:[%1] 
echo EPOC source tree os the directory containing v3 system definition
echo and package definitions
goto EOF

:EOF