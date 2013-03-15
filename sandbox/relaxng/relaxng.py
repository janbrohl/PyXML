"""relaxng

Code for a RELAX NG validator, using the algorithm described
by James Clark at http://www.thaiopensource.com/relaxng/derivative.html.
"""

__revision__ = "$Id: relaxng.py,v 1.28 2002/07/19 13:30:57 akuchling Exp $"

import sys

from xml.utils.characters import re_Name
import util

# Ensure that the name 'object' exists, so that all the other classes
# can subclass from it.

try:
    object
except NameError:
    class object: pass


# Useful functions

def apply_after (func, pattern):
    if pattern is NotAllowed:
        return NotAllowed
    elif isinstance(pattern, After):
        return make_after(pattern.p1, func(pattern.p2))
    elif isinstance(pattern, Choice):
        return make_choice(apply_after(func, pattern.p1),
                           apply_after(func, pattern.p2))
    else:
        raise RuntimeError, \
              'apply_after called on unexpected pattern %r' % pattern

def curry (f, x):
    def g(y):
        return f(x, y)
    return g
    
def flip (f, x):
    """Flips order of arguments of a 2-argument function, and supplies
    a value for the second argument."""
    
    def g(y):
        return f(y, x)
    return g

def whitespace (node):
    if (node.type == util.TEXT_NODE and
        node.value.strip() == ""):
        return 1
    else:
        return 0


def filter_childNodes (node):
    """Filter out attribute nodes that are namespace declarations.
    """
    if node.type != util.ATTRIBUTE_NODE: return 1
    elif not (node.nodeName == 'xmlns' or
              node.nodeName.startswith('xmlns:')):
        return 1
    else:
        return 0


def datatypeAllows (datatype, paramlist, node, context):
    # XXX Should the namespace URI be None and not ""?
    if (datatype == ("", "string") and paramlist == []):
        return 1
    elif (datatype == ("", "token") and paramlist == []):
        return 1
    else:
        return 0


def datatypeEqual (datatype, s1, cx1, s2, cx2):
    if datatype == ("", "string"):
        return s1 == s2
    elif datatype == ("", "token"):
        words1 = s1.split()
        words2 = s2.split()
        return words1 == words2
    else:
        return 0


def make_choice (p1, p2):
    """Factory to create Choice instances, applying the algebraic identities
    for NotAllowed and Empty."""
    if   p1 is NotAllowed: return p2
    elif p2 is NotAllowed: return p1
    elif p1 is Empty and p2 is Empty:
        return Empty
    elif p2 is Empty:
        # Ensure that the first child is Empty.
        return Choice(p1=p2, p2=p1)
    else:
        return Choice(p1=p1, p2=p2)

    
def make_group (p1, p2):
    """Factory to create Group instances, applying the algebraic identities
    for NotAllowed and Empty."""
    if p1 is NotAllowed or p2 is NotAllowed: return NotAllowed
    elif p1 is Empty: return p2
    elif p2 is Empty: return p1
    else:
        return Group(p1=p1, p2=p2)
    
def make_interleave (p1, p2):
    """Factory to create Interleave instances, applying the algebraic
    identities for NotAllowed and Empty."""
    if p1 is NotAllowed or p2 is NotAllowed: return NotAllowed
    elif p1 is Empty: return p2
    elif p2 is Empty: return p1
    else:
        return Interleave(p1=p1, p2=p2)
    
    
def make_after (p1, p2):
    """Factory to create After."""
    if p1 is NotAllowed or p2 is NotAllowed:
        return NotAllowed
    else:
        return After(p1=p1, p2=p2)

def make_oneormore (p1):
    if p1 is NotAllowed:
        return NotAllowed
    else:
        return OneOrMore(p1=p1)
    
class Context(object):
    """Context of an XML element, containing a base URI
    and a mapping from prefixes to namespace URIs.
    """
    __slots__ = ('uri', 'mapping')
    
    def __init__ (self, uri, mapping):
        self.uri = uri
        self.mapping = mapping

    
