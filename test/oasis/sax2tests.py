#! /usr/bin/env python
"""
Conformance test engine for PyXML SAX2 parsers.
Based on "runtests.py" by LMG.

TODO:
    - Add output conformance checking

$Id: sax2tests.py,v 1.2 2001/09/01 01:14:14 jhermann Exp $
"""
__version__ = "$Revision: 1.2 $"[11:-2]

import getopt, string, os, time, types, sys, cStringIO
from xml.sax import handler, sax2exts
from xml.sax._exceptions import *

try:
    UnicodeType = types.UnicodeType
except ImportError:
    UnicodeType = -1 # fails compare to any type
from types import StringType, ListType, TupleType, \
     DictionaryType, NoneType


#############################################################################
### COMPARISON
#############################################################################

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


#############################################################################
### TEST LOGGER
#############################################################################

class TestResult(Exception):
    def __init__(self, type, exc):
        self.type = type
        self.exc = exc

    def __str__(self):
        return "%s: %s" % (self.type, str(self.exc))


class TestLogger(handler.ContentHandler, handler.ErrorHandler,
                 handler.DTDHandler, handler.EntityResolver):

    def __init__(self):
        handler.ContentHandler.__init__(self)
        self._out = cStringIO.StringIO()


    # ContentHandler

    def startDocument(self):
        self._out.write("doc_start()\n")

    def endDocument(self):
        self._out.write("doc_end()\n")

    def startElement(self, name, attrs):
        attrs = attrs.items()
        attrs.sort()
        attrs = string.join(map(lambda pair: ("%s : %s" % (prepr(pair[0]),
                                                           prepr(pair[1]))),
                                attrs), ", ")
        self._out.write("handle_start_tag(%s, {%s})\n" % (pstr(name), attrs))

    def endElement(self,name):
        self._out.write("handle_end_tag(%s)\n" % pstr(name))
    
    def characters(self, data):
        self._out.write("handle_data(%s)\n" % prepr(data))

    def ignorableWhitespace(self,data):
        self._out.write("handle_ignorable_data(%s)\n" %
                        repr(data))
    
    def processingInstruction(self,target,data):
        self._out.write("handle_pi(%s, %s)\n" % (target, prepr(data)))


    # ErrorHandler
        
    def warning(self, msg):
        raise TestResult('W', msg)

    def error(self, msg):
        raise TestResult('E', msg)
    
    def fatalError(self, msg):
        raise TestResult('F', msg)


#############################################################################
### TEST RUNNER
#############################################################################

