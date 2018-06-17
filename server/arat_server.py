# -*- coding: utf-8 -*-
'''
Main entry for the arat server, ensures integrity, handles dispatch and
processes potential exceptions before returning them to be sent as responses.


Author:     Pontus Stenetorp   <pontus is s u-tokyo ac jp>
Version:    2011-09-29
'''

# future
from __future__ import absolute_import
from __future__ import print_function

# standard
from os import access, R_OK, W_OK
from os.path import join as path_join
import logging
from logging import basicConfig as log_basic_config
import sys
from sys import version_info, stderr
from time import time
from traceback import print_exc

try:
    from cStringIO import StringIO
except ImportError:
    try:
        from StringIO import StringIO
    except:
        from io import StringIO


# third party
from six.moves._thread import allocate_lock  # pylint: disable=import-error
import six

# arat
from server.jsonwrap import dumps
from server.message import Messager
from server.common import ProtocolError, ProtocolArgumentError, NoPrintJSONError
from server.dispatch import dispatch
from server.session import get_session, init_session, close_session, NoSessionError, SessionStoreError
import config
from config import DATA_DIR, WORK_DIR
from config import DEBUG
from config import LOG_LEVEL, ADMIN_CONTACT_EMAIL


# Constants
# This handling of version_info is strictly for backwards compatibility
PY_VER_STR = '%d.%d.%d-%s-%d' % tuple(version_info)
REQUIRED_PY_VERSION = (2, 7, 0, 'alpha', 1)
REQUIRED_PY_VERSION_STR = '%d.%d.%d-%s-%d' % tuple(REQUIRED_PY_VERSION)
JSON_HDR = ('Content-Type', 'application/json')
CONF_FNAME = 'config.py'
CONF_TEMPLATE_FNAME = 'config_template.py'
CONFIG_CHECK_LOCK = allocate_lock()
###
_PYTHON3 = (sys.version_info > (3, 0))


class PermissionError(Exception):
    def json(self, json_dic):
        json_dic['exception'] = 'permissionError'


class ConfigurationError(Exception):
    def json(self, json_dic):
        json_dic['exception'] = 'configurationError'


def _permission_check():

    if not access(WORK_DIR, R_OK | W_OK):
        Messager.error((('Work dir: "%s" is not read-able and ' % WORK_DIR) +
                        'write-able by the server'), duration=-1)
        raise PermissionError

    if not access(DATA_DIR, R_OK):
        Messager.error((('Data dir: "%s" is not read-able ' % DATA_DIR) +
                        'by the server'), duration=-1)
        raise PermissionError


# Error message template functions
def _miss_var_msg(var):
    return ('Missing variable "%s" in %s, make sure that you have '
            'not made any errors to your configurations and to start over '
            'copy the template file %s to %s in your '
            'installation directory and edit it to suit your environment'
            ) % (var, CONF_FNAME, CONF_TEMPLATE_FNAME, CONF_FNAME)


def _miss_config_msg():
    return ('Missing file %s in the installation dir. If this is a new '
            'installation, copy the template file %s to %s in '
            'your installation directory ("cp %s %s") and edit '
            'it to suit your environment.'
            ) % (CONF_FNAME, CONF_TEMPLATE_FNAME, CONF_FNAME,
                 CONF_TEMPLATE_FNAME, CONF_FNAME)


# Convert internal log level to `logging` log level


def _convert_log_level(log_level):
    res = None
    if log_level == config.LL_DEBUG:
        res = logging.DEBUG
    elif log_level == config.LL_INFO:
        res = logging.INFO
    elif log_level == config.LL_WARNING:
        res = logging.WARNING
    elif log_level == config.LL_ERROR:
        res = logging.ERROR
    elif log_level == config.LL_CRITICAL:
        res = logging.CRITICAL
    else:
        assert False, 'Should not happen'
    return res


class DefaultNoneDict(dict):
    def __missing__(self, key):
        return None


def _safe_serve(params, client_ip, client_hostname, cookie_data):
    # Note: Only logging imports here

    # Enable logging
    log_level = _convert_log_level(LOG_LEVEL)
    log_basic_config(filename=path_join(WORK_DIR, 'server.log'),
                     level=log_level)

    init_session(client_ip, cookie_data=cookie_data)
    response_is_JSON = True
    try:
        # Unpack the arguments into something less obscure than the
        #   Python FieldStorage object (part dictonary, part list, part FUBAR)
        http_args = DefaultNoneDict()
        for k in params:
            # Also take the opportunity to convert Strings into Unicode,
            #   according to HTTP they should be UTF-8
            try:
                http_args[k] = params.getvalue(k)
            except TypeError:
                Messager.error('protocol argument error: expected string argument %s, got %s' % (
                    k, type(params.getvalue(k))))
                raise ProtocolArgumentError

        # Dispatch the request
        json_dic = dispatch(http_args, client_ip, client_hostname)
    except ProtocolError as e:
        # Internal error, only reported to client not to log
        json_dic = {}
        e.json(json_dic)

        # Add a human-readable version of the error
        err_str = six.text_type(e)
        if err_str != '':
            Messager.error(err_str, duration=-1)
    except NoPrintJSONError as e:
        # Terrible hack to serve other things than JSON
        response_data = (e.hdrs, e.data)
        response_is_JSON = False

    # Get the potential cookie headers and close the session (if any)
    try:
        cookie_hdrs = get_session().cookie.hdrs()
        close_session()
    except SessionStoreError:
        Messager.error(
            "Failed to store cookie (missing write permission to arat work directory)?", -1)
    except NoSessionError:
        cookie_hdrs = None

    if response_is_JSON:
        response_data = ((JSON_HDR, ), dumps(Messager.output_json(json_dic)))

    return (cookie_hdrs, response_data)
# Programmatically access the stack-trace


def _get_stack_trace():

    # Getting the stack-trace requires a small trick
    buf = StringIO()
    print_exc(file=buf)
    buf.seek(0)
    return buf.read()

# Encapsulate an interpreter crash


def _server_crash(cookie_hdrs, e):

    stack_trace = _get_stack_trace()

    if DEBUG:
        # Send back the stack-trace as json
        error_msg = '\n'.join(('Server Python crash, stack-trace is:\n',
                               stack_trace))
        Messager.error(error_msg, duration=-1)
    else:
        # Give the user an error message
        # Use the current time since epoch as an id for later log look-up
        error_msg = ('The server encountered a serious error, '
                     'please contact the administrators at %s '
                     'and give the id #%d'
                     ) % (ADMIN_CONTACT_EMAIL, int(time()))
        Messager.error(error_msg, duration=-1)

    # Print to stderr so that the exception is logged by the webserver
    print(stack_trace, file=stderr)

    json_dic = {
        'exception': 'serverCrash',
    }
    return (cookie_hdrs, ((JSON_HDR, ), dumps(Messager.output_json(json_dic))))

# Serve the client request


def serve(params, client_ip, client_hostname, cookie_data):
    # The session relies on the config, wait-for-it
    cookie_hdrs = None

    # We can now safely read the config

    try:
        _permission_check()
    except PermissionError as e:
        json_dic = {}
        e.json(json_dic)
        return cookie_hdrs, ((JSON_HDR, ), dumps(Messager.output_json(json_dic)))

    try:
        # Safe region, can throw any exception, has verified installation
        return _safe_serve(params, client_ip, client_hostname, cookie_data)
    except BaseException as e:
        # Handle the server crash
        return _server_crash(cookie_hdrs, e)