class Schema(object):
    def __init__ (self, pattern):
        self._pattern = pattern

    def dump (self):
        self._pattern.dump()
        
    def is_valid (self, document):
        context = Context(None, {})
        return self._pattern.matches(document, context)
# class Schema

#
# Name classes
#

class NameClass:
    def contains (self, qname):
        raise RuntimeError, 'Unimplemented abstract contains() method'
        
class AnyName(NameClass):
    def contains (self, qname):
        return 1
    def dump (self, depth=0):
        sys.stdout.write(depth*' ' + '<AnyName>\n')
    
class AnyNameExcept(NameClass):
    def __init__ (self, nc):
        self._nc = nc
    def contains (self, qname):
        return not self._nc.contains(qname)
    def dump (self, depth=0):
        sys.stdout.write('<AnyNameExcept>\n')
        sys.stdout.write((depth+2)*' ')
        self._nc.dump(depth+2)

class Name(NameClass):
    def __init__ (self, uri, localname):
        if not re_Name().match(localname):
            raise RuntimeError, "Illegal name specified: %r" % localname
        
        self._qname = (uri, localname)

    def contains (self, qname):
        # Check if the namespace URIs are both false (None or "");
        # if yes, just compare the local name
        ##print self._qname, qname
        if not self._qname[0] and not qname[0]:
            return self._qname[1] == qname[1]
        return self._qname == qname
    
    def dump (self, depth=0):
        sys.stdout.write(depth*' ' + '<Name %r>\n' % (self._qname,) )
    
class NsName(NameClass):
    def __init__ (self, uri):
        self.uri = uri
    def contains (self, qname):
        if not self.uri and not qname[0]:
            return 1
        return self.uri == qname[0]
    def dump (self, depth=0):
        sys.stdout.write(depth*' ' + '<NsName %r>\n' % self.uri)
    
class NsNameExcept(NameClass):
    def __init__ (self, uri, nc):
        self._uri = uri
        self._nc = nc
    def contains (self, qname):
        return self._uri == qname[0] and not self._nc.contains(qname)
    def dump (self, depth=0):
        sys.stdout.write(depth*' ' + '<NsNameExcept %r>\n' % self._uri)
        self._nc.dump(depth+2)
        
class NameClassChoice(NameClass):
    def __init__ (self, nc1, nc2):
        self._nc1 = nc1
        self._nc2 = nc2
    def contains (self, qname):
        return self._nc1.contains(qname) or self._nc2.contains(qname)
    def dump (self, depth=0):
        sys.stdout.write(depth*' ' + '<NameClassChoice>\n')
        self._nc1.dump(depth+2)
        self._nc2.dump(depth+2)


#
# Pattern classes
#

