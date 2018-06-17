#!/usr/bin/env python

# Minimal standalone arat server based on SimpleHTTPRequestHandler.

# Run as apache, e.g. as
#
#     APACHE_USER=`./apache-user.sh`
#     sudo -u $APACHE_USER python standalone.py

# future
from __future__ import absolute_import
from __future__ import print_function
from posixpath import normpath

# standard
import sys
import os
from cgi import FieldStorage
import socket

from six.moves.BaseHTTPServer import HTTPServer  # pylint: disable=import-error
from six.moves.SimpleHTTPServer import SimpleHTTPRequestHandler  # pylint: disable=import-error
from six.moves.socketserver import ForkingMixIn  # pylint: disable=import-error
from six.moves.urllib.parse import unquote  # pylint: disable=import-error
import six  # pylint: disable=import-error

# arat imports
from server.arat_server import serve

_PYTHON3 = (sys.version_info > (3, 0))

_VERBOSE_HANDLER = False
_DEFAULT_SERVER_ADDR = ''
_DEFAULT_SERVER_PORT = 8001

_PERMISSIONS = """
Allow: /ajax.cgi
Disallow: *.py
Disallow: *.cgi
Disallow: /.htaccess
Disallow: *.py~  # no emacs backups
Disallow: *.cgi~
Disallow: /.htaccess~
Allow: /
"""


class PermissionParseError(Exception):
    def __init__(self, linenum, line, message=None):
        self.linenum = linenum
        self.line = line
        self.message = ' (%s)' % message if message is not None else ''

    def __str__(self):
        return 'line %d%s: %s' % (self.linenum, self.message, self.line)


class PathPattern(object):
    def __init__(self, path):
        self.path = path
        self.plen = len(path)

    def match(self, path):
        # Require prefix match
        res = path[:self.plen] == self.path

        # and separator/end.
        res = res and (self.path[-1] == '/' or
                       path[self.plen:] == '' or
                       path[self.plen] == '/')
        return res


class ExtensionPattern(object):
    def __init__(self, ext):
        self.ext = ext

    def match(self, path):
        return os.path.splitext(path)[1] == self.ext


class PathPermissions(object):
    """Implements path permission checking with a robots.txt-like syntax.

    TODO: issue #8 use robotparser instead of reimplementing the logic
    """

    def __init__(self, default_allow=False):
        self._entries = []
        self.default_allow = default_allow

    def allow(self, path):
        # First match wins
        for pattern, allow in self._entries:
            if pattern.match(path):
                return allow
        return self.default_allow

    def parse(self, lines):
        # Syntax: "DIRECTIVE : PATTERN" where
        # DIRECTIVE is either "Disallow:" or "Allow:" and
        # PATTERN either has the form "*.EXT" or "/PATH".
        # Strings starting with "#" and empty lines are ignored.

        for lineno, line in enumerate(lines):
            i = line.find('#')
            if i != -1:
                line = line[:i]
            line = line.strip()

            if not line:
                continue

            i = line.find(':')
            if i == -1:
                raise PermissionParseError(
                    lineno, lines[lineno], 'missing colon')

            directive = line[:i].strip().lower()
            pattern = line[i+1:].strip()

            if directive == 'allow':
                allow = True
            elif directive == 'disallow':
                allow = False
            else:
                raise PermissionParseError(
                    lineno, lines[lineno], 'unrecognized directive')

            if pattern.startswith('/'):
                patt = PathPattern(pattern)
            elif pattern.startswith('*.'):
                patt = ExtensionPattern(pattern[1:])
            else:
                raise PermissionParseError(
                    lineno, lines[lineno], 'unrecognized pattern')

            self._entries.append((patt, allow))

        return self


class AratHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Minimal handler for arat server."""

    permissions = PathPermissions().parse(_PERMISSIONS.split('\n'))

    def log_request(self, code='-', size='-'):
        if _VERBOSE_HANDLER:
            SimpleHTTPRequestHandler.log_request(self, code, size)
        else:
            # just ignore logging
            pass

    def is_arat(self):
        # minimal cleanup
        path = self.path
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]

        return path == '/ajax.cgi'

    def run_arat_direct(self):
        """Execute arat server directly."""

        remote_addr = self.client_address[0]
        remote_host = self.address_string()
        if self.headers.get('cookie'):
            cookie_data = self.headers.get('cookie')
        else:
            cookie_data = ""
        query_string = ''
        i = self.path.find('?')
        if i != -1:
            query_string = self.path[i+1:]

        # set env to get FieldStorage to read params
        env = {}
        env['REQUEST_METHOD'] = self.command
        content_length = self.headers.get('content-length')
        if content_length:
            env['CONTENT_LENGTH'] = content_length
        if query_string:
            env['QUERY_STRING'] = query_string
        os.environ.update(env)
        params = FieldStorage(self.rfile)

        # Call main server
        cookie_hdrs, response_data = serve(params, remote_addr, remote_host,
                                           cookie_data)

        # Package and send response
        if cookie_hdrs is not None:
            response_hdrs = [hdr for hdr in cookie_hdrs]
        else:
            response_hdrs = []
        response_hdrs.extend(response_data[0])

        self.send_response(200)
        for k, v in response_hdrs:
            self.send_header(k, v)
        self.end_headers()

        # Hack to support binary data and general Unicode for SVGs and JSON
        if isinstance(response_data[1], six.text_type):
            self.wfile.write(response_data[1].encode('utf-8'))
        else:
            self.wfile.write(response_data[1])
        return 0

    def allow_path(self):
        """Test whether to allow a request for self.path."""

        # Cleanup in part following SimpleHTTPServer.translate_path()
        path = self.path
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = unquote(path)
        path = normpath(path)
        parts = path.split('/')
        parts = [_f for _f in parts if _f]
        if '..' in parts:
            return False
        path = '/'+'/'.join(parts)

        return self.permissions.allow(path)

    def list_directory(self, path):
        """Override SimpleHTTPRequestHandler.list_directory()"""
        # TODO: permissions for directory listings
        self.send_error(403)

    def do_POST(self):
        """Serve a POST request. Only implemented for arat server."""

        if self.is_arat():
            self.run_arat_direct()
        else:
            self.send_error(501, "Can only POST to arat")

    def do_GET(self):
        """Serve a GET request."""
        if not self.allow_path():
            self.send_error(403)
        elif self.is_arat():
            self.run_arat_direct()
        else:
            SimpleHTTPRequestHandler.do_GET(self)

    def do_HEAD(self):
        """Serve a HEAD request."""
        if not self.allow_path():
            self.send_error(403)
        else:
            SimpleHTTPRequestHandler.do_HEAD(self)


class AratServer(ForkingMixIn, HTTPServer):
    def __init__(self, server_address):
        HTTPServer.__init__(self, server_address, AratHTTPRequestHandler)


def main(argv):
    # warn if root/admin
    try:
        if os.getuid() == 0:
            print("""
! WARNING: running as root. The arat standalone server is experimental   !
! and may be a security risk. It is recommend to run the standalone      !
! server as a non-root user with write permissions to the arat work/ and !
! data/ directories (e.g. apache if arat is set up using standard        !
! installation).                                                         !
""", file=sys.stderr)
    except AttributeError:
        # not on UNIX
        print("""
Warning: could not determine user. Note that the arat standalone
server is experimental and should not be run as administrator.
""", file=sys.stderr)

    if len(argv) > 1:
        try:
            port = int(argv[1])
        except ValueError:
            print("Failed to parse", argv[1],
                  "as port number.", file=sys.stderr)
            return 1
    else:
        port = _DEFAULT_SERVER_PORT

    try:
        server = AratServer((_DEFAULT_SERVER_ADDR, port))
        print("Serving arat at http://%s:%d" %
              server.server_address, file=sys.stderr)
        server.serve_forever()
    except KeyboardInterrupt:
        # normal exit
        pass
    except socket.error as why:
        if _PYTHON3:
            print("Error binding to port", port, ":", why, file=sys.stderr)
        else:
            print("Error binding to port", port, ":",
                  why[1], file=sys.stderr)  # pylint: disable=unsubscriptable-object
    except Exception as exception:
        print("Server error", exception, file=sys.stderr)
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
