#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 23:01:02 2018

@author: neophnx
"""

# futures
from __future__ import print_function

# standard
import unittest
import socket
from subprocess import Popen
import sys
import os
from shutil import rmtree

# third party
import requests
import six
from six.moves.urllib.parse import urlencode  # pylint: disable=import-error

# arat
import standalone


def wait_net_service(server, port, timeout=None):
    """
    Wait for network service to appear
    @param timeout: in seconds, if None or 0 wait forever
    @return: True of False, if timeout is None may return only True or
             throw unhandled network exception
    """

    sock = socket.socket()
    if timeout:
        from time import time as now
        # time module is needed to calc timeout shared between two exceptions
        end = now() + timeout

    while True:
        try:
            if timeout:
                next_timeout = end - now()
                if next_timeout < 0:
                    return False
                else:
                    sock.settimeout(next_timeout)

            sock.connect((server, port))

        except socket.timeout:
            # this exception occurs only if timeout is set
            if timeout:
                return False

        except socket.error:
            pass
        else:
            sock.close()
            return True


class TestStandalone(unittest.TestCase):
    """
    Integration test, run the standalone server as seperate process
    then test protocol compliance.
    """

    @classmethod
    def _find_free_port(cls):
        """
        Automatically get a free port


        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

    @classmethod
    def setUpClass(cls):
        # run server
        free_port = cls._find_free_port()
        cls.url = "http://localhost:%i/" % free_port
        cls.proc = Popen([sys.executable, "standalone.py", str(free_port)])

        if not wait_net_service("localhost", free_port, 5):
            cls.proc.kill()
            raise OSError

        # get a session id
        response = requests.post(cls.url+"ajax.cgi", json={"action": "getCollectionInformation",
                                                           "collection": "/",
                                                           "protocol": "1"})
        cls.sid = response.cookies.get("sid", "")

        # populate a datadir with simple test file
        if not os.path.isdir("data/test-data"):
            os.mkdir("data/test-data")

        with open("data/test-data/test-01.txt", "wb") as fd:
            fd.write(six.u("This is a very simple text.").encode("utf-8"))

        with open("data/test-data/test-01.ann", "wb") as fd:
            fd.write(six.u("").encode("utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.proc.kill()

        # remove test directory recursively
        rmtree("data/test-data", ignore_errors=True)

    def test_permission_parse_error(self):
        """
        PermissionParseError
        """
        value = standalone.PermissionParseError(linenum=10,
                                                line="invalid line",
                                                message=None)
        self.assertEquals(str(value),
                          'line 10: invalid line')

        value = standalone.PermissionParseError(linenum=10,
                                                line="invalid line",
                                                message="message")
        self.assertEquals(str(value),
                          'line 10 (message): invalid line')

    def test_path_permissions(self):
        """
        test permission file parser
        """

        valid_permissions = ["#ignored comment",
                             "Allow : *.txt",
                             "Disallow : *.png",
                             "Allow : /allowed",
                             "Disallow : /disallowed"]

        # check permission with default=True
        value = standalone.PathPermissions(default_allow=True)
        self.assertEquals(value.entries,
                          [])
        self.assertEquals(value.default_allow,
                          True)

        self.assertTrue(value.allow("/default"))
        self.assertTrue(value.allow("/default/index.html"))
        self.assertTrue(value.allow("/allowed"))
        self.assertTrue(value.allow("/disallowed"))
        self.assertTrue(value.allow("/allowed/text.txt"))
        self.assertTrue(value.allow("/disallowed/text.txt"))
        self.assertTrue(value.allow("/allowed/img.png"))
        self.assertTrue(value.allow("/disallowed/img.png"))

        # check permission with default=False
        value = standalone.PathPermissions(default_allow=False)
        self.assertEquals(value.entries,
                          [])
        self.assertEquals(value.default_allow,
                          False)

        self.assertFalse(value.allow("/default"))
        self.assertFalse(value.allow("/default/index.html"))
        self.assertFalse(value.allow("/allowed"))
        self.assertFalse(value.allow("/disallowed"))
        self.assertFalse(value.allow("/allowed/text.txt"))
        self.assertFalse(value.allow("/disallowed/text.txt"))
        self.assertFalse(value.allow("/allowed/img.png"))
        self.assertFalse(value.allow("/disallowed/img.png"))

        # check permission with defined rules and default=False
        value.parse(valid_permissions)
        self.assertEquals(value.entries,
                          [(standalone.ExtensionPattern(".txt"), True),
                           (standalone.ExtensionPattern(".png"), False),
                           (standalone.PathPattern("/allowed"), True),
                           (standalone.PathPattern("/disallowed"), False)],
                          str(value.entries))
        self.assertEquals(value.default_allow,
                          False)

        self.assertFalse(value.allow("/default"))
        self.assertFalse(value.allow("/default/index.html"))
        self.assertTrue(value.allow("/allowed"))
        self.assertFalse(value.allow("/disallowed"))
        self.assertTrue(value.allow("/allowed/text.txt"))
        self.assertTrue(value.allow("/disallowed/text.txt"))
        self.assertFalse(value.allow("/allowed/img.png"))
        self.assertFalse(value.allow("/disallowed/img.png"))

        # check for syntax error

        missing_colon_permissions = ["#ignored comment",
                                     "Allow = *.txt",
                                     "Disallow : *.png",
                                     "Allow : /allowed",
                                     "Disallow : /disallowed"]
        self.assertRaises(standalone.PermissionParseError,
                          value.parse,
                          missing_colon_permissions)

        unknown_directive_permissions = ["#ignored comment",
                                         "Allow : *.txt",
                                         "Disallow : *.png",
                                         "DontAllow : /allowed",
                                         "Disallow : /disallowed"]
        self.assertRaises(standalone.PermissionParseError,
                          value.parse,
                          unknown_directive_permissions)

        wrong_pattern_permissions = ["#ignored comment",
                                     "Allow : *.txt",
                                     "Disallow : index.html?",
                                     "Allow : /allowed",
                                     "Disallow : /disallowed"]
        self.assertRaises(standalone.PermissionParseError,
                          value.parse,
                          wrong_pattern_permissions)

    def test_01_home(self):
        """
        test GET index  page
        """
        response = requests.get(self.url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.headers.get(
            "Content-Type", ""), "text/html")
        self.assertEquals(response.content, open("index.html", "rb").read())

    def test_02_cookie(self):
        """
        test cookie presence
        """
        self.assertNotEquals(self.sid, "")

    def test_03_whoami(self):
        """
        test whoami action
        """
        response = requests.post(self.url+"ajax.cgi", data="action=whoami&protocol=1",
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.headers.get(
            "Content-Type", ""), "application/json")
        self.assertTrue("user" in response.json())

    def test_04_login_known_user(self):
        """
        test to authenticate and login
        """
        data = urlencode({"action": "login",
                          "user": "admin",
                          "password": "admin",
                          "protocol": "1"})
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(self.url+"ajax.cgi",
                                 data=data,
                                 headers=headers,
                                 cookies={"sid": self.sid})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get(
            "Content-Type", ""), "application/json")

        self.assertTrue(u"Hello!" in response.json()["messages"][0],
                        response.json()["messages"])

        # whoami

        response = requests.post(self.url+"ajax.cgi",
                                 data="action=whoami&protocol=1",
                                 headers=headers,
                                 cookies={"sid": self.sid})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get(
            "Content-Type", ""), "application/json")

        self.assertTrue(response.json()[u"user"], u"admin")

    def test_10_collection_information(self):
        """
        test the getCollectionInformation action
        """
        data = urlencode({"action": "getCollectionInformation",
                          "collection": "/test-data",
                          "protocol": "1"})
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        response = requests.post(self.url+"ajax.cgi",
                                 data=data,
                                 headers=headers,
                                 cookies={"sid": self.sid})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get(
            "Content-Type", ""), "application/json")

        for i in [six.u('normalization_config'), six.u('ner_taggers'),
                  six.u('entity_types'),
                  six.u('protocol'), six.u('description'), six.u('parent'),
                  six.u('event_attribute_types'), six.u(
                      'items'), six.u('unconfigured_types'),
                  six.u('messages'), six.u(
                      'disambiguator_config'), six.u('ui_names'),
                  six.u('header'), six.u(
                      'entity_attribute_types'), six.u('event_types'),
                  six.u('relation_types'), six.u(
                      'action'), six.u('search_config'),
                  six.u('annotation_logging'), six.u(
                      'relation_attribute_types'),
                  six.u('visual_options')]:
            self.assertTrue(i in response.json())

        item_type, _, name, _, nb_entities, _, _ = response.json()[
            "items"][-1]
        self.assertEquals(item_type, six.u('d'))  # document
        self.assertEquals(name, six.u('test-01'))
        self.assertEquals(nb_entities, 0)  # no annotations so far

    def test_11_create_span(self):
        """
        test the createSpan action
        """
        data = urlencode({"action": "createSpan",
                          "collection": "/test-data",
                          "document": "test-01",
                          "attributes": "{}",
                          "normalizations": "[]",
                          "offsets": "[[15,21]]",
                          "type": "Protein",
                          "protocol": "1"})
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        response = requests.post(self.url+"ajax.cgi",
                                 data=data,
                                 headers=headers,
                                 cookies={"sid": self.sid})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get("Content-Type", ""),
                          "application/json")

        self.assertEquals(response.json()["edited"], [[six.u("T1")]])

        # check numbers on the collection level
        data = urlencode({"action": "getCollectionInformation",
                          "collection": "/test-data",
                          "protocol": "1"})
        response = requests.post(self.url+"ajax.cgi", data,
                                 headers=headers,
                                 cookies={"sid": self.sid})

        item_type, _, name, _, nb_entities, _, _ = response.json()[
            "items"][-1]
        self.assertEquals(item_type, six.u('d'))  # document
        self.assertEquals(name, six.u('test-01'))
        self.assertEquals(nb_entities, 1)  # this is the one

        # check annotation file content
        with open("data/test-data/test-01.ann", "rb") as fd:
            self.assertEquals(fd.read().decode("utf-8").strip(),
                              six.u("T1	Protein 15 21	simple"))

#    def test_arat_http_request_handler(self):
#        """
#        AratHTTPRequestHandler
#        """


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestStandalone)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
