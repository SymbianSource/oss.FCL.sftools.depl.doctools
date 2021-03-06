#!
#! This TMAKE template - Microsoft Visual C++ 5.0 libraries
#!
#${
    if ( Config("qt") || Config("opengl") ) {
	Project('CONFIG += windows');
    }
    if ( Config("qt") ) {
	$moc_aware = 1;
	AddIncludePath(Project('TMAKE_INCDIR_QT'));
    }

    $project{"VC_PROJ_TYPE"} = 'Win32 (x86) Static Library';
    $project{"VC_PROJ_CODE"} = '0x0104';

    $vc_cpp_def_release = '/D "NDEBUG" /D "WIN32" /D "_WINDOWS" ';
    $vc_cpp_def_debug   = '/D "_DEBUG" /D "WIN32" /D "_WINDOWS" ';
    $vc_cpp_opt_release = '/nologo /W3 /GX /O2 ';
    $vc_cpp_opt_debug   = '/nologo /W3 /Gm /GX /Zi /Od ';
    $vc_cpp_opt_common  = '/YX /FD /c';
    $project{"VC_BASE_CPP_RELEASE"} = $vc_cpp_opt_release . $vc_cpp_def_release . $vc_cpp_opt_common;
    $project{"VC_BASE_CPP_DEBUG"}   = $vc_cpp_opt_debug   . $vc_cpp_def_debug   . $vc_cpp_opt_common;
    ExpandPath("INCPATH",'/I ',' /I ','');
    if ( $text ne "" ) { $vc_inc = $text . " ";  $text = ""; } else { $vc_inc = ""; }
    ExpandGlue("DEFINES",'/D "','" /D "','"');
    if ( $text ne "" ) { $vc_def = $text . " ";  $text = ""; } else { $vc_def = ""; }
    $project{"VC_CPP_RELEASE"} = $vc_cpp_opt_release . $vc_inc . $vc_cpp_def_release . $vc_def . $vc_cpp_opt_common;
    $project{"VC_CPP_DEBUG"}   = $vc_cpp_opt_debug   . $vc_inc . $vc_cpp_def_debug   . $vc_def . $vc_cpp_opt_common;

    $project{"MAKEFILE"}  = $project{"PROJECT"} . ".mak";
    $project{"TARGETLIB"} = $project{"TARGET"}  . ".lib";
    Project('TMAKE_FILETAGS = HEADERS SOURCES TARGET DESTDIR $$FILETAGS');
    foreach ( split(/\s/,Project('TMAKE_FILETAGS')) ) {
	$project{$_} =~ s-/-\\-g;
    }
    StdInit();
    if ( defined($project{"DESTDIR"}) ) {
	$project{"TARGETLIB"} = $project{"DESTDIR"} . "\\" . $project{"TARGETLIB"};
	$project{"TARGETLIB"} =~ s/\\+/\\/g;
    }
    %all_files = ();
    @files = split(/\s+/,$project{"HEADERS"});
    foreach ( @files ) { $all_files{$_} = "h" };
    @files = split(/\s+/,$project{"SOURCES"});
    foreach ( @files ) { $all_files{$_} = "s" };
    if ( $moc_aware ) {
        @files = split(/\s+/,$project{"_HDRMOC"});
	foreach ( @files ) { $all_files{$_} = "m"; }
	@files = split(/\s+/,$project{"_SRCMOC"});
	foreach ( @files ) { $all_files{$_} = "i"; }
    }
    %file_names = ();
    foreach $f ( %all_files ) {
	$n = $f;
	$n =~ s/^.*\\//;
	$file_names{$n} = $f;
	$file_path{$n}  = ".\\" . $f;
	$file_path2{$n} = (($f =~ /^\./) ? "" : ".\\") . $f;
    }
#$}
# Microsoft Developer Studio Project File - #$ Substitute('Name="$$TARGET" - Package Owner=<4>');
# Microsoft Developer Studio Generated Build File, Format Version 5.00
# ** DO NOT EDIT **

# TARGTYPE #$ Substitute('"$$VC_PROJ_TYPE" $$VC_PROJ_CODE');

CFG=#$ Substitute('$$TARGET - Win32 Debug');
!MESSAGE This is not a valid makefile. To build this project using NMAKE,
!MESSAGE use the Export Makefile command and run
!MESSAGE 
!MESSAGE NMAKE /f "#$ ExpandGlue('MAKEFILE','','','".');
!MESSAGE 
!MESSAGE You can specify a configuration when running NMAKE
!MESSAGE by defining the macro CFG on the command line. For example:
!MESSAGE 
!MESSAGE NMAKE /f #$ Substitute('"$$MAKEFILE" CFG="$$TARGET - Win32 Debug"');
!MESSAGE 
!MESSAGE Possible choices for configuration are:
!MESSAGE 
!MESSAGE #$ Substitute('"$$TARGET - Win32 Release" (based on "$$VC_PROJ_TYPE")');
!MESSAGE #$ Substitute('"$$TARGET - Win32 Debug" (based on "$$VC_PROJ_TYPE")');
!MESSAGE 

