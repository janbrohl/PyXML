"""datatypes.errors

Contains the exception classes used by the datatype support.
"""

# created 2002/02/14, AMK (kiss kiss)

__revision__ = "$Id: errors.py,v 1.1 2002/02/15 02:54:21 akuchling Exp $"

class DatatypeValueError(Exception):
    """
    Exception raised when a supplied string does not represent
    a legal value for a datatype.
    
    Instance attributes:
      message : string
        Message explaining what's wrong with the string
    """

class DatatypeURIError(Exception):
    """
    Exception raised when there's no datatype library corresponding
    to a given URI.
    """


