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

# arat
from arat import standalone


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

        cls.proc = Popen([sys.executable, standalone.__file__, str(free_port)])

        if not wait_net_service("localhost", free_port, 5):
            raise OSError

        cls.user = None

        # populate a datadir with simple test file
        if not os.path.isdir("data/test-data"):
            os.mkdir("data/test-data")

        with open("data/test-data/test-01.txt", "wb") as fd:
            fd.write(six.u("This is a very simple text.").encode("utf-8"))

        with open("data/test-data/test-01.ann", "wb") as fd:
            fd.write(six.u("").encode("utf-8"))

    @classmethod
    def tearDownClass(cls):

        # remove test directory recursively
        rmtree("data/test-data", ignore_errors=True)

        cls.proc.terminate()

    def test_01_home(self):
        """
        test GET index  page
        """
        response = requests.get(self.url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.headers.get(
            "Content-Type", ""), "application/xhtml+xml")
        self.assertEquals(response.content, open(
            "arat/client/index.xhtml", "rb").read())

    def test_03_whoami(self):
        """
        test whoami action
        """
        response = requests.post(self.url+"whoami", json={})

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.headers.get(
            "Content-Type", ""), "text/json")
        self.assertTrue("user" in response.json())

    def test_04_login_known_user(self):
        """
        test to authenticate and login
        """
        data = {"user": "admin",
                "password": "admin"}
#        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(self.url+"login",
                                 json=data)
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get(
            "Content-Type", ""), "text/json")

        self.assertTrue(u"Hello!" in response.json()["messages"][0],
                        response.json()["messages"])

        # get the user cookie
        TestStandalone.user = response.cookies.get("user", "")

        # whoami

        response = requests.post(self.url+"whoami",
                                 json={},
                                 cookies={"user": self.user})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get(
            "Content-Type", ""), "text/json")

        self.assertTrue(response.json()[u"user"], u"admin")

    def test_10_collection_information(self):
        """
        test the getCollectionInformation action
        """
        data = {"collection": "/test-data",
                "protocol": "1"}
#        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        response = requests.post(self.url+"getCollectionInformation",
                                 json=data,
                                 cookies={"user": self.user})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get(
            "Content-Type", ""), "text/json")

        for i in [six.u('normalization_config'), six.u('ner_taggers'),
                  six.u('entity_types'), six.u('description'), six.u('parent'),
                  six.u('event_attribute_types'), six.u(
                      'items'), six.u('unconfigured_types'),
                  six.u('messages'), six.u(
                      'disambiguator_config'), six.u('ui_names'),
                  six.u('header'), six.u(
                      'entity_attribute_types'), six.u('event_types'),
                  six.u('relation_types'), six.u('search_config'),
                  six.u('annotation_logging'), six.u(
                      'relation_attribute_types'),
                  six.u('visual_options')]:
            self.assertTrue(i in response.json(), i)

        item_type, _, name, _, nb_entities, _, _ = response.json()[
            "items"][-1]
        self.assertEquals(item_type, six.u('d'))  # document
        self.assertEquals(name, six.u('test-01'))
        self.assertEquals(nb_entities, 0)  # no annotations so far

    def test_get_document(self):
        """
        get_document
        """
        data = {u'document': u'000-introduction',
                u'collection': u'/example-data/tutorials/news/'}

        response = requests.post(self.url+"getDocument",
                                 json=data,
                                 cookies={"user": self.user})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get(
            "Content-Type", ""), "text/json")

        response_keys = set(response.json().keys())
        self.assertTrue(response_keys.intersection(['offsets',
                                                    'sentence_offsets',
                                                    'sentence_offsets',
                                                    'entities',
                                                    'triggers']))

    def test_get_document_timestamp(self):
        """
        get_document_timestamp
        """
        data = {u'document': u'000-introduction',
                u'collection': u'/example-data/tutorials/news/'}

        response = requests.post(self.url+"getDocumentTimestamp",
                                 json=data,
                                 cookies={"user": self.user})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get(
            "Content-Type", ""), "text/json")

        self.assertTrue('mtime' in response.json().keys())

    def test_11_create_span(self):
        """
        test the createSpan action
        """
        data = {"collection": "/test-data",
                "document": "test-01",
                "attributes": "{}",
                "normalizations": "[]",
                "offsets": "[[15,21]]",
                "type": "Protein",
                "protocol": "1"}

        response = requests.post(self.url+"createSpan",
                                 json=data,
                                 cookies={"user": self.user})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get("Content-Type", ""),
                          "text/json")

        self.assertEquals(response.json()["edited"], [[six.u("T1")]])

        # check numbers on the collection level
        data = {"collection": "/test-data"}
        response = requests.post(self.url+"getCollectionInformation",
                                 json=data,
                                 cookies={"user": self.user})

        item_type, _, name, _, nb_entities, _, _ = response.json()[
            "items"][-1]
        self.assertEquals(item_type, six.u('d'))  # document
        self.assertEquals(name, six.u('test-01'))
        self.assertEquals(nb_entities, 1)  # this is the one

        # check annotation file content
        with open("data/test-data/test-01.ann", "rb") as fd:
            self.assertEquals(fd.read().decode("utf-8").strip(),
                              six.u("T1	Protein 15 21	simple"))

    def test_12_logout(self):
        """
        test to logout
        """
        response = requests.post(self.url+"logout",
                                 json={},
                                 cookies={"user": self.user})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get(
            "Content-Type", ""), "text/json")

        # get the user cookie
        self.assertEquals(response.cookies.get("user", None), None)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(__file__)))
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestStandalone)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
