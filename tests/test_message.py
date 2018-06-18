# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 10:16:24 2018

@author: phnx
"""
# future
from __future__ import absolute_import

# standard
import os
import unittest
from tempfile import NamedTemporaryFile
try:
    from stringIO import StringIO
except ImportError:
    from io import StringIO

from server.message import Messager


class TestMessage(unittest.TestCase):
    """
    Test Messager facilty
    """

    def test_01_warning(self):
        """
        test warning level
        """
        Messager.warning(u'Hello 世界！')
        json_dic = {}
        Messager.output_json(json_dic)
        self.assertEquals(
            json_dic, {'messages': [(u'Hello \u4e16\u754c\uff01', 'warning', 3)]})

    def test_02_info(self):
        """
        test info level
        """
        Messager.info(u'Hello 世界！')
        json_dic = {}
        Messager.output_json(json_dic)
        self.assertEquals(
            json_dic, {'messages': [(u'Hello \u4e16\u754c\uff01', 'comment', 3)]})

    def test_03_error(self):
        """
        test error level
        """
        Messager.error(u'Hello 世界！')
        json_dic = {}
        Messager.output_json(json_dic)
        self.assertEquals(
            json_dic, {'messages': [(u'Hello \u4e16\u754c\uff01', 'error', 3)]})

    def test_04_debug(self):
        """
        test debug level
        """
        Messager.debug(u'Hello 世界！')
        json_dic = {}
        Messager.output_json(json_dic)
        self.assertEquals(
            json_dic, {'messages': [(u'Hello \u4e16\u754c\uff01', 'debug', 3)]})

    def test_05_output(self):
        """
        test ouput of pending messages
        """
        Messager.warning(u'Hello warning')
        Messager.info(u'Hello info')
        Messager.debug(u'Hello debug')
        
        Messager.error(u'Hello error')
        output = NamedTemporaryFile("w", delete=False)
        try:
            Messager.output(output)
            
            output.close()
            with open(output.name, "r") as output:
                self.assertEquals(output.read(),
                                  u"warning : Hello warning\n"
                                  u"comment : Hello info\n"
                                  u'debug : Hello debug\n'
                                  u'error : Hello error\n')
            Messager.clear()
            
            with open(output.name, "w") as output:
                Messager.output(output)
            with open(output.name, "r") as output:
                self.assertEquals(output.read(), "")
        finally:
            os.unlink(output.name)
            
            
        
        
if __name__ == "__main__":
    import sys
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestMessage)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
