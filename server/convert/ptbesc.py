
'''
Penn TreeBank escaping.

Author:     Pontus Stenetorp    <pontus stenetorp se>
Version:    2011-09-12
'''

# future
from __future__ import absolute_import
from __future__ import print_function

# third party
import six

# Constants
# From: To
PTB_ESCAPES = {
    u'(': u'-LRB-',
    u')': u'-RRB-',
    u'[': u'-LSB-',
    u']': u'-RSB-',
    u'{': u'-LCB-',
    u'}': u'-RCB-',
    u'/': u'\\/',
    u'*': u'\\*',
}
###


def escape(text):
    """
    Escape treebank
    """
    for _from, _to in six.iteritems(PTB_ESCAPES):
        text = text.replace(_from, _to)
    return text


def unescape(text):
    """
    Unescape treebank
    """
    for _from, _to in six.iteritems(PTB_ESCAPES):
        text = text.replace(_to, _from)
    return text


def main(args):
    """
    CLI entry point
    """
    from argparse import ArgumentParser
    from sys import stdin

    # TODO: Doc!
    argparser = ArgumentParser()
    argparser.add_argument('-u', '--unescape', action='store_true')
    argp = argparser.parse_args(args[1:])

    for line in stdin:
        line = line.rstrip('\n')
        if argp.unescape:
            line = unescape(line)
        else:
            line = escape(line)
        print(line)


if __name__ == '__main__':
    from sys import argv
    exit(main(argv))
