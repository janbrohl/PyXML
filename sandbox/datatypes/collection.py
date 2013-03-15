
from datatypes.errors import DatatypeValueError, DatatypeURIError
from datatypes.interfaces import DatatypeLibCollectionInterface

class DatatypeLibCollection (DatatypeLibCollectionInterface):

    def __init__ (self):
        self._libs = {}

        
    def register (self, library):
        """register(library : DatatypeLibrary)
        Add 'library' to the list of libraries available in this collection.
        """
        if self._libs.has_key(library.uri):
            raise ValueError, \
                  "Library with URI %r already in collection" % library.uri

        self._libs[library.uri] = library


    def has_uri (self, uri):
        """has_uri(uri:string) : boolean
        Returns true if there's a datatype library registered for the given
        URI.
        """
        return self._libs.has_key(uri)

    
    def has_type (self, (uri,type)):
        """has_type(type:string) : boolean
        Returns true if the library supports a type with the given name.
        """
        if not self._libs.has_key(uri): return 0
        lib = self._libs[uri]
        return lib.has_type(type)

        
    def is_type_legal (self, (uri,type), params):
        """is_type_legal((uri:string,type:string),
                          params:{string:string}) : boolean
        Returns true if the type and corresponding parameters are legal.
        """
        if not self._libs.has_key(uri): return 0
        lib = self._libs[uri]
        return lib.is_type_legal(type, params)

        
    def evaluate (self, (uri,type), params, value):
        """evaluate((uri:string,type:string),
                    params: {string : string},
                    value : string) : any

        Evaluate the string 'value' as a value of the datatype
        selected by the (uri,type) pair, taking the additional
        parameters 'params' into account.  Raises DatatypeValueError
        if the value is illegal; raises DatatypeURIError if there's
        no library registered for that URI.
        """        
        if not self._libs.has_key(uri):
            raise DatatypeURIError, "No library for URI %r" % uri

        lib = self._libs[uri]
        return lib.evaluate(type, params, value)

        
