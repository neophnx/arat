#!/usr/bin/env python
# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; coding: utf-8; -*-
# vim:set ft=python ts=4 sw=4 sts=4 autoindent:

'''
Deletion functionality.

TODO: implement deletion facilties
'''

from __future__ import absolute_import
from server.common import AratNotImplementedError


def delete_document(collection, document):
    """
    Document deletion, not implemented
    """
    assert collection is not None
    assert document is not None
    raise AratNotImplementedError()


def delete_collection(collection):
    """
    Collection deletion, not implemented
    """
    assert collection is not None
    raise AratNotImplementedError()
