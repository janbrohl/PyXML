#!/www/python/bin/python

#
# Test script for the DatatypeLibCollection class.
#

__revision__ = "$Id: test_collection.py,v 1.1 2002/02/15 02:54:21 akuchling Exp $"

from datatypes import get_standard_collection, get_xsd_library
from datatypes import interfaces

from sancho.unittest import TestScenario, parse_args, run_scenarios

tested_modules = ["datatypes.collection"]

XSD_URI = "http://www.w3.org/2001/XMLSchema-datatypes"

class TestLib(interfaces.DatatypeLibraryInterface):
    uri = "http://www.amk.ca/datatypes"
    
class CollectionTest (TestScenario):

    def setup (self):
        self.coll = get_standard_collection()

    def shutdown (self):
        del self.coll

    def check_initial (self):
        "Check initial state of collection: 2"
        self.test_bool('self.coll.has_uri(XSD_URI)')
        self.test_bool('self.coll.has_type((XSD_URI, "string"))')
        
    def check_register (self):
        "Check registration of additional libraries: 5"
        self.test_exc('self.coll.register(get_xsd_library())',
                      ValueError)
        t = TestLib()
        self.test_bool('self.coll.has_uri(t.uri)', want_true=0)
        self.test_stmt('self.coll.register(t)')
        self.test_bool('self.coll.has_uri(t.uri)')
        self.test_exc('self.coll.register(t)', ValueError)

    def check_type (self):
        "Check various type-related methods: 6"
        self.test_bool('self.coll.has_uri(XSD_URI)')
        self.test_bool('self.coll.has_uri(XSD_URI + "abc")', want_true=0)
        self.test_bool('self.coll.has_type((XSD_URI, "string"))')
        self.test_bool('self.coll.has_type((XSD_URI, "dummy_type"))',
                       want_true=0)
        self.test_bool('self.coll.is_type_legal((XSD_URI, "string"), {})')
        self.test_bool('self.coll.is_type_legal((XSD_URI, "dummy_type"), {})',
                       want_true=0)
        
# class CollectionTest


if __name__ == "__main__":
    (scenarios, options) = parse_args()
    run_scenarios(scenarios, options)
