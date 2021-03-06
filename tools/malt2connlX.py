#!/usr/bin/env python

'''
Convert Malt dependencies to CoNLL-X dependencies.

Usage:

    cat *.malt | ./malt2connlX.py > output.conll

NOTE: Beware of nasty Windows newlines:

    dos2unix *.malt

Author:     Pontus Stenetorp    <pontus stenetorp se>
Version:    2011-12-05
'''

from __future__ import absolute_import
from sys import stdin, stdout
from re import compile as _compile
from codecs import open as _open

# Constants
MALT_REGEX = _compile(u'^(?P<token>.*?)\\t(?P<pos>[^\\t]+)\\t'
                      u'(?P<head>[^\\t]+)\\t(?P<rel>[^\\t]+)$')
# NOTE: My interpretation from reversing the format by example
OUTPUT_LINE = u'{token_num}\t{token}\t_\t{pos}\t{pos}\t_\t{head}\t{rel}\t_\t_'
###


def main(args):
    token_cnt = 0
    for line in (l.decode('utf-8').rstrip('\n') for l in stdin):
        if not line:
            # Done with the sentence
            token_cnt = 0
            stdout.write('\n')
            continue
        else:
            token_cnt += 1

        m = MALT_REGEX.match(line)
        assert m is not None, 'parse error (sorry...)'
        g_dic = m.groupdict()
        output = OUTPUT_LINE.format(
            token_num=token_cnt,
            token=g_dic['token'],
            pos=g_dic['pos'],
            head=g_dic['head'],
            rel=g_dic['rel']
        )
        stdout.write(output.encode('utf-8'))
        stdout.write('\n')


if __name__ == '__main__':
    from sys import argv
    exit(main(argv))
