#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  2 06:55:31 2018

@author: phnx

TODO: add test case for the following actions
'downloadCollection': download_collection,

"splitSpan"


# NOTE: search actions are redundant to allow different
# permissions for single-document and whole-collection search.
'searchEventInDocument': search_event,
'searchRelationInDocument': search_relation,
'searchNoteInDocument': search_note,
'searchEventInCollection': search_event,
'searchRelationInCollection': search_relation,
'searchNoteInCollection': search_note,

'suggestSpanTypes': suggest_span_types,

'logAnnotatorAction': logging_no_op,

'saveConf': save_conf,
'loadConf': load_conf,

'undo': undo,
'tag': tag,

'deleteCollection': delete_collection,

# normalization support
'normGetName': norm_get_name,
'normSearch': norm_search,
'normData': norm_get_data,

# Visualisation support
'getConfiguration': get_configuration,
'convert': convert,

"""

# future
from __future__ import absolute_import

# standard
import os
import unittest


# arat
from arat import server
from arat.server import session
from arat.server.dispatch import Dispatcher
from config import DATA_DIR


DISPATCHER = Dispatcher()


class TestScenario(unittest.TestCase):
    """
    Test action with for simple valid input.

    Action handler are not stressed here.
    """

    def setUp(self):
        """
        Create a session and login
        """
        session.init_session("127.0.0.1")
#        self.assertEquals(session.CURRENT_SESSION, "")

        res = DISPATCHER({"action": "login",
                          "user": "admin",
                          "password": "admin",
                          "protocol": "1",
                          "collection": "/"},
                         "127.0.0.1",
                         "localhost")
        self.assertEquals(res, {"action": "login",
                                'protocol': 1})

    @classmethod
    def tearDownClass(cls):
        session.CURRENT_SESSION = None
        try:
            os.remove(DATA_DIR+"/id01.txt")
        except:  # pylint: disable=W0702
            pass
        try:
            os.remove(DATA_DIR+"/id01.ann")
        except:  # pylint: disable=W0702
            pass

    def test02_get_collection_information(self):
        """
        Walk the collection hierarchy
        """

        # list the root content
        res = DISPATCHER({"action": "getCollectionInformation",
                          "protocol": "1",
                          "collection": u"/"},
                         "127.0.0.1",
                         "localhost")
        self.assertEquals(res['items'], [['c', None, 'example-data']])

        # list example-data content
        res = DISPATCHER({"action": "getCollectionInformation",
                          "protocol": "1",
                          "collection": "/example-data/"},
                         "127.0.0.1",
                         "localhost")
        self.assertEquals(sorted(res['items']), [['c', None, '..'],
                                                 ['c', None, 'corpora'],
                                                 ['c', None, 'normalisation'],
                                                 ['c', None, 'tutorials'], ])

        # list corpora content
        res = DISPATCHER({"action": "getCollectionInformation",
                          "protocol": "1",
                          "collection": "/example-data/corpora/"},
                         "127.0.0.1",
                         "localhost")
        self.assertEquals(sorted(res['items']), [['c', None, '..'],
                                                 ['c', None, 'BioNLP-ST_2011'],
                                                 ['c', None, 'CoNLL-ST_2002'],
                                                 ['c', None, 'CoNLL-ST_2006'],
                                                 ['c', None, 'NCBI-disease'],
                                                 ['c', None, 'TDT']])

        # list CoNLL-ST_2002 content
        res = DISPATCHER({"action": "getCollectionInformation",
                          "protocol": "1",
                          "collection": "/example-data/corpora/CoNLL-ST_2002"},
                         "127.0.0.1",
                         "localhost")
        self.assertEquals(sorted(res['items']), [['c', None, '..'],
                                                 ['c', None, 'esp'],
                                                 ['c', None, 'ned']])

        # list esp content
        res = DISPATCHER({"action": "getCollectionInformation",
                          "protocol": "1",
                          "collection": "/example-data/corpora/CoNLL-ST_2002/esp"},
                         "127.0.0.1",
                         "localhost")

        res = [i[:3] for i in sorted(res['items'])[:3]]
        self.assertEquals(res, [['c', None, '..'],
                                ['d', None, 'esp.train-doc-100'],
                                ['d', None, 'esp.train-doc-1400']])

    def test03_get_document(self):
        """
        get a document from CoNLL-ST_2002/esp
        """
        res = DISPATCHER({"action": "getDocument",
                          "protocol": "1",
                          "collection": "/example-data/corpora/"
                                        "CoNLL-ST_2002/esp",
                          "document": "esp.train-doc-100"},
                         "127.0.0.1",
                         "localhost")

        self.assertEquals(res["text"][:40],
                          "Por Viruca Atanes Madrid, 24 may (EFE).\n")
        self.assertEquals(res["entities"][:2],
                          [['T1', 'PER', [(4, 17)]],
                           ['T2', 'LOC', [(18, 24)]]])
        self.assertEquals(res["attributes"], [])
        self.assertEquals(res["relations"], [])
        self.assertEquals(res["events"], [])
        self.assertEquals(res["triggers"], [])

    def test04_get_document_timestamp(self):
        """
        get document timestamp
        """
        res = DISPATCHER({"action": "getDocumentTimestamp",
                          "protocol": "1",
                          "collection": "/example-data/corpora/"
                                        "CoNLL-ST_2002/esp",
                          "document": "esp.train-doc-100"},
                         "127.0.0.1",
                         "localhost")

        self.assertGreater(res["mtime"], 1528000000)

    def test04_import_document(self):
        """
        add a test document
        """
        res = DISPATCHER({"action": "importDocument",
                          "protocol": "1",
                          "collection": "/",
                          "text": "This is a test file.",
                          "docid": "id01",
                          "mtime": 0},
                         "127.0.0.1",
                         "localhost")

        self.assertEquals(res,
                          {'document': 'id01',
                           'action': 'importDocument',
                           'protocol': 1})

    def test05_whoami(self):
        """
        check user session login
        """
        res = DISPATCHER({"action": "whoami",
                          "protocol": "1",
                          "collection": "/"},
                         "127.0.0.1",
                         "localhost")

        self.assertEquals(
            res, {'action': 'whoami', 'protocol': 1, 'user': 'admin'})

    def test06_logout(self):
        """
        logout then login again
        """
        res = DISPATCHER({"action": "logout",
                          "protocol": "1",
                          "collection": "/"},
                         "127.0.0.1",
                         "localhost")

        self.assertEquals(res, {'action': 'logout', 'protocol': 1})

        res = DISPATCHER({"action": "login",
                          "user": "admin",
                          "password": "admin",
                          "protocol": "1",
                          "collection": "/"},
                         "127.0.0.1",
                         "localhost")
        self.assertEquals(res, {"action": "login",
                                'protocol': 1})

# TODO: rewrite when search protocol becomes stable
#    def test07_search_text_in_document(self):
#        """
#        Search a single word in a document
#        """
#        res = DISPATCHER({"action": "searchTextInDocument",
#                          "protocol": "1",
#                          "text_match": "word",
#                          "text": "test",
#                          "collection": "/",
#                          "scope": "document",
#                          'concordancing': False,
#                          'context_length': 10,
#                          'match_case': False,
#                          "document": "id01"},
#                         "127.0.0.1",
#                         "localhost")
#
#        self.assertEquals(res, {'action': 'searchTextInDocument',
#                                'collection': '/',
#                                'header': [('Document', 'string'),
#                                           ('Annotation', 'string'),
#                                           ('Text', 'string')],
#                                'items': [['a',
#                                           {'match': [],
#                                            'matchfocus': [[10, 14]]},
#                                           'id01',
#                                           '10-14',
#                                           'test']],
#                                'protocol': 1})
#
#    def test08_search_text_in_collection(self):
#        """
#        Search a single word in a collection
#        """
#        res = DISPATCHER({"action": "searchTextInCollection",
#                          "protocol": "1",
#                          "text_match": "word",
#                          "text": "test",
#                          "collection": "/",
#                          "scope": "collection",
#                          'concordancing': False,
#                          'context_length': 10,
#                          'match_case': False,
#                          "document": "id01"},
#                         "127.0.0.1",
#                         "localhost")
#
#        self.assertEquals(res, {'action': 'searchTextInCollection',
#                                'collection': '/',
#                                'header': [('Document', 'string'),
#                                           ('Annotation', 'string'),
#                                           ('Text', 'string')],
#                                'items': [['a',
#                                           {'match': [],
#                                            'matchfocus': [[10, 14]]},
#                                           'id01',
#                                           '10-14',
#                                           'test']],
#                                'protocol': 1})

    def test09_create_span(self):
        """
        Create span annotations
        """
        res = DISPATCHER({"action": "createSpan",
                          "protocol": "1",
                          "collection": "/",
                          "offsets": "[[10, 14]]",
                          "type": "Protein",
                          "attributes": "{}",
                          "normalizations": "",
                          "document": "id01",
                          "id": None,
                          "comment": ""},
                         "127.0.0.1",
                         "localhost")
        self.assertEquals(res["edited"], [['T1']])

        res = DISPATCHER({"action": "createSpan",
                          "protocol": "1",
                          "collection": "/",
                          "offsets": "[[15, 19]]",
                          "type": "Protein",
                          "attributes": "{}",
                          "normalizations": "",
                          "document": "id01",
                          "id": None,
                          "comment": ""},
                         "127.0.0.1",
                         "localhost")
        self.assertEquals(res["edited"], [['T2']])

    def test10_create_arc(self):
        """
        Create arc between span annotations
        """
        res = DISPATCHER({"action": "createArc",
                          "collection": "/",
                          "comment": "",
                          "document": "id01",
                          "origin": "T1",
                          "protocol": "1",
                          "type": "Equiv",
                          "target": "T2",
                          "attributes": None,
                          "old_type": None,
                          "old_target": None},
                         "127.0.0.1",

                         "localhost")
        self.assertEquals(res["edited"], [['equiv', 'Equiv', u'T1']])

    def test11_reverse_arc(self):
        """
        Reverse arc between span annotations
        """
        res = DISPATCHER({"action": "reverseArc",
                          "collection": "/",
                          "document": "id01",
                          "origin": "T1",
                          "protocol": "1",
                          "type": "Equiv",
                          "target": "T2",
                          "attributes": None},
                         "127.0.0.1",

                         "localhost")
        self.assertTrue("edited" not in res)

    def test12_delete_arc(self):
        """
        Delete arc between span annotations
        """
        res = DISPATCHER({"action": "deleteArc",
                          "collection": "/",
                          "document": "id01",
                          "origin": "T2",
                          "protocol": "1",
                          "type": "Equiv",
                          "target": "T1"},
                         "127.0.0.1",

                         "localhost")
        self.assertEquals(res["edited"], [['equiv', u'Equiv', []]])

