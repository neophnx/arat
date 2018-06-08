#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  2 06:55:31 2018

@author: phnx
"""
from __future__ import absolute_import
import unittest

from six.moves import zip

try:  # python2
    from cStringIO import StringIO
except ImportError:
    try:
        from StringIO import StringIO
    except:  # python3
        from io import StringIO

from server import sdistance


class TestSDistance(unittest.TestCase):
    input_data = [('kitten', 'sitting'),
                  ('Saturday', 'Sunday'),
                  ('Caps', 'caps'),
                  ('', 'bar'),
                  ('dog', 'dog'),
                  ('dog', '___dog__'),
                  ('dog', '__d_o_g__')]

    def test_levenshtein(self):
        expected_values = [3, 3, 1, 3, 0, 5, 6]
        for (a, b), expected in zip(TestSDistance.input_data, expected_values):
            self.assertEquals(sdistance.levenshtein(a, b),
                              expected,
                              'levenshtein(%r, %r) != %r' % (a, b, sdistance.levenshtein(a, b)))

    def test_tsuruoka(self):
        expected_values = [200, 250, 10, 300, 0, 500, 600]
        for (a, b), expected in zip(TestSDistance.input_data, expected_values):
            self.assertEquals(sdistance.tsuruoka(a, b),
                              expected,
                              'tsuruoka(%r, %r) != %r' % (a, b, sdistance.tsuruoka(a, b)))

    def test_tsuruoka_local(self):
        expected_values = [101, 250, 10, 3, 0, 5, 106]
        for (a, b), expected in zip(TestSDistance.input_data, expected_values):
            self.assertEquals(sdistance.tsuruoka_local(a, b),
                              expected,
                              'tsuruoka(%r, %r) != %r' % (a, b, sdistance.tsuruoka_local(a, b)))

    def test_tsuruoka_norm(self):
        expected_values = [0.714, 0.687, 0.975, 0.0, 1.0, 0.375, 0.333]
        for (a, b), expected in zip(TestSDistance.input_data, expected_values):
            self.assertAlmostEqual(sdistance.tsuruoka_norm(a, b),
                                   expected,
                                   msg='tsuruoka(%r, %r) != %r' % (
                                       a, b, sdistance.tsuruoka_norm(a, b)),
                                   places=3)
