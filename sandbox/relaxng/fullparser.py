"""fullparser

Parser for the RELAX NG full syntax, as described in section 3 and 4
of the RELAX NG specification.

XXX not currently thread-safe; globals will have to be moved into
an object for that.
XXX use an exception other than RuntimeError
"""

# created 2002/01/07, AMK

__revision__ = "$Id: fullparser.py,v 1.30 2002/07/19 13:31:24 akuchling Exp $"

import urlparse, urllib
from xml.ns import RNG
from xml.dom import pulldom
from xml.utils.characters import re_Name

import relaxng, parser
import util

def xlink_escape (uri):
    return uri

# This dictionary maps element names to a (possibly-empty) list of the legal
# attributes for that starting tag.

_legal_attributes = {
    'element': ['name', 'ns', 'datatypeLibrary'],
    'attribute': ['name', 'ns', 'datatypeLibrary'],
    'ref': ['name', 'ns', 'datatypeLibrary'],
    'parentRef': ['name', 'ns', 'datatypeLibrary'],
    'externalRef': ['href', 'ns', 'datatypeLibrary'],
    'value': ['type', 'ns', 'datatypeLibrary'],
    'data': ['type', 'ns', 'datatypeLibrary'],
    'param': ['name', 'ns', 'datatypeLibrary'],
    'include': ['href', 'ns', 'datatypeLibrary'],
    'start': ['combine', 'ns', 'datatypeLibrary'],
    'define': ['name', 'combine', 'ns', 'datatypeLibrary'],
    'group': ['ns', 'datatypeLibrary'],
    'interleave': ['ns', 'datatypeLibrary'],
    'choice': ['ns', 'datatypeLibrary'],
    'optional': ['ns', 'datatypeLibrary'],
    'zeroOrMore': ['ns', 'datatypeLibrary'],
    'oneOrMore': ['ns', 'datatypeLibrary'],
    'list': ['ns', 'datatypeLibrary'],
    'mixed': ['ns', 'datatypeLibrary'],
    'empty': ['ns', 'datatypeLibrary'],
    'text': ['ns', 'datatypeLibrary'],
    'notAllowed': ['ns', 'datatypeLibrary'],
    'grammar': ['ns', 'datatypeLibrary'],
    'except': ['ns', 'datatypeLibrary'],
    'div': ['ns', 'datatypeLibrary'],
    'name': ['ns', 'datatypeLibrary'],
    'anyName': ['ns', 'datatypeLibrary'],
    'nsName': ['ns', 'datatypeLibrary'],
    'choice': ['ns', 'datatypeLibrary'],
    }

class Ref(relaxng.Pattern):
    __slots__ = ('p1', 'depth', 'ref_name', 'grammar')

    def childDeriv (self, node, context):
        return self.p1.childDeriv(node, context)
    def listDeriv (self, nodes, context):
        return self.p1.listDeriv(nodes, context)
    def startTagOpenDeriv (self, qname):
        return self.p1.startTagOpenDeriv(qname)
    def endTagDeriv (self):
        return self.p1.endTagDeriv()
    def startTagCloseDeriv (self):
        return self.p1.startTagCloseDeriv()
    def attDeriv (self, node, context):
        return self.p1.attDeriv(node, context)
    def attsDeriv (self, nodes, context):
        return self.p1.attsDeriv(nodes, context)
    def textDeriv (self, node, context):
        return self.p1.textDeriv(node, context)
    def childrenDeriv (self, nodes, context):
        return self.p1.childrenDeriv(nodes, context)
    def valueMatch (self, node, context):
        return self.p1.valueMatch(node, context)
    def is_nullable (self):
        return self.p1.is_nullable()
    
    
class ExternalRef:
    def __init__ (self, ref_name):
        self.ref_name = ref_name

def expect_end_element (stream, event, node, name):
    if event == pulldom.END_ELEMENT and node.localName == name:
        return
    raise RuntimeError, 'unexpected element inside <%s>: %r, %r' % (name, event, node)


def is_legal_xml_name (name):
    m = re_Name().match(name)
    if m is None or m.end() != len(name): return 0
    else:
        return 1
    
