#! /usr/bin/env python
"""
Conformance test engine for PyXML SAX2 parsers.
Based on "runtests.py" by LMG.

TODO:
    - Add output conformance checking

$Id: sax2tests.py,v 1.8 2001/09/06 23:13:11 jhermann Exp $
"""
__version__ = "$Revision: 1.8 $"[11:-2]

import getopt, string, os, time, types, sys, cStringIO
from xml.sax import handler, sax2exts, saxutils, xmlreader
from xml.sax._exceptions import *


#############################################################################
### HELPERS
#############################################################################

def ISOTime(t=None):
    """Return (the current) date and time in ISO format."""
    if not t: t = time.time()
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


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
        #self._out = cStringIO.StringIO()


    # ContentHandler

    def startDocument(self):
        pass

    def endDocument(self):
        pass

    def startElement(self, name, attrs):
        pass

    def endElement(self, name):
        pass
    
    def characters(self, data):
        pass

    def ignorableWhitespace(self, data):
        pass
    
    def processingInstruction(self, target, data):
        pass


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

class TestReport(saxutils.XMLGenerator):
    def __init__(self):
        saxutils.XMLGenerator.__init__(self)

    def docType(self, root, pubid, sysid):
        self._out.write('<!DOCTYPE %s ' % root)
        if pubid:
            self._out.write('PUBLIC "%s" "%s"' % (pubid, sysid,))
        else:
            self._out.write('SYSTEM "%s"' % (sysid,))
        self._out.write('>\n')

    def textElement(self, tag, text):
        self.startElement(tag, xmlreader.AttributesImpl({}))
        self.characters(text)
        self.endElement(tag)

    def memo(self, text):
        self.startElement("MEMO", xmlreader.AttributesImpl({}))
        self.characters(text)
        self.endElement("MEMO")

    def startElement(self, name, attrs):
        saxutils.XMLGenerator.startElement(self, name, attrs)
        if name not in ['PARSER', 'HARNESS', 'PLATFORM',
                        'RUNTIME', 'TEST', 'MEMO', 'B', 'EM']:
            self.ignorableWhitespace("\n")

    def endElement(self, name):
        saxutils.XMLGenerator.endElement(self, name)
        if name not in ['B', 'EM']:
            self.ignorableWhitespace("\n")


