#!/usr/bin/env python
# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; coding: utf-8; -*-
# vim:set ft=python ts=4 sw=4 sts=4 autoindent:

'''
Server request dispatching mechanism.

Author:     Pontus Stenetorp    <pontus is s u-tokyo ac jp>
Version:    2011-04-21
'''

# TODO: refactor protocol using an object oriented implementation
#       actions and messages should be defined as objects
#       at definition time, an Action observe a Message type
#       dispatch will be easier to maintain

# standard
from __future__ import absolute_import
from os.path import abspath, normpath
from os.path import join as path_join
from inspect import getargspec
from logging import info as log_info

# third party
from six.moves import zip

# arat
from server.annotator import create_arc, delete_arc, reverse_arc
from server.annotator import create_span, delete_span
from server.annotator import split_span
from server.auth import login, logout, whoami, NotAuthorisedError
from server.common import ProtocolError
from config import DATA_DIR
from server.convert.convert import convert
from server.docimport import save_import
from server.document import (get_directory_information, get_document,
                             get_document_timestamp, get_configuration)
from server.download import download_file, download_collection

from server.annlog import log_annotation
from server.svg import store_svg, retrieve_stored
from server.session import get_session, load_conf, save_conf
from server.search import search_text, search_entity, search_event, search_relation, search_note
from server.predict import suggest_span_types
from server.undo import undo
from server.tag import tag
from server.delete import delete_document, delete_collection

# unsupported action because of unmaintened dependency
# from server.norm import norm_get_name, norm_search, norm_get_data


def logging_no_op(collection, document, log):
    """
    no-op function that can be invoked by client to log a user action
    """
    return {}


# Constants
# Function call-backs
DISPATCHER = {
    'getCollectionInformation': get_directory_information,
    'getDocument': get_document,
    'getDocumentTimestamp': get_document_timestamp,
    'importDocument': save_import,

    'storeSVG': store_svg,
    'retrieveStored': retrieve_stored,
    'downloadFile': download_file,
    'downloadCollection': download_collection,

    'login': login,
    'logout': logout,
    'whoami': whoami,

    'createSpan': create_span,
    'deleteSpan': delete_span,
    'splitSpan': split_span,

    'createArc': create_arc,
    'reverseArc': reverse_arc,
    'deleteArc': delete_arc,

    # NOTE: search actions are redundant to allow different
    # permissions for single-document and whole-collection search.
    'searchTextInDocument': search_text,
    'searchEntityInDocument': search_entity,
    'searchEventInDocument': search_event,
    'searchRelationInDocument': search_relation,
    'searchNoteInDocument': search_note,
    'searchTextInCollection': search_text,
    'searchEntityInCollection': search_entity,
    'searchEventInCollection': search_event,
    'searchRelationInCollection': search_relation,
    'searchNoteInCollection': search_note,

    'suggestSpanTypes': suggest_span_types,

    'logAnnotatorAction': logging_no_op,

    'saveConf': save_conf,
    'loadConf': load_conf,

    'undo': undo,
    'tag': tag,

    'deleteDocument': delete_document,
    'deleteCollection': delete_collection,

    # normalization support
    # deactivated because of unmaintened dependency simstring
    #'normGetName': norm_get_name,
    #'normSearch': norm_search,
    #'normData': norm_get_data,

    # Visualisation support
    'getConfiguration': get_configuration,
    'convert': convert,
}

# Actions that correspond to annotation functionality
ANNOTATION_ACTION = set((
    'createArc',
    'deleteArc',
    'createSpan',
    'deleteSpan',
    'splitSpan',
    'suggestSpanTypes',
    'undo',
))

# Actions that will be logged as annotator actions (if so configured)
LOGGED_ANNOTATOR_ACTION = ANNOTATION_ACTION | set((
    'getDocument',
    'logAnnotatorAction',
))

# Actions that require authentication
REQUIRES_AUTHENTICATION = ANNOTATION_ACTION | set((
    # Document functionality
    'importDocument',

    # Search functionality in whole collection (heavy on the CPU/disk ATM)
    'searchTextInCollection',
    'searchEntityInCollection',
    'searchEventInCollection',
    'searchRelationInCollection',
    'searchNoteInCollection',

    'tag',
))

# Sanity check
for req_action in REQUIRES_AUTHENTICATION:
    assert req_action in DISPATCHER, (
        'INTERNAL ERROR: undefined action in REQUIRES_AUTHENTICATION set')
###


class NoActionError(ProtocolError):
    """
    Action is midding in message
    """

    def __str__(self):
        return 'Client sent no action for request'

    def json(self, json_dic):
        json_dic['exception'] = 'noAction'
        return json_dic


class InvalidActionError(ProtocolError):
    """
    Action not included in the protocol
    """

    def __init__(self, attempted_action):
        ProtocolError.__init__(self)
        self.attempted_action = attempted_action

    def __str__(self):
        return 'Client sent an invalid action "%s"' % self.attempted_action

    def json(self, json_dic):
        json_dic['exception'] = 'invalidAction',
        return json_dic


class InvalidActionArgsError(ProtocolError):
    """
    Action exists but an argument is invalid
    """

    def __init__(self, attempted_action, missing_arg):
        ProtocolError.__init__(self)
        self.attempted_action = attempted_action
        self.missing_arg = missing_arg

    def __str__(self):
        return 'Client did not supply argument "%s" for action "%s"' % (self.missing_arg, self.attempted_action)

    def json(self, json_dic):
        json_dic['exception'] = 'invalidActionArgs',
        return json_dic


