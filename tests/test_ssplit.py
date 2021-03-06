#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 23:01:02 2018

@author: neophnx
"""
import unittest

from arat.server import ssplit


class TestSentenceSplit(unittest.TestCase):

    def testJapanese(self):
        sentence = u'　変しん！　両になった。うそ！　かも　'
        print('Sentence:', sentence)
        print('Len sentence:', len(sentence))

        ret = [o for o in ssplit.jp_sentence_boundary_gen(sentence)]
        ans = [(1, 5), (6, 12), (12, 15), (16, 18)]
        self.assertEqual(ret, ans)
        print('Successful!')

    def testEnglish(self):
        sentence = ' One of these days Jimmy, one of these days. Boom! Kaboom '
        print('Sentence:', sentence)
        print('Len sentence:', len(sentence))

        ret = [o for o in ssplit.en_sentence_boundary_gen(sentence)]
        ans = [(1, 44), (45, 50), (51, 57)]
        self.assertEqual(ret, ans)
        print('Successful!')
