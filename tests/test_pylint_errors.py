# -*- coding: utf-8 -*-
"""
Created on Fri Jun  8 21:09:59 2018

@author: phnx
"""

# future
from __future__ import print_function

# standard
import unittest

# third party
from pylint.lint import Run
from pylint.reporters import BaseReporter


class DummyReporter(BaseReporter):
    """
    A pylint reporter ignoring all messages
    Typical usage: running pylint to get overall statistics (like score)
    """

    def __init__(self, output=None):
        BaseReporter.__init__(self, output)

    def add_message(self, msg_id, location, msg):
        """
        ignore all message coming from pylint
        """
        pass

    def _display(self, layout):
        """
        don't display anything
        """
        pass


class PylintTestCase(unittest.TestCase):
    """
    All errors found staticaly by pylint fail this unit test
    """

    def test_pylint_errors(self):
        """
        check if pylint reports errors
        """
        out = DummyReporter()
        run = Run(['--errors-only', "--jobs=8", 'standalone',
                   'server', 'tests'], reporter=out, exit=False)
        self.assertEquals(run.linter.stats["error"],
                          0,
                          "%i pylint error found: "
                          "please run `make static-test{2,3}' "
                          "for detail report" % run.linter.stats["error"])


if __name__ == "__main__":
    import sys
    print("Please wait, this unit test is quite long...")
    SUITE = unittest.TestLoader().loadTestsFromTestCase(PylintTestCase)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
