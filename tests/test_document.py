# -*- coding: utf-8 -*-
"""
Created on Sat Jun  2 06:19:53 2018

@author: phnx
"""
from __future__ import absolute_import
import unittest
from tempfile import mkdtemp
from shutil import rmtree

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
        doc01 = FileDocument("/doc01", "file content doc01")

        coll01 = FileCollection("/coll01")
        doc02 = FileDocument("/coll01/doc02", "file content doc02")

        coll02 = FileCollection("/coll02")

        # coll02 is empty, so it does not exists yet
        self.assertNotIn(coll02, list(root))

        coll03 = FileCollection("/coll02/coll03")

        # coll03 is empty, so it does not exists yet
        self.assertNotIn(coll02, list(coll02))

        doc03 = FileDocument("/coll02/coll03/doc03", "file content doc03")

        # coll02 and coll03 should be created now
        self.assertIn(coll02, list(root))
        self.assertIn(coll03, list(coll02))
        self.assertIn(doc03, list(coll03))

        self.assertIn(coll01, list(root))

        # doc01 is the only direct child of root
        self.assertIn(doc01, list(root))
        self.assertNotIn(doc02, list(root))
        self.assertNotIn(doc03, list(root))

        # all docs are in the tree
        self.assertIn(doc01, list(
            root.breadth_first_iter(include_collection=False)))
        self.assertIn(doc02, list(
            root.breadth_first_iter(include_collection=False)))
        self.assertIn(doc03, list(
            root.breadth_first_iter(include_collection=False)))


if __name__ == "__main__":
    import sys
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestFileDocument)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