class Pattern(object):
    __slots__ = ('_isnull',)
    
    def __init__ (self, **args):
        for key, value in args.items():
            setattr(self, key, value)
        self._isnull = None

    def dump (self, depth=0):
        sys.stdout.write(('<%s>\n' % self.__class__.__name__))
        for key in dir(self):
            if key not in self.__slots__: continue
            value = getattr(self, key)
            sys.stdout.write((depth+1)*' ' + key + '=')
            if hasattr(value, 'dump'):
                value.dump(depth+2)
            else: print repr(value)
            
    def matches (self, node, context):
        ##print 'matches', self, node, context
        deriv = self.childDeriv(node, context)
        ##print 'Derivative', self, deriv
        return deriv.is_nullable()

    def is_nullable (self):
        if self._isnull is None:
            self._isnull = self._nullable()
        return self._isnull

    def childDeriv (self, node, context):
        if node.type == util.TEXT_NODE:
            return self.textDeriv(node, context)
        elif node.type == util.ELEMENT_NODE:
            p1 = self.startTagOpenDeriv(node.qname)
            p2 = p1.attsDeriv(node.attrs, context)
            p3 = p2.startTagCloseDeriv()
            p4 = p3.childrenDeriv(node.children, context)
            p5 = p4.endTagDeriv()
            return p5
        else:
            return NotAllowed
        
    def listDeriv (self, nodes, context):
        if len(nodes) == []:
            return self

        deriv = self
        for node in nodes:
            deriv = deriv.textDeriv(node, context)
            if deriv is NotAllowed:
                break
        return deriv

    def startTagOpenDeriv (self, qname):
        return NotAllowed

    def startTagCloseDeriv (self):
        return self

    def endTagDeriv (self):
        return NotAllowed
        
    def attDeriv (self, node, context):
        return NotAllowed

    def attsDeriv (self, nodes, context):
        if len(nodes) == 0:
            return self
        p = self
        for node in nodes:
            if node.type != util.ATTRIBUTE_NODE:
                return NotAllowed
            p = p.attDeriv(node, context)
        return p

    def valueMatch (self, node, context):
         if ((self.is_nullable() and whitespace(node)) or
             self.textDeriv(node, context).is_nullable()):
             return Empty
         else:
             return NotAllowed
        
    
    def childrenDeriv (self, nodes, context):
        if len(nodes) == 0:
            n = util.TextNode("")
            p1 = self.childDeriv(n, context)
            return make_choice(self, p1)
        
        if len(nodes) == 1 and nodes[0].type == util.TEXT_NODE:
            n = nodes[0]
            p1 = self.childDeriv(n, context)
            if n.value.strip() == "":
                return make_choice(self, p1)
            else:
                return p1

        p = self
        for n in nodes:
            if (n.type == util.TEXT_NODE and n.value.strip() == ""):
                pass
            else:
                p = p.childDeriv(n, context)
                if p is NotAllowed: break

        return p

    # Abstract methods that must be overridden by subclasses
    def _nullable (self):
        raise RuntimeError, 'Unimplemented abstract _nullable() method'
    def textDeriv (self, node, context):
        raise RuntimeError, 'Unimplemented abstract deriv() method'
# class Pattern

    
class _Empty(Pattern):
    __slots__ = ()
    def _nullable (self):
        return 1
    def textDeriv (self, node, context):
        if whitespace(node): return Empty
        else: return NotAllowed
# Create Empty singleton  
Empty = _Empty()

class _NotAllowed(Pattern):
    __slots__ = ()
    def _nullable (self):
        return 0
    def textDeriv (self, node, context):
        # A NotAllowed instance should be returned; we won't bother
        # to create a new one.
        return self 

# Create NotAllowed singleton
NotAllowed = _NotAllowed()

class _Text(Pattern):
    __slots__ = ()
    def _nullable (self):
        return 1
    def textDeriv (self, node, context):
        return self # XXX correct now?
        if node.type == util.TEXT_NODE:
            return self
        else:
            return NotAllowed
# Create Text singleton    
Text = _Text()

class Choice(Pattern):
    __slots__ = ('p1', 'p2')
    def _nullable (self):
        return self.p1.is_nullable() or self.p2.is_nullable()
    def textDeriv (self, node, context):
        return make_choice(self.p1.textDeriv(node, context),
                           self.p2.textDeriv(node, context))
    def startTagOpenDeriv (self, qname):
        return make_choice(self.p1.startTagOpenDeriv(qname),
                           self.p2.startTagOpenDeriv(qname))
    def startTagCloseDeriv (self):
        return make_choice(self.p1.startTagCloseDeriv(),
                           self.p2.startTagCloseDeriv())
    def endTagDeriv (self):
        return make_choice(self.p1.endTagDeriv(),
                           self.p2.endTagDeriv())
    def attDeriv (self, node, context):
        if node.type != util.ATTRIBUTE_NODE:
            return NotAllowed
        
        return make_choice(self.p1.attDeriv(node, context),
                           self.p2.attDeriv(node, context))
    
    
