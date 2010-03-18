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

REM Publishing target options. Possible values are "mode" or "ditaot". Default is "mode".
REM Set the default publishing target to be mode
set publishing_target=mode

REM Process arg 2 as publishing target if the user has specified it
if not "%2" == "" (
	if not "%2" == "mode" (
		if not "%2" == "ditaot" (
			GOTO INVALIDPUBLISHINGTARGETARG
		)
		set publishing_target=ditaot
	)
)

set python_home=%sbs_home%\win32\python252
set PATH=%python_home%;%PATH%
set current_drive=%cd:~0,2%

set input=%current_drive%%EPOCROOT%epoc32\release\doxygen\dita
rem set maps_output=%current_drive%%EPOCROOT%epoc32\release\doxygen\maps
rem set dita_output=%current_drive%%EPOCROOT%epoc32\release\doxygen\ditareference

set ANT_OPTS=-Xmx512m
set ant_home=%sbs_home%\ant
set ant_path=%ant_home%\bin\ant.bat
set build_file=%sbs_home%\CxxApiRef2Dita\build.xml

set map_creator_path=%sbs_home%\bin\MapCreator\mapcreator.exe
set component_map_creator_path=%sbs_home%\python\doxygen\component_map_creator.py
set guidiser_path=%sbs_home%\python\doxygen\guidiser.py
set filerenamer_path=%sbs_home%\python\doxygen\filerenamer.py
set linkinserter_path=%sbs_home%\python\doxygen\linkinserter.py

rem md %maps_output%
rem md %dita_output%
call :TRY "python %component_map_creator_path% %current_drive%%EPOCROOT%epoc32\build %input%"
call :TRY "%map_creator_path%  %sys_def_path% -o %input%\toc.ditamap %input%" 

rem call :TRY "python %guidiser_path% -p %publishing_target% -l 10 %maps_output%"
call :TRY "python %guidiser_path% -p %publishing_target% -l 10 %input%"
rem call :TRY "python %guidiser_path% -p %publishing_target% -l 10 %dita_output%\transformed"
rem call :TRY "python %filerenamer_path% -p %publishing_target% -l 10 %maps_output%"
call :TRY "python %filerenamer_path% -p %publishing_target% -l 10 %input%"
rem call :TRY "python %filerenamer_path% -p %publishing_target% -l 10 %dita_output%\transformed"
rem call :TRY "python %linkinserter_path% %input%"
rem call :TRY "python %linkinserter_path% %dita_output%\transformed"
rem call :TRY "%ant_path% -f %build_file% -Dinput="%input%" -Doutput="%dita_output%""
GOTO EOF

:ARGMISSING
echo Error Arguments missing were 1.system_defintion.xml path:[%1] 
echo.
goto USAGE

:INVALIDPUBLISHINGTARGETARG
echo Error invalid publishing target, possible values are "mode" or "ditaot". Invalid arg was "%2".
echo.
goto USAGE

:USAGE
echo Usage: orb_proces_cxx.bat SYSTEM_DEFINITION_PATH [PUBLISHING_TARGET]
echo Post process for Doxygen extension to sbs.
echo.
echo SYSTEM_DEFINITION_PATH		EPOC source tree os the directory containing v3 system definition and package definitions
echo PUBLISHING_TARGET		[mode], ditaot
echo.
goto EOF

:TRY
echo %TIME:~0,2%:%TIME:~3,2%:%TIME:~6,2% orb_process_cxx.bat is running %1
call %~1
IF %ERRORLEVEL%==0 echo %TIME:~0,2%:%TIME:~3,2%:%TIME:~6,2% orb_process_cxx.bat SUCCEEDED running %1
IF ERRORLEVEL 1 echo %TIME:~0,2%:%TIME:~3,2%:%TIME:~6,2% orb_process_cxx.bat FAILED running %1
echo ---------------------
:EOF