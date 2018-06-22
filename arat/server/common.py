#!/usr/bin/env python
# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; coding: utf-8; -*-
# vim:set ft=python ts=4 sw=4 sts=4 autoindent:

'''
Functionality shared between server components.

Author:     Pontus Stenetorp    <pontus is s u-tokyo ac jp>
Version:    2011-04-21
'''

# future
from __future__ import absolute_import
from __future__ import print_function

# standard
import warnings

# third party
from tornado.web import RequestHandler
import ujson as json


class JsonHandler(RequestHandler):
    """
    Abstract class tking care of JSON serialization/ deserialization

    """

    def post(self):
        """
        This method should be called by tornado
        """
        body = json.loads(self.request.body)
        action = body.get(u"action", None)

        print(body)
        if u"protocol" in body:
            del body["protocol"]
        if u"action" in body:
            del body["action"]

        body = {(i+"_" if i in ["id", "type"] else i): j
                for i, j
                in body.items()}

        response = self._post(**body)

        if "messages" not in response:
            response["messages"] = []

        if "action" not in response and action is not None:
            response["action"] = action

        print(response)

        self.set_header("Content-Type", "text/json")
        self.write(json.dumps(response))

    def _post(self, **args):
        """
        Overide this method to implement handler.

        args are unpacked from JSON request
        expect a dict result to serialized to JSON

        """
        raise NotImplementedError

    def data_received(self):
        """
        Streamed request are not implemented
        """
        # provides a no-op implementation to prevent pylint to complain about
        # missing overide
        pass


class AuthenticatedJsonHandler(JsonHandler):
    """
    Same a JsonHandler with authentication check
    """

    def post(self,):
        if self.get_secure_cookie('user') is None:
            self.set_status(403)
            self.finish()
            return

        JsonHandler.post(self)

    def _post(self, **args):
        """
        Overide this method to implement an handler
        wich requires authorization.

        args are unpacked from JSON request
        expect a dict result to serialized to JSON

        """
        raise NotImplementedError


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
        raise NotImplementedError

    def json(self, json_dic):
        """
        This method don't need to be overidden
        """
        assert isinstance(json_dic, dict)
        name = self.__class__.__name__

        name = name[0].lower() + name[1:]
        if name.endswith("Error"):
            name = name[:-5]
        json_dic['exception'] = name

        return json_dic


class ProtocolArgumentError(ProtocolError):
    """
    Wrong argument usage.
    """
    @classmethod
    def json(cls, json_dic):
        json_dic['exception'] = 'protocolArgumentError'

    def __str__(self):
        return "Protocol error: wrong argument"


class AratNotImplementedError(ProtocolError):
    """
    Indicates a missing implementation, this exception
    should never be encountered during normal operations.
    """

    def __str__(self):
        return u'Not implemented'


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
    from arat.server.message import Messager

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
