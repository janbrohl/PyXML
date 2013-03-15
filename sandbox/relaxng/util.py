"""util

Utility functions for parsing out of a DOMstream.
"""

__revision__ = "$Id: util.py,v 1.24 2002/07/19 13:36:30 akuchling Exp $"

import string, sys, urlparse

from xml.ns import RNG
from xml.dom import pulldom

DATATYPE_LIBS = ['http://www.w3.org/2001/XMLSchema-datatypes', '']

def check_uri (uri):
    if uri == "":
        return

    scheme, netloc, path, params, query, fragment = urlparse.urlparse(uri)
    if scheme == "":
        raise RuntimeError, ("No URI scheme supplied, or "
                             "illegal character in URI scheme")
    
    if fragment != "" or uri.endswith('#'):
        raise RuntimeError, "Fragment not allowed in datatypeLibrary URI"
    # XXX is this the correct test, or should it be
    # 'scheme in ["http", "ftp"...]'
    if '_' in scheme:
        raise RuntimeError, "Unknown scheme %r in datatypeLibrary URI" % scheme

    return None

    
def combine_deflist (name, L):
    """combine_deflist (name:string, L:[Pattern]) -> Pattern
    """
    from fullparser import make_interleave, make_choice
    # 4.17: combine definitions with the same name
    assert len(L) != 0, "empty list of 'define' patterns"
    children = []
    empty_combine_seen = 0
    combine = ""
    for c2, pattern in L:
        children.append(pattern)
        if c2 == "":
            if empty_combine_seen:
                raise RuntimeError, ("Multiple <define> elements "
                                     "with empty combine attribute")
            else:
                empty_combine_seen = 1
                continue
        elif combine == "":
            combine = c2
        elif c2 != combine:
            raise RuntimeError, ("Different values of 'combine' attribute "
                                 "for %r definition" % name)

    if combine == 'choice' or (combine == "" and len(L)==1):
        return make_choice(children)
    elif combine == 'interleave':
        return make_interleave(children)
    else:
        raise RuntimeError, "Illegal value of 'combine' attribute: %r" % combine
    

class Grammar:
    def __init__ (self):
        self.defines = {}
        self._start_syms = []
        self._refs = {}
        self.grammar = None
        self.start_symbol = None
        
    def dump (self, depth=0):
        sys.stdout.write(repr(self)+'\n')
        sys.stdout.write((depth+2)*' ' + repr(self.defines) + '\n')
        sys.stdout.write((depth+2)*' ' + repr(self._start_syms) + '\n')


    def add_define (self, name, combine, pattern):
        L = self.defines.get(name, None)
        if L is None: L = self.defines[name] = []
        L.append( (combine, pattern) )
        
    def add_start_sym (self, combine, pattern):
        self._start_syms.append((combine, pattern))

    def get_ref (self, ref_name):
        try:
            return self._refs[ref_name]
        except KeyError:
            from fullparser import Ref
            ref = Ref(ref_name=ref_name, grammar=self,
                      p1=None, depth=-1)
            self._refs[ref_name] = ref
            return ref

    def get_definition (self, name):
        if not self.defines.has_key(name):
            raise RuntimeError, "No definition named %r in grammar" % name

        deflist = self.defines[name]
        return combine_deflist(name, deflist)


    def check_all_refs (self):
        for ref in self._refs.values():
            if ref.p1 is None:
                raise RuntimeError, 'Undefined reference: %r' % ref.ref_name
            
    def combine (self):
        for name, deflist in self.defines.items():
            # Unreferenced definition
            if not self._refs.has_key(name):
                continue
            ref = self._refs[name]
            result = combine_deflist(name, deflist)
            ref.p1 = result
            
        if len(self._start_syms) == 0:
            raise RuntimeError, "Grammar without starting symbol"
        
        self.start_symbol = combine_deflist('start', self._start_syms)

    def expand (self):
        pass

    def check_recursion_depth (self):
        pass

