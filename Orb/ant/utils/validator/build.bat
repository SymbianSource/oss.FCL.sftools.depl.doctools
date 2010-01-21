REM Copyright (c) 2007-2010 Nokia Corporation and/or its subsidiary(-ies) All rights reserved.
REM This component and the accompanying materials are made available under the terms of the License 
REM "Eclipse Public License v1.0" which accompanies this distribution, 
REM and is available at the URL "http://www.eclipse.org/legal/epl-v10.html".
REM Initial Contributors:
	REM Nokia Corporation - initial contribution.
REM Contributors: 
@ECHO OFF

pushd %~dp0

SET OLD_ANT_HOME=%ANT_HOME%
SET OLD_HOSTNAME=%HOSTNAME%
set ANT_HOME=..\..\..\ant

IF not EXIST "%~dp0%computername%.properties" goto :propertiesError

call "..\..\bin\ant.bat" %*

:END
SET ANT_HOME=%OLD_ANT_HOME%
SET OLD_ANT_HOME=
SET OLD_HOSTNAME=
popd
Exit /b

:versionError
ECHO Please set the VERSION environment variable
goto :END

:propertiesError
ECHO Copy %~dp0properties.txt to %~dp0%computername%.properties and modify it for your system
goto :END