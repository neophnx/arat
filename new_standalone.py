#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 19 15:20:30 2018

@author: jgo
"""

import os

import ujson as json
import tornado.ioloop
import tornado.web

from arat.server.dispatch import dispatch
from arat.server.message import Messager

INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))+"/arat/client/"
print(INSTALL_DIR)

class AjaxRestAdapter(tornado.web.RequestHandler):
    def post(self):
        body = json.loads(self.request.body)
        
        # ensure a collection is set
        body["collection"] = body.get("collection", "/")
        
        response = dispatch(http_args=body,
                            client_ip="127.0.0.1",
                            client_hostname="localhost")
        
        # add messages add clear the queue
        response = Messager.output_json(response)
        
        self.set_header("Content-Type", "text/json")
        self.write(json.dumps(response))

def make_app():
    return tornado.web.Application([
            (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': INSTALL_DIR+'static'}),
            (r'/client/(.*)', tornado.web.StaticFileHandler, {'path': INSTALL_DIR}),
            (r'/ajax.cgi', AjaxRestAdapter),
            (r'/data/(.*)(/[^/]*)', None, {'path': 'client'}),
            (r'/(index.x?html|favicon.ico)?', tornado.web.StaticFileHandler, {"path": INSTALL_DIR})],
            verbose=True,
            autoreload=True,
           serve_traceback=True )

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()