#!/www/python/bin/python

#
# Test script for the XML Schema datatypes
#

__revision__ = "$Id: test_xsd.py,v 1.1 2002/02/15 02:54:21 akuchling Exp $"

from mx import DateTime
from datatypes.errors import DatatypeValueError
from datatypes import get_xsd_library

from sancho.unittest import TestScenario, parse_args, run_scenarios

tested_modules = ["datatypes.xsd"]

class XSDTest (TestScenario):

    def setup (self):
        self.xsd = get_xsd_library()

    def shutdown (self):
        del self.xsd

    def check_string (self):
        "String data type: 2"
        self.test_val('self.xsd.evaluate("string", value="")', "")
        self.test_val('self.xsd.evaluate("string", value="string")', "string")
        
    def check_boolean (self):
        "Boolean type: 5"
        self.test_bool('self.xsd.evaluate("boolean", value="1")', )
        self.test_bool('self.xsd.evaluate("boolean", value="true")', )
        self.test_bool('self.xsd.evaluate("boolean", value="0")',
                       want_true=0)
        self.test_bool('self.xsd.evaluate("boolean", value="false")',
                       want_true=0)
        self.test_exc('self.xsd.evaluate("boolean", value="dummy")',
                       DatatypeValueError)

    def check_decimal (self):
        "Decimal type: 5"
        self.test_val('self.xsd.evaluate("decimal", value="1.2")',
                      1.2)
        self.test_val('self.xsd.evaluate("decimal", value="+1.2")',
                      1.2)
        self.test_val('self.xsd.evaluate("decimal", value="-1.2")',
                      -1.2)
        self.test_val('self.xsd.evaluate("decimal", value="-2")',
                      -2)
        self.test_val('self.xsd.evaluate("decimal", value=".2")',
                      .2)
        
    def check_float (self):
        "Float type: 4"
        self.test_val('self.xsd.evaluate("float", value="1.2")',
                      1.2)
        self.test_val('self.xsd.evaluate("float", value="-1.2")',
                      -1.2)
        self.test_val('self.xsd.evaluate("float", value="1.2e1")',
                      12)
        self.test_val('self.xsd.evaluate("float", value="-352.5e-1")',
                      -35.25)
#        self.test_val('self.xsd.evaluate("float", value="INF")',
#                      -35.25)
#        self.test_val('self.xsd.evaluate("float", value="-INF")',
#                      -35.25)
#        self.test_val('self.xsd.evaluate("float", value="NaN")',
#                      -35.25)

    def check_double (self):
        "Double type: 1"
        self.test_val('self.xsd.evaluate("double", value="1.2")',
                      1.2)

    def check_duration (self):
        "Duration type: 2"
        # RelativeDateTime doesn't seem to support __cmp__
        self.test_stmt('self.xsd.evaluate("duration", value="P1Y2M3DT10H30M5S")')
#                      DateTime.RelativeDateTime(1,2,3, 10, 30, 5) 
        self.test_stmt('self.xsd.evaluate("duration", value="-P1Y2M3DT10H30M5S")')
        
# class XSDTest


if __name__ == "__main__":
    (scenarios, options) = parse_args()
    run_scenarios(scenarios, options)
