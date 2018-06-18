# -*- coding: utf-8 -*-
"""
Created on Sun Jun  3 10:58:39 2018

@author: phnx
"""
from __future__ import absolute_import
import unittest

from server.annotation import annotation_exceptions as excep


class TestAnnotationExceptions(unittest.TestCase):
    """
    Test annotation exceptions

    makes sure exceptions are instantiable and printable
    """

    def setUp(self):
        self.json_dic = {"foo": "bar"}

    def test_01(self):
        """
        AnnotationLineSyntaxError
        """
        value = excep.AnnotationLineSyntaxError(
            "a line of text", 10, "/file/path")
        self.assertEquals(str(value),
                          'Syntax error on line 10: "a line of text"')

    def test_02(self):
        """
        IdedAnnotationLineSyntaxError
        """
        value = excep.IdedAnnotationLineSyntaxError("T1",
                                                    "a line of text",
                                                    10,
                                                    "/file/path")
        self.assertEquals(str(value),
                          'Syntax error on line 10 (id T1): "a line of text"')

    def test_03(self):
        """
        AnnotationNotFoundError
        """
        value = excep.AnnotationNotFoundError("T1")
        self.assertEquals(str(value),
                          'Could not find an annotation with id: T1')

    def test_04(self):
        """
        AnnotationFileNotFoundError
        """
        value = excep.AnnotationFileNotFoundError("/some/path")
        self.assertEquals(str(value),
                          'Could not find any annotations for /some/path')
        value.json(self.json_dic)
        self.assertEquals(self.json_dic,
                          {'exception': 'annotationFileNotFound',
                           'foo': 'bar'})

    def test_05(self):
        """
        AnnotationCollectionNotFoundError
        """
        value = excep.AnnotationCollectionNotFoundError("/some/path")
        self.assertEquals(str(value),
                          'Error accessing collection /some/path')
        self.assertEquals(value.json(self.json_dic),
                          {'exception': 'annotationCollectionNotFound',
                           'foo': 'bar'})

    def test_06(self):
        """
        EventWithoutTriggerError
        """
        value = excep.EventWithoutTriggerError("E1")
        self.assertEquals(str(value),
                          'Event "E1" lacks a trigger')
        self.assertEquals(value.json(self.json_dic),
                          {'exception': 'eventWithoutTrigger',
                           'foo': 'bar'})

    def test_07(self):
        """
        EventWithNonTriggerError
        """
        value = excep.EventWithNonTriggerError("E1", "T1")
        self.assertEquals(str(value),
                          'Non-trigger "T1" used by "E1" as trigger')
        self.assertEquals(value.json(self.json_dic),
                          {'exception': 'eventWithNonTrigger',
                           'foo': 'bar'})

    def test_08(self):
        """
        TriggerReferenceError
        """
        value = excep.TriggerReferenceError("E1", "T1")
        self.assertEquals(str(value),
                          'Trigger "E1" referenced by non-event "T1"')
        self.assertEquals(value.json(self.json_dic),
                          {'exception': 'triggerReference',
                           'foo': 'bar'})

    def test_09(self):
        """
        AnnotationTextFileNotFoundError
        """
        value = excep.AnnotationTextFileNotFoundError("/some/path")
        self.assertEquals(str(value),
                          'Could not read text file for /some/path')
        self.assertEquals(value.json(self.json_dic),
                          {'exception': 'annotationTextFileNotFound',
                           'foo': 'bar'})

    def test_10(self):
        """
        AnnotationsIsReadOnlyError
        """
        value = excep.AnnotationsIsReadOnlyError("/some/path")
        self.assertEquals(str(value),
                          '')
        self.assertEquals(value.json(self.json_dic),
                          {'exception': 'annotationsIsReadOnly',
                           'foo': 'bar'})

    def test_11(self):
        """
        DuplicateAnnotationIdError
        """
        value = excep.DuplicateAnnotationIdError(id_="T1",
                                                 line="T1 10 12",
                                                 line_num=23,
                                                 filepath="/some/path")
        self.assertEquals(str(value),
                          'Duplicate id: T1 on line 23 (id T1): "T1 10 12"')

    def test_12(self):
        """
        InvalidIdError
        """
        value = excep.InvalidIdError("_*<")
        self.assertEquals(str(value),
                          'Invalid id: _*<')

    def test_13(self):
        """
        DependingAnnotationDeleteError
        """
        value = excep.DependingAnnotationDeleteError("T1", ["E2", "T2"])
        self.assertEquals(str(value),
                          'T1 can not be deleted due to depending annotations E2,T2')
        self.assertEquals(value.html_error_str(),
                          'Annotation:\n'
                          '        T1\n'
                          '        Has depending annotations attached to it:\n'
                          '        E2,T2')

    def test_14(self):
        """
        SpanOffsetOverlapError
        """
        value = excep.SpanOffsetOverlapError([(0, 10), (5, 15)])
        self.assertEquals(str(value),
                          'The offsets [[(0, 10), (5, 15)]] overlap')


if __name__ == "__main__":
    import sys
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestAnnotationExceptions)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
