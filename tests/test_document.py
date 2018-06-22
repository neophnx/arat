# -*- coding: utf-8 -*-
"""
Created on Sat Jun  2 06:19:53 2018

@author: phnx
"""
from __future__ import absolute_import
import unittest
from tempfile import mkdtemp
from shutil import rmtree
from time import sleep
from os import listdir
from os.path import join as join_path
from datetime import timedelta

from arat.server.document import FileCollection, FileDocument
import config


class TestFileDocument(unittest.TestCase):
    """
    FileCollection and FileDocument test cases
    """
    
    @classmethod
    def setUpClass(cls):
        # mock config.DATA_DIR
        cls.DATA_DIR = config.DATA_DIR
        config.DATA_DIR = mkdtemp()

    @classmethod
    def tearDownClass(cls):
        # revert to user defined DATA_DIR
        rmtree(config.DATA_DIR)
        config.DATA_DIR = cls.DATA_DIR
        
    
    def test_01_empty_collection(self):
        """
        empty collection
        """
        collection = FileCollection.root()
        
        self.assertEqual(list(collection), [])

    def test_02_add_document_root(self):
        """
        add documents in the root collection
        """
        
        root = FileCollection.root()
        collection = root
        doc01 = FileDocument("doc01", collection, "file content doc01")
        doc02 = FileDocument("doc02", collection, "file content doc02")

        coll01 = collection.addCollection("coll01")
        doc02 = coll01.addDocument("doc02", "file content doc02")

        collection = coll01.addCollection("coll02")
        collection = coll01.addCollection("coll03")
        
        self.assertIn(coll01, list(root))

if __name__ == "__main__":
    import sys
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestFileDocument)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)