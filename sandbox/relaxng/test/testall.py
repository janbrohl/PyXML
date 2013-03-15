
# Script to run the entire test suite

# Add the directory containing the code to Python's path
import sys ; sys.path.insert(0, '..')

import os, glob

from xml.dom.ext.reader import PyExpat

import fullparser, util

# Directory where the RELAX NG test suite has been unpacked.  The
# value below assumes that you've checked out the 'test' module from
# CVS.
RELAXNG_DIR = '../../../test/relaxng'

# Tests to skip
SKIPPED_TESTS = (
                 # Ones with externalRef
                 #[100, 101, 102, 103, 104, 105, 106, 107, 108, 124] +
                 # Ones with include
                 [45, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118,
                  119, 120] +
		 # Ones that use datatypes
		 [95, 99, 137, 141, 253, 254, 255, 257, 258, 261, 262,
		  263, 265, 266, 269, 270, 271, 272, 273, 274, 279, 280,
		  281, 283]
                )

# Verbosity flag
verbose = 0

# 'Correct' and 'incorrect' tests refers to whether the schema in the
# test is valid or invalid, not whether our RELAX NG engine actually runs
# them correctly, which is termed 'success' or 'failure'.

total_incorrect_tests = 0
incorrect_tests_succeeded = 0
total_correct_tests = 0
correct_tests_succeeded = 0

def run_test_dir  (path):
    global total_incorrect_tests, total_correct_tests
    global incorrect_tests_succeeded, correct_tests_succeeded
    contents = os.listdir(path)
    contents.sort()
    parser = fullparser.RelaxNGParser()
    if 'i.rng' in contents:
        total_incorrect_tests += 1
        filename = os.path.join(path, 'i.rng')
        stream = open(filename)
        try:
            schema = parser.parse(stream, filename)
        except RuntimeError:
            # We reported an error
            print 'ok'
            incorrect_tests_succeeded += 1
        except:
            # Unexpected exception
            typ, value, traceback = sys.exc_info()
            print 'unexpected exception on parse: %s %s' % (typ, value)
        else:
            # Nothing reported
            print 'no error reported on parse'

    else:
        # Assume it's a correct test
        total_correct_tests += 1
        filename = os.path.join(path, 'c.rng')
        stream = open(filename)
        try:
            schema = parser.parse(stream, filename)
        except RuntimeError:
            # We reported an error
            print 'parse error'
            return
        except RuntimeError:
            # Unexpected exception
            typ, value, traceback = sys.exc_info()
            print 'unexpected exception on parse: %s' % typ
            return

        # Nothing reported
        print 'parse ok,',
        correct_tests_succeeded += 1

        # Try validating various files
        valid_ok = 1
        for filename in contents:
            if not filename.endswith('.xml'):
                continue
            total_correct_tests += 1

            # Read the document to be validated
            stream = open(os.path.join(path, filename))
            document = util.get_rng_document(stream)

            # Validate it
            try:
                result = schema.is_valid(document)
            except:
                typ, value, traceback = sys.exc_info()
                print 'unexpected exception on %s: %s, %s' % (filename, typ,
                                                              value)
                valid_ok = 0
            else:
                if filename.find('.v.') == -1:
                    # Input file expected to be invalid
                    if result:
                        print 'not reported as invalid: %s' % filename
                        valid_ok = 0
                    else:
                        correct_tests_succeeded += 1
                else:
                    # Input file expected to be valid
                    if not result:
                        print 'not reported as valid: %s' % filename
                        valid_ok = 0
                    else:
                        correct_tests_succeeded += 1
                    
        if valid_ok: 
            print 'validation ok'
            
def main ():
    if len(sys.argv) > 1:
        L = [os.path.join(RELAXNG_DIR, '%03i' % int(dir_num))
             for dir_num in sys.argv[1:]]
    else:
        L = glob.glob(os.path.join(RELAXNG_DIR, '[012][0-9][0-9]'))
        L.sort()
    for dir in L:
        dir_num = int(dir[-3:])
        if dir_num in SKIPPED_TESTS:
            continue
        print '%-3i ...' % dir_num,
        result = run_test_dir(dir)

    print
    print 'Results:'
    print ('Incorrect tests: %i of %i (%2.0f%%) succeeded' %
           (incorrect_tests_succeeded,
            total_incorrect_tests,
            100.0*incorrect_tests_succeeded/(total_incorrect_tests or 1)))
    print ('Correct tests:   %i of %i (%2.0f%%) succeeded' %
           (correct_tests_succeeded,
            total_correct_tests,
            100.0*correct_tests_succeeded/(total_correct_tests or 1)))
           

if __name__ == '__main__':
    main()