class TestRunner(handler.ContentHandler):

    def __init__(self, suitedef, parserlist, quiet, strict):
        handler.ContentHandler.__init__(self)

        self.start = time.clock()
        self.suitedef = suitedef
        self.parserlist = parserlist.split(',')
        self.strict = strict
        self.quiet = quiet
        self.basedir = ''
        self.test_desc = ''
        self.has_namespaces = 1
        self.has_validation = 1
        self.problems = 0
        self.testcases = 0
        self.stats = {'LOW': 0, 'MED': 0, 'HI': 0}

    def run(self):
        self.parser = sax2exts.make_parser(self.parserlist)
        try:
            self.parser.setFeature(handler.feature_namespaces, 0)
        except SAXException:
            self.has_namespaces = 0
        try:
            self.parser.setFeature(handler.feature_validation, 1)
        except SAXException:
            self.has_validation = 0
        self.parser.setContentHandler(self)
        self.parser.parse(self.suitedef)

    def endDocument(self):
        print
        print '-' * 78
        print "Found %d (%d LOW / %d MED / %d HI) conformance violations in %d tests." % (
            self.problems, self.stats['LOW'], self.stats['MED'], self.stats['HI'],
            self.testcases)
        print "Needed %.3f secs to run the tests." % (time.clock() - self.start)

    def startElement(self, name, attrs):
        if name == "TESTSUITE":
            profile = attrs.getValue("PROFILE")
            print "=" * len(profile)
            print profile
            print "=" * len(profile)
            print
            print "Running this testsuite with", self.parser
        elif name == "TESTCASES":
            self.profile = attrs.getValue("PROFILE")
            self.basedir = ''
            if self.profile.startswith("Sun"):
                self.basedir = "sun"
        elif name == "TEST":
            self.test_attrs = attrs
            self.test_desc = ''

    def characters(self, data):
        self.test_desc += data

    def endElement(self, name):
        if name == "TEST":
            # run the test
            self.runTest(validate=0)
            if self.has_validation:
                self.runTest(validate=1)

    def runTest(self, **kw):
        validate = kw.get('validate', 0)
        self.testcases += 1

        # get attributes of test definition
        type = self.test_attrs.getValue("TYPE") # valid|invalid|not-wf|error
        entities = self.test_attrs.getValue("ENTITIES") # both|none|parameter|general
        id = self.test_attrs.getValue("ID")
        uri = self.test_attrs.getValue("URI")
        sections = self.test_attrs.getValue("SECTIONS")
        #output = self.test_attrs.getValue("OUTPUT")
        #output3 = self.test_attrs.getValue("OUTPUT3")

        # build path to test file
        file = os.path.normpath(uri)
        if self.basedir:
            file = os.path.join(self.basedir, uri)

        result = self.doParse(file, **kw)
        msg = ''
        severity = 'HI'
        if type == "valid":
            if result and result.type != "W":
                msg = "Error for valid file"
        elif type == "invalid":
            if validate:
                if not result or result.type == "W":
                    msg = "No error for invalid document reported"
                elif result.type != "E" and self.strict:
                    severity = 'LOW'
                    msg = "Error was not reported as recoverable"
            elif result and result != "W":
                severity = 'MED'
                msg = "Non-validating parser reported error for invalid document"
        elif type == "not-wf":
            if not result or result.type == "W":
                msg = "No error for non-wellformed document reported"
            elif result.type != "F" and self.strict:
                severity = 'LOW'
                msg = "Error was not reported as fatal"
        elif type == "error" and strict and not result:
            severity = 'LOW'
            msg = 'Optional error was not reported'

        # report result
        if not msg:
            if not self.quiet: sys.stderr.write('.')
        else:
            self.problems += 1
            self.stats[severity] += 1
            if not self.quiet: sys.stderr.write(result and result.type or '?')
        if not self.quiet: sys.stderr.flush()

        if msg:
            print
            print (("--- %s %s (cf. %s) " + "-" * 78) % (id, self.profile, sections))[:78]
            print "    %s" % self.test_desc.strip()
            print
            print "%3s %s" % (severity, msg)
            print "    %s" % (file,)
            print "    %s" % (result,)
            sys.stdout.flush()

    def doParse(self, file, **kw):
        validate = kw.get('validate', 0)

        logger = TestLogger()

        parser = sax2exts.make_parser(self.parserlist)
        if self.has_namespaces:
            # all testing w/o namespaces at the moment
            parser.setFeature(handler.feature_namespaces, 0)
        if self.has_validation:
            parser.setFeature(handler.feature_validation, validate)
        parser.setContentHandler(logger)
        parser.setErrorHandler(logger)
        parser.setEntityResolver(logger)
        parser.setDTDHandler(logger)

        try:
            parser.parse(file)
        except TestResult, result:
            return result
        except Exception, exc:
            return TestResult('X', exc)

        return None


#############################################################################
### MAIN PROGRAM
#############################################################################

def haveOptions(optlist, options):
    """ Check whether one of the options in "options" is in the list of
        options ("optlist") created from the command line
    """
    return filter(lambda flag, o=options: flag[0] in o, optlist) != []


def getOption(optlist, options):
    """ Get the value of the options in "options", from the list of
        options ("optlist") created from the command line
    """
    match = filter(lambda flag, o=options: flag[0] in o, optlist)
    if match:
        return match[-1][1]
    else:
        return ""


def usage():
    """ Print usage information.
    """
    sys.stderr.write("""
%(cmd)s v%(version)s, Copyright (c) 2001 by Jürgen Hermann <jh@web.de>

Usage: %(cmd)s [options] [testsuite] >results

Options:
    --help              This help text
    --version           Version information
    --parser            Comma-separated list of parsers (like $PY_SAX_PARSER)
    -s, --strict        No distinction between recoverable and fatal errors
    -q, --quiet         Be quiet (no progress indication)

""" % {'cmd': os.path.splitext(os.path.basename(sys.argv[0]))[0], 'version': __version__})
    sys.exit(1)


def version():
    """ Print version information.
    """
    sys.stderr.write("%s %s\n" % (
        os.path.splitext(os.path.basename(sys.argv[0]))[0], __version__))
    sys.exit(1)


if __name__ == "__main__":
    try:
        optlist, args = getopt.getopt(sys.argv[1:],
            'qs',
            ['help', 'parser=', 'quiet', 'strict', 'version'])
    except getopt.GetoptError:
        print >>sys.stderr, "Invalid arguments"
        sys.exit(1)

    #print optlist, args; sys.exit(1)

    parser = getOption(optlist, ["--parser"])
    quiet = haveOptions(optlist, ["-q", "--quiet"])
    strict = haveOptions(optlist, ["-s", "--strict"])
    if haveOptions(optlist, ["--version"]): version()
    if haveOptions(optlist, ["--help"]): usage()

    if not args: args = ["xmlconf.xml"]
    TestRunner(args[0], parser, quiet, strict).run()