class Interleave(Pattern):
    __slots__ = ('p1', 'p2')
    def _nullable (self):
        return self.p1.is_nullable() and self.p2.is_nullable()
    def textDeriv (self, node, context):
        value = make_choice(make_interleave(self.p1.textDeriv(node, context),
                                            self.p2),
                            make_interleave(self.p1,
                                            self.p2.textDeriv(node, context)),
                            )
        return value
    def startTagOpenDeriv (self, qname):
        a1 = apply_after(flip(make_interleave, self.p2),
                         self.p1.startTagOpenDeriv(qname))
        a2 = apply_after(curry(make_interleave, self.p1),
                         self.p2.startTagOpenDeriv(qname))
        return make_choice(a1, a2)
    def startTagCloseDeriv (self):
        return make_interleave(self.p1.startTagCloseDeriv(),
                               self.p2.startTagCloseDeriv())
    def attDeriv (self, node, context):
        if node.type != util.ATTRIBUTE_NODE:
            return NotAllowed
        
        return make_choice(make_interleave(self.p1.attDeriv(node, context),
                                           self.p2),
                           make_interleave(self.p1, 
                                           self.p2.attDeriv(node, context)))

class After(Pattern):
    __slots__ = ('p1', 'p2')
    def _nullable (self):
        return 0
    def textDeriv (self, node, context):
        value = make_after(self.p1.textDeriv(node, context), self.p2)
        return value
    def startTagOpenDeriv (self, qname):
        return apply_after(flip(make_after, self.p2),
                           self.p1.startTagOpenDeriv(qname))
    def startTagCloseDeriv (self):
        return make_after(self.p1.startTagCloseDeriv(), self.p2)
    def endTagDeriv (self):
        if self.p1.is_nullable():
            return self.p2
        else:
            return NotAllowed
    def attDeriv (self, node, context):
        if node.type != util.ATTRIBUTE_NODE:
            return NotAllowed
        
        return make_after(self.p1.attDeriv(node, context),
                          self.p2)
        
class Group(Pattern):
    __slots__ = ('p1', 'p2')
    def _nullable (self):
        return self.p1.is_nullable() and self.p2.is_nullable()
    def textDeriv (self, node, context):
        if node.type == util.ATTRIBUTE_NODE:
            return make_choice(make_group(self.p1.textDeriv(node, context),
                                          self.p2),
                               make_group(self.p1,
                                          self.p2.textDeriv(node, context))
                               )
        else:
            tem = make_group(self.p1.textDeriv(node, context),
                             self.p2)
            if self.p1.is_nullable():
                return make_choice(tem,
                                   self.p2.textDeriv(node, context))
            else:
                return tem
    def startTagOpenDeriv (self, qname):
        x = apply_after(flip(make_group, self.p2),
                        self.p1.startTagOpenDeriv(qname))
        if self.p1.is_nullable():
            return make_choice(x,
                               self.p2.startTagOpenDeriv(qname))
        else:
            return x
    def startTagCloseDeriv (self):
        return make_group(self.p1.startTagCloseDeriv(),
                          self.p2.startTagCloseDeriv())
    def attDeriv (self, node, context):
        if node.type != util.ATTRIBUTE_NODE:
            return NotAllowed
        
        return make_choice(make_group(self.p1.attDeriv(node, context),
                                      self.p2),
                           make_group(self.p1, 
                                      self.p2.attDeriv(node, context)))
    
class OneOrMore(Pattern):
    __slots__ = ('p1',)
    def _nullable (self):
        return self.p1.is_nullable()
    def textDeriv (self, node, context):
        return make_group(self.p1.textDeriv(node, context),
                          make_choice(OneOrMore(p1=self.p1),
                                      Empty))
    def startTagOpenDeriv (self, qname):
        a1 = apply_after(flip(make_group,
                              make_choice(OneOrMore(p1=self.p1), Empty)),
                         self.p1.startTagOpenDeriv(qname))
        return a1
    def startTagCloseDeriv (self):
        return make_oneormore(self.p1.startTagCloseDeriv())
    def attDeriv (self, node, context):
        if node.type != util.ATTRIBUTE_NODE:
            return NotAllowed
        return make_group(self.p1.attDeriv(node, context),
                          make_choice(self, Empty))
    
        
