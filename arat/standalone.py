# -*- coding: utf-8 -*-
"""
Arat server based on tornado


Created on Tue Jun 19 15:20:30 2018

@author: jgo
"""

# standard
import os
import argparse

# third party
import tornado.ioloop
import tornado.web

# arat
from arat.server import auth
from arat.server import document
# from arat.server import delete # not implemented yet
from arat.server import annotator
from arat.server import svg
from arat.server import download

INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))+"/client/"


def make_app():
    """
    Tornado application which define routes to handlers
    """

    routes = [(r'/static/(.*)',
               tornado.web.StaticFileHandler, {'path': INSTALL_DIR+'static'}),
              (r'/client/(.*)',
               tornado.web.StaticFileHandler, {'path': INSTALL_DIR}),
              (r'/data/(.*)(/[^/]*)', None, {'path': 'client'}),
              (r'/(index.x?html|favicon.ico)',
               tornado.web.StaticFileHandler, {"path": INSTALL_DIR}),
              (r"/",
               tornado.web.RedirectHandler, {"url": "/index.xhtml"}),

              (r'/login', auth.LoginHandler),
              (r'/logout', auth.LogoutHandler),
              (r'/whoami', auth.WhoAmIHandler),


              (r'/getCollectionInformation', document.CollectionInformationHandler),
              (r'/getDocument', document.DocumentHandler),
              (r'/getDocumentTimestamp', document.DocumentTimestampHandler),
              (r'/importDocument', document.SaveDocumentHandler),

              #              (r'/deleteDocument', delete.DeleteDocumentHandler),
              #              (r'/deleteCollection', delete.DeleteCollectionHandler),


              (r'/createSpan', annotator.CreateSpanHandler),
              (r'/deleteSpan', annotator.DeleteSpanHandler),
              (r'/splitSpan', annotator.SplitSpanHandler),
              (r'/createArc', annotator.CreateArcHandler),
              (r'/deleteArc', annotator.DeleteArcHandler),
              (r'/reverseArc', annotator.ReverseArcHandler),
              (r'/storeSVG', svg.StoreSvgHandler),
              (r'/retrieveSVG', svg.RetrieveSvgHandler),

              (r'/downloadFile', download.DownloadFileHandler),
              (r'/downloadCollection', download.DownloadCollectionHandler)

              #
              #        'getConfiguration': get_configuration,
              #    'convert': convert,
              ]

    return tornado.web.Application(routes,
                                   verbose=True,
                                   autoreload=True,
                                   serve_traceback=True,
                                   cookie_secret="arat secret")


def argparser():
    """
    Arat server CLI argument parser

    :rtype ArgumentParser:
    """
    parser = argparse.ArgumentParser(description='Arat server')
    parser.add_argument('port',
                        type=int,
                        default=8888,
                        help='bind server to this prt instead '
                             'of the default 8888')
    return parser


def main():
    """
    Tornado web server
    """
    import sys
    if len(sys.argv) == 1:
        sys.argv.append("8888")

    args = argparser().parse_args()

    app = make_app()
    app.listen(args.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
