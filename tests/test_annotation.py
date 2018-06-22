# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 10:58:39 2018

@author: phnx
"""
from __future__ import absolute_import
import unittest

from server import annotation as anno
import config


class TestAnnotation(unittest.TestCase):
    """
    Test annotation
    """

    def test_annotation_id_prefix(self):
        self.assertEquals(anno.annotation_id_prefix("foo1"),
                          'foo')

        self.assertEquals(anno.annotation_id_prefix("foo"),
                          'foo')

        self.assertEquals(anno.annotation_id_prefix("foo10_a"),
                          "foo")

        self.assertRaises(anno.InvalidIdError,
                          anno.annotation_id_prefix,
                          "12_a")

    def test_annotation_id_number(self):
        self.assertEquals(anno.annotation_id_number("foo1"),
                          "1")

        self.assertRaises(anno.InvalidIdError,
                          anno.annotation_id_number,
                          'foo')

        self.assertEquals(anno.annotation_id_number("foo10_a"),
                          "10")

        self.assertRaises(anno.InvalidIdError,
                          anno.annotation_id_number,
                          "12_a")

    def test_is_valid_id(self):
        self.assertEquals(anno.is_valid_id("foo1"),
                          True)

        self.assertEquals(anno.is_valid_id('foo'),
                          False)

        self.assertEquals(anno.is_valid_id("foo10_a"),
                          True)

        self.assertEquals(anno.is_valid_id("foo10_a"),
                          True)

        self.assertEquals(anno.is_valid_id("*"),
                          True)

    def test_annotations(self):
        """
        Test Annotations the base class of all annotations
        """

        document_path = config.DATA_DIR+"/example-data/corpora/NCBI-disease/PMID-8929264"

        anno0 = anno.Annotations(document_path)

        self.assertEquals(anno0.get_document(), document_path)
        self.assertEquals(anno0.input_files, [document_path+".ann"])

        expected = anno.TextBoundAnnotation(spans=[(33, 50)],
                                            id_="T1",
                                            type_="Disease",
                                            tail="\tcolorectal cancer\n")
        self.assertTrue(anno0.get_ann_by_id("T1").same_span(expected))
        self.assertEquals(str(anno0.get_ann_by_id("T1")),
                          str(expected))

        # empty document
        document_path = config.DATA_DIR+"/empty"

        anno0 = anno.Annotations(document_path)

        self.assertEquals(anno0.get_document(), document_path)
        self.assertEquals(anno0.input_files, [document_path+".ann"])


if __name__ == "__main__":
    import sys
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestAnnotation)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
