#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 23:01:02 2018

@author: neophnx
"""
import unittest

from server import ssplit


class TestSentenceSplit(unittest.TestCase):
    def testEnglish1(self):

        sentence = u'This is a short sentence.\nthis is another one.'
        print('Sentence:', sentence)
        print('Len sentence:', len(sentence))

        ret = [o for o in ssplit.en_sentence_boundary_gen(sentence)]
        last_end = 0
        for start, end in ret:
            self.assertEquals(last_end, start)
            if last_end != start:
                print('DROPPED: "%s"' % sentence[last_end:start])
            print('SENTENCE: "%s"' % sentence[start:end])
            last_end = end
        print(ret)

    def testJapanese(self):
        sentence = u'　変しん！　両になった。うそ！　かも　'
        print('Sentence:', sentence)
        print('Len sentence:', len(sentence))

        ret = [o for o in ssplit.jp_sentence_boundary_gen(sentence)]
        ans = [(1, 5), (6, 12), (12, 15), (16, 18)]
        self.assertEquals(ret, ans)
        print('Successful!')

    def testEnglish1(self):
        sentence = ' One of these days Jimmy, one of these days. Boom! Kaboom '
        print('Sentence:', sentence)
        print('Len sentence:', len(sentence))

        ret = [o for o in ssplit.en_sentence_boundary_gen(sentence)]
        ans = [(1, 44), (45, 50), (51, 57)]
        self.assertEquals(ret, ans)
        print('Successful!')
