# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 10:58:39 2018

@author: phnx
"""

# future
from __future__ import absolute_import

# standard
import unittest
import json

# brat
from server import brat_server
from server import session
import config


class Params(dict):
    """
    Mocking the CGI encapsulation of url encoded params
    """

    def getvalue(self, key):
        """
        Get item value by key
        """
        return self[key]


class TestServer(unittest.TestCase):
    """
    Test server request handling
    """

    def tearDown(self):
        session.close_session()
        session.CURRENT_SESSION = None

    def test_empty_input(self):
        """
        test empty input
        """
        _, response_data = brat_server.serve(
            Params({}), '127.0.0.1', "me", None)
        self.assertEquals(json.loads(response_data[1])["exception"],
                          ["protocolVersionMismatch"])

    def test_higher_protocol(self):
        """
        test higher protocol
        """
        _, response_data = brat_server.serve(
            Params({"protocol": 3}), '127.0.0.1', "me", None)
        self.assertEquals(json.loads(response_data[1])["exception"],
                          ["protocolVersionMismatch"])

    def test_lower_protocol(self):
        """
        test lower protocol
        """
        _, response_data = brat_server.serve(Params({"protocol": -1}),
                                             '127.0.0.1',
                                             "me",
                                             None)
        self.assertEquals(json.loads(response_data[1])["exception"],
                          ["protocolVersionMismatch"])

    def test_no_action(self):
        """
        test no action
        """
        _, response_data = brat_server.serve(Params({"protocol": 1}),
                                             '127.0.0.1',
                                             "me",
                                             None)
        self.assertEquals(json.loads(response_data[1])["exception"],
                          "noAction")

    def test_invalid_action(self):
        """
        test invalid action
        """
        _, response_data = brat_server.serve(Params({"protocol": 1,
                                                     "action": "bye"}),
                                             '127.0.0.1',
                                             "me",
                                             None)
        self.assertEquals(json.loads(response_data[1])["exception"],
                          ["invalidAction"])

    def test_crash(self):
        """
        test crash
        """
        serve_save = brat_server._safe_serve

        def crash_serve(*_):
            """
            Mock an unhandled exception during serve
            """
            raise BaseException
        brat_server._safe_serve = crash_serve

        # test in DEBUG mode
        config.DEBUG = True
        _, response_data = brat_server.serve(Params({"protocol": 1,
                                                     "action": "bye"}),
                                             '127.0.0.1',
                                             "me",
                                             None)
        self.assertEquals(json.loads(response_data[1])["exception"],
                          'serverCrash')

        # test in production mode
        config.DEBUG = False
        _, response_data = brat_server.serve(Params({"protocol": 1,
                                                     "action": "bye"}),
                                             '127.0.0.1',
                                             "me",
                                             None)
        self.assertEquals(json.loads(response_data[1])["exception"],
                          'serverCrash')

        brat_server._safe_serve = serve_save


if __name__ == "__main__":
    import sys
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestServer)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
