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
class MapEntry(object):
    "Encapsulates a ditamap entry and allows them to be compared"
    def __init__(self, tag, href=None, navtitle=None, children=[]):
        self.tag = tag
        self.href = href
        self.navtitle = navtitle
        self.children = children
        
    def __eq__(self, other):
        if (other is None or not getattr(other, 'href') 
                          or not getattr(other, 'navtitle')
                          or not getattr(other, 'tag')):
            return False
        return (
                self.tag == other.tag and 
                self.href == other.href and
                self.navtitle == other.navtitle
        )
    
    def __hash__(self):
        return hash((self.tag, self.href, self.navtitle))
    
    
################################################################
# Unit test code
################################################################
import unittest


class TestMapEntry(unittest.TestCase):
    def test_i_correctly_handle_possible_erros_when_comparing(self):
        map_a = MapEntry("a", "www.nokia.com", "Nokia")
        self.assertFalse(map_a == None)
        self.assertFalse(map_a == MapEntry("a", "www.nokia.com"))

    def test_i_correctly_compare_equal_map_entry_items(self):
        map_a = MapEntry("a", "www.nokia.com", "Nokia")
        map_b = MapEntry("a", "www.nokia.com", "Nokia")
        self.assertTrue(map_a == map_b)
        
    def test_i_correctly_compare_unequal_map_entry_items(self):
        map_a = MapEntry("a", "www.nokia.com", "Nokia")
        map_b = MapEntry("a", "www.symbian.com", "Nokia")
        self.assertFalse(map_a == map_b)