class List(Pattern):
    __slots__ = ('p1',)
    def _nullable (self):
        return 0
    def textDeriv (self, node, context):
        if node.type != util.TEXT_NODE:
            return NotAllowed

        # XXX any special Unicode handling required here?
        words = node.value.split()
        nodes = map(lambda x: util.TextNode(x), words)
        deriv = self.p1.listDeriv(nodes, context)
        if deriv.is_nullable():
            return Empty
        else:
            return NotAllowed

    
class Data(Pattern):
    __slots__ = ('datatype', 'paramlist')
    def _nullable (self):
        return 0
    def textDeriv (self, node, context):
        if node.type != util.TEXT_NODE:
            return NotAllowed
        if datatypeAllows(self.datatype, self.paramlist,
                          node.value, context):
            return Empty
        else:
            return NotAllowed

    
class DataExcept(Pattern):
    __slots__ = ('datatype', 'paramlist', 'p1')
    def _nullable (self):
        return 0
    def textDeriv (self, node, context):
        if node.type != util.TEXT_NODE:
            return NotAllowed
        if (datatypeAllows(self.datatype, self.paramlist,
                           node.value, context) and
            not self.p1.textDeriv(node, context).is_nullable()):
            return Empty
        else:
            return NotAllowed

    
class Value(Pattern):
    __slots__ = ('datatype', 'string', 'context')
    def _nullable (self):
        return 0
    def textDeriv (self, node, context):
        if node.type != util.TEXT_NODE:
            return NotAllowed
        if datatypeEquals(self.datatype,
                          self.string, self.context,
                          node.value, context):
            return Empty
        else:
            return NotAllowed
        
    
class Attribute(Pattern):
    __slots__ = ('nc', 'p1')
    def _nullable (self):
        return 0
    def attDeriv (self, node, context):
        if node.type != util.ATTRIBUTE_NODE:
            return NotAllowed
        name_ok = self.nc.contains(node.qname)
        if name_ok:
            text = util.TextNode(node.value)
            return self.p1.valueMatch(text, context)
        else:
            return NotAllowed
    def startTagCloseDeriv (self):
        return NotAllowed
        
class Element(Pattern):
    __slots__ = ('nc', 'p1')
    def _nullable (self):
        return 0
    def textDeriv (self, node, context):
        return NotAllowed
    def startTagOpenDeriv (self, qname):
        name_ok = self.nc.contains(qname)
        if name_ok:
            return make_after(self.p1, Empty)
        else:
            return NotAllowed
        

            
# Convenience function for testing -- XXX remove later
def make_test_schema():
    attr = Attribute(nc=Name(None, 'attr'),
                     p1=Text)
    child = Element(nc=Name(None, 'child'),
                    p1=attr)
    child_alt = Element(nc=Name(None, 'child_alt'),
                    p1=attr)
    child3 = Element(nc=Name(None, 'child3'),
                     p1=attr)
    a_elem = Element(nc=Name(None, 'a'),
                     p1=Empty)
    b_elem = Element(nc=Name(None, 'b'),
                     p1=Empty)
    interleave = make_interleave(a_elem, b_elem)
    
    data = Data(datatype=("", "string"),
                paramlist=[])

    group1 = make_group(p1=make_choice(child, child_alt),
                        p2=interleave)
    group2 = make_group(p1=child3, p2=Text)

    root = Element(nc=Name(None, 'root'),
                   p1=Group(p1=group1, p2=group2)
                   )
    pattern = root
    return Schema(pattern)
