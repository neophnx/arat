#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 23:01:02 2018

@author: neophnx
"""
import unittest
import socket
from contextlib import closing
from subprocess import Popen
import sys
import requests
from time import sleep
from six.moves.urllib.parse import urlencode

import standalone

def wait_net_service(server, port, timeout=None):
    """ Wait for network service to appear 
        @param timeout: in seconds, if None or 0 wait forever
        @return: True of False, if timeout is None may return only True or
                 throw unhandled network exception
    """
    import socket
    import errno

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
      
        except socket.error as err:
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
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('', 0))
            return s.getsockname()[1]
        
    @classmethod
    def setUpClass(cls):
        free_port = cls._find_free_port()
        cls.url = "http://localhost:%i/"%free_port
        cls.proc = Popen([sys.executable, "standalone.py", str(free_port)])
        
        if not wait_net_service("localhost", free_port, 5):
            cls.proc.kill()
            raise TimeoutError


        response = requests.post(cls.url+"ajax.cgi", json={"action": "getCollectionInformation",
                 "collection": "/",
                 "protocol": "1"})

    
        cls.sid = response.cookies.get("sid", "")
    
    @classmethod
    def tearDownClass(cls):
        cls.proc.kill()
        
    def test_01_home(self):
        response = requests.get(self.url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.headers.get("Content-Type", ""), "text/html")
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
        self.assertEquals(response.headers.get("Content-Type", ""), "application/json")
        self.assertTrue("user" in response.json())

    def test_04_login_known_user(self):
        response = requests.post(self.url+"ajax.cgi", data=urlencode({"action": "login",
                                                 "user": "admin",
                                                 "password": "admin",
                                                 "protocol": "1"}),
                                            headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                            cookies={"sid": self.sid})
        self.assertEquals(response.status_code, 200)
        
        
        self.assertEquals(response.headers.get("Content-Type", ""), "application/json")
        
        self.assertTrue(u"Hello!" in response.json()["messages"][0], response.json()["messages"])
        
        # whoami 
        response = requests.post(self.url+"ajax.cgi", data="action=whoami&protocol=1",
                                            headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                            cookies={"sid": self.sid})
        self.assertEquals(response.status_code, 200)
        
        
        self.assertEquals(response.headers.get("Content-Type", ""), "application/json")
        
        self.assertTrue(response.json()[u"user"], u"admin")
        