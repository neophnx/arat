#!/usr/bin/env python

'''
Annotation undo functionality.

Author:     Pontus Stenetorp    <pontus stenetorp se>
Version:    2011-11-30
'''

from __future__ import with_statement
from __future__ import absolute_import

from os.path import join as path_join

from server.annotator import delete_span, create_span
from server.annotation import TextAnnotations
from server.common import ProtocolError
from server.jsonwrap import loads as json_loads


class CorruptUndoTokenError(ProtocolError):
    def __str__(self):
        return 'Undo token corrupted, unable to process'

    def json(self, json_dic):
        json_dic['exception'] = 'corruptUndoTokenError'


class InvalidUndoTokenError(ProtocolError):
    def __init__(self, attrib):
        self.attrib = attrib

    def __str__(self):
        return 'Undo token missing %s' % self.attrib

    def json(self, json_dic):
        json_dic['exception'] = 'invalidUndoTokenError'


class NonUndoableActionError(ProtocolError):
    def __str__(self):
        return 'Unable to undo the given action'

    def json(self, json_dic):
        json_dic['exception'] = 'nonUndoableActionError'


def undo(collection, document, token):
    try:
        token = json_loads(token)
    except ValueError:
        raise CorruptUndoTokenError
    try:
        action = token['action']
    except KeyError:
        raise InvalidUndoTokenError('action')

    if action == 'add_tb':
        # Undo an addition
        return delete_span(collection, document, token['id'])
    if action == 'mod_tb':
        # Undo a modification
        # TODO: We do not handle attributes and comments
        raise NotImplementedError

        # FIX: create_span call does not fit with the current implementation
#        return create_span(collection, document, token['start'], token['end'],
#                token['type'], id=token['id'], attributes=token['attributes'],
#                comment=token['comment'] if 'comment' in token else None)
    else:
        raise NonUndoableActionError
    assert False, 'should have returned prior to this point'


if __name__ == '__main__':
    # XXX: Path to...
    pass
