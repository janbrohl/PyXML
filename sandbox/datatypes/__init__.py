
from datatypes.errors import DatatypeValueError, DatatypeURIError
from datatypes.collection import DatatypeLibCollection
from datatypes.xsd import XSDLibrary

def get_xsd_library ():
    """get_xsd_library(): DatatypeLibrary
    Return the library for the XML Schema standard's primitive
    datatypes.
    """
    return XSDLibrary()

def get_standard_collection ():
    """get_standard_collection(): DatatypeLibCollection
    Return a collection containing just the library for the XML Schema 
    datatypes.
    """
    coll = DatatypeLibCollection()
    coll.register(get_xsd_library())
    return coll


