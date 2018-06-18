# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 10:58:39 2018

@author: phnx
"""

from __future__ import absolute_import

import unittest
import os

from server.verify_annotations import main, FOUND_ISSUES, CHECK_PASSED, FILE_NOT_FOUND
import config


class TestVerifyAnnotations(unittest.TestCase):
    """
    Test the annotations schema checker
    """

    def test_nicb_disease(self):
        """
        test NICB-disease collection
        """
        directory = config.DATA_DIR+"/example-data/corpora/NCBI-disease/"
        for filename in os.listdir(directory):
            if filename.endswith(".txt"):
                filename = directory+filename[:-4]
                retcode = main([None, "-q", filename])
                self.assertEquals(retcode, CHECK_PASSED, filename)

    def test_missing_file(self):
        """
        test missing file
        """
        directory = config.DATA_DIR+"/example-data/corpora/NCBI-disease/"
        for filename in os.listdir(directory):
            if filename.endswith(".txt"):
                filename = directory+(filename[:-4])[::-1]
                retcode = main([None, "-q", filename, ])
                self.assertEquals(retcode, FILE_NOT_FOUND, filename)

    def test_bionlp_with_issues(self):
        """
        test BioNLP-ST_2011 collection with issues
        """
        filename = config.DATA_DIR+"/example-data/corpora/BioNLP-ST_2011/BioNLP-ST_2011_ID/PMC2639726-02-Results-04"
        retcode = main([None, "-q", filename])
        self.assertEquals(retcode, FOUND_ISSUES, filename)


if __name__ == "__main__":
    import sys
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestVerifyAnnotations)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
