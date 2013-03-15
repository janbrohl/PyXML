"""
This script runs regression tests on xvcmd.py and xpcmd.py.
"""

import os

testno=0
app="xvcmd.py"

def compare(basefile,testfile):
    try:
        bf=open(basefile)
    except:
        print "Basefile '%s' does not exist." % basefile
        return
    tf=open(testfile)

    pos=1
    bfch=bf.read(1)
    tfch=tf.read(1)
    while bfch!="" and tfch!="":
        if bfch!=tfch:
            print "ERROR: %s and %s disagree in pos %d (%s,%s)" %\
                  (basefile,testfile,pos,bfch,tfch)
            return
        bfch=bf.read(1)
        tfch=tf.read(1)
        pos=pos+1

    if bfch!=tfch:
        print "%s and %s disagree in pos %d (%s,%s)" %\
              (basefile,testfile,pos,bfch,tfch)

def make_option(option,value):
    if not value:
        return ""
    elif type(value)!=type("abc"):
        return option
    else:
        return "%s %s" % (option,value)

def run_test(catalog,language,format,ns,nowarn,url, options = ""):
    global testno
    testno=testno+1
    
    catalog=make_option("-c",catalog)
    language=make_option("-l",language)
    format=make_option("-o",format)
    ns=make_option("-n",ns)
    nowarn=make_option("--nowarn",nowarn)
    url=make_option("",url)

    cmd="%s %s %s %s %s %s %s %s > out%stest%d.txt" % \
        (app,catalog,language,format,ns,nowarn,url, options, os.sep, testno)
    #print cmd
    os.system(cmd)

    compare("baseline%stest%d.txt" % (os.sep, testno),
            "out%stest%d.txt" % (os.sep, testno))

def do_tests():
    # Test cases:
    if app=="xvcmd.py":
        # (1) modify os.environ to point to non-existent xcatalog (OK)
        os.environ["XMLXCATALOG"]="non-existent.xml"
        run_test(0,0,0,0,0,0)

        # (2) modify os.environ to point to non-existent socatalog (OK)
        os.environ["XMLXCATALOG"]=""
        os.environ["XMLSOCATALOG"]="non-existent.soc"
        run_test(0,0,0,0,0,0)

        # (3) make os.environ point to existent xcatalog without DOCUMENT entry (OK)
        os.environ["XMLXCATALOG"]="in/catalog.xml"
        run_test(0,0,0,0,0,0)

        # (4) use the xcatalog directly (OK)
        os.environ["XMLXCATALOG"]=""
        os.environ["XMLSOCATALOG"]=""
        run_test("in/catalog.xml",0,0,0,0,0)

        # (5) modify os.environ to point to existent socatalog with DOCUMENT entry (OK)
        os.environ["XMLSOCATALOG"]="in/catalog.soc"
        run_test(0,0,0,0,0,0)

        # (6) use the socatalog directly (OK)
        os.environ["XMLSOCATALOG"]=""
        run_test("in/catalog.soc",0,0,0,0,0)

        # (7) make os.environ point to existent socatalog without DOCUMENT entry (OK)
        os.environ["XMLSOCATALOG"]="in/catalog2.soc"
        run_test(0,0,0,0,0,0)

        # (8) use the socatalog (w/o) directly (OK)
        os.environ["XMLSOCATALOG"]=""
        run_test("in/catalog2.soc",0,0,0,0,0)

    # (9,32) try a norwegian fatal error (OK,OK)
    run_test(0,"no",0,0,0,"in/doc2.xml")

    # (10,33) try an english fatal error (OK,OK)
    run_test(0,"en",0,0,0,"in/doc2.xml")

    # (11,34) try a norwegian validity error (OK,OK)
    run_test(0,"no",0,0,0,"in/doc3.xml")

    # (12,35) try an english validity error (OK,OK)
    run_test(0,"en",0,0,0,"in/doc3.xml")

    # (13,36) try a norwegian warning (OK,OK)
    run_test(0,"no",0,0,0,"in/doc4.xml")

    # (14,37) try an english warning (OK,OK)
    run_test(0,"en",0,0,0,"in/doc4.xml")

    # (15,38) try document that causes warnings with nowarn (OK,OK)
    run_test(0,0,0,0,1,"in/doc4.xml")

    # (16,39) try an unsupported language (OK,OK)
    run_test(0,"uggabugga",0,0,0,"in/doc4.xml")

    # (17,40) try esis output (OK,OK)
    run_test(0,0,"e",0,0,"in/doc5.xml")

    # (18,41) try esis output with fatal error (OK,OK)
    run_test(0,0,"e",0,0,"in/doc2.xml")

    # (19,42) try canonxml output (OK,OK)
    run_test(0,0,"x",0,0,"in/doc5.xml")

    # (20,43) try canonxml output with fatal error (OK,OK)
    run_test(0,0,"x",0,0,"in/doc2.xml")

    # (21,44) try namespace processing on non-ns doc (OK,OK)
    run_test(0,0,"x",1,0,"in/doc5.xml")

    # (22,45) try namespace processing on ns doc (OK,OK)
    run_test(0,0,"x",1,0,"in/nstest2.xml")

    # (23,46) try namespace processing on ns doc with errors in english (OK,OK)
    run_test(0,0,"x",1,0,"in/nstest4.xml")

    # (24,47) try namespace processing on ns doc with errors in norwegian (OK)
    run_test(0,"no","x",1,0,"in/nstest4.xml")

    # (25,48) show entity stack on errors
    run_test("", 0, 0, 0, 0, "in/doc6.xml", "--entstck")

    # (26,49) show raw xml on errors
    run_test("", 0, 0, 0, 0, "in/doc6.xml", "--rawxml")
    
    if app=="xvcmd.py":
        # (27) try an erroneous xcatalog in norwegian (OK)
        run_test("in/catalog2.xml","no",0,0,0,0)

        # (28) try an erroneous xcatalog in english (OK)
        run_test("in/catalog2.xml",0,0,0,0,0)

        # (29) try an erroneous socatalog in norwegian (OK)
        run_test("in/catalog3.soc","no",0,0,0,0)

        # (30) try an erroneous socatalog in english (OK)
        run_test("in/catalog3.soc",0,0,0,0,0)

        # (31) try a syntactically invalid socatalog (OK)
        run_test("in/catalog4.soc",0,0,0,0,0)

    if app == "xpcmd.py":
        # (50) read external subset
        run_test("", 0, "x", 0, 0, "in/doc7.xml", "--extsub")
        
# --- Main program

print "Testing xvcmd.py"
do_tests() # for xvcmd.py
app="xpcmd.py"
print "Testing xpcmd.py"
do_tests() # again