def is_start_of_pattern (event, node):
    """is_start_of_pattern(event, node) -> Boolean
    Returns true if the event marks the beginning of a pattern.
    """

    if event != pulldom.START_ELEMENT:
        return 0
    return node.localName in ['element', 'attribute',
                              'group', 'interleave', 'choice',
                              'optional', 'zeroOrMore', 'oneOrMore',
                              'list', 'mixed', 'ref', 'parentRef',
                              'empty', 'text', 'value', 'data',
                              'notAllowed', 'externalRef',
                              'grammar']
    
def is_start_of_grammarcontent (event, node):
    """is_start_of_grammarcontent(event, node) -> Boolean
    Returns true if the event marks the beginning of a grammar content element.
    """

    if event != pulldom.START_ELEMENT:
        return 0
    return node.localName in ['div', 'start', 'define', 'include']


def is_start_of_includecontent (event, node):
    """is_start_of_includecontent(event, node) -> Boolean
    Returns true if the event marks the beginning of a include content element.
    """

    if event != pulldom.START_ELEMENT:
        return 0
    return node.localName in ['div', 'start', 'define']


def make_two_children (klass, children):
    if len(children) == 1: return children[0]
    c = children[-1]
    cr = children[:-1] ; cr.reverse()
    for pattern in cr:
        c = klass(p1=pattern, p2=c)
    return c


def make_choice (children):
    return make_two_children(relaxng.make_choice, children)
def make_group (children):
    return make_two_children(relaxng.make_group, children)
def make_interleave (children):
    return make_two_children(relaxng.make_interleave, children)

def make_oneOrMore (children):
    p1=make_group(children)
    if p1 is relaxng.NotAllowed or p1 is relaxng.Empty:
        return p1
    return relaxng.OneOrMore(p1=p1)

def make_mixed (children):
    # 4.13: transform mixed into an interleave
    if relaxng.Text not in children:
        children.append(relaxng.Text)
    return make_interleave(children)

def make_optional (children):
    # 4.14: transform optional into a choice
    return make_choice([relaxng.Empty,
                        make_group(children)])

def make_zeroOrMore (children):
    # 4.15: transform zeroOrMore into a choice
    return make_choice([relaxng.Empty,
                        make_oneOrMore(children)])

def make_element (nc, patterns):
    p1 = make_group(patterns)
    if nc is relaxng.NotAllowed or p1 is relaxng.NotAllowed:
        return relaxng.NotAllowed
    return relaxng.Element(nc=nc, p1=p1)

def make_list (children):
    p1 = make_group(children)
    if p1 is relaxng.NotAllowed:
        return p1
    elif p1 is relaxng.Empty:
        return relaxng.Empty
    return relaxng.List(p1=p1)


def make_attribute (nc, pattern):
    if pattern is None: pattern = relaxng.Text
    p1 = make_group([pattern])
    if p1 is relaxng.NotAllowed:
        return p1
    return relaxng.Attribute(nc=nc, p1=p1)

factories = {
    'group': make_group, 
    'interleave': make_interleave, 
    'choice': make_choice, 
    'optional': make_optional, 
    'zeroOrMore': make_zeroOrMore, 
    'oneOrMore': make_oneOrMore, 
    'list': make_list, 
    'mixed': make_mixed, 
    }

def parse_nameclass_plus (self, end_element, check_xmlns=0):
    event, node = self.stream.next()
    nc_list = []
    while 1:
        if event == pulldom.END_ELEMENT and node.localName == end_element:
            break
        elif event == pulldom.START_ELEMENT:
            nc = self.parse_rest_of_nameclass(event, node, check_xmlns)
            nc_list.append(nc)
        event, node = self.stream.next()

    if len(nc_list) == 0:
        raise RuntimeError, "<except> contains no name classes"
    nc = nc_list[0]
    for nc2 in nc_list[1:]:
        nc = relaxng.NameClassChoice(nc, nc2)

    return nc


def parse_nameclass (self, check_xmlns=1):
    """parse_nameclass() : NameClass
    Parse a nameclass declaration.
    """
    event, node = self.stream.get_next_event()
    return self.parse_rest_of_nameclass(event, node, check_xmlns)

