# -*- coding: utf-8 -*-
"""
Created on Thu Jun 14 00:25:06 2018

@author: phnx
"""

import sys
import re

import six
try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache


from arat.server.message import Messager
from arat.server.projectconfig import constants as cst

_CACHE_SIZE = 1000
_PYTHON3 = (sys.version_info > (3, 0))


class InvalidProjectConfigException(Exception):
    pass


@lru_cache(_CACHE_SIZE)
def normalize_to_storage_form(token):
    """
    Given a label, returns a form of the term that can be used for
    disk storage. For example, space can be replaced with underscores
    to allow use with space-separated formats.

    >>> normalize_to_storage_form(u'identical') == six.u('identical')
    True

    >>> normalize_to_storage_form(u'with underscore') == six.u('with_underscore')
    True

    >>> normalize_to_storage_form(u'un été') == six.u('un___t__')
    True

    """
    # conservative implementation: replace any space with
    # underscore, replace unicode accented characters with
    # non-accented equivalents, remove others, and finally replace
    # all characters not in [a-zA-Z0-9_-] with underscores.

    # Is there a way to iterate characters of a string in version 2 ?
    # this hack assure consistency
    if _PYTHON3:
        token = token.encode("utf-8")
    token = re.sub(six.b(r'[^a-zA-Z0-9_\-]'), six.b('_'), token)

    return token.decode("ascii")


class TypeHierarchyNode(object):
    """
    Represents a node in a simple (possibly flat) hierarchy.

    Each node is associated with a set of terms, one of which (the
    storage_form) matches the way in which the type denoted by the
    node is referenced to in data stored on disk and in client-server
    communications. This term is guaranteed to be in "storage form" as
    defined by normalize_to_storage_form().

    Each node may be associated with one or more "arguments", which
    are (multivalued) key:value pairs. These determine various characteristics
    of the node, but their interpretation depends on the hierarchy the
    node occupies: for example, for events the arguments correspond to
    event arguments.
    """

    def __init__(self, terms, args=None):
        if args is None:
            args = []
        self.terms, self.args = terms, args

        if not terms or len([t for t in terms if t == ""]) != 0:
            Messager.debug("Empty term in configuration", duration=-1)
            raise InvalidProjectConfigException

        # unused if any of the terms marked with "!"
        self.unused = False
        for i in range(len(self.terms)):
            if self.terms[i][0] == "!":
                self.terms[i] = self.terms[i][1:]
                self.unused = True
        self.children = []

        # The first of the listed terms is used as the primary term for
        # storage (excepting for "special" config-only types). Due to
        # format restrictions, this form must not have e.g. space or
        # various special characters.
        if self.terms[0] not in cst.SPECIAL_RELATION_TYPES:
            self.__primary_term = normalize_to_storage_form(self.terms[0])
        else:
            self.__primary_term = self.terms[0]
        # TODO: this might not be the ideal place to put this warning
        if self.__primary_term != self.terms[0]:
            Messager.warning("Note: in configuration, term '%s' is not "
                             "appropriate for storage (should match "
                             "'^[a-zA-Z0-9_-]*$'), using '%s' instead. "
                             "(Revise configuration file to get rid of "
                             "this message. Terms other than the first are "
                             "not subject to this restriction.)" % (
                                 self.terms[0], self.__primary_term), -1)
            self.terms[0] = self.__primary_term

        # TODO: cleaner and more localized parsing
        self.arguments = {}
        self.special_arguments = {}
        self.arg_list = []
        self.arg_min_count = {}
        self.arg_max_count = {}
        self.keys_by_type = {}
        for a in self.args:
            self._process_arg(a, args)

    def _process_arg(self, arg, args):
        arg = arg.strip()
        match_obj = re.match(r'^(\S*?):(\S*)$', arg)
        if not match_obj:
            Messager.warning(
                "Project configuration: Failed to parse argument "
                "'%s' (args: %s)" % (arg, args), 5)
            raise InvalidProjectConfigException
        key, atypes = match_obj.groups()

        # special case (sorry): if the key is a reserved config
        # string (e.g. "<REL-TYPE>" or "<URL>"), parse differently
        # and store separately
        if key in cst.RESERVED_CONFIG_STRING:
            if key is self.special_arguments:
                Messager.warning(
                    "Project configuration: error parsing: %s argument "
                    "'%s' appears multiple times." % key, 5)
                raise InvalidProjectConfigException
            # special case in special case: relation type specifications
            # are split by hyphens, nothing else is.
            # (really sorry about this.)
            if key == "<REL-TYPE>":
                self.special_arguments[key] = atypes.split("-")
            else:
                self.special_arguments[key] = [atypes]
            # NOTE: skip the rest of processing -- don't add in normal args
            return

        # Parse "repetition" modifiers. These are regex-like:
        # - Arg      : mandatory argument, exactly one
        # - Arg?     : optional argument, at most one
        # - Arg*     : optional argument, any number
        # - Arg+     : mandatory argument, one or more
        # - Arg{N}   : mandatory, exactly N
        # - Arg{N-M} : mandatory, between N and M

        match_obj = re.match(r'^(\S+?)(\{\S+\}|\?|\*|\+|)$', key)
        if not match_obj:
            Messager.warning(
                "Project configuration: error parsing "
                "argument '%s'." % key, 5)
            raise InvalidProjectConfigException
        key, rep = match_obj.groups()

        if rep == '':
            # exactly one
            minimum_count = 1
            maximum_count = 1
        elif rep == '?':
            # zero or one
            minimum_count = 0
            maximum_count = 1
        elif rep == '*':
            # any number
            minimum_count = 0
            maximum_count = sys.maxsize
        elif rep == '+':
            # one or more
            minimum_count = 1
            maximum_count = sys.maxsize
        else:
            # exact number or range constraint
            assert '{' in rep and '}' in rep, "INTERNAL ERROR"
            m = re.match(r'\{(\d+)(?:-(\d+))?\}$', rep)
            if not m:
                Messager.warning(
                    "Project configuration: error parsing range '%s' in "
                    "argument '%s' (syntax is "
                    "'{MIN-MAX}')." % (rep, key+rep), 5)
                raise InvalidProjectConfigException
            n1, n2 = m.groups()
            n1 = int(n1)
            if n2 is None:
                # exact number
                if n1 == 0:
                    Messager.warning(
                        "Project configuration: cannot have exactly "
                        "0 repetitions of argument '%s'." % (key+rep), 5)
                    raise InvalidProjectConfigException
                minimum_count = n1
                maximum_count = n1
            else:
                # range
                n2 = int(n2)
                if n1 > n2:
                    Messager.warning(
                        "Project configuration: invalid range %d-%d "
                        "for argument '%s'." % (n1, n2, key+rep), 5)
                    raise InvalidProjectConfigException
                minimum_count = n1
                maximum_count = n2

        # format / config sanity: an argument whose label ends
        # with a digit label cannot be repeated, as this would
        # introduce ambiguity into parsing. (For example, the
        # second "Theme" is "Theme2", and the second "Arg1" would
        # be "Arg12".)
        if maximum_count > 1 and key[-1].isdigit():
            Messager.warning(
                "Project configuration: error parsing: arguments ending "
                "with a digit cannot be repeated: '%s'" % (key+rep), 5)
            raise InvalidProjectConfigException

        if key in self.arguments:
            Messager.warning(
                "Project configuration: error parsing: %s argument '%s' "
                "appears multiple times." % key, 5)
            raise InvalidProjectConfigException

        assert (key not in self.arg_min_count and
                key not in self.arg_max_count), "INTERNAL ERROR"
        self.arg_min_count[key] = minimum_count
        self.arg_max_count[key] = maximum_count

        self.arg_list.append(key)

        for atype in atypes.split("|"):
            if atype.strip() == "":
                Messager.warning(
                    "Project configuration: error parsing: empty type for "
                    "argument '%s'." % arg, 5)
                raise InvalidProjectConfigException

            # Check disabled; need to support arbitrary UTF values
            # for visual.conf. TODO: add this check for other configs.
            # TODO: consider checking for similar for appropriate confs.
