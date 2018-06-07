# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 23:47:41 2018

@author: neophnx
"""
from __future__ import absolute_import
from __future__ import print_function
import unittest

from server import session



class TestSentenceSplit(unittest.TestCase):
    def test01_SessionNotInitialize(self):

        # Some simple sanity checks
        try:
            session.get_session()
            print((session.CURRENT_SESSION))
            assert False
        except session.NoSessionError:
            pass
    
    def test02_SessionSimple(self):
        # New "fresh" cookie session check
        session.init_session('127.0.0.1')
        
        try:
            this_session = session.get_session()
            this_session['foo'] = 'bar'
        except session.NoSessionError:
            assert False
            
    def testSessionPickle(self):
        # Pickle check
        session.init_session('127.0.0.1')
        tmp_file_path = None
        try:
            tmp_file_fh, tmp_file_path = session.mkstemp()
            session.os_close(tmp_file_fh)
            this_session = session.get_session()
            this_session['foo'] = 'bar'
            with open(tmp_file_path, 'wb') as tmp_file:
                session.pickle_dump(this_session, tmp_file)
            del this_session
    
            with open(tmp_file_path, 'rb') as tmp_file:
                this_session = session.pickle_load(tmp_file)
                self.assertEquals(this_session['foo'], 'bar')
        finally:
            if tmp_file_path is not None:
                session.remove(tmp_file_path)