# Copyright (c) 2008-2010 Nokia Corporation and/or its subsidiary(-ies).
# All rights reserved.
# This component and the accompanying materials are made available
# under the terms of the License "Eclipse Public License v1.0"
# which accompanies this distribution, and is available
# at the URL "http://www.eclipse.org/legal/epl-v10.html".
#
# Initial Contributors:
# Nokia Corporation - initial contribution.
#
# Contributors:
#
"""
Stubs shared across tests in different modules
"""
from orb.sysdef import Component, Collection, Package, Layer
from mapentry import MapEntry


class StubSysdef(object):    
    def __init__(self):
        self.name = "Symbian^3"
        kernelhwsrv_comps = [
            Component(id="ubootldr", name="Boot Loader", bldinfs=[]),
            Component(id="asspandvariant", name="Template ASSP and Variant", bldinfs=[]),
            Component(id="eka", name="Kernel Architecture", bldinfs=[])
        ]
        kernelhwsrv_colls = [
            Collection(id="brdbootldr", name="Board Boot Loader", components=kernelhwsrv_comps),
            Collection(id="dummy", name="Dummy", components=[])
        ]
        os_packages = [
            Package(id="kernelhwsrv", name="Kernel and Hardware Services", collections=kernelhwsrv_colls)
        ]
        mw_packages = [
            Package(id="classicui", name="Classic UI", collections=[])
        ]
        self.layers = [
            Layer(id="os", name="OS", packages=os_packages), 
            Layer(id="mw", name="Middleware", packages=mw_packages)
        ]
    
    def get_packages(self):
        return (
            Package(id="graphics", name="Graphics", 
                    components=(Component("classicui_pub","Classic UI Public Interfaces",["W:/sf/mw/classicui/classicui_pub/group/bld.inf"]),
                                Component("classicui_plat","Classic UI Platform Interfaces",["W:/sf/mw/classicui/classicui_plat/group/bld.inf"]) 
                                )
            ),
            Package(id="classicui", name="Classic UI", 
                    components=(Component("aknglobalui","Avkon Global UI",["W:/sf/mw/classicui/uifw/aknglobalui/group/bld.inf"]),
                                Component("commonui","Common UI",["W:/sf/mw/classicui/commonuis/commonui/group/bld.inf"])
                                )
            )
        )
    
    def get_components(self, package_id):
        component_classicui_pub = Component("classicui_pub","Classic UI Public Interfaces",["W:/sf/mw/classicui/classicui_pub/group/bld.inf"])
        component_classicui_plat = Component("classicui_plat","Classic UI Platform Interfaces",["W:/sf/mw/classicui/classicui_plat/group/bld.inf"])        
        component_aknglobalui = Component("aknglobalui","Avkon Global UI",["W:/sf/mw/classicui/uifw/aknglobalui/group/bld.inf"])
        component_commonui = Component("commonui","Common UI",["W:/sf/mw/classicui/commonuis/commonui/group/bld.inf"])
        
        if package_id == "classicui":
            return [component_classicui_pub, component_classicui_plat, component_aknglobalui, component_commonui]
        if package_id == "graphics":
            return ["commongraphicsheaders"]
        
    def get_sbs_output_dir(self, component_id):
        if component_id == "classicui_pub":   
            return "classicui_pub"
        elif component_id == "classicui_plat": 
            return "classicui_plat"
        elif component_id == "commongraphicsheaders":   
            return "commongraphicsheaders"
        elif component_id == "aknglobalui":
            return "aknglobalui"
        elif component_id == "commonui":
            return "commonui" 
        else:
            raise Exception("component id '%s' is not defined in stub"%component_id)

    def get_bldinfs(self, component_id):
        return ["W:/sf/mw/classicui/classicui_pub/group/bld.inf"]


