"""datatypes.xsd

Contains an implementation of the primitive datatypes specified
by the XML Schema (or XSD) recommendation.
"""

# created 2002/02/14, AMK (kiss kiss)

__revision__ = "$Id: xsd.py,v 1.1 2002/02/15 02:54:21 akuchling Exp $"

from mx import DateTime
from datatypes.errors import DatatypeValueError
from datatypes import interfaces

import re
decimal_re = '([-+]?)(\d+)?(\.\d+)?$'
decimal_pat = re.compile(decimal_re)
float_re = """(?x)
(?:  ([-+]?)
     ((\d+)?(\.\d+)?)
     ([Ee] [-+]?\d+)?)
| 0 | -0 | INF | -INF | NaN     
$
"""
float_pat = re.compile(float_re)
duration_pat = re.compile("""(?x)([-+])?P(\d+)Y(\d+) M(\d+)DT(\d+)H 
(\d+)M(\d+(?:.\d+)?)S$
""")

class XSDLibrary (interfaces.DatatypeLibraryInterface):
    uri = 'http://www.w3.org/2001/XMLSchema-datatypes'
    
    def evaluate(self, type, params={}, value=""):
        """evaluate(type:string,
                    params: {string : string},
                    value : string) : any

        Evaluate the string 'value' as a value of the datatype
        selected by the name 'type', taking the additional parameters
        'params' into account.  Raises DatatypeValueError with an
        explanatory message if the value is illegal.
        """
        method = self._get_method(type)
        return method(params, value)

    def _get_method (self, type):
        try:
            method = getattr(self, 'eval_'+type)
        except AttributeError:
            return None
        else:
            return method


    def has_type (self, type):
        """has_type(type:string) : boolean
        Returns true if the library supports a type with the given name.
        """
        method = self._get_method(type)
        return (method is not None)

    
    def is_type_legal (self, type, params):
        """is_type_legal(type:string, params:{string:string}) : boolean
        Returns true if the type and corresponding parameters are legal.
        """
        method = self._get_method(type)
        if method is None: return 0
        try:
            method(type, None)
        except DatatypeValueError:
            return 0
        else:
            return 1
        

    # Methods for each datatype

    def eval_string (self, params, value):
        return value

    def eval_boolean (self, params, value):
        if value == '1' or value == 'true':
            return 1
        elif value == '0' or value == 'false':
            return 0
        else:
            raise DatatypeValueError("Illegal literal for boolean type: %r"
                                     % value)
        
    def eval_decimal (self, params, value):
        m = decimal_pat.match(value)
        if m is None:
            raise DatatypeValueError("Illegal literal for decimal type: %r"
                                     % value)
        
        sign, integer, fraction = m.group(1,2,3)
        if integer is None and fraction is None:
            raise DatatypeValueError("Illegal literal for decimal type: %r"
                                     % value)

        value = 0.0
        if integer is not None:  value += float(integer)
        if fraction is not None: value += float(fraction)
        if sign == '-': value = -value
        return value

    def eval_float (self, params, value):
        m = float_pat.match(value)
        if m is None:
            raise DatatypeValueError("Illegal literal for float type: %r"
                                     % value)
        sign, mantissa, exponent = m.group(1, 2, 5)
        value = float(mantissa)
        if exponent is not None:
            exponent = int(exponent[1:])
            value *= pow(10.0, exponent)
        if sign == '-': value = -value
        return value

    eval_double = eval_float

    def eval_duration (self, params, value):
        m = duration_pat.match(value)
        if m is None:
            raise DatatypeValueError("Illegal literal for duration type: %r"
                                     % value)
        t = map(float, m.group(2,3,4,5,6,7))
        sign = m.group(1)

        duration = apply(DateTime.RelativeDateTime, t)
        if sign == '-':
            duration = DateTime.RelativeDateTime() - duration
        return duration
    
        
    

