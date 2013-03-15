
import string, os, types, sys
from xml.parsers.xmlproc import xmlproc, xmlapp

try:
    UnicodeType = types.UnicodeType
except ImportError:
    UnicodeType = -1 # fails compare to any type
from types import StringType, ListType, TupleType, \
     DictionaryType, NoneType

# --- COMPARISON

def compare(file1, file2):
    inf1 = open(file1)
    inf2 = open(file2)
    line1 = inf1.readline()
    line2 = inf2.readline()
    ix = 1

    while line1 != "" and line1 == line2:
        line1 = inf1.readline()
        line2 = inf2.readline()
        ix = ix + 1

    if line1 != line2:
        print "ERROR in", file1
        print "base: " + repr(line1)
        print "out:  " + repr(line2)
        print

    inf1.close()
    inf2.close()

# Python 2.1 produces \n instead of \012, and \x1b instead of \033
def _unescape_hex_to_oct(data):
    data = string.replace(data,r"\n",r"\012")
    while 1:
        pos = string.find(data,r"\x")
        if pos == -1:
            break
        val = string.atoi(data[pos+2:pos+4],16)
        data = data[:pos]+("\\%03o" % val)+data[pos+4:]
    return data

def prepr(o):
    "Pretty, Python-version independent repr implementation"
    # XXX complete
    t = type(o)
    if t is StringType:
        return _unescape_hex_to_oct(repr(o))
    if t is UnicodeType:
        # skip u prefix
        return _unescape_hex_to_oct(repr(o)[1:])
    if t is ListType:
        result = []
        for item in o:
            result.append(prepr(item))
        result = "["+string.join(result,", ")+"]"
        return result
    if t is TupleType:
        result = []
        for item in o:
            result.append(prepr(item))
        import sys
        if len(result)!=1:
            result = "("+string.join(result,", ")+")"
        else:
            result = "("+result[0]+",)"
        return result
    if t is DictionaryType:
        result = []
        for k,v in o.items():
            result = append(prepr(k)+" : "+prepr(v))
        result = "{"+string.join(result,", ")+"}"
        return result
    if t not in [types.NoneType]:
        return t.__name__+repr(o)
    return repr(o)

def pstr(o):
    t = type(o)
    if t is StringType:
        return o
    if t is UnicodeType:
        return o.encode("utf-8")
    if t in [ListType,TupleType,DictionaryType]:
        return prepr(o)
    return str(o)

def _mkdir(path):
    if os.path.isdir(path):
        return
    path1,dir = os.path.split(path)
    if path1:
        _mkdir(path1)
    os.mkdir(path)

# --- TEST RUNNER

class TestRunner(xmlapp.Application):

    def __init__(self):
        xmlapp.Application.__init__(self)

    def handle_start_tag(self, name, attrs):
        if name == "TEST":
            id = attrs["ID"]
            file = attrs["URI"]

            _mkdir("out" + os.sep + os.path.split(file)[0])
            out = open("out" + os.sep + file, "w")
            #print >>sys.stderr,"Running",file
            logger = TestLogger(out)
            parser = xmlproc.XMLProcessor()
            parser.set_application(logger)
            parser.set_error_handler(logger)
            parser.set_pubid_resolver(logger)
            parser.set_dtd_listener(logger)
            parser.parse_resource(file)
            out.close()

            compare("baseline" + os.sep + file, "out" + os.sep + file)

# --- TEST LOGGER

class TestLogger(xmlapp.Application):

    def __init__(self, out):
        xmlapp.Application.__init__(self)
        self._out = out

    def doc_start(self):
        self._out.write("doc_start()\n")

    def doc_end(self):
        self._out.write("doc_end()\n")
	
    def handle_comment(self, data):
        self._out.write("handle_comment(%s)\n" % prepr(data))

    def handle_start_tag(self, name, attrs):
        attrs = attrs.items()
        attrs.sort()
        attrs = string.join(map(lambda pair: ("%s : %s" % (prepr(pair[0]),
                                                           prepr(pair[1]))),
                                attrs), ", ")
        self._out.write("handle_start_tag(%s, {%s})\n" % (pstr(name), attrs))

    def handle_end_tag(self,name):
        self._out.write("handle_end_tag(%s)\n" % pstr(name))
    
    def handle_data(self, data, start, end):
        self._out.write("handle_data(%s)\n" % prepr(data[start : end]))

    def handle_ignorable_data(self,data,start,end):
        self._out.write("handle_ignorable_data(%s)\n" %
                        repr(data[start : end]))
    
    def handle_pi(self,target,data):
        self._out.write("handle_pi(%s, %s)\n" % (target, prepr(data)))

    def handle_doctype(self, root, pubID, sysID):
        self._out.write("handle_doctype(%s, %s, %s)\n" % (pstr(root), pstr(pubID), pstr(sysID)))
    
    def set_entity_info(self, xmlver, enc, sddecl):
        self._out.write("set_entity_info(%s, %s, %s)\n" %
                        (xmlver, enc, sddecl))

    # ErrorHandler
        
    def warning(self, msg):
        self._out.write("warning(%s)\n" % prepr(msg))

    def error(self, msg):
        self._out.write("error(%s)\n" % prepr(msg))
    
    def fatal(self, msg):
        self._out.write("fatal(%s)\n" % prepr(msg))

    # PubIdResolver

    def resolve_pe_pubid(self, pubid, sysid):
        self._out.write("resolve_pe_pubid(%s, %s)\n" % (prepr(pubid),
                                                        prepr(sysid)))
        return sysid
    
    def resolve_doctype_pubid(self,pubid,sysid):
        self._out.write("resolve_doctype_pubid(%s, %s)\n" % (prepr(pubid),
                                                             prepr(sysid)))
        return sysid

    def resolve_entity_pubid(self,pubid,sysid):
        self._out.write("resolve_entity_pubid(%s, %s)\n" % (prepr(pubid),
                                                            prepr(sysid)))
        return sysid

    # DTDConsumer

    def dtd_start(self):
        self._out.write("dtd_start()\n")
    
    def dtd_end(self):
        self._out.write("dtd_end()\n")
    
    def new_general_entity(self,name,val):
        self._out.write("new_general_entity(%s, %s)\n" % (name, prepr(val)))

    def new_external_entity(self,name,pubid,sysid,ndata):
        self._out.write("new_external_entity(%s, %s, %s, %s)\n" %
                        (name, prepr(pubid), prepr(sysid), ndata))

    def new_parameter_entity(self,name,val):
        self._out.write("new_parameter_entity(%s, %s)\n" % (name, prepr(val)))
    
    def new_external_pe(self,name,pubid,sysid):
        self._out.write("new_external_pe(%s, %s, %s)\n" %
                        (name, prepr(pubid), prepr(sysid)))
	
    def new_notation(self,name,pubid,sysid):
        self._out.write("new_notation(%s, %s, %s)\n" %
                        (name, prepr(pubid), prepr(sysid)))

    def new_element_type(self,name,elem_cont):
        self._out.write("new_element_type(%s, %s)\n" % (pstr(name), pstr(elem_cont)))
	    
    def new_attribute(self,elem,attr,a_type,a_decl,a_def):
        self._out.write("new_attribute(%s, %s, %s, %s, %s)\n" %
                        (pstr(elem), attr, pstr(a_type), a_decl, prepr(a_def)))
    
    
# --- MAIN PROGRAM

parser = xmlproc.XMLProcessor()
parser.set_application(TestRunner())
parser.parse_resource("xmlconf.xml")
