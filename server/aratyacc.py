#!/usr/bin/env python

'''
Grammar for the arat stand-off format.

Example, test grammar on a collection:

    find . -name '*.ann' | parallel cat | ./aratyacc.py

Author:   Pontus Stenetorp    <pontus stenetorp se>
Version:  2011-07-11
'''

from __future__ import absolute_import
from __future__ import print_function
try:
    import ply.yacc as yacc
except ImportError:
    # We need to add ply to path
    from sys import path as sys_path
    from os.path import join as path_join
    from os.path import dirname

    sys_path.append(path_join(dirname(__file__), '../lib/ply-3.4'))

    import ply.yacc as yacc


# TODO: Recurse all the way to a file
# TODO: Comment annotation


def p_annotation_line(parser):
    '''
    annotation_line : annotation NEWLINE
    '''
    parser[0] = '%s\n' % (parser[1], )
    return parser

# TODO: Ugly newline


def p_annotation(parser):
    '''
    annotation  : textbound
                | event
                | modifier
                | equiv
                | relation
                | comment
    '''
    parser[0] = parser[1]
    return parser

# TODO: What do we really call these?


def p_equiv(parser):
    '''
    equiv : equiv_core SPACE equiv_members
    '''
    parser[0] = '%s %s' % (parser[1], parser[3], )
    return parser


def p_equiv_core(parser):
    '''
    equiv_core : WILDCARD TAB TYPE
    '''
    parser[0] = '*\t%s' % (parser[3], )
    return parser


def p_equiv_members(parser):
    '''
    equiv_members   : equiv_member SPACE equiv_members
                    | equiv_member
    '''
    parser[0] = '%s' % (parser[1], )
    try:
        parser[0] += ' %s' % (parser[3], )
    except IndexError:
        # We did not have any more members
        pass
    return parser


def p_equiv_member(parser):
    '''
    equiv_member : id
    '''
    parser[0] = '%s' % (parser[1], )
    return parser


def p_textbound(parser):
    '''
    textbound   :  textbound_freetext
                |  textbound_core
    '''
    parser[0] = parser[1]
    return parser


def p_textbound_core(parser):
    '''
    textbound_core : TEXT_BOUND_ID TAB TYPE SPACE INTEGER SPACE INTEGER
    '''
    parser[0] = '%s\t%s %d %d' % (parser[1], parser[3], parser[5], parser[7], )
    return parser


def p_textbound_freetext(parser):
    '''
    textbound_freetext : textbound_core TAB FREETEXT
    '''
    parser[0] = '%s\t%s' % (parser[1], parser[3], )
    return parser


def p_comment(parser):
    '''
    comment : COMMENT_ID TAB TYPE SPACE id
    '''
    parser[0] = '%s\t%s %s' % (parser[1], parser[3], parser[5])
    return parser


def p_event(parser):
    '''
    event   : event_core SPACE event_arguments
            | event_core SPACE
            | event_core
    '''
    parser[0] = parser[1]
    try:
        parser[0] += parser[2]
    except IndexError:
        pass
    try:
        parser[0] += parser[3]
    except IndexError:
        pass
    return parser


def p_event_core(parser):
    '''
    event_core : EVENT_ID TAB TYPE COLON id
    '''
    parser[0] = '%s\t%s:%s' % (parser[1], parser[3], parser[5], )
    return parser


def p_event_arguments(parser):
    '''
    event_arguments : event_argument SPACE event_arguments
                    | event_argument
    '''
    parser[0] = '%s' % (parser[1], )
    try:
        parser[0] += ' ' + parser[3]
    except IndexError:
        pass
    return parser


def p_event_argument(parser):
    '''
    event_argument : argument COLON id
    '''
    parser[0] = '%s:%s' % (parser[1], parser[3], )
    return parser


def p_modifier(parser):
    '''
    modifier : MODIFIER_ID TAB TYPE SPACE id
    '''
    parser[0] = '%s\t%s %s' % (parser[1], parser[3], parser[5], )
    return parser


def p_relation(parser):
    '''
    relation : RELATION_ID TAB TYPE SPACE argument COLON id SPACE argument COLON id
    '''
    # TODO: Should probably require only one of each argument type
    parser[0] = '%s\t%s %s:%s %s:%s' % (
        parser[1], parser[3], parser[5], parser[7], parser[9], parser[11], )
    return parser


def p_argument(parser):
    '''
    argument    : TYPE
                | TYPE INTEGER
    '''
    parser[0] = parser[1]
    try:
        parser[0] += str(parser[2])
    except IndexError:
        pass
    return parser

# Generic id


def p_id(parser):
    '''
    id  : TEXT_BOUND_ID
        | EVENT_ID
        | RELATION_ID
        | MODIFIER_ID
        | COMMENT_ID
    '''
    parser[0] = parser[1]
    return parser


def p_error(parser):
    print('Syntax error in input! "%s"' % (str(parser), ))
    raise Exception


PARSER = yacc.yacc()


def _main():
    from sys import stdin
    for line in stdin:
        print('Input: "%s"' % line.rstrip('\n'))
        result = PARSER.parse(line)

        result_ref = ('"%s" != "%s"' % (result, line)).replace('\n', '\\n')
        assert result == line, result_ref
        print(result, end=' ')


if __name__ == '__main__':
    _main()