class StubBldInfExportsMap(object):
    set1 = set([('W:/epoc32/include/platform/graphics/displayconfiguration.h','W:/sf/os/graphics/graphicsutils/commongraphicsheaders/inc/displayconfiguration.h'),
                       ('W:/epoc32/include/platform/graphics/extensioncontainer.h','W:/sf/os/graphics/graphicsutils/commongraphicsheaders/inc/extensioncontainer.h'),
                       ('W:/epoc32/include/mw/foo/not_in_a_this_component.h','W:/sf/mw/foo/not_in_a_this_component.h')])
    set_pub = set([("W:/epoc32/include/mw/aknSoundinfo.h", "W:/sf/mw/classicui/classicui_pub/sounds_api/inc/aknSoundInfo.h"),
                      ("W:/epoc32/include/mw/AiwServiceHandler.h", "W:/sf/mw/classicui/classicui_pub/aiw_service_handler_api/inc/AiwServiceHandler.h"),
                      ('W:/epoc32/include/mw/bar/in_a_this_component.h','W:/sf/mw/bar/in_a_this_component.h')])
    set_plat = set([("W:/epoc32/include/platform/mw/mpslnfwappthemeobserver.h", "W:/sf/mw/classicui/classicui_plat/personalisation_framework_api/inc/MPslnFWAppThemeObserver.h"),
                       ("W:/epoc32/include/platform/mw/pslnfwappthemehandler.h", "W:/sf/mw/classicui/classicui_plat/personalisation_framework_api/inc/PslnFWAppThemeHandler.h")])                     
    set_internal = set([('W:/sf/os/graphics/displayconfiguration.h','W:/sf/os/graphics/displayconfiguration.h'),
                       ('W:/sf/os/graphics/extensioncontainer.h','W:/sf/os/graphics/extensioncontainer.h')])    
    set_all = set1.union(set_pub).union(set_plat).union(set_internal)
    
    def get_exports(self, bld_inf_path):
        if bld_inf_path == "W:/sf/os/graphics/graphicsutils/commongraphicsheaders/group/bld.inf":
            return self.set1
        elif bld_inf_path == "W:/sf/mw/classicui/classicui_pub/group/bld.inf":
            return self.set_pub    
        elif bld_inf_path == "W:/sf/mw/classicui/classicui_plat/group/bld.inf":
            return self.set_plat
        else: 
            return None    
            
    def is_public(self, header):
        if header in ["W:/epoc32/include/mw/aknSoundinfo.h", "W:/epoc32/include/mw/AiwServiceHandler.h", 
                        "W:/epoc32/include/mw/aknSoundinfo.h", "W:/epoc32/include/mw/foo/not_in_a_this_component.h",
                        "W:/epoc32/include/mw/bar/in_a_this_component.h"]:
            return True
        elif header in ["W:/epoc32/include/platform/mw/pslnfwappthemehandler.h", "W:/epoc32/include/platform/graphics/extensioncontainer.h", 
                        "W:/epoc32/include/platform/mw/mpslnfwappthemeobserver.h", "W:/sf/os/graphics/displayconfiguration.h"]:
            return False
        else:
            raise Exception("Header '%s' is not defined in is_public"%str(header))


class StubPackageLevelMapCreator(object):    
    def __init__(self, sysdef, build_dir):
        self.sysdef = sysdef
        self.build_dir = build_dir
    
    def get_package_level_map(self, package_id):
        if package_id.upper() == "inputmethods".upper():
            return [
                MapEntry("cxxStructRef", href="class_c_always_online_e_com_interface", navtitle="test_class_defined_in_src_path"),
                MapEntry("cxxClassRef", href="classicui_2.xml#test_class_defined_in_src_path", navtitle="test_class_defined_in_src_path")
            ]
        else:
            return [
                MapEntry("cxxStructRef", href="struct___array_util.xml#struct___array_util", navtitle="struct___array_util"),
                MapEntry("cxxClassRef", href="class_b_trace.xml#class_b_trace", navtitle="class_b_trace", children=[
                    MapEntry("cxxStructRef", href="struct_b_trace_1_1_s_exec_extension.xml#struct_b_trace_1_1_s_exec_extension", navtitle="struct_b_trace_1_1_s_exec_extension")
                ]),
                MapEntry("cxxClassRef", href="class_c_active.xml#class_c_active", navtitle="class_c_active"),
                MapEntry("cxxClassRef", href="class_c_active_scheduler.xml#class_c_active_scheduler", navtitle="class_c_active_scheduler", children=[
                    MapEntry("cxxClassRef", href="class_c_active_scheduler_1_1_t_cleanup_bundle.xml#class_c_active_scheduler_1_1_t_cleanup_bundle", navtitle="class_c_active_scheduler_1_1_t_cleanup_bundle")
                ]),
                MapEntry("cxxClassRef", href="class_c_active_scheduler_wait.xml#class_c_active_scheduler_wait", navtitle="class_c_active_scheduler_wait"),
                MapEntry("cxxClassRef", href="class_c_always_online_disk_space_observer.xml#class_c_always_online_disk_space_observer", navtitle="class_c_always_online_disk_space_observer"),
                MapEntry("cxxClassRef", href="class_c_always_online_e_com_interface.xml#class_c_always_online_e_com_interface", navtitle="class_c_always_online_e_com_interface", children=[
                    MapEntry("cxxStructRef", href="struct_c_always_online_e_com_interface_1_1___c_e_com_interface_init_params.xml#struct_c_always_online_e_com_interface_1_1___c_e_com_interface_init_params", navtitle="struct_c_always_online_e_com_interface_1_1___c_e_com_interface_init_params"),
                    MapEntry("cxxStructRef", href="nested_and_removed.xml"),
                ]),
                MapEntry("cxxClassRef", href="class_c_always_online_manager.xml#class_c_always_online_manager", navtitle="class_c_always_online_manager"),
                MapEntry("cxxClassRef", href="class_c_always_online_manager_server.xml#class_c_always_online_manager_server", navtitle="class_c_always_online_manager_server"),
                MapEntry("cxxClassRef", href="test_class_defined_in_src_path.xml#test_class_defined_in_src_path", navtitle="test_class_defined_in_src_path")                    
            ]