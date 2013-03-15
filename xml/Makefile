# Convenience make rules to help run the build/tests for several
# Python versions.  Edit to suit your choice of Python versions.

PLAT=$(shell python -c 'from distutils import util; print util.get_platform()')
DEFVERSION=$(shell python -c 'import sys; print sys.version[:3]')
LIBPREFIX=../build/lib.$(PLAT)

# Always build pyexpat, since PyXML contains a more advanced version
# of the extension, and binary distributions cannnot determine whether
# a version is included with the Python available on the target.
#
BUILDARGS=

.PHONY:	build

all:	build
test:	check

build:
	python setup.py $(BUILDARGS) -q build

check:	build
	cd test && PYTHONPATH=$(LIBPREFIX)-$(DEFVERSION) python testxml.py

buildall:
	python2.3 setup.py $(BUILDARGS) -q build
	python2.4 setup.py $(BUILDARGS) -q build

checkall:	buildall
	cd test && PYTHONPATH=$(LIBPREFIX)-2.3 python2.3 testxml.py
	cd test && PYTHONPATH=$(LIBPREFIX)-2.4 python2.4 testxml.py

clean:
	rm -rf build