class DOMTokenStream:
    def __init__ (self, stream):
        self.stream = stream
        self.parents = []
        self.root_grammar = Grammar()
        self.grammars = [self.root_grammar]
        self.grammar_stack = [self.root_grammar]
        self._legal_attributes = {}
        
    def get_prefix_map (self):
        # XXX unwarranted assumptions about DOMStream implementation
        d = {}
        for dict in self.stream.pulldom._ns_contexts:
            for uri, prefix in dict.items():
                d[prefix] = uri
        return d
    
    def push_grammar (self):
        g = Grammar()
        g.grammar = self.get_grammar()
        self.grammar_stack.insert(0, g)
        self.grammars.append(g)
        

    def pop_grammar (self):
        return self.grammar_stack.pop(0)

    def get_grammar (self):
        return self.grammar_stack[0]
    
    def find_ancestor_attribute (self, ns, attr):
        """find_ancestor_attribute(attr:string) : string
        Find the nearest ancestor element with the attribute 'attr',
        and return either its value or the empty string "".
        """

        for node in self.parents:
            if node.hasAttributeNS(ns, attr):
                return node.getAttributeNS(ns, attr)
        return ""
        
    def next (self):
        # Get an event, ignoring elements and attributes not in the RNG
        # namespace 
        while 1:
            event, node = self.stream.next()
            if event == pulldom.START_ELEMENT:
                # 4.1: drop foreign elements
                if node.namespaceURI != RNG.BASE:
	            # We need to drop the element's content, too, so
		    # the node is expanded before continuing.
                    self.stream.expandNode(node)
                    continue
                else:
                    # 4.1: Drop foreign attributes, and ensure 
                    # .namespaceURI is always set to RNG.BASE.
                    legal_attrs = self._legal_attributes.get(node.localName,
                                                             None)
                    if legal_attrs is None:
                        raise RuntimeError, 'Illegal element name: %r' % node.localName
                    for attr in node.attributes.values():
                        name = attr.name
                        is_namespacedecl = (name == 'xmlns' or
                                            name.startswith('xmlns:')
                                            or name.startswith('xml:'))

                        # XXX should check value of default namespace here!
                        if (not is_namespacedecl and 
                            attr.namespaceURI is not None and
                            attr.namespaceURI != RNG.BASE):  
                            node.removeAttributeNode(attr)
                            continue
                        
                        if not (name in legal_attrs or
                                is_namespacedecl):
                            raise RuntimeError, ("Attribute %r not legal "
                                                 "on element %r" %
                                                 (name, node.localName))

                        if not is_namespacedecl:
                            node.removeAttributeNode(attr)
                            attr.namespaceURI = RNG.BASE
                            node.setAttributeNode(attr)

                        # 4.2: Trim whitespace
                        attr.nodeValue = string.strip(attr.nodeValue)

                        if name == 'datatypeLibrary':
                            check_uri(attr.nodeValue)
                            
            elif event == pulldom.END_ELEMENT:
                if node.namespaceURI != RNG.BASE: continue

            break
        
        # Maintain the parent stack
        if event == pulldom.START_ELEMENT:
            self.parents.insert(0, node)
        elif event == pulldom.END_ELEMENT:
            self.parents.pop(0)
            
        return event, node

    def __iter__ (self):
        return self
    
    def get_next_event (self, chars=0):
        while 1:
            event, node = self.next()
            if event == pulldom.IGNORABLE_WHITESPACE:
                continue
            elif event == pulldom.CHARACTERS:
                # Ignore pure whitespace
                if node.nodeValue.strip() == "":
                    continue
                elif chars:
                    return event, node
                else:
                    raise RuntimeError, "Unexpected characters: %r" % node.nodeValue
            else:
                return event, node


    def accumulate_string (self):
        S = ""
        while 1:
            event, node = self.next()
            if event in [pulldom.IGNORABLE_WHITESPACE, pulldom.CHARACTERS]:
                S += node.nodeValue
            else:
                return S, event, node

    def expect_element (self, elem_name):
        """expect_element(elem_name) -> None
        Retrieves the next significant event from the stream,
        expecting it to be the start of an 'elem_name' element.
        Raises an exception if a different event is found instead.
        """
        while 1:
            event, node = self.get_next_event()
            if event == pulldom.START_ELEMENT:
                if node.localName == elem_name:
                    return 
                else:
                    raise RuntimeError, 'Unexpected element start: %r' % node.tagName
            else:
                raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)


    def expect_end_element (self, elem_name):
        """expect_end_element(elem_name) -> None
        Retrieves the next significant event from the stream,
        expecting it to be the end of an 'elem_name' element.
        Raises an exception if a different event is found instead.
        """
        while 1:
            event, node = self.get_next_event()
            if event == pulldom.END_ELEMENT:
                if node.localName == elem_name:
                    return 1
                else:
                    raise RuntimeError, 'Unexpected element end: %r' % node.tagName
            else:
                raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)

    def set_legal_attributes (self, dict):
        self._legal_attributes = dict


from xml.sax import saxlib

TEXT_NODE = 'text'
ELEMENT_NODE = 'element'
ATTRIBUTE_NODE = 'attribute'

class ChildNode:
    """Represents a bit of an XML stream"""

class ElementNode (ChildNode):
    type = ELEMENT_NODE
    def __init__ (self, qname, context, attrs=None):
        if attrs is None:
            attrs = []

        self.qname = qname
        self.context = context
        self.attrs = attrs
        self.children = []
        

class TextNode:
    type = TEXT_NODE

    def __init__ (self, value=""):
        self.value = value

class AttributeNode:
    type = ATTRIBUTE_NODE

    def __init__ (self, qname, value):
        self.qname = qname
        self.value = value


class RNGEventStream (saxlib.ContentHandler):
    def __init__ (self):
        saxlib.ContentHandler.__init__(self)
        self.stream = []
        self.stack = []

    def startElementNS (self, name, qname, attrs):
        L = []
        for qn, value in attrs.items():
            L.append(AttributeNode(qn, value))

        elem = ElementNode(name, None, L)
        self.stream.append(elem)
        if len(self.stack):
            self.stack[-1].children.append(elem)
        self.stack.append(elem)
                     
    def endElementNS (self, name, qname):
        self.stack.pop()

    def characters (self, content):
        children = self.stack[-1].children
        if len(children) and isinstance(children[-1], TextNode):
            # Append text to previous text node
            children[-1].value += content
        else:
            text =  TextNode(content)
            self.stack[-1].children.append(text)
            self.stream.append(text)

def get_rng_document (stream):
    import sys
    from xml import sax

    h = RNGEventStream()
    parser = sax.make_parser()
    parser.setFeature(saxlib.feature_namespaces, 1)
    parser.setContentHandler(h)
    parser.setErrorHandler(saxlib.ErrorHandler())
    parser.parse(stream)
    return h.stream[0]

if __name__ == '__main__':
    import sys
    from xml import sax

    d = get_rng_document(sys.stdin)
    print d
    
