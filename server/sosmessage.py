#!/usr/bin/env python
# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; coding: utf-8; -*-
# vim:set ft=python ts=4 sw=4 sts=4 autoindent:

'''
Dummy Messager that can replace the real one in case it goes down.
Doesn't actually send any messages other than letting the user
know of the problem.
Use e.g. as

    try:
        from server.message import Messager
    except:
        from server.sosmessage import Messager
'''

from __future__ import print_function


class SosMessager(object):
    """
    Messager fallback
    """
    @staticmethod
    def output_json(json_dict):
        """
        JSON output
        """
        json_dict['messages'] = [
            ['HELP: messager down! (internal error in message.py, please contact administrator)',
             'error',
             -1]]
        return json_dict

    @staticmethod
    def output(file_desc):
        """
        screen output
        """
        print('HELP: messager down! (internal error in message.py, '
              'please contact administrator)', file=file_desc)

    @staticmethod
    def info(msg, duration=3, escaped=False):
        """
        information level
        """
        pass

    @staticmethod
    def warning(msg, duration=3, escaped=False):
        """
        warning level
        """
        pass

    @staticmethod
    def error(msg, duration=3, escaped=False):
        """
        error level
        """
        pass

    @staticmethod
    def debug(msg, duration=3, escaped=False):
        """
        debug level
        """
        pass
