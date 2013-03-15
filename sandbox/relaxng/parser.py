"""parser

Parser for the RELAX NG simple syntax, as described in section 5 of the
RELAX NG specification.

XXX use an exception other than RuntimeError
"""

# created 2002/01/06, AMK

__revision__ = "$Id: parser.py,v 1.15 2002/07/19 12:52:44 akuchling Exp $"

from xml.ns import RNG
from xml.dom import pulldom
import util
import relaxng

class Ref:
    def __init__ (self, ref_name):
        self.ref_name = ref_name
        
def parse_top (stream):
    """parse_top(stream) : Pattern
    Parse a pattern declaration.
    """
    return parse_pattern(stream, notallowed_ok=1, empty_ok=1)


def parse_pattern (stream, notallowed_ok=0, empty_ok=1):
    """parse_pattern(stream, notallowed_ok, empty_ok) : Pattern
    Parse a pattern declaration.
   
    If notallowed_ok is true, the 'notAllowed' element will be legal
    (corresponding to the 'top' production in the grammar).  Otherwise
    that element will cause an exception (the 'pattern' production).
    'empty_ok' controls whether the 'empty' element is legal.
    """
    event, node = stream.get_next_event()
    if event != pulldom.START_ELEMENT:
        raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)

    localName = node.localName
    if notallowed_ok and localName == 'notAllowed':
        stream.expect_end_element('notAllowed')
        return relaxng.NotAllowed
    elif empty_ok and localName == 'empty':
        stream.expect_end_element('empty')
        return relaxng.Empty
    elif localName == 'text':
        stream.expect_end_element('text')
        return relaxng.Text
    elif localName == 'ref':
        ref_name = node.getAttributeNS(RNG.BASE, 'name')
        stream.expect_end_element('ref')
        return Ref(ref_name)
    
    # More complicated pattern elements
    elif localName == 'list':
        pattern = parse_pattern(stream)
        stream.expect_end_element('list')
        return relaxng.List(p1=pattern)

    elif localName == 'attribute':
        nc = parse_nameclass(stream)
        pattern = parse_pattern(stream)
        stream.expect_end_element('attribute')
        return relaxng.Attribute(nc=nc, p1=pattern)

    elif localName == 'oneOrMore':
        pattern = parse_pattern(stream, empty_ok=0)
        stream.expect_end_element('oneOrMore')
        return relaxng.OneOrMore(p1=pattern)
    
    elif localName == 'choice':
        pattern1 = parse_pattern(stream, empty_ok=1)
        pattern2 = parse_pattern(stream, empty_ok=0)
        stream.expect_end_element('choice')
        return relaxng.Choice(p1=pattern1, p2=pattern2)
    
    elif localName == 'group':
        pattern1 = parse_pattern(stream, empty_ok=0)
        pattern2 = parse_pattern(stream, empty_ok=0)
        stream.expect_end_element('group')
        return relaxng.Group(p1=pattern1, p2=pattern2)
    
    elif localName == 'interleave':
        pattern1 = parse_pattern(stream, empty_ok=0)
        pattern2 = parse_pattern(stream, empty_ok=0)
        stream.expect_end_element('interleave')
        return relaxng.Interleave(p1=pattern1, p2=pattern2)

    elif localName == 'value':
        type = node.getAttributeNS(RNG.BASE, 'type')
        datalib = node.getAttributeNS(RNG.BASE, 'datatypeLibrary')
        ns = node.getAttributeNS(RNG.BASE, 'ns')
        S, event, node = stream.accumulate_string()
        assert event == pulldom.END_ELEMENT and node.localName == 'value'
        return relaxng.Value(datatype=(datalib,type),
                             string=S,
                             context="XXX I don't know what this should be")
        
    elif localName == 'data':
        type = node.getAttributeNS(RNG.BASE, 'type')
        datalib = node.getAttributeNS(RNG.BASE, 'datatypeLibrary')
        paramlist = []
        exception = None
        # XXX Too liberal: allows mixing param and except elements
        while 1:
            event, node = stream.get_next_event()
            if event == pulldom.START_ELEMENT and node.localName == 'param':
                name = node.getAttributeNS(RNG.BASE, 'name')
                S, event, node = stream.accumulate_string()
                paramlist.append((name, S))
                assert event == pulldom.END_ELEMENT and node.localName == 'param'
                
            elif event == pulldom.START_ELEMENT and node.localName == 'except':
                exception = parse_pattern(stream)
                stream.expect_end_element('except')
                
            elif event == pulldom.END_ELEMENT and node.localName == 'data':
                break
            else:
                raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)
            
        if exception is None:
            return relaxng.Data(datatype=(datalib,type),
                                paramlist=paramlist)
        else:
            return relaxng.DataExcept(datatype=(datalib,type),
                                      paramlist=paramlist,
                                      p1=exception)
            
        