def parse_rest_of_nameclass (self, event, node, check_xmlns):
    
    if (event != pulldom.START_ELEMENT or
        node.localName not in ['anyName', 'nsName', 'name', 'choice']):
        raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)

    # Parse 4 possible forms for a nameclass
    localName = node.localName
    if localName == 'choice':
        nc1 = self.parse_nameclass()
        nc2 = self.parse_nameclass()
        self.stream.expect_end_element('choice')
        if isinstance(nc1, relaxng.AnyName): return nc1
        elif isinstance(nc2, relaxng.AnyName): return nc2
        return relaxng.NameClassChoice(nc1, nc2)

    elif localName == 'name':
        prefix_map = self.stream.get_prefix_map()
        ns = node.getAttributeNS(RNG.BASE, 'ns')
        ns = ns.strip()
        ncname = ""
        while 1:
            ncname, event, node = self.stream.accumulate_string()
            if (event == pulldom.END_ELEMENT and node.localName == 'name'):
                break
            else:
                raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)

        ncname = ncname.strip()
        # 4.10: QNames are transformed into a uri,name pair.
        if ':' in ncname:
            assert ns is None
            prefix, ncname = ncname.split(':', 1)
            ns = prefix_map[prefix]
        if check_xmlns:
            if ns == "" and ncname == 'xmlns':
                raise RuntimeError, "Attribute must not be named 'xmlns'"
            elif ns == "http://www.w3.org/2000/xmlns":
                raise RuntimeError, \
                      "Attribute must not have namespace URI %r" % ns
        return relaxng.Name(ns, ncname)

    elif localName == 'nsName':
        ns = node.getAttributeNS(RNG.BASE, 'ns')
        ns = ns.strip()
        event, node = self.stream.get_next_event()
        if event == pulldom.END_ELEMENT and node.localName == 'nsName':
            return relaxng.NsName(ns)
        elif event == pulldom.START_ELEMENT and node.localName == 'except':
            nc = self.parse_nameclass_plus('except', check_xmlns)
            self.stream.expect_end_element('nsName')
            if isinstance(nc, relaxng.AnyName):
                raise RuntimeError, "<except> contains AnyName"
            elif isinstance(nc, relaxng.NsName):
                raise RuntimeError, "<except> contains NsName"
            return relaxng.NsNameExcept(ns, nc)
        else:
            raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)
    
    elif localName == 'anyName':
        event, node = self.stream.get_next_event()
        if event == pulldom.END_ELEMENT and node.localName == 'anyName':
            return relaxng.AnyName()
        elif event == pulldom.START_ELEMENT and node.localName == 'except':
            nc = self.parse_nameclass_plus('except', check_xmlns)
            self.stream.expect_end_element('anyName')
            if isinstance(nc, relaxng.AnyName):
                raise RuntimeError, "<except> contains AnyName"
            return relaxng.AnyNameExcept(nc)
        else:
            raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)
        

    
def parse_rest_of_pattern (self, event, node):
    assert is_start_of_pattern(event, node)
    localName = node.localName

    # Empty elements
    if localName == 'empty':
        self.stream.expect_end_element('empty')
        return relaxng.Empty
    elif localName == 'text':
        self.stream.expect_end_element('text')
        return relaxng.Text
    elif localName == 'notAllowed':
        self.stream.expect_end_element('notAllowed')
        return relaxng.NotAllowed
    elif localName == 'ref':
        name = node.getAttributeNS(RNG.BASE, 'name')
        if name == "":
            raise RuntimeError, '<ref> without name attribute'
        elif ':' in name:
            raise RuntimeError, ("name attribute of <ref> "
                                 "cannot be qualified")
        elif not is_legal_xml_name(name):
            raise RuntimeError, "Illegal name specified: %r" % name
        
        self.stream.expect_end_element('ref')
        grammar=self.stream.get_grammar()
        ref = grammar.get_ref(name)
        return ref

    elif localName == 'parentRef':
        name = node.getAttributeNS(RNG.BASE, 'name')
        if name == "":
            raise RuntimeError, '<parentRef> without name attribute'
        elif ':' in name:
            raise RuntimeError, ("name attribute of <parentRef> "
                                 "cannot be qualified")
        elif not is_legal_xml_name(name):
            raise RuntimeError, "Illegal name specified: %r" % name
        
        self.stream.expect_end_element('parentRef')
        grammar = self.stream.get_grammar().grammar
        ref = grammar.get_ref(name)
        return ref
    elif localName == 'externalRef':
        href = node.getAttributeNS(RNG.BASE, 'href')
        if href == "":
            raise RuntimeError, "<externalRef> must have 'href' attribute"
        ns = node.getAttributeNS(RNG.BASE, 'ns')

        # XXX This processing of xml:base doesn't seem to be correct yet.
        base_uri = self.base_uri
        for p in self.stream.parents:
            xml_base = p.getAttributeNS('http://www.w3.org/XML/1998/namespace',
                                        'base')
            if xml_base != "":
                base_uri = urlparse.urljoin(base_uri, xml_base)
                break
            
        ext_uri = urlparse.urljoin(base_uri, href)
            
        self.stream.expect_end_element('externalRef')
        
        #print 'Opening', ext_uri
        parser = RelaxNGParser()
        # XXX shouldn't use bare 'except' here
        try:
            f = urllib.urlopen(ext_uri)
        except:
            raise RuntimeError, "Couldn't open URI %r" % ext_uri
        
        schema = parser.parse(f, ext_uri)
        pattern = schema._pattern
