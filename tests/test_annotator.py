# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 10:58:39 2018

@author: phnx
"""
from __future__ import absolute_import
import unittest

from arat.server import annotator as ant
from arat.server.common import ProtocolArgumentError
from arat.server.annotation.annotation_common import TextAnnotations
from arat.server.annotation.annotation_exceptions import AnnotationNotFoundError
from arat.server.projectconfig.projectconfiguration import ProjectConfiguration
import config


class TestAnnotator(unittest.TestCase):
    """
    Test annotator
    """

    def test__offsets_equal(self):
        """
        annotator._offsets_equal
        """
        # pylint: disable=W0212
        # common cases
        self.assertTrue(ant._offsets_equal([], []))
        self.assertTrue(ant._offsets_equal([(1, 1)], [(1, 1)]))
        self.assertTrue(ant._offsets_equal([(0, 1), (3, 5)],
                                           [(0, 1), (3, 5)]))
        self.assertFalse(ant._offsets_equal([(0, 1), (3, 5)],
                                            [(0, 1), (3, 6)]))

        # unorderd list of offsets
        self.assertTrue(ant._offsets_equal([(0, 1), (3, 5)],
                                           [(3, 5), (0, 1)]))
        self.assertFalse(ant._offsets_equal([(0, 1), (3, 5)],
                                            [(3, 6), (0, 1)]))

        # repetition
        self.assertTrue(ant._offsets_equal([(0, 1), (3, 5)],
                                           [(3, 5), (0, 1), (0, 1)]))
        self.assertFalse(ant._offsets_equal([(0, 1), (3, 5)],
                                            [(3, 6), (0, 1), (0, 1)]))

        # overlap
        self.assertTrue(ant._offsets_equal([(0, 5)],
                                           [(3, 5), (0, 3)]))
        self.assertFalse(ant._offsets_equal([(0, 5)],
                                            [(3, 6), (0, 3)]))

    def test__text_for_offsets(self):
        """
        annotator._text_for_offsets
        """
        # pylint: disable=W0212

        # common case
        self.assertEqual(ant._text_for_offsets("Welcome home!",
                                               [(0, 2), (8, 10)]),
                         "We ho")

        # overlap
        self.assertEqual(ant._text_for_offsets("Welcome home!",
                                               [(0, 2), (0, 1)]),
                         "We")

        # out of bounds
        self.assertRaises(ProtocolArgumentError,
                          ant._text_for_offsets,
                          "Welcome home!",
                          [(-10, 2), (0, 1)])

        self.assertRaises(ProtocolArgumentError,
                          ant._text_for_offsets,
                          "Welcome home!",
                          [(0, 2), (0, 100)])

    def test__edit_span(self):
        """
        annotator.__edit_span
        """
        # pylint: disable=W0212

        ann_obj = TextAnnotations(
            config.DATA_DIR+"/example-data/corpora/BioNLP-ST_2011/BioNLP-ST_2011_EPI/PMID-11393792")
        projectconf = ProjectConfiguration(
            "/example-data/corpora/BioNLP-ST_2011/BioNLP-ST_2011_EPI/")
        modif_tracker = ant.ModificationTracker()
        undo_resp = {}

        # change type
        self.assertEqual(ann_obj.get_ann_by_id('T6').type_,
                         'Protein')

        ant._edit_span(ann_obj=ann_obj,
                       mods=modif_tracker,
                       id_="T6",
                       offsets=[(1254, 1263)],
                       projectconf=projectconf,
                       attributes={},
                       type_='Entity',
                       undo_resp=undo_resp)

        self.assertEqual(modif_tracker.json_response(),
                         {'edited': [[u'T6']]})

        self.assertEqual(ann_obj.get_ann_by_id('T6').type_,
                         'Entity')

        self.assertEqual(undo_resp,
                         {'action': 'mod_tb',
                          'type': u'Protein',
                          'id': u'T6',
                          'offsets': [(1254, 1263)]})

        self.assertRaises(AnnotationNotFoundError,
                          ant._edit_span,
                          ann_obj=ann_obj,
                          mods=modif_tracker,
                          id_="T2048",
                          offsets=[(1254, 1263)],
                          projectconf=projectconf,
                          attributes={},
                          type_='Entity',
                          undo_resp=undo_resp)

        # change offset
        ant._edit_span(ann_obj=ann_obj,
                       mods=modif_tracker,
                       id_="T6",
                       offsets=[(1254, 1265)],
                       projectconf=projectconf,
                       attributes={},
                       type_='Protein',
                       undo_resp=undo_resp)

        self.assertEqual(modif_tracker.json_response(),
                         {'edited': [[u'T6']]})

        self.assertEqual(undo_resp,
                         {'action': 'mod_tb',
                          'type': u'Entity',
                          'id': u'T6',
                          'offsets': [(1254, 1263)]})

        self.assertRaises(AnnotationNotFoundError,
                          ant._edit_span,
                          ann_obj=ann_obj,
                          mods=modif_tracker,
                          id_="T2048",
                          offsets=[(1254, 1263)],
                          projectconf=projectconf,
                          attributes={},
                          type_='Entity',
                          undo_resp=undo_resp)


if __name__ == "__main__":
    import sys
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestAnnotator)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
