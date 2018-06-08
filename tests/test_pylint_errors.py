#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  8 21:09:59 2018

@author: phnx
"""

from unittest import TestCase
from pylint.lint import Run
from pylint.reporters import BaseReporter
from pprint import pformat


class DummyReporter(BaseReporter):
    def __init__(self, output=None):
        BaseReporter.__init__(self, output)

    def add_message(self, msg_id, location, msg):
        pass

    def _display(self, layout):
        pass


class PylintTestCase(TestCase):

    def test_score(self):
        out = DummyReporter()
        r = Run(['--errors-only', "--jobs=8", 'standalone',
                 'server', 'tests'], reporter=out, exit=False)
#        self.assertEquals(len(out.messages), 2, msg=str(out.messages))
        self.assertEquals(
            r.linter.stats["error"], 0, "%i pylint error found: please run make static-test for further detail" % r.linter.stats["error"])