#        if not pattern.hasAttributeNS(RNG.BASE, 'ns'):
#            pattern.setAttributeNS(RNG.BASE, 'ns', ns)
        return pattern
    
    elif factories.has_key(localName):
        factory = factories[localName]
        patterns, event, node = self.parse_pattern_plus()
        expect_end_element(self.stream, event, node, localName)
        return factory(patterns)

    elif localName == 'element':
        name = node.getAttributeNS(RNG.BASE, 'name')
        ns = self.stream.find_ancestor_attribute(RNG.BASE, 'ns')
        if name != "":
            # [4.8: name attribute is equivalent to a <name> child]
            if ':' in name:
                prefix, name = name.split(':', 1)
                pmap = self.stream.get_prefix_map()
                ns = pmap.get(prefix, None)
                if ns is None:
                    raise RuntimeError, \
                          'Namespace prefix %r not defined' % prefix
                if ':' in name:
                    raise RuntimeError, "':' not legal in element name %r" % name
            nc = relaxng.Name(ns, name)
        else:
            nc = self.parse_nameclass()
            if (isinstance(nc, relaxng.NsName) and nc.uri == ""):
                nc.uri = ns

        patterns, event, node = self.parse_pattern_plus()
        expect_end_element(self.stream, event, node, 'element')
        return make_element(nc, patterns)

    elif localName == 'attribute':
        name = node.getAttributeNS(RNG.BASE, 'name')
        ns = self.stream.find_ancestor_attribute(RNG.BASE, 'ns')
        if name:
            # [4.8: name attribute is equivalent to a <name> child]
            if ':' in name:
                prefix, name = name.split(':', 1)
                pmap = self.stream.get_prefix_map()
                ns = pmap.get(prefix, None)
                if ns is None:
                    raise RuntimeError, \
                          'Namespace prefix %r not defined' % prefix
                if ':' in name:
                    raise RuntimeError, \
                          "':' not legal in element name %r" % name

            if ns == "" and name == 'xmlns':
                raise RuntimeError, "Attribute must not be named 'xmlns'"
            elif ns == "http://www.w3.org/2000/xmlns":
                raise RuntimeError, \
                      "Attribute must not have namespace URI %r" % ns
            nc = relaxng.Name(ns, name)
        else:
            nc = self.parse_nameclass(check_xmlns=True)
            if (isinstance(nc, relaxng.NsName) and nc.uri == ""):
                nc.uri = ns

        pattern, event, node = self.parse_pattern_optional()
        expect_end_element(self.stream, event, node, 'attribute')
        return make_attribute(nc, pattern)
    
    elif localName == 'grammar':
        self.stream.push_grammar()
        gcl, event, node = self.parse_grammarcontent()
        expect_end_element(self.stream, event, node, 'grammar')
        grammar = self.stream.pop_grammar()
        grammar.combine()
        grammar.check_all_refs()
        return grammar.start_symbol
        
    elif localName == 'value':
        # 4.4: if no 'type' attribute, add one
        if node.hasAttributeNS(RNG.BASE, 'type'):
            typ = node.getAttributeNS(RNG.BASE, 'type')
            if ':' in typ:
                raise RuntimeError, ("'type' attribute of <value> "
                                     "cannot be qualified")
            elif not is_legal_xml_name(typ):
                raise RuntimeError, "Illegal name specified: %r" % typ
            
            datalib = self.stream.find_ancestor_attribute(RNG.BASE, 'datatypeLibrary')
            util.check_uri(datalib)
        else:
            typ = 'token'
            datalib = ""
        ns = self.stream.find_ancestor_attribute(RNG.BASE, 'ns')
        
        S, event, node = self.stream.accumulate_string()
        expect_end_element(self.stream, event, node, 'value')
        return relaxng.Value(datatype=(datalib,typ),
                             string=S,
                             context="XXX I don't know what this should be")

    elif localName == 'data':
        typ = node.getAttributeNS(RNG.BASE, 'type')
        if typ == "":
            raise RuntimeError, "<data> doesn't have 'type' attribute"
        elif ':' in typ:
            raise RuntimeError, ("name attribute of <data> "
                                 "cannot be qualified")
        elif not is_legal_xml_name(typ):
            raise RuntimeError, "Illegal name specified: %r" % typ
        
        datalib = self.stream.find_ancestor_attribute(RNG.BASE, 'datatypeLibrary')
        util.check_uri(datalib)
        paramlist = []
        while 1:
            event, node = self.stream.get_next_event()
            if event == pulldom.START_ELEMENT and node.localName == 'param':
                name = node.getAttributeNS(RNG.BASE, 'name')
                if name == "":
                    raise RuntimeError, "<param> without 'name' attribute"
                elif ':' in name:
                    raise RuntimeError, ("name attribute of <param> "
                                         "cannot be qualified")
                elif not is_legal_xml_name(name):
                    raise RuntimeError, "Illegal name specified: %r" % name
                
                S, event, node = self.stream.accumulate_string()
                paramlist.append((name, S))
                expect_end_element(self.stream, event, node, 'param')
                
            elif event == pulldom.END_ELEMENT and node.localName == 'data':
                break
            elif event == pulldom.START_ELEMENT and node.localName == 'except':
                break
            else:
                raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)

        patterns = None
        if event == pulldom.START_ELEMENT and node.localName == 'except':
            patterns, event, node = self.parse_pattern_plus()
            expect_end_element(self.stream, event, node, 'except')
            event, node = self.stream.next()
            
        if patterns is not None:
            exception = make_choice(patterns)
            if exception is relaxng.NotAllowed:
                exception = None
        else:
            exception = None

        expect_end_element(self.stream, event, node, 'data')
        if exception is None:
            return relaxng.Data(datatype=(datalib,typ),
                                paramlist=paramlist)
        else:
            return relaxng.DataExcept(datatype=(datalib,typ),
                                      paramlist=paramlist,
                                      p1=exception)
    else:
        raise RuntimeError, 'Unknown tag: %r' % localName
        
