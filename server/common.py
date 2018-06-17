#!/usr/bin/env python
# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; coding: utf-8; -*-
# vim:set ft=python ts=4 sw=4 sts=4 autoindent:

'''
Functionality shared between server components.

Author:     Pontus Stenetorp    <pontus is s u-tokyo ac jp>
Version:    2011-04-21
'''


from __future__ import absolute_import
import warnings
try:  # python2
    from exceptions import NotImplementedError as NotImplementedErrorBultin
except:
    from builtins import NotImplementedError as NotImplementedErrorBultin


def deprecation(message):
    """
    Deprecation warning
    """
    warnings.warn(message, DeprecationWarning, stacklevel=2)


class ProtocolError(Exception):
    """
    Base exception class. This class is abstract, __str__ and json methods
    must be implemented.
    """

    def __str__(self):
        # TODO: just adding __str__ to ProtocolError, not all
        # currently support it, so falling back on this assumption
        # about how to make a (nearly) human-readable string. Once
        # __str__ added to all ProtocolErrors, raise
        # NotImplementedError instead.
        deprecation("Relying on ProtocolError.__str__ is deprecated, "
                    "subclass must implement it")
        return 'ProtocolError: %s (TODO: __str__() method)' % self.__class__

    @classmethod
    def json(cls, json_dic):
        """
        Overide json in order to provide a message to the client
        """
        assert isinstance(json_dic, dict)
        raise NotImplementedErrorBultin('abstract method')


class ProtocolArgumentError(ProtocolError):
    """
    Wrong argument usage.
    """
    @classmethod
    def json(cls, json_dic):
        json_dic['exception'] = 'protocolArgumentError'

    def __str__(self):
        return "Protocol error: wrong argument"

# If received by ajax.cgi, no JSON will be sent
# XXX: This is an ugly hack to circumvent protocol flaws


class NoPrintJSONError(Exception):
    """
    Critical situation, JSON can't be print
    """

    def __init__(self, hdrs, data):
        Exception.__init__(self)
        self.hdrs = hdrs
        self.data = data


class AratNotImplementedError(ProtocolError):
    """
    Indicates a missing implementation, this exception
    should never be encountered during normal operations.
    """
    @classmethod
    def json(cls, json_dic):
        json_dic['exception'] = 'notImplemented'


class NotImplementedError(AratNotImplementedError):
    """
    Deprecated see AratNotImplementedError
    """

    def __init__(self):
        deprecation("NotImplementedError is deprecated, "
                    "use AratNotImplementedError instead")
        AratNotImplementedError.__init__(self)


class CollectionNotAccessibleError(ProtocolError):
    """
    I/O exception while loading or storing a collection
    """
    @classmethod
    def json(cls, json_dic):
        json_dic['exception'] = 'collectionNotAccessible'

    def __str__(self):
        return 'Error: collection not accessible'

# TODO: We have issues using this in relation to our inspection
#       in dispatch, can we make it work?
# Wrapper to send a deprecation warning to the client if debug is set


def deprecated_action(func):
    """
    Encapsulate a deprecation warning to the client in DEBUG mode.
    """
    try:
        from config import DEBUG
    except ImportError:
        DEBUG = False
    from functools import wraps
    from server.message import Messager

    @wraps(func)
    def wrapper(*args, **kwds):
        """
        Add message sending to func
        """
        if DEBUG:
            Messager.warning(('Client sent "%s" action '
                              'which is marked as deprecated') % func.__name__,)
        return func(*args, **kwds)
    return wrapper


def relpath(path, start='.'):
    """Return a relative version of a path"""
    deprecation("common.relpath is deprecated, use os.relpath instead")
    from os import path
    return path.relpath(path, start)
