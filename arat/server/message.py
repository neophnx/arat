#!/usr/bin/env python
# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; coding: utf-8; -*-
# vim:set ft=python ts=4 sw=4 sts=4 autoindent:

'''
Server-to-client messaging-related functionality
for Arat Rapid Annotation Tool (arat)


Author:     Pontus Stenetorp    <pontus is s u-tokyo ac jp>
Author:     Sampo Pyysalo       <smp is s u-tokyo ac jp>
Version:    2011-05-31
'''

# future
from __future__ import absolute_import
from __future__ import print_function

# standard
import re
from cgi import escape

# third party
import six
from six.moves import map
from six import unichr  # pylint: disable=W0622
from six.moves import range  # pylint: disable=W0622

# for cleaning up control chars from a string, from
# http://stackoverflow.com/questions/92438/stripping-non-printable-characters-from-a-string-in-python
# allow tab (9) and [unix] newline (10)
__control_chars = ''.join(
    map(unichr, list(range(0, 9)) + list(range(11, 32)) + list(range(127, 160))))
__control_char_re = re.compile('[%s]' % re.escape(__control_chars))


def _remove_control_chars(s):
    """
    Remove non ascii and non printable characters
    """
    return __control_char_re.sub('', s)


class Messager(object):
    """
    Heap of pending messages
    """
    __pending_messages = []

    @classmethod
    def info(cls, msg, duration=3, escaped=False):
        """
        Add an info message
        """
        cls.__message(msg, 'comment', duration, escaped)

    @classmethod
    def warning(cls, msg, duration=3, escaped=False):
        """
        Add a warning message
        """
        cls.__message(msg, 'warning', duration, escaped)

    @classmethod
    def error(cls, msg, duration=3, escaped=False):
        """
        Add an error message
        """
        cls.__message(msg, 'error', duration, escaped)

    @classmethod
    def debug(cls, msg, duration=3, escaped=False):
        """
        Add a debug message
        """
        cls.__message(msg, 'debug', duration, escaped)

    @classmethod
    def output(cls, file_desc):
        """
        Output all message to the given file handler.
        The heap is unaltered, see clear()
        """
        for message, level, _ in cls.__pending_messages:
            print(level, ":", message, file=file_desc)

    @classmethod
    def output_json(cls, json_dict):
        """
        Add pending messages to json_dict and clear the heap
        """
        try:
            return cls.__output_json(json_dict)
        except Exception as e:
            json_dict['messages'] = [
                ['Messager error adding messages to json (internal error in message.py, please contact administrator): %s' % str(e), 'error', -1]]
            return json_dict

    @classmethod
    def clear(cls):
        """
        Remove all pending messages
        """
        Messager.__pending_messages = []

    @classmethod
    def __output_json(cls, json_dict):
        """
        Prepare message and set it in json_dict
        """
        # protect against non-unicode inputs
        convertable_messages = []
        for m in Messager.__pending_messages:
            try:
                encoded = m[0].encode('utf-8')
                convertable_messages.append(m)
            except UnicodeDecodeError:
                convertable_messages.append(
                    (u'[ERROR: MESSAGE THAT CANNOT BE ENCODED AS UTF-8 OMITTED]', 'error', 5))
        cls.__pending_messages = convertable_messages

        # clean up messages by removing possible control characters
        # that may cause trouble clientside
        cleaned_messages = []
        for s, t, r in cls.__pending_messages:
            cs = _remove_control_chars(s)
            if cs != s:
                s = cs + \
                    u'[NOTE: SOME NONPRINTABLE CHARACTERS REMOVED FROM MESSAGE]'
            cleaned_messages.append((s, t, r))
        cls.__pending_messages = cleaned_messages

        # to avoid crowding the interface, combine messages with identical content
        msgcount = {}
        for m in cls.__pending_messages:
            msgcount[m] = msgcount.get(m, 0) + 1

        merged_messages = []
        for m in cls.__pending_messages:
            if m in msgcount:
                count = msgcount[m]
                del msgcount[m]
                s, t, r = m
                if count > 1:
                    s = s + '<br/><b>[message repeated %d times]</b>' % count
                merged_messages.append((s, t, r))

        if 'messages' not in json_dict:
            json_dict['messages'] = []
        json_dict['messages'] += merged_messages
        cls.__pending_messages = []
        return json_dict

    @classmethod
    def __escape(cls, msg):
        """
        CGI escape message content
        """
        return escape(msg).replace('\n', '\n<br/>\n')

    @classmethod
    def __message(cls, msg, type_, duration, escaped):
        """
        Prepare and append a message to the pending heap
        """
        if not isinstance(msg, str) and not isinstance(msg, six.text_type):
            msg = str(msg)
        if not escaped:
            msg = cls.__escape(msg)
        cls.__pending_messages.append((msg, type_, duration))