class DirectorySecurityError(ProtocolError):
    """
    Wrong directory or missing access right to a directory
    """

    def __init__(self, requested):
        ProtocolError.__init__(self)
        self.requested = requested

    def __str__(self):
        return 'Client sent request for bad directory: ' + self.requested

    def json(self, json_dic):
        json_dic['exception'] = 'directorySecurity',
        return json_dic


class ProtocolVersionMismatchError(ProtocolError):
    """
    Client/Server protocol mismatch
    """

    def __init__(self, was, correct):
        ProtocolError.__init__(self)
        self.was = was
        self.correct = correct

    def __str__(self):
        return '\n'.join((
            ('Client-server mismatch, please reload the page to update your '
             'client. If this does not work, please contact your '
             'administrator'),
            ('Client sent request with version "%s", server is using version '
             '%s') % (self.was, self.correct),
        ))

    def json(self, json_dic):
        json_dic['exception'] = 'protocolVersionMismatch',
        return json_dic


class Dispatcher(object):
    """
    Dispatcher class is reponsible of the routing of message
    to right action handler. This class ensure security the policy.
    """

    PROTOCOL_VERSION = 1

    def __init__(self):
        self.http_args = None
        self.client_ip = None
        self.client_hostname = None
        self.action = None
        self.action_function = None
        self.action_args = None

    @classmethod
    def _directory_is_safe(cls, dir_path):
        """
        Simple test that the directory is absolute and inside
        the data directory.
        """
        # TODO: Make this less naive
        if not dir_path.startswith('/'):
            # We only accept absolute paths in the data directory
            return False

        # Make a simple test that the directory is inside the data directory
        actual_dir_path = abspath(path_join(DATA_DIR, dir_path[1:]))
        return actual_dir_path.startswith(normpath(DATA_DIR))

    def _check_protocol_version(self):
        """
        CHeck that we don't have a protocol version mismatch
        """
        try:
            protocol_version = int(self.http_args['protocol'])
            if protocol_version != self.PROTOCOL_VERSION:
                raise ProtocolVersionMismatchError(protocol_version,
                                                   self.PROTOCOL_VERSION)
        except TypeError:
            raise ProtocolVersionMismatchError('None', self.PROTOCOL_VERSION)
        except ValueError:
            raise ProtocolVersionMismatchError(self.http_args['protocol'],
                                               self.PROTOCOL_VERSION)

    def _ensure_security_policy(self):
        """
        Ensure directory access right and authentication
        """

        # If we got a directory (collection), check it for security
        if self.http_args['collection'] is not None:
            if not self._directory_is_safe(self.http_args['collection']):
                raise DirectorySecurityError(self.http_args['collection'])

        # Make sure that we are authenticated if we are to do certain actions
        if self.action in REQUIRES_AUTHENTICATION:
            try:
                user = get_session()['user']
            except KeyError:
                user = None
            if user is None:
                log_info('Authorization failure for "%s" with hostname "%s"'
                         % (self.client_ip, self.client_hostname))
                raise NotAuthorisedError(self.action)

    def _get_action_handler_and_args(self):
        """
        Determine action handler and its arguements
        """

        # Fetch the action function for this action (if any)
        try:
            action_function = DISPATCHER[self.action]
        except KeyError:
            log_info('Invalid action "%s"' % self.action)
            raise InvalidActionError(self.action)

        # Determine what arguments the action function expects
        args, varargs, keywords, defaults = getargspec(action_function)

        # convert python argument names to protocol name
        # i.e.: id_ -> id
        args = [i.strip("_") for i in args]

        # We will not allow this for now, there is most likely no need for it
        assert varargs is None, 'no varargs for action functions'
        assert keywords is None, 'no keywords for action functions'

        # XXX: Quick hack
        if defaults is None:
            defaults = []

        # These arguments already has default values
        default_val_by_arg = {}
        for arg, default_val in zip(args[-len(defaults):], defaults):
            default_val_by_arg[arg] = default_val

        action_args = []
        for arg_name in args:
            arg_val = self.http_args[arg_name]

            # The client failed to provide this argument
            if arg_val is None:
                try:
                    arg_val = default_val_by_arg[arg_name]
                except KeyError:
                    raise InvalidActionArgsError(self.action, arg_name)

            action_args.append(arg_val)

        log_info('dispatcher will call %s(%s)' % (self.action,
                                                  ', '.join((repr(a) for a in action_args)), ))

        # Log annotation actions separately (if so configured)
        self._logging("START")

        self.action_function = action_function
        self.action_args = action_args

    def _logging(self, state):
        """
        Log annotation actions separately (if so configured)
        """
        if self.action in LOGGED_ANNOTATOR_ACTION:
            log_annotation(self.http_args['collection'],
                           self.http_args['document'],
                           state, self.action, self.action_args)

    def __call__(self, http_args, client_ip, client_hostname):
        """
        Dispatch message to the right action handler
        """

        self.http_args = http_args
        self.client_ip = client_ip
        self.client_hostname = client_hostname
        self.action = http_args['action']

        log_info('dispatcher handling action: %s' % (self.action, ))

        self._check_protocol_version()

        # Was an action supplied?
        if self.action is None:
            raise NoActionError

        self._ensure_security_policy()

        self._get_action_handler_and_args()

        # TODO: log_annotation for exceptions?

        json_dic = self.action_function(*self.action_args)

        self._logging("FINNISH")

        # Assign which action that was performed to the json_dic
        json_dic['action'] = self.action
        # Return the protocol version for symmetry
        json_dic['protocol'] = self.PROTOCOL_VERSION
        return json_dic

    def last_call(self):
        """
        Last call arguments
        """
        return (self.http_args, self.client_ip, self.client_hostname)


def dispatch(http_args, client_ip, client_hostname):
    """
    Wrapper around Dispatcher class
    """
    return Dispatcher()(http_args, client_ip, client_hostname)
