#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  2 06:55:31 2018

@author: phnx

TODO: add test case for the following actions
'downloadCollection': download_collection,

"splitSpan"


'createArc': create_arc,
'reverseArc': reverse_arc,
'deleteArc': delete_arc,

# NOTE: search actions are redundant to allow different
# permissions for single-document and whole-collection search.
'searchEntityInDocument': search_entity,
'searchEventInDocument': search_event,
'searchRelationInDocument': search_relation,
'searchNoteInDocument': search_note,
'searchEntityInCollection': search_entity,
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
from __future__ import absolute_import
import unittest
from server.dispatch import Dispatcher
from server import session
from server.common import BratNotImplementedError
import os
from config import DATA_DIR

dispatcher = Dispatcher()

class ScenarioAnnotation(unittest.TestCase):
    def test01_login(self):
        """
        Create a session and login
        """
        session.init_session("127.0.0.1")
#        self.assertEquals(session.CURRENT_SESSION, "")


        res = dispatcher({"action": "login",\
                            "user": "admin",\
                            "password": "admin",\
                            "protocol": "1",\
                            "collection":"/"},\
                           "127.0.0.1",\
                           "localhost")
        self.assertEquals(res, {"action": "login",
                                'protocol': 1})
        
    def test02_getCollectionInformation(self):
        """
        Walk the collection hierarchy
        """
        
        # list the root content
        res = dispatcher({"action": "getCollectionInformation",
                            "protocol": "1",\
                            "collection":u"/"},\
                           "127.0.0.1",\
                           "localhost")
        self.assertEquals(res['items'], [['c', None, 'example-data']])
        
        
        # list example-data content
        res = dispatcher({"action": "getCollectionInformation",
                            "protocol": "1",\
                            "collection":"/example-data/"},\
                           "127.0.0.1",\
                           "localhost")
        self.assertEquals(sorted(res['items']), [['c', None, '..'],
                                                 ['c', None, 'corpora'],
                                                 ['c', None, 'normalisation'],
                                                 ['c', None, 'tutorials'],])

        # list corpora content
        res = dispatcher({"action": "getCollectionInformation",
                            "protocol": "1",\
                            "collection":"/example-data/corpora/"},\
                           "127.0.0.1",\
                           "localhost")
        self.assertEquals(sorted(res['items']), [['c', None, '..'],
                                                 ['c', None, 'BioNLP-ST_2011'],
                                                 ['c', None, 'CoNLL-ST_2002'],
                                                 ['c', None, 'CoNLL-ST_2006'],
                                                 ['c', None, 'NCBI-disease'],
                                                 ['c', None, 'TDT']])
    
        # list CoNLL-ST_2002 content
        res = dispatcher({"action": "getCollectionInformation",
                            "protocol": "1",\
                            "collection":"/example-data/corpora/CoNLL-ST_2002"},\
                           "127.0.0.1",\
                           "localhost")
        self.assertEquals(sorted(res['items']), [['c', None, '..'],
                                                 ['c', None, 'esp'],
                                                 ['c', None, 'ned']])

        # list esp content
        res = dispatcher({"action": "getCollectionInformation",
                            "protocol": "1",\
                            "collection":"/example-data/corpora/CoNLL-ST_2002/esp"},\
                           "127.0.0.1",\
                           "localhost")
        
        res = [i[:3] for i in sorted(res['items'])[:3]]
        self.assertEquals(res, [['c', None, '..'],
                                ['d', None, 'esp.train-doc-100'],
                                ['d', None, 'esp.train-doc-1400']])
    
    def test03_getDocument(self):
        """
        get a document from CoNLL-ST_2002/esp
        """
        res = dispatcher({"action": "getDocument",
                            "protocol": "1",\
                            "collection":"/example-data/corpora/CoNLL-ST_2002/esp",
                            "document":"esp.train-doc-100"},\
                           "127.0.0.1",\
                           "localhost")
        
        self.assertEquals(res["text"][:40], "Por Viruca Atanes Madrid, 24 may (EFE).\n")
        self.assertEquals(res["entities"][:2], [['T1', 'PER', [(4, 17)]], ['T2', 'LOC', [(18, 24)]]])
        self.assertEquals(res["attributes"], [])
        self.assertEquals(res["relations"], [])
        self.assertEquals(res["events"], [])
        self.assertEquals(res["triggers"], [])
        
    def test04_getDocumentTimestamp(self):
        """
        get document timestamp
        """
        res = dispatcher({"action": "getDocumentTimestamp",
                            "protocol": "1",\
                            "collection":"/example-data/corpora/CoNLL-ST_2002/esp",
                            "document":"esp.train-doc-100"},\
                           "127.0.0.1",\
                           "localhost")
        
        self.assertGreater(res["mtime"], 1528000000)
        
    def test04_importDocument(self):
        """
        add a test document
        """
        res = dispatcher({"action": "importDocument",
                            "protocol": "1",\
                            "collection":"/",
                            "text":"This is a test file.",
                            "docid":"id01",
                            "mtime":0},\
                           "127.0.0.1",\
                           "localhost")
        
        self.assertEquals(res, {'document': 'id01', 'action': 'importDocument', 'protocol': 1})
    
    
    def test05_whoami(self):
        """
        check user session login
        """
        res = dispatcher({"action": "whoami",
                            "protocol": "1",\
                            "collection":"/"},\
                           "127.0.0.1",\
                           "localhost")
        
        self.assertEquals(res, {'action': 'whoami', 'protocol': 1, 'user': 'admin'})

    def test06_logout(self):
        """
        logout then login again
        """
        res = dispatcher({"action": "logout",
                            "protocol": "1",\
                            "collection":"/"},\
                           "127.0.0.1",\
                           "localhost")
        
        self.assertEquals(res, {'action': 'logout', 'protocol': 1})
        
        res = dispatcher({"action": "login",\
                            "user": "admin",\
                            "password": "admin",\
                            "protocol": "1",\
                            "collection":"/"},\
                           "127.0.0.1",\
                           "localhost")
        self.assertEquals(res, {"action": "login",
                                'protocol': 1})
        
    def test07_searchTextInDocument(self):
        res = dispatcher({"action": "searchTextInDocument",
                            "protocol": "1",\
                            "text_match": "word",
                            "text": "test",
                            "collection":"/",
                            "scope":"document",
                            'concordancing':False,
                            'context_length':10,
                            'match_case':False,
                            "document":"id01"},\
                           "127.0.0.1",\
                           "localhost")
        
        self.assertEquals(res, {'action': 'searchTextInDocument',
                                  'collection': '/',
                                  'header': [('Document', 'string'),
                                             ('Annotation', 'string'),
                                             ('Text', 'string')],
                                  'items': [['a',
                                             {'match': [], 'matchfocus': [[10, 14]]},
                                             'id01',
                                             '10-14',
                                             'test']],
                                  'protocol': 1})

    def test08_searchTextInCollection(self):
        res = dispatcher({"action": "searchTextInCollection",
                            "protocol": "1",\
                            "text_match": "word",
                            "text": "test",
                            "collection":"/",
                            "scope":"collection",
                            'concordancing':False,
                            'context_length':10,
                            'match_case':False,
                            "document":"id01"},\
                           "127.0.0.1",\
                           "localhost")
        
        self.assertEquals(res, {'action': 'searchTextInCollection',
                                  'collection': '/',
                                  'header': [('Document', 'string'),
                                             ('Annotation', 'string'),
                                             ('Text', 'string')],
                                  'items': [['a',
                                             {'match': [], 'matchfocus': [[10, 14]]},
                                             'id01',
                                             '10-14',
                                             'test']],
                                  'protocol': 1})
    
    
    def test09_createSpan(self):
        res = dispatcher({"action": "createSpan",
                            "protocol": "1",\
                            "collection":"/",\
                            "offsets": "[[10, 14]]",\
                            "type": "Protein",\
                            "attributes": "{}",\
                            "normalizations": "",
                            "document":"id01",
                            "id":None,
                            "comment":""},\
                           "127.0.0.1",\
                           "localhost")
        self.assertEquals(res["edited"], [['T1']])
        
    def test10_deleteSpan(self):
        res = dispatcher({"action": "deleteSpan",
                                "protocol": "1",\
                                "collection":"/",\
                                "document":"id01",
                                "id":'T1'},\
                               "127.0.0.1",\
                               "localhost")
        self.assertEquals(res["edited"], [])
        
    def test10_storeSVG(self):
        svgData = open("tests/test_data/test.svg", "rb").read().decode("utf-8")
        
        res = dispatcher({"action": "storeSVG",
                                "protocol": "1",\
                                "collection":"/",\
                                "document":"id01",
                                "svg": svgData},\
                               "127.0.0.1",\
                               "localhost")
        self.assertEquals(res["stored"], [{'name': 'svg', 'suffix': 'svg'}])
        
        self.assertGreater(len(open("work/svg/%s.svg"%session.get_session().get_sid(), "rb").read().decode("utf-8")),
                           len(svgData))
        
    def test11_retrieveStored(self):
        svgData = open("work/svg/%s.svg"%session.get_session().get_sid(), "rb").read()
        import server
        with self.assertRaises(server.common.NoPrintJSONError) as context:
            dispatcher({"action": "retrieveStored",
                                "protocol": "1",\
                                "collection":"/",\
                                "document":"id01",
                                "suffix": "svg"},\
                               "127.0.0.1",\
                               "localhost")
        self.assertEquals(dict(context.exception.hdrs)["Content-Type"], "image/svg+xml")
        self.assertEquals(context.exception.data, svgData)
    
    
    def test12_downloadFile(self):
        import server
        
        for extension in ["txt", "ann"]:
            data = open("data/id01.%s"%extension, "rb").read()
            with self.assertRaises(server.common.NoPrintJSONError) as context:
                dispatcher({"action": "downloadFile",
                                    "protocol": "1",\
                                    "collection":"/",\
                                    "document":"id01",
                                    "extension":extension},\
                                   "127.0.0.1",\
                                   "localhost")
            self.assertEquals(dict(context.exception.hdrs)["Content-Type"], "text/plain; charset=utf-8")
            self.assertEquals(context.exception.data, data)
    
    def test13_downloadCollection(self):
        import server
        
        with self.assertRaises(server.common.NoPrintJSONError) as context:
            dispatcher({"action": "downloadCollection",
                                "protocol": "1",\
                                "collection":"/", 
                                "include_conf":True},\
                               "127.0.0.1",\
                               "localhost")
        self.assertEquals(dict(context.exception.hdrs)["Content-Type"], "application/octet-stream")
        # TODO: write extra check
    
#'downloadCollection': download_collection,
        
    def test99_deleteDocument(self):
        """
        delete the test document
        
        # TODO: complete this test once deleteDocument has been implemented
        """
        
        # remove the document
        os.remove(DATA_DIR+"/id01.txt")
        os.remove(DATA_DIR+"/id01.ann")
        
#        res = dispatcher({"action": "deleteDocument",
#                            "protocol": "1",\
#                            "collection":"/",
#                            "document":"id01"},\
#                           "127.0.0.1",\
#                           "localhost"))
        
    def test200_logoutDeleteSession(self):
        """
        logout and delete session
        """
        res = dispatcher({"action": "logout",
                            "protocol": "1",\
                            "collection":"/"},\
                           "127.0.0.1",\
                           "localhost")
        
        self.assertEquals(res, {'action': 'logout', 'protocol': 1})
        
        session.CURRENT_SESSION = None