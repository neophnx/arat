# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 10:58:39 2018

@author: phnx
"""
from __future__ import absolute_import
import unittest

from server import annotator as ant
from server.common import ProtocolArgumentError


class TestAnnotator(unittest.TestCase):
    """
    Test annotator
    """

    def test__offsets_equal(self):
        # common cases
        self.assertTrue(ant._offsets_equal([], []))
        self.assertTrue(ant._offsets_equal([(1, 1)], [(1, 1)]))
        self.assertTrue(ant._offsets_equal([(0, 1), (3, 5)],
                                           [(0, 1), (3, 5)]))
        self.assertFalse(ant._offsets_equal([(0, 1), (3, 5)],
                                            [(0, 1), (3, 6)]))

        # unorderd list of offsets
        self.assertTrue(ant._offsets_equal([(0, 1), (3, 5)],
                                           [(3, 5), (0, 1)]))
        self.assertFalse(ant._offsets_equal([(0, 1), (3, 5)],
                                            [(3, 6), (0, 1)]))

        # repetition
        self.assertTrue(ant._offsets_equal([(0, 1), (3, 5)],
                                           [(3, 5), (0, 1), (0, 1)]))
        self.assertFalse(ant._offsets_equal([(0, 1), (3, 5)],
                                            [(3, 6), (0, 1), (0, 1)]))

        # overlap
        self.assertTrue(ant._offsets_equal([(0, 5)],
                                           [(3, 5), (0, 3)]))
        self.assertFalse(ant._offsets_equal([(0, 5)],
                                            [(3, 6), (0, 3)]))

    def test__text_for_offsets(self):

        # common case
        self.assertEquals(ant._text_for_offsets("Welcome home!",
                                                [(0, 2), (8, 10)]),
                          "We ho")

        # overlap
        self.assertEquals(ant._text_for_offsets("Welcome home!",
                                                [(0, 2), (0, 1)]),
                          "We")

        # out of bounds
        self.assertRaises(ProtocolArgumentError,
                          ant._text_for_offsets,
                          "Welcome home!",
                          [(-10, 2), (0, 1)])

        self.assertRaises(ProtocolArgumentError,
                          ant._text_for_offsets,
                          "Welcome home!",
                          [(0, 2), (0, 100)])


if __name__ == "__main__":
    import sys
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestAnnotator)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
