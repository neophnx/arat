# -*- coding: utf-8 -*-
"""
Created on Sat Jun  2 06:55:31 2018

@author: phnx
"""

# future
from __future__ import absolute_import

# standard
import unittest

# third party
from six.moves import zip

# arat
from arat.server import sdistance as dist


class TestSDistance(unittest.TestCase):
    """
    server.sdistance unit tests
    """
    input_data = [('kitten', 'sitting'),
                  ('Saturday', 'Sunday'),
                  ('Caps', 'caps'),
                  ('', 'bar'),
                  ('dog', 'dog'),
                  ('dog', '___dog__'),
                  ('dog', '__d_o_g__')]

    def test_levenshtein(self):
        """
        test levenshtein
        """
        expected_values = [3, 3, 1, 3, 0, 5, 6]
        for (i, j), expected in zip(TestSDistance.input_data, expected_values):
            msg = 'levenshtein(%r, %r) != %r' % (i,
                                                 j,
                                                 dist.levenshtein(i, j))
            self.assertEquals(dist.levenshtein(i, j),
                              expected,
                              msg)

    def test_tsuruoka(self):
        """
        test tsuroka
        """
        expected_values = [200, 250, 10, 300, 0, 500, 600]
        for (i, j), expected in zip(TestSDistance.input_data, expected_values):
            msg = 'tsuruoka(%r, %r) != %r' % (i,
                                              j,
                                              dist.tsuruoka(i, j))
            self.assertEquals(dist.tsuruoka(i, j),
                              expected,
                              msg)

    def test_tsuruoka_local(self):
        """
        test tsuroka local
        """
        expected_values = [101, 250, 10, 3, 0, 5, 106]
        for (i, j), expected in zip(TestSDistance.input_data, expected_values):
            msg = 'tsuruoka_local(%r, %r) != %r' % (i,
                                                    j,
                                                    dist.tsuruoka_local(i, j))
            self.assertEquals(dist.tsuruoka_local(i, j),
                              expected,
                              msg)

    def test_tsuruoka_norm(self):
        """
        test tsuroka normalized
        """
        expected_values = [0.714, 0.687, 0.975, 0.0, 1.0, 0.375, 0.333]
        for (i, j), expected in zip(TestSDistance.input_data, expected_values):
            msg = 'tsuruoka_norm(%r, %r) != %r' % (i,
                                                   j,
                                                   dist.tsuruoka_norm(i, j))
            self.assertAlmostEqual(dist.tsuruoka_norm(i, j),
                                   expected,
                                   msg=msg,
                                   places=3)
