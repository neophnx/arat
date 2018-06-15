# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 10:16:24 2018

@author: phnx
"""
# future
from __future__ import absolute_import

# standard
import unittest
try:
    from io import StringIO
except ImportError:
    from stringIO import StringIO

from server.message import Messager


class TestMessage(unittest.TestCase):
    """
    Test Messager facilty
    """

    def test_warning(self):
        """
        test warning level
        """
        Messager.warning(u'Hello 世界！')
        json_dic = {}
        Messager.output_json(json_dic)
        self.assertEquals(
            json_dic, {'messages': [(u'Hello \u4e16\u754c\uff01', 'warning', 3)]})

    def test_info(self):
        """
        test info level
        """
        Messager.info(u'Hello 世界！')
        json_dic = {}
        Messager.output_json(json_dic)
        self.assertEquals(
            json_dic, {'messages': [(u'Hello \u4e16\u754c\uff01', 'comment', 3)]})

    def test_error(self):
        """
        test error level
        """
        Messager.error(u'Hello 世界！')
        json_dic = {}
        Messager.output_json(json_dic)
        self.assertEquals(
            json_dic, {'messages': [(u'Hello \u4e16\u754c\uff01', 'error', 3)]})

    def test_debug(self):
        """
        test debug level
        """
        Messager.debug(u'Hello 世界！')
        json_dic = {}
        Messager.output_json(json_dic)
        self.assertEquals(
            json_dic, {'messages': [(u'Hello \u4e16\u754c\uff01', 'debug', 3)]})

    def test_output(self):
        """
        test ouput of pending messages
        """
        Messager.warning(u'Hello warning')
        Messager.info(u'Hello info')
        Messager.debug(u'Hello debug')
        Messager.error(u'Hello error')
        output = StringIO()
        Messager.output(output)
        self.assertEquals(output.getvalue(),
                          "warning : Hello warning\n"
                          "comment : Hello info\n"
                          'debug : Hello debug\n'
                          'error : Hello error\n')
        Messager.clear()
        output = StringIO()
        Messager.output(output)
        self.assertEquals(output.getvalue(), "")