def parse_nameclass (stream):
    """parse_nameclass(stream) : NameClass
    Parse a nameclass declaration.
    """
    event, node = stream.get_next_event()
    if (event != pulldom.START_ELEMENT or
        node.localName not in ['anyName', 'nsName', 'name', 'choice']):
        raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)

    # Parse 4 possible forms for a nameclass
    localName = node.localName
    if localName == 'choice':
        nc1 = parse_nameclass(stream)
        nc2 = parse_nameclass(stream)
        stream.expect_end_element('choice')
        return relaxng.NameClassChoice(nc1, nc2)

    elif localName == 'name':
        prefix_map = stream.get_prefix_map()
        ns = node.getAttributeNS(RNG.BASE, 'ns')
        ncname = ""
        while 1:
            ncname, event, node = stream.accumulate_string()
            if (event == pulldom.END_ELEMENT and node.localName == 'name'):
                break
            else:
                raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)

        # 4.10: QNames are transformed into a uri,name pair.
        if ':' in ncname:
            assert ns is None
            prefix, ncname = ncname.split(':', 1)
            ns = prefix_map[prefix]
        return relaxng.Name(ns, ncname)

    elif localName == 'nsName':
        ns = node.getAttributeNS(RNG.BASE, 'ns')
        event, node = stream.get_next_event()
        if event == pulldom.END_ELEMENT and node.localName == 'nsName':
            return relaxng.NsName(ns)
        elif event == pulldom.START_ELEMENT and node.localName == 'except':
            nc = parse_nameclass(stream)
            stream.expect_end_element('except')
            stream.expect_end_element('nsName')
            return relaxng.NsNameExcept(ns, nc)
        else:
            raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)
    
    elif localName == 'anyName':
        event, node = stream.get_next_event()
        if event == pulldom.END_ELEMENT and node.localName == 'anyName':
            return relaxng.AnyName()
        elif event == pulldom.START_ELEMENT and node.localName == 'except':
            nc = parse_nameclass(stream)
            stream.expect_end_element('except')
            stream.expect_end_element('anyName')
            return relaxng.AnyNameExcept(nc)
        else:
            raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)
        

    
def parse (source):
    """parse(source) : Pattern
    Parses the XML from the input stream and returns a Pattern tree.
    """
    stream = util.DOMTokenStream(pulldom.parse(source))
    element_map = {}
#    for item in stream:
#        print item, stream.parents
    
    # Process the document prologue and the first two elements
    assert stream.next()[0] == pulldom.START_DOCUMENT
    stream.expect_element('grammar')
    stream.expect_element('start')

    # Parse the main pattern body
    pattern = parse_top(stream)
    
    stream.expect_end_element('start')

    # Process definition section
    while 1:
        event, node = stream.get_next_event()
        if event == pulldom.END_ELEMENT and node.localName == 'grammar':
            # We're done
            break 
        elif event == pulldom.START_ELEMENT and node.localName == 'define':
            # Parse definition
            ncname = node.getAttributeNS(RNG.BASE, 'name')
            stream.expect_element('element')
            nc = parse_nameclass(stream)
            pattern = parse_top(stream)
            stream.expect_end_element('element')
            stream.expect_end_element('define')
            element_map[ncname] = relaxng.Element(nc=nc,
                                                  p1=pattern)
        else:
            raise RuntimeError, 'Unexpected event: %r, %r' % (event, node)

    # Loop through all the patterns, replacing Ref instances
    # with the corresponding Element instance
    # XXX does this always terminate, given that there can be
    # cycles of Elements?
    # XXX on the other hand, does this cover every single pattern
    # node that could contain a Ref instance?
    queue = [pattern] + element_map.values()
    while len(queue):
        head = queue.pop()
        if hasattr(head, 'p1'):
            if isinstance(head.p1, Ref):
                head.p1 = element_map[head.p1.ref_name]
            else:
                queue.append(head.p1)

        if hasattr(head, 'p2'):
            if isinstance(head.p2, Ref):
                head.p2 = element_map[head.p2.ref_name]
            else:
                queue.append(head.p2)
            
    return relaxng.Schema(pattern)
    
if __name__ == '__main__':
    f = open('simple-test.xml', 'r')
    schema = parse(f)
    f.close()
    schema.dump()