#                 if atype not in RESERVED_CONFIG_STRING and
#                           normalize_to_storage_form(atype) != atype:
#                     Messager.warning("Project configuration: '%s' "
#                                      "is not a valid argument (should "
#                                      "match '^[a-zA-Z0-9_-]*$')" % atype, 5)
#                     raise InvalidProjectConfigException

            if key not in self.arguments:
                self.arguments[key] = []
            self.arguments[key].append(atype)

            if atype not in self.keys_by_type:
                self.keys_by_type[atype] = []
            self.keys_by_type[atype].append(key)

    def argument_minimum_count(self, arg):
        """
        Returns the minimum number of times the given argument is
        required to appear for this type.
        """
        return self.arg_min_count.get(arg, 0)

    def argument_maximum_count(self, arg):
        """
        Returns the maximum number of times the given argument is
        allowed to appear for this type.
        """
        return self.arg_max_count.get(arg, 0)

    def mandatory_arguments(self):
        """
        Returns the arguments that must appear at least once for
        this type.
        """
        return [a for a in self.arg_list if self.arg_min_count[a] > 0]

    def multiple_allowed_arguments(self):
        """
        Returns the arguments that may appear multiple times for this
        type.
        """
        return [a for a in self.arg_list if self.arg_max_count[a] > 1]

    def storage_form(self):
        """
        Returns the form of the term used for storage serverside.
        """
        return self.__primary_term

    def normalizations(self):
        """
        Returns the normalizations applicable to this node, if any.
        """
        return self.special_arguments.get('<NORM>', [])
