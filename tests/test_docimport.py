# -*- coding: utf-8 -*-
"""
Created on Tue Jun  5 11:02:48 2018

@author: jgo
"""
# standard
import unittest
from tempfile import mkdtemp
from shutil import rmtree
from os import mkdir
from os.path import join as join_path
# brat
import config
from server import docimport


class SaveImportTest(unittest.TestCase):
    test_text = 'This is not a drill, this is a drill *BRRR!*'
    test_dir = 'test'
    test_filename = 'test'

    def setUp(self):
        self.tmpdir = mkdtemp(dir=config.DATA_DIR)

    def tearDown(self):
        rmtree(self.tmpdir)

    def test_import(self):
        docimport.save_import(SaveImportTest.test_text,
                              SaveImportTest.test_filename,
                              collection="/"+self.tmpdir.split("/")[-1])
