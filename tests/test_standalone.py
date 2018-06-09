#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 23:01:02 2018

@author: neophnx
"""

from __future__ import print_function

import unittest
import socket
from contextlib import closing
from subprocess import Popen
import sys
import os
import requests
from time import sleep
from six.moves.urllib.parse import urlencode # pylint: disable=import-error
import six



def wait_net_service(server, port, timeout=None):
    """ Wait for network service to appear 
        @param timeout: in seconds, if None or 0 wait forever
        @return: True of False, if timeout is None may return only True or
                 throw unhandled network exception
    """

    s = socket.socket()
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
                    s.settimeout(next_timeout)

            s.connect((server, port))

        except socket.timeout:
            # this exception occurs only if timeout is set
            if timeout:
                return False

        except socket.error:
            pass
            # catch timeout exception from underlying network library
            # this one is different from socket.timeout
#            if timeout and err[0] == errno.ETIMEDOUT:
#                return False
        else:
            s.close()
            return True


class TestStandalone(unittest.TestCase):

    @classmethod
    def _find_free_port(cls):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        port = s.getsockname()[1]
        s.close()
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
        try:
            os.mkdir("data/test-data")
        except:
            pass

        with open("data/test-data/test-01.txt", "wb") as fd:
            fd.write(six.u("This is a very simple text.").encode("utf-8"))

        with open("data/test-data/test-01.ann", "wb") as fd:
            fd.write(six.u("").encode("utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.proc.kill()

    def test_01_home(self):
        response = requests.get(self.url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.headers.get(
            "Content-Type", ""), "text/html")
        self.assertEquals(response.content, open("index.html", "rb").read())

    def test_02_cookie(self):
        self.assertNotEquals(self.sid, "")

    def test_03_whoami(self):
        #        response = requests.post(self.url+"ajax.cgi", json={"action": "whoami",
        #                                                 "protocol": "1"},
        #                                            cookies={"sid": self.sid},
        #                                            headers={'Connection': 'close'})
        #        from subprocess import Popen
        #        proc = Popen(["curl", self.url+"ajax.cgi", "-v",
        #                      "-H", 'Content-Type: application/json',
        #                      "-X", "POST",
        #                      "-d", 'action=whoami&protocol=1'])

        #        print(proc.communicate())
        response = requests.post(self.url+"ajax.cgi", data="action=whoami&protocol=1",
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})

#        self.assertEquals(response.request.headers, 200)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.headers.get(
            "Content-Type", ""), "application/json")
        self.assertTrue("user" in response.json())

    def test_04_login_known_user(self):
        response = requests.post(self.url+"ajax.cgi", data=urlencode({"action": "login",
                                                                      "user": "admin",
                                                                      "password": "admin",
                                                                      "protocol": "1"}),
                                 headers={
                                     'Content-Type': 'application/x-www-form-urlencoded'},
                                 cookies={"sid": self.sid})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get(
            "Content-Type", ""), "application/json")

        self.assertTrue(u"Hello!" in response.json()[
                        "messages"][0], response.json()["messages"])

        # whoami
        response = requests.post(self.url+"ajax.cgi", data="action=whoami&protocol=1",
                                 headers={
                                     'Content-Type': 'application/x-www-form-urlencoded'},
                                 cookies={"sid": self.sid})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get(
            "Content-Type", ""), "application/json")

        self.assertTrue(response.json()[u"user"], u"admin")

    def test_10_getCollectionInformation(self):
        response = requests.post(self.url+"ajax.cgi", data=urlencode({"action": "getCollectionInformation",
                                                                      "collection": "/test-data",
                                                                      "protocol": "1"}),
                                 headers={
                                     'Content-Type': 'application/x-www-form-urlencoded'},
                                 cookies={"sid": self.sid})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get(
            "Content-Type", ""), "application/json")

        for i in [six.u('normalization_config'), six.u('ner_taggers'), six.u('entity_types'),
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

        item_type, _, name, timestamp, nb_entities, nb_relations, nb_events = response.json()[
            "items"][-1]
        self.assertEquals(item_type, six.u('d'))  # document
        self.assertEquals(name, six.u('test-01'))
        self.assertEquals(nb_entities, 0)  # no annotations so far
        self.assertEquals(nb_relations, 0)
        self.assertEquals(nb_events, 0)

    def test_11_createSpan(self):
        response = requests.post(self.url+"ajax.cgi", data=urlencode({"action": "createSpan",
                                                                      "collection": "/test-data",
                                                                      "document": "test-01",
                                                                      "attributes": "{}",
                                                                      "normalizations": "[]",
                                                                      "offsets": "[[15,21]]",
                                                                      "type": "Protein",
                                                                      "protocol": "1"}),
                                 headers={
                                     'Content-Type': 'application/x-www-form-urlencoded'},
                                 cookies={"sid": self.sid})
        self.assertEquals(response.status_code, 200)

        self.assertEquals(response.headers.get(
            "Content-Type", ""), "application/json")

        self.assertEquals(response.json()["edited"], [[six.u("T1")]])

        # check numbers on the collection level
        response = requests.post(self.url+"ajax.cgi", data=urlencode({"action": "getCollectionInformation",
                                                                      "collection": "/test-data",
                                                                      "protocol": "1"}),
                                 headers={
                                     'Content-Type': 'application/x-www-form-urlencoded'},
                                 cookies={"sid": self.sid})

        item_type, _, name, timestamp, nb_entities, nb_relations, nb_events = response.json()[
            "items"][-1]
        self.assertEquals(item_type, six.u('d'))  # document
        self.assertEquals(name, six.u('test-01'))
        self.assertEquals(nb_entities, 1)  # this is the one
        self.assertEquals(nb_relations, 0)
        self.assertEquals(nb_events, 0)

        # check annotation file content
        with open("data/test-data/test-01.ann", "rb") as fd:
            self.assertEquals(fd.read().decode("utf-8").strip(),
                              six.u("T1	Protein 15 21	simple"))
