# -*- coding: utf-8 -*-
"""
Created on Sat Jun  2 06:55:31 2018

@author: phnx
"""

# future
from __future__ import absolute_import

# standard
import unittest

# brat
from server.convert.ptbesc import escape, unescape


class TestPTBesc(unittest.TestCase):
    """
    server.convert.ptbesc unit tests
    """
    input_data = [('one life', 'one life'),
                  ('one day !', 'one day !'),
                  ('(doh!)', '-LRB-doh!-RRB-'),
                  ('(>>a<<)', '-LRB->>a<<-RRB-'),
                  ('[^]', '-LSB-^-RSB-'),
                  (u'été ça', u'été ça')]

    def test_escape(self):
        """
        test escape penn tree bank
        """
        for input_, expected in TestPTBesc.input_data:
            msg = 'escape(%r) -> %r (!= %r)' % (input_,
                                                escape(input_),
                                                expected)
            self.assertEquals(escape(input_),
                              expected,
                              msg)

    def test_unescape(self):
        """
        test unescape penn tree bank
        """
        for expected, input_ in TestPTBesc.input_data:
            msg = 'unescape(%r) -> %r (!= %r)' % (input_,
                                                  unescape(input_),
                                                  expected)
            self.assertEquals(unescape(input_),
                              expected,
                              msg)


if __name__ == "__main__":
    import sys
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestPTBesc)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