# Begin Project
# PROP Scc_ProjName ""
# PROP Scc_LocalPath ""
CPP=cl.exe

!IF  "$(CFG)" == #$ Substitute('"$$TARGET - Win32 Release"');

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 0
# PROP BASE Output_Dir "Release"
# PROP BASE Intermediate_Dir "Release"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 0
# PROP Output_Dir "Release"
# PROP Intermediate_Dir "Release"
# PROP Target_Dir ""
# ADD BASE CPP #$ Expand("VC_BASE_CPP_RELEASE");
# ADD CPP #$ Expand("VC_CPP_RELEASE");
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LIB32=link.exe -lib
# ADD BASE LIB32 /nologo
# ADD LIB32 /nologo #$ Project("TARGETLIB") && Substitute('/out:"$$TARGETLIB"');

!ELSEIF  "$(CFG)" == #$ Substitute('"$$TARGET - Win32 Debug"');

# PROP BASE Use_MFC 0
# PROP BASE Use_Debug_Libraries 1
# PROP BASE Output_Dir "Debug"
# PROP BASE Intermediate_Dir "Debug"
# PROP BASE Target_Dir ""
# PROP Use_MFC 0
# PROP Use_Debug_Libraries 1
# PROP Output_Dir "Debug"
# PROP Intermediate_Dir "Debug"
# PROP Target_Dir ""
# ADD BASE CPP #$ Expand("VC_BASE_CPP_DEBUG");
# ADD CPP #$ Expand("VC_CPP_DEBUG");
BSC32=bscmake.exe
# ADD BASE BSC32 /nologo
# ADD BSC32 /nologo
LIB32=link.exe -lib
# ADD BASE LIB32 /nologo
# ADD LIB32 /nologo #$ Project("TARGETLIB") && Substitute('/out:"$$TARGETLIB"');

!ENDIF 

# Begin Target

# Name #$Substitute('"$$TARGET - Win32 Release"');
# Name #$Substitute('"$$TARGET - Win32 Debug"');
#${
    foreach $n ( sort keys %file_names ) {
	$f  = $file_names{$n};
	$p  = $file_path{$n};
	$p2 = $file_path2{$n};
	$t  = $all_files{$f};
	if ( ($t eq "h") && $moc_output{$f} ) {
	    my($build);
	    $build = "\n\n# Begin Custom Build - Running moc...\nInputPath=" . $p2 . "\n\n"
		   . '"' . $moc_output{$f} . '" : $(SOURCE) "$(INTDIR)" "$(OUTDIR)"'
		   . "\n\tmoc $p2 -o " . $moc_output{$f} . "\n\n"
		   . "# End Custom Build\n\n";
	    $text .= ("# Begin Source File\n\nSOURCE=$p\n\n"
		   . '!IF  "$(CFG)" == "' . $project{"TARGET"} . ' - Win32 Release"'
		   . $build);
	    $text .= ('!ELSEIF  "$(CFG)" == "' . $project{"TARGET"} . ' - Win32 Debug"'
		   . $build
		   . "!ENDIF \n\n# End Source File\n");
	} elsif ( $t eq "i" ) {
	    my($build,$dn);
	    $build = "\n\n# Begin Custom Build - Running moc...\nInputPath=" . $p2 . "\n\n"
		   . '"' . $f . '" : $(SOURCE) "$(INTDIR)" "$(OUTDIR)"'
		   . "\n\tmoc ". $moc_input{$f} . " -o $f\n\n"
		   . "# End Custom Build\n\n";
	    $dn = $n;
	    $dn =~ s/\..*//;
	    $dn =~ tr/a-z/A-Z/;
	    $text .= ("# Begin Source File\n\nSOURCE=$p\n"
		   . "USERDEP__$dn=" . '"' . $moc_input{$f} . '"' . "\n\n"
		   . '!IF  "$(CFG)" == "' . $project{"TARGET"} . ' - Win32 Release"'
		   . $build);
	    $text .= ('!ELSEIF  "$(CFG)" == "' . $project{"TARGET"} . ' - Win32 Debug"'
		   . $build
		   . "!ENDIF \n\n# End Source File\n");
	} elsif ( $t eq "s" || $t eq "m" || $t eq "h" ) {
	    $text .= "# Begin Source File\n\nSOURCE=$p\n# End Source File\n";
	}
    }
    chop $text;
#$}
# End Target
# End Project
