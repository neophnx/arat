#!/usr/bin/env python

'''
Tokenisation for the arat stand-off format.

Example, test tokenisation on a collection:

    find . -name '*.ann' | parallel cat | ./aratlex.py

Author:  Pontus Stenetorp    <pontus stenetorp se>
Version: 2011-07-11
'''

from __future__ import absolute_import
from __future__ import print_function
try:
    import ply.lex as lex
except ImportError:
    # We need to add ply to path
    from sys import path as sys_path
    from os.path import join as path_join
    from os.path import dirname

    sys_path.append(path_join(dirname(__file__), '../lib/ply-3.4'))

    import ply.lex as lex

TOKENS = (
    # Primitives
    'COLON',
    'NEWLINE',
    'SPACE',
    'TAB',
    'WILDCARD',

    # Identifiers
    'COMMENT_ID',
    'EVENT_ID',
    'MODIFIER_ID',
    'RELATION_ID',
    'TEXT_BOUND_ID',

    # Values
    'INTEGER',
    'TYPE',

    # Special-case for freetext
    'FREETEXT',
)

STATES = (
    ('freetext', 'exclusive'),
)

T_COLON = r':'
T_SPACE = r'\ '
T_WILDCARD = r'\*'


def t_comment_id(text):
    r'\#[0-9]+'
    return text


def t_event_id(text):
    r'E[0-9]+'
    return text


def t_modifier_id(text):
    r'M[0-9]+'
    return text


def t_relation_id(text):
    r'R[0-9]+'
    return text


def t_text_bound_id(text):
    r'T[0-9]+'
    return text


def t_newline(text):
    r'\n'
    # Increment the lexers line-count
    text.lexer.lineno += 1
    # Reset the count of tabs on this line
    text.lexer.line_tab_count = 0
    return text


def t_tab(text):
    r'\t'
    # Increment the number of tabs we have soon on this line
    text.lexer.line_tab_count += 1
    if text.lexer.line_tab_count == 2:
        text.lexer.begin('freetext')
    return text


def t_integer(text):
    r'\d+'
    text.value = int(text.value)
    return text


def t_type(text):
    r'[A-Z][A-Za-z_-]*'
    return text


def t_freetext_freetext(text):
    r'[^\n\t]+'
    return text


def t_freetext_tab(text):
    r'\t'
    # End freetext mode INITAL
    text.lexer.begin('INITIAL')
    return text


def t_freetext_newline(text):
    r'\n'
    # Increment the lexers line-count
    text.lexer.lineno += 1
    # Reset the count of tabs on this line
    text.lexer.line_tab_count = 0
    # End freetext mode INITAL
    text.lexer.begin('INITIAL')
    return text

# Error handling rule


def t_error(text):
    print("Illegal character '%s'" % text.value[0])
    raise Exception


def t_freetext_error(text):
    return t_error(text)


LEXER = lex.lex()
LEXER.line_tab_count = 0


def _main():
    from sys import stdin
    for line in stdin:
        LEXER.input(line)

        for tok in LEXER:
            print(tok)


if __name__ == '__main__':
    _main()
