# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 10:58:39 2018

@author: phnx
"""
from __future__ import absolute_import
import unittest

from arat.server import tokenise
from arat.server.message import Messager


class TestTokenise(unittest.TestCase):
    """
    Test tokeniser
    """
    TEXT = u"Specialized tokenizer for this p65(RelA)/p50 and that E. coli"

    def test_gtb_token_boundary_gen(self):
        """
        gtb_token_boundary_gen
        """
        self.assertEquals(list(tokenise.gtb_token_boundary_gen(self.TEXT)),
                          [(0, 11), (12, 21), (22, 25),
                           (26, 30), (31, 44), (45, 48),
                           (49, 53), (54, 56), (57, 61)])

    def test_whitespace(self):
        """
        whitespace_token_boundary_gen
        """
        self.assertEquals(list(tokenise.whitespace_token_boundary_gen(self.TEXT)),
                          [(0, 11), (12, 21), (22, 25),
                           (26, 30), (31, 44), (45, 48),
                           (49, 53), (54, 56), (57, 61)])

    def test_tokeniser_by_name(self):
        """
        tokeniser_by_name
        """
        self.assertEquals(tokenise.tokeniser_by_name('whitespace'),
                          tokenise.whitespace_token_boundary_gen)
        self.assertEquals(tokenise.tokeniser_by_name('ptblike'),
                          tokenise.gtb_token_boundary_gen)

        # check that no messsage has been published
        self.assertEquals(Messager.output_json({}),
                          {'messages': []})

        # Any other name will returns default whitespace
        # and leave a message
        self.assertEquals(tokenise.tokeniser_by_name('invalid!'),
                          tokenise.whitespace_token_boundary_gen)
        self.assertEquals(Messager.output_json({}),
                          {'messages': [('Unrecognized tokenisation option , '
                                         'reverting to whitespace '
                                         'tokenisation.', 'warning', 3)]})


if __name__ == "__main__":
    import sys
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestTokenise)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