#    def test20_search_entity_in_document(self):
#        """
#        search a single word with type constraint in document
#        """
#        res = DISPATCHER({"action": "searchEntityInDocument",
#                          "protocol": "1",
#                          "type": "Protein",
#                          "text_match": "word",
#                          "text": "test",
#                          "collection": "/",
#                          "scope": "document",
#                          'concordancing': "false",
#                          'context_length': 10,
#                          'match_case': "false",
#                          "document": "id01"},
#                         "127.0.0.1",
#                         "localhost")
#
#        self.assertEquals(res["items"],
#                          [['a', {'match': [],
#                                  'matchfocus': [['T1']]},
#                            'id01', 'T1', 'Protein', 'test']])
#
#        res = DISPATCHER({"action": "searchEntityInDocument",
#                          "protocol": "1",
#                          "type": "dont_exists",
#                          "text_match": "word",
#                          "text": "test",
#                          "collection": "/",
#                          "scope": "document",
#                          'concordancing': "false",
#                          'context_length': 10,
#                          'match_case': "false",
#                          "document": "id01"},
#                         "127.0.0.1",
#                         "localhost")
#
#        self.assertEquals(res["items"], [])
#
#    def test20_search_entity_in_collection(self):
#        """
#        search a single word with type constraint in collection
#        """
#        res = DISPATCHER({"action": "searchEntityInCollection",
#                          "protocol": "1",
#                          "type": "Protein",
#                          "text_match": "word",
#                          "text": "test",
#                          "collection": "/",
#                          "scope": "collection",
#                          'concordancing': "false",
#                          'context_length': 10,
#                          'match_case': "false",
#                          'document': 'id01'},
#                         "127.0.0.1",
#                         "localhost")
#
#        self.assertEquals(res["items"],
#                          [['a', {'match': [],
#                                  'matchfocus': [['T1']]},
#                            'id01', 'T1', 'Protein', 'test']])
#
#        res = DISPATCHER({"action": "searchEntityInCollection",
#                          "protocol": "1",
#                          "type": "dont_exists",
#                          "text_match": "word",
#                          "text": "test",
#                          "collection": "/",
#                          "scope": "collection",
#                          'concordancing': "false",
#                          'context_length': 10,
#                          'match_case': "false",
#                          'document': 'id01'},
#                         "127.0.0.1",
#                         "localhost")
#
#        self.assertEquals(res["items"], [])

    def test30_delete_span(self):
        """
        Delete previous span annotation
        """
        res = DISPATCHER({"action": "deleteSpan",
                          "protocol": "1",
                          "collection": "/",
                          "document": "id01",
                          "id": 'T1'},
                         "127.0.0.1",
                         "localhost")
        self.assertEquals(res["edited"], [])

    def test31_store_retrieve_svg(self):
        """
        Store then retrieveSVG
        """
        svg_data = open("tests/test_data/test.svg",
                        "rb").read().decode("utf-8")

        res = DISPATCHER({"action": "storeSVG",
                          "protocol": "1",
                          "collection": "/",
                          "document": "id01",
                          "svg": svg_data},
                         "127.0.0.1",
                         "localhost")
        self.assertEquals(res["stored"], [{'name': 'svg', 'suffix': 'svg'}])

        sid = session.get_session().get_sid()

        file_content = open("work/svg/%s.svg" % sid, "rb").read()
        self.assertGreater(len(file_content.decode("utf-8")),
                           len(svg_data))

        svg_data = open("work/svg/%s.svg" %
                        session.get_session().get_sid(), "rb").read()
        with self.assertRaises(server.common.NoPrintJSONError) as context:
            DISPATCHER({"action": "retrieveStored",
                        "protocol": "1",
                        "collection": "/",
                        "document": "id01",
                        "suffix": "svg"},
                       "127.0.0.1",
                       "localhost")
        self.assertEquals(dict(context.exception.hdrs)["Content-Type"],
                          "image/svg+xml")
        self.assertEquals(context.exception.data, svg_data)

    def test33_download_file(self):
        """
        Donwload a document and its annotation file
        """

        for extension in ["txt", "ann"]:
            data = open("data/id01.%s" % extension, "rb").read()
            with self.assertRaises(server.common.NoPrintJSONError) as context:
                DISPATCHER({"action": "downloadFile",
                            "protocol": "1",
                            "collection": "/",
                            "document": "id01",
                            "extension": extension},
                           "127.0.0.1",
                           "localhost")
            self.assertEquals(dict(context.exception.hdrs)["Content-Type"],
                              "text/plain; charset=utf-8")
            self.assertEquals(context.exception.data, data)

    def test34_download_collection(self):
        """
        Donwload a collection
        """

        with self.assertRaises(server.common.NoPrintJSONError) as context:
            DISPATCHER({"action": "downloadCollection",
                        "protocol": "1",
                        "collection": "/",
                        "include_conf": True},
                       "127.0.0.1",
                       "localhost")
        self.assertEquals(dict(context.exception.hdrs)["Content-Type"],
                          "application/octet-stream")
        # TODO: write extra check


#    def test99_deleteDocument(self):
#        """
#        delete the test document
#
#        # TODO: complete this test once deleteDocument has been implemented
#        """
#
#        # remove the document
#        os.remove(DATA_DIR+"/id01.txt")
#        os.remove(DATA_DIR+"/id01.ann")
#
#        res = DISPATCHER({"action": "deleteDocument",
#                            "protocol": "1",\
#                            "collection":"/",
#                            "document":"id01"},\
#                           "127.0.0.1",\
#                           "localhost"))

    def test200_logout_delete_session(self):
        """
        logout and delete session
        """
        res = DISPATCHER({"action": "logout",
                          "protocol": "1",
                          "collection": "/"},
                         "127.0.0.1",
                         "localhost")

        self.assertEquals(res, {'action': 'logout', 'protocol': 1})

        session.CURRENT_SESSION = None


if __name__ == "__main__":
    import sys
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TestScenario)
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(SUITE)
