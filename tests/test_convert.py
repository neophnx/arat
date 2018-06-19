# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 10:58:39 2018

@author: phnx
"""
from __future__ import absolute_import
import unittest

from server.convert import convert
from tests.test_stanford import TestStanford


class TestConvert(unittest.TestCase):
    """
    Test convert
    """

    def test_invalid_src_format(self):
        """
        InvalidSrcFormat
        """
        value = convert.InvalidSrcFormat("invalid!")
        self.assertEquals(str(value),
                          "Invalid convert src fomat: 'invalid!`")

    def test_convert_stanford_pos(self):
        """
        convert stanford-pos
        """
        self.assertEquals(convert.convert(TestStanford.STANFORD_XML,
                                          "stanford-pos")["sentence_offsets"],

                          [(0, 45), (46, 71)])

    def test_convert_invalid_src(self):
        """
        convert invalid src
        """
        self.assertRaises(convert.InvalidSrcFormat,
                          convert.convert,
                          TestStanford.STANFORD_XML,
                          "invalid!")


if __name__ == "__main__":
    import sys
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestConvert)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