class TestRunner(handler.ContentHandler):

    result_types = {
        'X': 'EXCEPTION',
        'W': 'WARNING',
        'E': 'ERROR',
        'F': 'FATAL ERROR',
    }
    xml_severities = {
        '': 'success',
        'LOW': 'low',
        'MED': 'medium',
        'HI': 'high',
    }

    def __init__(self, suitedef, parserlist, validate, quiet, strict):
        handler.ContentHandler.__init__(self)

        self.start = time.clock()
        self.suitedef = suitedef
        if parserlist:
            self.parserlist = parserlist.split(',')
        else:
            self.parserlist = []
        self.validate = validate
        self.strict = strict
        self.quiet = quiet
        self.basedirs = []
        self.in_test = 0
        self.test_desc = ''
        self.has_namespaces = 1
        self.has_validation = 1
        self.problems = 0
        self.testcases = 0
        self.stats = {'LOW': 0, 'MED': 0, 'HI': 0}

        self.report = TestReport()

        #print self.parserlist

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
            if self.validate == 'yes':
                print >>sys.stderr, "Parser is non-validating!!!"
                sys.exit(1)
        self.parser.setContentHandler(self)
        self.parser.parse(self.suitedef)

    def startDocument(self):
        self.report.startDocument()
        self.report.docType('REPORT', None, 'testresults.dtd')

    def endDocument(self):
        self.report.endDocument()

    def startElement(self, name, attrs):
        if name == "TESTSUITE":
            ra = attrs._attrs.copy()
            ra["DATE"] = ISOTime()
            self.report.startElement("REPORT", xmlreader.AttributesImpl(ra))
            parsername = str(self.parser)
            if parsername[0] == "<":
                parsername = parsername[1:].split()[0]
            self.report.textElement("PARSER", parsername)
            self.report.textElement("HARNESS", "%s %s" % (
                os.path.splitext(os.path.basename(sys.argv[0]))[0], __version__))
            self.report.textElement("PLATFORM", "%s / %s" % (os.name, sys.platform))
            runtime = "Python %s" % sys.version
            try:
                from xml import version_info
                runtime += " / PyXML %s" % ('.'.join(map(str, version_info)))
            except ImportError:
                pass
            self.report.textElement("RUNTIME", runtime)
            self.report.memo("Validation mode is '%s'" % self.validate)
            if self.strict:
                self.report.memo("Running in strict mode")
        elif name == "TESTCASES":
            self.profile = attrs.getValue("PROFILE")
            if attrs.has_key("xml:base"):
                self.basedirs.append(attrs.getValue("xml:base"))
            else:
                self.basedirs.append('')
        elif name == "TEST":
            self.test_attrs = attrs
            self.in_test = 1
            self.report.startElement("TESTRESULT", xmlreader.AttributesImpl({
                'PROFILE': self.profile,
                }))
            self.report.startElement(name, attrs)
        elif self.in_test:
            self.report.startElement(name, attrs)

    def characters(self, data):
        if self.in_test:
            self.report.characters(data)

    def endElement(self, name):
        if name == "TESTSUITE":
            self.report.memo("Found %d (%d LOW / %d MED / %d HI) conformance violations in %d tests." % (
                self.problems, self.stats['LOW'], self.stats['MED'], self.stats['HI'],
                self.testcases))
            self.report.memo("Needed %.3f secs to run the tests." % (time.clock() - self.start))
            self.report.endElement("REPORT")
        elif name == "TESTCASES":
            del self.basedirs[-1]
        elif name == "TEST":
            self.report.endElement(name)

            # run the test
            if self.validate != 'yes':
                self.runTest(validate=0)
            if self.validate != 'no' and self.has_validation:
                self.runTest(validate=1)
            self.report.endElement("TESTRESULT")
            self.in_test = 0
        elif self.in_test:
            self.report.endElement(name)

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
        path = filter(None, self.basedirs) + uri.split('/')
        file = os.path.join(*tuple(path))

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

        # report result to stderr
        if not msg:
            if not self.quiet: sys.stderr.write('.')
        else:
            self.problems += 1
            self.stats[severity] += 1
            if not self.quiet: sys.stderr.write(result and result.type or '?')
        if not self.quiet: sys.stderr.flush()

        # emit XML result
        if not msg: severity = ''
        self.report.startElement("TESTRUN", xmlreader.AttributesImpl({
            'PARSER-TYPE': ('non-validating','validating')[validate],
            'SEVERITY': self.xml_severities[severity],
            }))

        if msg:
            self.report.characters(msg)
            self.report.characters('\n')
            if result:
                self.report.startElement("B", xmlreader.AttributesImpl({}))
                self.report.characters(self.result_types[result.type])
                self.report.endElement("B")
                self.report.characters(':\n')
                self.report.characters(str(result.exc))
                self.report.characters('\n')

        self.report.endElement("TESTRUN")

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


def usage(msg = None):
    """ Print usage information.
    """
    if msg: sys.stderr.write(msg + '\n')

    sys.stderr.write("""
%(cmd)s v%(version)s, Copyright (c) 2001 by Jürgen Hermann <jh@web.de>

Usage: %(cmd)s [options] [testsuite] >results

Options:
    --help              This help text
    --version           Version information
    --parser            Comma-separated list of parsers (like $PY_SAX_PARSER)
    -v, --validate      Validation mode (no/yes/both, default both)
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
            'qs-v:',
            ['help', 'parser=', 'quiet', 'strict', 'validate=', 'version'])
    except getopt.GetoptError:
        usage("Invalid arguments")

    #print optlist, args; sys.exit(1)

    parser = getOption(optlist, ["--parser"])
    validate = getOption(optlist, ["-v", "--validate"]) or "both"
    quiet = haveOptions(optlist, ["-q", "--quiet"])
    strict = haveOptions(optlist, ["-s", "--strict"])
    if haveOptions(optlist, ["--version"]): version()
    if haveOptions(optlist, ["--help"]): usage()
    if validate not in ['no', 'yes', 'both']: usage("'validate' must be no, yes or both")

    if not args: args = ["xmlconf.xml"]
    TestRunner(args[0], parser, validate, quiet, strict).run()

