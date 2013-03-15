import unittest
from os.path import dirname, abspath, join
from xml.sax.saxutils import escape, absolute_system_id

class EscapeTC(unittest.TestCase):

    def test(self):
        v1, v2 = escape('&<>'), '&amp;&lt;&gt;'
        self.assertEquals(v1, v2)
        v1, v2 = escape('foo&amp;bar'), 'foo&amp;amp;bar'
        self.assertEquals(v1, v2)
        v1, v2 = escape('< test > &', {'test': '&myentity;'}), '&lt; &myentity; &gt; &amp;'
        self.assertEquals(v1, v2)
        v1, v2 = escape('&\'"<>', {'"': '&quot;', "'": '&apos;'}), '&amp;&apos;&quot;&lt;&gt;'
        self.assertEquals(v1, v2)
        

TEST_DIR = abspath(dirname(__file__)) + '/'

class AbsoluteSystemIdTC(unittest.TestCase):

    def test_base(self):
        res = absolute_system_id('http://www.xml.com')
        self.assertEquals(res, 'http://www.xml.com')
        
        res = absolute_system_id('http://www.xml.com', 'http://whatever')
        self.assertEquals(res, 'http://www.xml.com')
        
        res = absolute_system_id('quotes.xml')
        self.assertEquals(res, 'file://%s' % join(TEST_DIR, 'quotes.xml'))


    def test_relative(self):
        # FIXME: empty authority // added by MakeUrlLibSafe (actually by
        # urlunsplit), which is probably acceptable since the sysid is designed
        # to be used by urlopen
        
        res = absolute_system_id('quotes.xml', 'file:%s' % TEST_DIR)
        self.assertEquals(res, 'file://%squotes.xml' % TEST_DIR)
        
        res = absolute_system_id('relative.xml', 'file:/base')
        self.assertEquals(res, 'file:///relative.xml')
        
        res = absolute_system_id('relative.xml', 'file:/base/')
        self.assertEquals(res, 'file:///base/relative.xml') 
        
        res = absolute_system_id('file:relative.xml', 'file:/base')
        self.assertEquals(res, 'file:///relative.xml')

        
    def test_no_base_scheme(self):
        # FIXME: warning ?
        self.assertRaises(ValueError, absolute_system_id, 'file:relative.xml', '/base')

if __name__ == '__main__':
    unittest.main()
