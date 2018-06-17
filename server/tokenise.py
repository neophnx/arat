# -*- coding: utf-8 -*-


'''
Tokenisation related functionality.

Author:     Pontus Stenetorp <pontus stenetorp se>
Version:    2011-05-23
'''

# furure
from __future__ import with_statement
from __future__ import absolute_import
from __future__ import print_function


# arat
from server.message import Messager


def _token_boundaries_by_alignment(tokens, original_text):
    """
    Given a list of tokens and the original text,
    deduce the offsets of tokens
    """
    curr_pos = 0
    for tok in tokens:
        start_pos = original_text.index(tok, curr_pos)
        # TODO: Check if we fail to find the token!
        end_pos = start_pos + len(tok)
        yield (start_pos, end_pos)
        curr_pos = end_pos


def jp_token_boundary_gen(text):
    """
    Japanese tokenization via mecab
    """
    try:
        from mecab import token_offsets_gen
        for i in token_offsets_gen(text):
            yield i
    except ImportError:
        Messager.error('Failed to import MeCab, '
                       'falling back on whitespace tokenization. '
                       'Please check configuration and/or server setup.')
        for i in whitespace_token_boundary_gen(text):
            yield i


def gtb_token_boundary_gen(text):
    """
    >>> text = u"Specialized tokenizer for this p65(RelA)/p50 and that E. coli"

    >>> list(whitespace_token_boundary_gen(text))
    [(0, 11), (12, 21), (22, 25), (26, 30), (31, 44), (45, 48), (49, 53), (54, 56), (57, 61)]
    """
    from server.gtbtokenize import tokenize
    tokens = tokenize(text).split()
    for i in _token_boundaries_by_alignment(tokens, text):
        yield i


def whitespace_token_boundary_gen(text):
    """
    >>> text = u"A simple text to tokenize ."

    >>> list(whitespace_token_boundary_gen(text))
    [(0, 1), (2, 8), (9, 13), (14, 16), (17, 25), (26, 27)]
    """
    tokens = text.split()
    for i in _token_boundaries_by_alignment(tokens, text):
        yield i


REGISTERED_TOKENISER = {"mecab": jp_token_boundary_gen,
                        'whitespace': whitespace_token_boundary_gen,
                        'ptblike': gtb_token_boundary_gen}


def tokeniser_by_name(name):
    """
    load a tokenizer by name
    """
    if name in REGISTERED_TOKENISER:
        return REGISTERED_TOKENISER[name]

    Messager.warning('Unrecognized tokenisation option '
                     ', reverting to whitespace tokenisation.')
    return whitespace_token_boundary_gen


def _main():
    """
    CLI for testing purpose
    """
    from sys import argv

    def _text_by_offsets_gen(text, offsets):
        for start, end in offsets:
            yield text[start:end]

    if len(argv) == 1:
        argv.append('/dev/stdin')

    try:
        for txt_file_path in argv[1:]:
            print()
            print('### Tokenising:', txt_file_path)
            with open(txt_file_path, 'r') as txt_file:
                text = txt_file.read()
                print(text)
            print('# Original text:')
            print(text.replace('\n', '\\n'))
            #offsets = [o for o in jp_token_boundary_gen(text)]
            #offsets = [o for o in whitespace_token_boundary_gen(text)]
            offsets = [o for o in gtb_token_boundary_gen(text)]
            print('# Offsets:')
            print(offsets)
            print('# Tokens:')
            for tok in _text_by_offsets_gen(text, offsets):
                assert tok, 'blank tokens disallowed'
                assert not tok[0].isspace() and not tok[-1].isspace(), (
                    'tokens may not start or end with white-space "%s"' % tok)
                print('"%s"' % tok)
    except IOError:
        raise


if __name__ == '__main__':
    _main()
