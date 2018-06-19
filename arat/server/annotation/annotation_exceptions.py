#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  4 15:03:18 2018

@author: jgo
"""

import warnings
import six

from arat.server.common import ProtocolError


class AnnotationLineSyntaxError(Exception):
    """
    AnnotationLineSyntaxError includes context of error
    """

    def __init__(self, line, line_num, filepath):
        Exception.__init__(self)
        self.line = line
        self.line_num = line_num
        self.filepath = filepath

    def __str__(self):
        return u'Syntax error on line %d: "%s"' % (self.line_num, self.line)


class IdedAnnotationLineSyntaxError(AnnotationLineSyntaxError):
    """
    Same as AnnotationLineSyntaxError with id included in the context
    """

    def __init__(self, id_, line, line_num, filepath):
        AnnotationLineSyntaxError.__init__(self, line, line_num, filepath)
        self.id_ = id_

    def __str__(self):
        return u'Syntax error on line %d (id %s): "%s"' % (
            self.line_num, self.id_, self.line)


class AnnotationNotFoundError(Exception):
    """
    AnnotationNotFoundError means no annotation with the given id exists
    """

    def __init__(self, id_):
        Exception.__init__(self)
        self.id_ = id_

    def __str__(self):
        return u'Could not find an annotation with id: %s' % (self.id_, )


class AnnotationFileNotFoundError(ProtocolError):
    """
    AnnotationCollectionNotFoundError: collection of annotations can't be found
    """

    def __init__(self, filename):
        ProtocolError.__init__(self)
        self.filename = filename

    def __str__(self):
        return u'Could not find any annotations for %s' % (self.filename, )


class AnnotationCollectionNotFoundError(ProtocolError):
    """
    AnnotationCollectionNotFoundError: collection of annotations can't be found
    """

    def __init__(self, collection):
        ProtocolError.__init__(self)
        self.collection = collection

    def __str__(self):
        return u'Error accessing collection %s' % (self.collection, )


class EventWithoutTriggerError(ProtocolError):
    """
    Event missing a trigger
    """

    def __init__(self, event):
        ProtocolError.__init__(self)
        self.event = event

    def __str__(self):
        return u'Event "%s" lacks a trigger' % (self.event, )


class EventWithNonTriggerError(ProtocolError):
    """
    Wrong type used as trigger
    """

    def __init__(self, event, non_trigger):
        ProtocolError.__init__(self)
        self.event = event
        self.non_trigger = non_trigger

    def __str__(self):
        return u'Non-trigger "%s" used by "%s" as trigger' % (self.non_trigger,
                                                              self.event)


class TriggerReferenceError(ProtocolError):
    def __init__(self, trigger, referencer):
        ProtocolError.__init__(self)
        self.trigger = trigger
        self.referencer = referencer

    def __str__(self):
        return u'Trigger "%s" referenced by non-event "%s"' % (self.trigger,
                                                               self.referencer)


class AnnotationTextFileNotFoundError(AnnotationFileNotFoundError):
    def __str__(self):
        return u'Could not read text file for %s' % (self.filename, )


class AnnotationsIsReadOnlyError(ProtocolError):
    def __init__(self, filename):
        ProtocolError.__init__(self)
        self.filename = filename

    def __str__(self):
        # No extra message; the client is doing a fine job of reporting this
        # return
        return ''


class DuplicateAnnotationIdError(AnnotationLineSyntaxError):
    def __init__(self, id_, line, line_num, filepath):
        AnnotationLineSyntaxError.__init__(self, line, line_num, filepath)
        self.id_ = id_

    def __str__(self):
        return u'Duplicate id: %s on line %d (id %s): "%s"' % (self.id_,
                                                               self.line_num,
                                                               self.id_,
                                                               self.line)


class InvalidIdError(Exception):
    def __init__(self, id_):
        Exception.__init__(self)
        self.id_ = id_

    def __str__(self):
        return u'Invalid id: %s' % (self.id_, )


class DependingAnnotationDeleteError(Exception):
    """
    Can't delete this annotation, other annotations still depends on it
    """

    def __init__(self, target, dependants):
        Exception.__init__(self)
        self.target = target
        self.dependants = dependants

    def __str__(self):
        args = (six.text_type(self.target).rstrip(),
                ",".join([six.text_type(d).rstrip() for d in self.dependants]))
        return u'%s can not be deleted due to depending annotations %s' % args

    def html_error_str(self, response=None):
        args = (six.text_type(self.target).rstrip(),
                ",".join([six.text_type(d).rstrip() for d in self.dependants]))
        return u'''Annotation:
        %s
        Has depending annotations attached to it:
        %s''' % args


class SpanOffsetOverlapError(ProtocolError):
    def __init__(self, offsets):
        ProtocolError.__init__(self)
        self.offsets = offsets

    def __str__(self):
        arg = ', '.join(six.text_type(e) for e in [self.offsets])
        return u'The offsets [%s] overlap' % arg


def deprecation(message):
    warnings.warn(message, DeprecationWarning, stacklevel=2)
