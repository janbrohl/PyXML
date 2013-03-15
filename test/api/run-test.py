
### Regression testing script for xmlproc. Tests as many aspects of
### the various APIs as possible.

import sys
from xml.parsers.xmlproc import xmlproc, xmlval, xmlapp
import string, urllib

# --- Escapement functions

def data_escape(data):
    return string.replace(data,"\n","&#10;")

def compare(basefile, testfile):
    try:
        bf = open(basefile)
    except:
        print "Basefile '%s' does not exist." % basefile
        return
    tf = open(testfile)

    pos = 1
    bfch = bf.read(1)
    tfch = tf.read(1)
    while bfch != "" and tfch != "":
        if bfch != tfch:
            print "ERROR: %s and %s disagree in pos %d (%s,%s)" % \
                  (basefile, testfile, pos, bfch, tfch)
            return
        bfch = bf.read(1)
        tfch = tf.read(1)
        pos = pos+1

    if bfch != tfch:
        print "%s and %s disagree in pos %d (%s,%s)" % \
              (basefile, testfile, pos, bfch, tfch)

# --- The logging class

class Logger(xmlapp.Application, xmlapp.ErrorHandler):

    def __init__(self,out):
        self.out = out

    # Application
        
    def doc_start(self):
        self.out.write("doc_start()\n")

    def doc_end(self):
        self.out.write("doc_end()\n")

    def handle_comment(self,data):
        self.out.write("handle_comment('%s')\n" % data)

    def handle_start_tag(self,name,attrs):
        self.out.write("handle_start_tag(%s,[" % name)
        for item in attrs.items():
            self.out.write("'%s','%s'" % item)
        self.out.write("])\n")

    def handle_end_tag(self,name):
        self.out.write("handle_end_tag('%s')\n" % name)

    def handle_data(self,data,start,end):
        self.out.write("handle_data('%s')\n" % data_escape(data[start:end]))

    def handle_ignorable_data(self,data,start,end):
        self.out.write("handle_ignorable_data('%s')\n" % \
                       data_escape(data[start:end]))

    def handle_pi(self,target,data):
        self.out.write("handle_pi('%s','%s')\n" % (target,data))

    def handle_doctype(self,root,pubid,sysid):
        self.out.write("handle_doctype('%s','%s','%s')\n" % (root,pubid,sysid))

    def set_entity_info(self,xmlver,enc,sddecl):
        self.out.write("set_entity_info('%s','%s','%s')\n" % (xmlver,enc,
                                                              sddecl))

    # ErrorHandler
        
    def warning(self,msg):
        self.out.write("warning('%s')\n" % msg)

    def error(self,msg):
        self.out.write("error('%s')\n" % msg)

    def fatal(self,msg):
        self.out.write("fatal('%s')\n" % msg)

    # PubIdResolver
        
    def resolve_pe_pubid(self, pubid, sysid):
        self.out.write("resolve_pe_pubid('%s', '%s')\n" % (pubid, sysid))
        return sysid
    
    def resolve_doctype_pubid(self, pubid, sysid):
        self.out.write("resolve_doctype_pubid('%s', '%s')\n" % (pubid, sysid))
        return sysid

    def resolve_entity_pubid(self, pubid, sysid):
        self.out.write("resolve_entity_pubid('%s', '%s')\n" % (pubid, sysid))
        return sysid

    # InputSourceFactory

    def create_input_source(self, sysid):
        self.out.write("create_input_source('%s')\n" % sysid)
        
        if sysid[1:3]==":/":
            return open(sysid)
        else:
            return urllib.urlopen(sysid)

    # DTDConsumer

    def dtd_start(self):
        self.out.write("dtd_start()\n")
        
    def dtd_end(self):
        self.out.write("dtd_end()\n")
    
    def new_general_entity(self, name, val):
        self.out.write("new_general_entity('%s', '%s')\n" % (name, val))

    def new_external_entity(self, ent_name, pub_id, sys_id, ndata):
        self.out.write("new_external_entity('%s', '%s', '%s', '%s')\n" %
                       (ent_name, pub_id, sys_id, ndata))

    def new_parameter_entity(self, name, val):
        self.out.write("new_parameter_entity('%s', '%s')\n" % (name, val))
    
    def new_external_pe(self,name,pubid,sysid):
        self.out.write("new_external_pe('%s', '%s', '%s')\n" %
                       (name, pubid, sysid))
	
    def new_notation(self, name, pubid, sysid):
        self.out.write("new_notation('%s', '%s', '%s')\n" %
                       (name, pubid, sysid))

    def new_element_type(self, elem_name, elem_cont):
        self.out.write("new_element_type('%s', %s)\n" % (elem_name, elem_cont))
	    
    def new_attribute(self, elem, attr, a_type, a_decl, a_def):
        self.out.write("new_attribute('%s', '%s', '%s', '%s', '%s')\n" %
                       (elem, attr, a_type, a_decl, a_def))
    
    
def test_driver(parser,raw_dir,to_dir,old_dir):
    """Parses all files in raw_dir with parser, putting the logs in to_dir
    and comparing them to the corresponding files in old_dir."""

    for file in glob.glob(raw_dir+"/*.xml"):
        #1: Run xmlproc to produce an output file
        
        fncomps=string.split(file,"/")
        outfile=open(to_dir+"/"+fncomps[-1],"w")

        log=Logger(outfile)
        parser.reset()
        parser.set_data_after_wf_error(0)
        parser.set_application(log)
        parser.set_error_handler(log)
        parser.parse_resource(file)
        
        outfile.close()

        #2: Compare the output file with an old one
        compare(old_dir+"/"+fncomps[-1],to_dir+"/"+fncomps[-1])

# --- Main program

# Produce events with non-validating, without reading external subset

outf = open("out/nvp-no-extdtd.txt", "w")
log = Logger(outf)

parser = xmlproc.XMLProcessor()
parser.set_data_after_wf_error(0)
parser.set_application(log)
parser.set_error_handler(log)
parser.set_pubid_resolver(log)
parser.set_inputsource_factory(log)
parser.set_dtd_listener(log)
parser.parse_resource("docs/doc.xml")

outf.close()
compare("base/nvp-no-extdtd.txt", "out/nvp-no-extdtd.txt")

# Produce events with non-validating, when reading external subset

outf = open("out/nvp-extdtd.txt", "w")
log = Logger(outf)

parser = xmlproc.XMLProcessor()
parser.set_data_after_wf_error(0)
parser.set_application(log)
parser.set_error_handler(log)
parser.set_pubid_resolver(log)
parser.set_inputsource_factory(log)
parser.set_dtd_listener(log)
parser.set_read_external_subset(1)
parser.parse_resource("docs/doc.xml")

outf.close()
compare("base/nvp-extdtd.txt", "out/nvp-extdtd.txt")

# Produce events with validating parser

outf = open("out/validating.txt", "w")
log = Logger(outf)

parser = xmlval.XMLValidator()
parser.set_data_after_wf_error(0)
parser.set_application(log)
parser.set_error_handler(log)
parser.set_pubid_resolver(log)
parser.set_inputsource_factory(log)
parser.set_dtd_listener(log)
parser.set_read_external_subset(1)
parser.parse_resource("docs/doc.xml")

outf.close()
compare("base/validating.txt", "out/validating.txt")

