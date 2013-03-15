"""Generates the www.python.org website style
Adapted for use on offsite python.org locations
"""

import os
import string
import whrandom

from Skeleton import Skeleton
from Sidebar import Sidebar, BLANKCELL
from Banner import Banner
from HTParser import HTParser
from LinkFixer import LinkFixer



sitelinks = [
    ('http://www.python.org/',           'Home'),
    ('http://www.python.org/search/',    'Search'),
    ('http://www.python.org/download/',  'Download'),
    ('http://www.python.org/doc/',       'Documentation'),
    ('http://www.python.org/Help.html',  'Help'),
    ('http://www.python.org/psa/',       'Community'),
    ('http://www.python.org/sigs/',      'SIGs'),
#    ('%(rootdir)s/download/Contributed.html', 'Modules'),
    ]


class RemotePDOGenerator(Skeleton, Sidebar, Banner):
    AUTHOR = 'webmaster@python.org'

    def __init__(self, file, rootdir, relthis):
        fdir, fname = os.path.split(file)
        root, ext = os.path.splitext(fname)
        html = root + '.html'
        p = self.__parser = HTParser(file, self.AUTHOR)
        f = self.__linkfixer = LinkFixer(html, rootdir, relthis)
        self.__body = None
        self.__cont = None
        # calculate the sidebar links, adding a few of our own
        self.__d = {'rootdir': rootdir}
        p.process_sidebar()
        p.sidebar.append(BLANKCELL)
        # it is important not to have newlines between the img tag and the end
        # end center tags, otherwise layout gets messed up
        p.sidebar.append((None, '''
<center><a href='http://www.python.org'>
    <img border=0 src="http://www.python.org/pics/PythonPoweredSmall.gif" alt="Python Powered"></a></center>
''' % self.__d))
        self.__linkfixer.massage(p.sidebar, self.__d)
        Sidebar.__init__(self, p.sidebar)
        #
        # fix up our site links, no relthis because the site links are
        # relative to the root of our web pages
        #
        sitelink_fixer = LinkFixer(f.myurl(), rootdir)
        sitelink_fixer.massage(sitelinks, self.__d, aboves=1)
        Banner.__init__(self, sitelinks)
        # calculate the random corner
        # XXX Should really do a list of the pics directory...
        NBANNERS = 64
        i = whrandom.randint(0, NBANNERS-1)
        s = "PyBanner%03d.gif" % i
        self.__d['banner'] = s
        self.__whichbanner = i

    def get_meta(self):
        return self.__parser.get('meta', '')

    def get_title(self):
        return self.__parser.get('title')

    def get_sidebar(self):
        if string.lower(self.__parser.get('wide-page', 'no')) == 'yes':
            return None
        return Sidebar.get_sidebar(self)

    def get_banner(self):
        return Banner.get_banner(self)

    def get_banner_attributes(self):
        return 'CELLSPACING=0 CELLPADDING=0'

    def get_corner(self):
        # it is important not to have newlines between the img tag and the end
        # anchor and end center tags, otherwise layout gets messed up
        return '''
<center>
    <a href="http://www.python.org/">
    <img border=0 src="http://www.python.org/pics/%(banner)s" alt="banner"></a></center>''' % \
    self.__d 

    def get_corner_bgcolor(self):
        # this may not be 100% correct.  it uses PIL to get the RGB values at
        # the corners of the image and then takes a vote as to the most likely
        # value.  Some images may be `bizarre'.  See .../pics/backgrounds.py
        return [
             '#3399ff',  '#6699cc',  '#3399ff',  '#0066cc',  '#3399ff', 
             '#0066cc',  '#0066cc',  '#3399ff',  '#3399ff',  '#3399ff', 
             '#3399ff',  '#6699cc',  '#3399ff',  '#3399ff',  '#ffffff', 
             '#6699cc',  '#0066cc',  '#3399ff',  '#0066cc',  '#3399ff', 
             '#6699cc',  '#0066cc',  '#6699cc',  '#3399ff',  '#3399ff', 
             '#6699cc',  '#3399ff',  '#3399ff',  '#6699cc',  '#6699cc', 
             '#0066cc',  '#6699cc',  '#0066cc',  '#6699cc',  '#0066cc', 
             '#0066cc',  '#6699cc',  '#3399ff',  '#0066cc',  '#bbd6f1', 
             '#0066cc',  '#6699cc',  '#3399ff',  '#3399ff',  '#0066cc', 
             '#0066cc',  '#0066cc',  '#6699cc',  '#6699cc',  '#3399ff', 
             '#3399ff',  '#6699cc',  '#0066cc',  '#0066cc',  '#6699cc', 
             '#0066cc',  '#6699cc',  '#3399ff',  '#6699cc',  '#3399ff', 
             '#d6ebff',  '#6699cc',  '#3399ff',  '#0066cc',
             ][self.__whichbanner]

    def get_body(self):
        self.__grokbody()
        return self.__body

    def get_cont(self):
        self.__grokbody()
        return self.__cont

    def __grokbody(self):
        if self.__body is None:
            text = self.__parser.fp.read()
            i = string.find(text, '<!--table-stop-->')
            if i >= 0:
                self.__body = text[:i]
                self.__cont = text[i+17:]
            else:
                # there is no wide body
                self.__body = text

    # python.org color scheme overrides
    def get_lightshade(self):
        return '#99ccff'

    def get_mediumshade(self):
        return '#3399ff'

    def get_darkshade(self):
        return '#003366'
