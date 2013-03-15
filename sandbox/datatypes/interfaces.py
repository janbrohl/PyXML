#
# Datatype interfaces
#

class DatatypeLibCollectionInterface:
    """
    Holds a collection of a bunch of datatype libraries.
    """
    
    def register (self, library):
        """register(library : DatatypeLibrary)
        Add 'library' to the list of libraries available in this collection.
        """

    def has_uri (self, uri):
        """has_uri(uri:string) : boolean
        Returns true if there's a datatype library registered for the given
        URI.
        """

    def has_type (self, (uri, type)):
        """has_type((uri:string,type:string)) : boolean
        Returns true if the specified datatype exists.
        """
        
    def is_type_legal (self, (uri,type), params):
        """is_type_legal(type:string, params:{string:string}) : boolean
        Returns true if the type and corresponding parameters are legal.
        """

    def check (self, (uri,type), params, value):
        """check((uri:string,type:string),
                 params: {string : string},
                 value : string) : boolean
        Returns true if the string 'value' represents a legal
        value for the datatype selected by the (uri,type) pair,
        taking the additional parameters 'params' into account.
        If this method returns false, it might mean either
        that the uri isn't for any registered library, or
        that the library is OK and the value is wrong.
        XXX should this return an explanatory message, or should
        there be a third function (explain()?)
        """

        try:
            value = self.evaluate((uri,type), params, value)
        except (DatatypeValueError, DatatypeURIError):
            return 0
        else:
            return 1
            

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


class DatatypeLibraryInterface:
    """
    Instance attributes:
      uri : string
        Namespace URI for this collection of data types
    """

    def evaluate(self, type, params, value):
        """evaluate(type:string,
                    params: {string : string},
                    value : string) : any

        Evaluate the string 'value' as a value of the datatype
        selected by the name 'type', taking the additional parameters
        'params' into account.  Raises DatatypeValueError with an
        explanatory message if the value is illegal.
        """

    def has_type (self, (uri,type)):
        """has_type(type:string) : boolean
        Returns true if the library supports a type with the given name.
        """

    def is_type_legal (self, type, params):
        """is_type_legal(type:string, params:{string:string}) : boolean
        Returns true if the type and corresponding parameters are legal.
        """
    
        
