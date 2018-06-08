# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 10:16:24 2018

@author: phnx
"""

from __future__ import absolute_import
import unittest

from server import realmessage


class TestSDistance(unittest.TestCase):

    def test_warning(self):
        # Try out Unicode, that is always fun
        realmessage.Messager.warning(u'Hello 世界！')
        json_dic = {}
        realmessage.Messager.output_json(json_dic)
        self.assertEquals(
            json_dic, {'messages': [(u'Hello \u4e16\u754c\uff01', 'warning', 3)]})
