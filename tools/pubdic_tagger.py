#!/usr/bin/env python

'''
Dictionary-based NER tagging server using PubDictionaries.
This code is based on that of randomtagger.py

Author:     Han-Cheol Cho
(Author of the original script:	Pontus Stenetorp)
Version:    2014-04-05
'''

from __future__ import absolute_import
from __future__ import print_function

from argparse import ArgumentParser
from cgi import FieldStorage
from random import choice, randint
from sys import stderr
import json
import base64

from six.moves.urllib.parse import urlparse
from six.moves.BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import six.moves.urllib.request # pylint: disable=import-error
import six.moves.urllib.parse
import six.moves.urllib.error

from server.jsonwrap import dumps

# Constants
ARGPARSER = ArgumentParser(description='An example HTTP tagging service, '
                           'tagging Confuse-a-Cat **AND** Dead-parrot mentions!')
ARGPARSER.add_argument('-p', '--port', type=int, default=56789,
                       help='port to run the HTTP service on (default: 56789)')
###


#
# 1. Use PubDictionaries's ID (email) and password to use both uploaded dictionary and
#   modified information (disabled and added entries).
# 2. Use "" for both variables to use only originally uploaded dictionary.
# 3. PubDictionaries does not provide any encryption yet!!
#
def build_headers(email="", password=""):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': b'Basic ' + base64.b64encode(email + b':' + password),
    }
    return headers


def build_data(text):
    return json.dumps({'text': text}).encode('utf-8')


def convert_for_arat(pubdic_result, text):
    anns = {}
    for idx, entity in enumerate(pubdic_result):
        ann_id = 'T%d' % idx
        anns[ann_id] = {
            'type': entity['obj'],     # ID of an entry
            'offsets': ((entity['begin'], entity['end']), ),
            'texts': (text[entity['begin']:entity['end']], ),
            # Use entity['dictionary_name'] to distinguish the dictionary of this entry
            #   when you use an annotator url of multiple dictionaries.
        }
    return anns


class RandomTaggerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        field_storage = FieldStorage(
            headers=self.headers,
            environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': self.headers['Content-type'],
            },
            fp=self.rfile)

        # Do your random tagging magic
        try:
                # Prepare the request header and data
            # email and password of PubDictionaries
            headers = build_headers("", "")
            # For "ann['texts']" in format conversion
            text = field_storage.value.decode('utf-8')
            data = build_data(text)

            # Make a request and retrieve the result
            annotator_url = "http://pubdictionaries.dbcls.jp:80/dictionaries/EntrezGene%20-%20Homo%20Sapiens/text_annotation?matching_method=approximate&max_tokens=6&min_tokens=1&threshold=0.8&top_n=0"
            request = six.moves.urllib.request.Request(
                annotator_url, data=data, headers=headers)

            f = six.moves.urllib.request.urlopen(request)
            res = f.read()
            f.close()

            # Format the result for BRAT
            json_dic = convert_for_arat(json.loads(res), text)

        except KeyError:
            # We weren't given any text to tag, such is life, return nothing
            json_dic = {}

        # Write the response
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()

        self.wfile.write(dumps(json_dic))
        print(('Generated %d annotations' % len(json_dic)), file=stderr)

    def log_message(self, format, *args):
        return  # Too much noise from the default implementation


def main(args):
    argp = ARGPARSER.parse_args(args[1:])

    server_class = HTTPServer
    httpd = server_class(('localhost', argp.port), RandomTaggerHandler)

    print('PubDictionary NER tagger service started on port %s' %
          (argp.port), file=stderr)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print('PubDictionary tagger service stopped', file=stderr)


if __name__ == '__main__':
    from sys import argv
    exit(main(argv))
