"""
A unit test module for xmlproc.
"""

import unittest

from xml.parsers.xmlproc import xmldtd

# ============================================================================
#   xmldtd
# ============================================================================

# --- ExternalEntity

class ExternalEntityTestCase(unittest.TestCase):

    def setUp(self):
        self.entity = xmldtd.ExternalEntity("entity", "pubid", "sysid", "not")
    
    def check_is_parsed(self):
        assert not self.entity.is_parsed()

        entity = xmldtd.ExternalEntity("entity", "pubid", "sysid", "")
        assert not entity.is_parsed()

        entity = xmldtd.ExternalEntity("entity", "pubid", "sysid", None)
        assert entity.is_parsed()
        
    def check_is_internal(self):
        assert not self.entity.is_internal()

    def check_get_pubid(self):
        assert self.entity.get_pubid() == "pubid"

    def check_get_sysid(self):
        assert self.entity.get_sysid() == "sysid"

    def check_get_notation(self):
        assert self.entity.get_notation() == "not"

    def check_get_name(self):
        assert self.entity.get_name() == "entity"

# --- InternalEntity

class InternalEntityTestCase(unittest.TestCase):

    def setUp(self):
        self.entity = xmldtd.InternalEntity("name", "value")
    
    def check_is_internal(self):
        assert self.entity.is_internal()
        
    def check_get_value(self):
        assert self.entity.get_value() == "value"

    def check_get_name(self):
        assert self.entity.get_name() == "name"

# --- Attribute

# ???
        
# ============================================================================
#   Testing
# ============================================================================

suite = unittest.TestSuite()
suite.addTests(unittest.makeSuite(ExternalEntityTestCase, 'check')._tests)
suite.addTests(unittest.makeSuite(InternalEntityTestCase, 'check')._tests)

runner = unittest.TextTestRunner()
runner.run(suite)