def parse_pattern (self):
    """parse_pattern(self.stream) -> Pattern
    Parse a single pattern declaration.
    """
    event, node = self.stream.get_next_event()
    if not is_start_of_pattern(event, node):
        raise RuntimeError, 'Expecting a pattern here'
    return self.parse_rest_of_pattern(event, node)


def parse_pattern_optional (self):
    event, node = self.stream.get_next_event()
    if is_start_of_pattern(event, node):
        pattern = self.parse_rest_of_pattern(event, node)
        event, node = self.stream.get_next_event()
    else:
        pattern = None

    return pattern, event, node


def parse_pattern_plus (self):
    L = []
    while 1:
        event, node = self.stream.get_next_event()
        if not is_start_of_pattern(event, node):
            break
        L.append(self.parse_rest_of_pattern(event, node))
    if len(L) == 0:
        raise RuntimeError, 'Must supply at least one pattern'
    return L, event, node


def parse_includecontent (self):
    icl = []
    while 1:
        event, node = self.stream.get_next_event()
        if not is_start_of_includecontent(event,node):
            break

        localName = node.localName
        if localName == 'start':
            combine = node.getAttributeNS(RNG.BASE, 'combine')
            pattern = self.parse_pattern()
            self.stream.expect_end_element('start')
            self.stream.get_grammar().add_start_sym(combine, pattern)
            
        elif localName == 'define':
            combine = node.getAttributeNS(RNG.BASE, 'combine')
            name = node.getAttributeNS(RNG.BASE, 'name')
            if name == "":
                raise RuntimeError, '<define> without name attribute'
            elif ':' in name:
                raise RuntimeError, ("name attribute of <define> "
                                     "cannot be qualified")
            elif not is_legal_xml_name(name):
                raise RuntimeError, "Illegal name specified: %r" % name


            patterns, event, node = self.parse_pattern_plus()
            expect_end_element(self.stream, event, node, 'define')

            # Add to grammar
            ref = self.stream.get_grammar().get_ref(name)
            
        elif localName == 'div':
            icl2, event, node = self.parse_grammarcontent()
            expect_end_element(self.stream, event, node, 'div')
            icl.append(icl2)

    return icl, event, node


