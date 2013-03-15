
# Demonstration driver for the RELAX-NG processing code

import glob, os, StringIO, sys
from xml.dom.ext.reader import PyExpat

import relaxng, fullparser, util


DOCUMENT = """<?xml version="1.0"?>
<root>
  <child name="foo">abc</child>
</root>
"""

TEST_DOCUMENT = """<?xml version="1.0"?>
<root>
  <?proc inst?>
  <child_alt attr="goofy"/>
  <b/><a/>
  <child3 attr="goofy"/>
string
</root>
"""


def test_pattern ():
    # Read the document to be validated
    reader = PyExpat.Reader()
    stream = StringIO.StringIO(TEST_DOCUMENT)
    document = reader.fromStream(stream)
    document.normalize()
    
    # Create the schema object
    schema = relaxng.make_test_schema()

    # Validate it
    result = schema.is_valid(document)
    if result:
        print 'Document is valid'
    else:
        print 'Document is not valid'
    
def main():
    if len(sys.argv) == 2:
        try:
            test_num = int(sys.argv[1])
        except ValueError:
            pass
        else:
            dir = '../../test/relaxng/%03i/' % test_num
            schema = glob.glob(os.path.join(dir, '*.rng'))
            xml_files = glob.glob(os.path.join(dir, '*.xml'))
            sys.argv = sys.argv[0:1] + schema + xml_files
        
    # Read the schema
    stream = open(sys.argv[1])
    parser = fullparser.RelaxNGParser()
    schema = parser.parse(stream, sys.argv[1])
    print '================='
    schema.dump()
    print '================='
    
    # No file to validate supplied, so just return
    if len(sys.argv) < 3:
        return

    # Read the documents to be validated
    for filename in sys.argv[2:]:
        stream = open(filename)
        document = util.get_rng_document(stream)

        # Validate it
        result = schema.is_valid(document)
        print filename, ':',
        if result:
            print 'Document is valid'
        else:
            print 'Document is not valid'

if __name__ == '__main__':
    main()
    
