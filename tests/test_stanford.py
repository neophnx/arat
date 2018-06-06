
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 10:58:39 2018

@author: phnx
"""
from __future__ import absolute_import
import unittest
from sys import stdout

import tests_common
from convert import stanford



class TestStanford(unittest.TestCase):
    STANFORD_XML = '''<?xml version="1.0" encoding="UTF-8"?>
    <?xml-stylesheet href="CoreNLP-to-HTML.xsl" type="text/xsl"?>
    <root>
      <document>
        <sentences>
          <sentence id="1">
            <tokens>
              <token id="1">
                <word>Stanford</word>
                <lemma>Stanford</lemma>
                <CharacterOffsetBegin>0</CharacterOffsetBegin>
                <CharacterOffsetEnd>8</CharacterOffsetEnd>
                <POS>NNP</POS>
                <NER>ORGANIZATION</NER>
              </token>
              <token id="2">
                <word>University</word>
                <lemma>University</lemma>
                <CharacterOffsetBegin>9</CharacterOffsetBegin>
                <CharacterOffsetEnd>19</CharacterOffsetEnd>
                <POS>NNP</POS>
                <NER>ORGANIZATION</NER>
              </token>
              <token id="3">
                <word>is</word>
                <lemma>be</lemma>
                <CharacterOffsetBegin>20</CharacterOffsetBegin>
                <CharacterOffsetEnd>22</CharacterOffsetEnd>
                <POS>VBZ</POS>
                <NER>O</NER>
              </token>
              <token id="4">
                <word>located</word>
                <lemma>located</lemma>
                <CharacterOffsetBegin>23</CharacterOffsetBegin>
                <CharacterOffsetEnd>30</CharacterOffsetEnd>
                <POS>JJ</POS>
                <NER>O</NER>
              </token>
              <token id="5">
                <word>in</word>
                <lemma>in</lemma>
                <CharacterOffsetBegin>31</CharacterOffsetBegin>
                <CharacterOffsetEnd>33</CharacterOffsetEnd>
                <POS>IN</POS>
                <NER>O</NER>
              </token>
              <token id="6">
                <word>California</word>
                <lemma>California</lemma>
                <CharacterOffsetBegin>34</CharacterOffsetBegin>
                <CharacterOffsetEnd>44</CharacterOffsetEnd>
                <POS>NNP</POS>
                <NER>LOCATION</NER>
              </token>
              <token id="7">
                <word>.</word>
                <lemma>.</lemma>
                <CharacterOffsetBegin>44</CharacterOffsetBegin>
                <CharacterOffsetEnd>45</CharacterOffsetEnd>
                <POS>.</POS>
                <NER>O</NER>
              </token>
            </tokens>
            <parse>(ROOT (S (NP (NNP Stanford) (NNP University)) (VP (VBZ is) (ADJP (JJ located) (PP (IN in) (NP (NNP California))))) (. .))) </parse>
            <basic-dependencies>
              <dep type="nn">
                <governor idx="2">University</governor>
                <dependent idx="1">Stanford</dependent>
              </dep>
              <dep type="nsubj">
                <governor idx="4">located</governor>
                <dependent idx="2">University</dependent>
              </dep>
              <dep type="cop">
                <governor idx="4">located</governor>
                <dependent idx="3">is</dependent>
              </dep>
              <dep type="prep">
                <governor idx="4">located</governor>
                <dependent idx="5">in</dependent>
              </dep>
              <dep type="pobj">
                <governor idx="5">in</governor>
                <dependent idx="6">California</dependent>
              </dep>
            </basic-dependencies>
            <collapsed-dependencies>
              <dep type="nn">
                <governor idx="2">University</governor>
                <dependent idx="1">Stanford</dependent>
              </dep>
              <dep type="nsubj">
                <governor idx="4">located</governor>
                <dependent idx="2">University</dependent>
              </dep>
              <dep type="cop">
                <governor idx="4">located</governor>
                <dependent idx="3">is</dependent>
              </dep>
              <dep type="prep_in">
                <governor idx="4">located</governor>
                <dependent idx="6">California</dependent>
              </dep>
            </collapsed-dependencies>
            <collapsed-ccprocessed-dependencies>
              <dep type="nn">
                <governor idx="2">University</governor>
                <dependent idx="1">Stanford</dependent>
              </dep>
              <dep type="nsubj">
                <governor idx="4">located</governor>
                <dependent idx="2">University</dependent>
              </dep>
              <dep type="cop">
                <governor idx="4">located</governor>
                <dependent idx="3">is</dependent>
              </dep>
              <dep type="prep_in">
                <governor idx="4">located</governor>
                <dependent idx="6">California</dependent>
              </dep>
            </collapsed-ccprocessed-dependencies>
          </sentence>
          <sentence id="2">
            <tokens>
              <token id="1">
                <word>It</word>
                <lemma>it</lemma>
                <CharacterOffsetBegin>46</CharacterOffsetBegin>
                <CharacterOffsetEnd>48</CharacterOffsetEnd>
                <POS>PRP</POS>
                <NER>O</NER>
              </token>
              <token id="2">
                <word>is</word>
                <lemma>be</lemma>
                <CharacterOffsetBegin>49</CharacterOffsetBegin>
                <CharacterOffsetEnd>51</CharacterOffsetEnd>
                <POS>VBZ</POS>
                <NER>O</NER>
              </token>
              <token id="3">
                <word>a</word>
                <lemma>a</lemma>
                <CharacterOffsetBegin>52</CharacterOffsetBegin>
                <CharacterOffsetEnd>53</CharacterOffsetEnd>
                <POS>DT</POS>
                <NER>O</NER>
              </token>
              <token id="4">
                <word>great</word>
                <lemma>great</lemma>
                <CharacterOffsetBegin>54</CharacterOffsetBegin>
                <CharacterOffsetEnd>59</CharacterOffsetEnd>
                <POS>JJ</POS>
                <NER>O</NER>
              </token>
              <token id="5">
                <word>university</word>
                <lemma>university</lemma>
                <CharacterOffsetBegin>60</CharacterOffsetBegin>
                <CharacterOffsetEnd>70</CharacterOffsetEnd>
                <POS>NN</POS>
                <NER>O</NER>
              </token>
              <token id="6">
                <word>.</word>
                <lemma>.</lemma>
                <CharacterOffsetBegin>70</CharacterOffsetBegin>
                <CharacterOffsetEnd>71</CharacterOffsetEnd>
                <POS>.</POS>
                <NER>O</NER>
              </token>
            </tokens>
            <parse>(ROOT (S (NP (PRP It)) (VP (VBZ is) (NP (DT a) (JJ great) (NN university))) (. .))) </parse>
            <basic-dependencies>
              <dep type="nsubj">
                <governor idx="5">university</governor>
                <dependent idx="1">It</dependent>
              </dep>
              <dep type="cop">
                <governor idx="5">university</governor>
                <dependent idx="2">is</dependent>
              </dep>
              <dep type="det">
                <governor idx="5">university</governor>
                <dependent idx="3">a</dependent>
              </dep>
              <dep type="amod">
                <governor idx="5">university</governor>
                <dependent idx="4">great</dependent>
              </dep>
            </basic-dependencies>
            <collapsed-dependencies>
              <dep type="nsubj">
                <governor idx="5">university</governor>
                <dependent idx="1">It</dependent>
              </dep>
              <dep type="cop">
                <governor idx="5">university</governor>
                <dependent idx="2">is</dependent>
              </dep>
              <dep type="det">
                <governor idx="5">university</governor>
                <dependent idx="3">a</dependent>
              </dep>
              <dep type="amod">
                <governor idx="5">university</governor>
                <dependent idx="4">great</dependent>
              </dep>
            </collapsed-dependencies>
            <collapsed-ccprocessed-dependencies>
              <dep type="nsubj">
                <governor idx="5">university</governor>
                <dependent idx="1">It</dependent>
              </dep>
              <dep type="cop">
                <governor idx="5">university</governor>
                <dependent idx="2">is</dependent>
              </dep>
              <dep type="det">
                <governor idx="5">university</governor>
                <dependent idx="3">a</dependent>
              </dep>
              <dep type="amod">
                <governor idx="5">university</governor>
                <dependent idx="4">great</dependent>
              </dep>
            </collapsed-ccprocessed-dependencies>
          </sentence>
        </sentences>
        <coreference>
          <coreference>
            <mention representative="true">
              <sentence>1</sentence>
              <start>1</start>
              <end>3</end>
              <head>2</head>
            </mention>
            <mention>
              <sentence>2</sentence>
              <start>1</start>
              <end>2</end>
              <head>1</head>
            </mention>
            <mention>
              <sentence>2</sentence>
              <start>3</start>
              <end>6</end>
              <head>5</head>
            </mention>
          </coreference>
        </coreference>
      </document>
    </root>
    '''

    def test_xml(self):
        
        xml_string = TestStanford.STANFORD_XML
        
        self.assertEquals(stanford.text(xml_string).encode('utf-8'), b"Stanford University is located in California. It is a great university.                                                    ")


    def test_pos(self):
        xml_string = TestStanford.STANFORD_XML
        self.assertEquals([i.type for i in stanford.pos(xml_string)],
                           [u'NNP',
                            u'NNP',
                            u'VBZ',
                            u'JJ',
                            u'IN',
                            u'NNP',
                            u'__DOT__',
                            u'PRP',
                            u'VBZ',
                            u'DT',
                            u'JJ',
                            u'NN',
                            u'__DOT__'])
                

    def test_ner(self):
        xml_string = TestStanford.STANFORD_XML
        self.assertEquals([(i.type, i.spans) for i in stanford.ner(xml_string)],
                           [(u'ORGANIZATION', ((0, 19),)), (u'LOCATION', ((34, 44),))])
                           
    def test_coref(self):
        xml_string = TestStanford.STANFORD_XML
        self.assertEquals([i.type for i in stanford.coref(xml_string)],
                           ['Mention', 'Mention', 'Mention', 'Coreference'])

    def test_coref(self):
        xml_string = TestStanford.STANFORD_XML

        self.assertEquals([i.type for i in stanford.basic_dep(xml_string)],
                           [u'NNP',
                            u'NNP',
                            u'VBZ',
                            u'JJ',
                            u'IN',
                            u'NNP',
                            u'__DOT__',
                            u'PRP',
                            u'VBZ',
                            u'DT',
                            u'JJ',
                            u'NN',
                            u'__DOT__',
                            'nn',
                            'nsubj',
                            'cop',
                            'prep',
                            'pobj',
                            'nsubj',
                            'cop',
                            'det',
                            'amod'])

    def test_collapsed_dep(self):
        xml_string = TestStanford.STANFORD_XML

        self.assertEquals([i.type for i in stanford.collapsed_dep(xml_string)],
                           [u'NNP',
                            u'NNP',
                            u'VBZ',
                            u'JJ',
                            u'IN',
                            u'NNP',
                            u'__DOT__',
                            u'PRP',
                            u'VBZ',
                            u'DT',
                            u'JJ',
                            u'NN',
                            u'__DOT__',
                            'nn',
                            'nsubj',
                            'cop',
                            'prep_in',
                            'nsubj',
                            'cop',
                            'det',
                            'amod'])
                           
    def test_collapsed_ccproc_dep(self):
        xml_string = TestStanford.STANFORD_XML

        self.assertEquals([i.type for i in stanford.collapsed_ccproc_dep(xml_string)],
                           [u'NNP',
                            u'NNP',
                            u'VBZ',
                            u'JJ',
                            u'IN',
                            u'NNP',
                            u'__DOT__',
                            u'PRP',
                            u'VBZ',
                            u'DT',
                            u'JJ',
                            u'NN',
                            u'__DOT__',
                            'nn',
                            'nsubj',
                            'cop',
                            'prep_in',
                            'nsubj',
                            'cop',
                            'det',
                            'amod'])

    def test_collapsed_token_offsets(self):
        xml_string = TestStanford.STANFORD_XML

        self.assertEquals([i for i in stanford.token_offsets(xml_string)],
                           [(0, 8),
                            (9, 19),
                            (20, 22),
                            (23, 30),
                            (31, 33),
                            (34, 44),
                            (44, 45),
                            (46, 48),
                            (49, 51),
                            (52, 53),
                            (54, 59),
                            (60, 70),
                            (70, 71)])

    def test_collapsed_sentence_offsets(self):
        """
        TODO: investigate missing stanford.collapsed_sentence_offsets
        """
        pass
        #xml_string = TestStanford.STANFORD_XML

        #self.assertEquals([i for i in stanford.collapsed_sentence_offsets(xml_string)],
        #                  [])