def parse_grammarcontent (self):
    gcl = []
    while 1:
        event, node = self.stream.get_next_event()
        if not is_start_of_grammarcontent(event,node):
            break

        localName = node.localName
        if localName == 'div':
            gcl2, event, node = self.parse_grammarcontent()
            expect_end_element(self.stream, event, node, 'div')
            gcl.extend(gcl2)
            
        elif localName == 'include':
            href = node.getAttributeNS(RNG.BASE, 'href')
            icl, event, node = self.parse_includecontent()
            expect_end_element(self.stream, event, node, 'include')
            gcl.append(icl)
            
        elif localName == 'start':
            combine = node.getAttributeNS(RNG.BASE, 'combine')
            pattern = self.parse_pattern()
            self.stream.expect_end_element('start')
            self.stream.get_grammar().add_start_sym(combine, pattern)
            
        elif localName == 'define':
            combine = node.getAttributeNS(RNG.BASE, 'combine')
            name = node.getAttributeNS(RNG.BASE, 'name')
            if name == "":
                raise RuntimeError, '<define> without name attribute'
            elif ':' in name:
                raise RuntimeError, ("name attribute of <define> "
                                     "cannot be qualified")
            elif not is_legal_xml_name(name):
                raise RuntimeError, "Illegal name specified: %r" % name

            patterns, event, node = self.parse_pattern_plus()
            
            expect_end_element(self.stream, event, node, 'define')

            # Add to dictionary
            self.stream.get_grammar().add_define(name, combine,
                                            make_group(patterns))

        else:
            raise RuntimeError, 'Unexpected element: %r' % localName

    return gcl, event, node


def parse (self, source, base_uri):
    """parse(source) : Pattern
    Parses the XML from the input stream and returns a Pattern tree.
    """
    self.base_uri = base_uri
    stream = util.DOMTokenStream(pulldom.parse(source))
    stream.set_legal_attributes(_legal_attributes)
    self.stream = stream
    
    # Process the document prologue
    assert stream.get_next_event()[0] == pulldom.START_DOCUMENT
    try:
        event, node = stream.get_next_event()
    except StopIteration:
        raise RuntimeError, ('No first element found -- '
                             'missing RELAX NG namespace declaration?')

    assert is_start_of_pattern(event, node)
    root_grammar = stream.root_grammar
    root_grammar.add_start_sym('', self.parse_rest_of_pattern(event, node))
    root_grammar.combine()

    pattern = root_grammar.start_symbol
    if pattern is relaxng.NotAllowed:
        raise RuntimeError, "Schema reduces to NotAllowed (can never be valid)"
    
    return relaxng.Schema(pattern)

class RelaxNGParser:
    pass

RelaxNGParser.parse_nameclass_plus = parse_nameclass_plus
RelaxNGParser.parse_nameclass = parse_nameclass
RelaxNGParser.parse_rest_of_nameclass = parse_rest_of_nameclass
RelaxNGParser.parse_rest_of_pattern = parse_rest_of_pattern
RelaxNGParser.parse_pattern = parse_pattern
RelaxNGParser.parse_pattern_optional = parse_pattern_optional
RelaxNGParser.parse_pattern_plus = parse_pattern_plus
RelaxNGParser.parse_includecontent = parse_includecontent
RelaxNGParser.parse_grammarcontent = parse_grammarcontent
RelaxNGParser.parse = parse

name_count = 0
def generate_name():
    global name_count
    name_count += 1
    return 'sym' + str(name_count)


if __name__ == '__main__':
    parser = RelaxNGParser()
    f = open('small-test.xml', 'r')
    schema = parser.parse(f, 'small-test.xml')
    f.close()
    print schema
    schema.dump()
    
