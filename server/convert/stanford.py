#!/usr/bin/env python

'''
Conversion scripts related to Stanford tools.

Author:     Pontus Stenetorp    <pontus stenetorp se>
Version:    2012-06-26
'''

# TODO: Currently pretty much every single call re-parses the XML, optimise?
# TODO: We could potentially put the lemma into a comment

from __future__ import with_statement

from __future__ import absolute_import
from collections import defaultdict
from itertools import chain
from sys import argv, path as sys_path, stderr, stdout
from os.path import dirname, join as path_join
from xml.etree import ElementTree

from .ptbesc import unescape as ptb_unescape
import six

try:
    from collections import namedtuple
except ImportError:
    sys_path.append(path_join(dirname(__file__), '..', '..', 'lib'))
    from altnamedtuple import namedtuple

try:
    from server.annotation import (BinaryRelationAnnotation, EquivAnnotation,
                                   TextBoundAnnotation)
except ImportError:
    sys_path.append(path_join(dirname(__file__), '..'))
    from server.annotation import (BinaryRelationAnnotation, EquivAnnotation,
                                   TextBoundAnnotation)

Token = namedtuple('Token', ('word', 'lemma', 'start', 'end', 'pos', 'ner', ))


def _escape_pos_tags(pos):
    pos_res = pos
    for _from, to in (
            ("'", '__SINGLEQUOTE__', ),
            ('"', '__DOUBLEQUOTE__', ),
            ('$', '__DOLLAR__', ),
            (',', '__COMMA__', ),
            ('.', '__DOT__', ),
            (':', '__COLON__', ),
            ('`', '__BACKTICK__', ),
    ):
        pos_res = pos_res.replace(_from, to)
    return pos_res


def _token_by_ids(soup):
    token_by_ids = defaultdict(dict)

    for sent_e in _find_sentences_element(soup).getiterator('sentence'):
        sent_id = int(sent_e.get('id'))
        for tok_e in sent_e.getiterator('token'):
            tok_id = int(tok_e.get('id'))
            tok_word = six.text_type(tok_e.find('word').text)
            tok_lemma = six.text_type(tok_e.find('lemma').text)
            tok_start = int(tok_e.find('CharacterOffsetBegin').text)
            tok_end = int(tok_e.find('CharacterOffsetEnd').text)
            tok_pos = six.text_type(tok_e.find('POS').text)
            tok_ner = six.text_type(tok_e.find('NER').text)

            token_by_ids[sent_id][tok_id] = Token(
                word=tok_word,
                lemma=tok_lemma,
                start=tok_start,
                end=tok_end,
                # Escape the PoS since brat dislike $ and .
                pos=_escape_pos_tags(tok_pos),
                ner=tok_ner
            )

    return token_by_ids


def _tok_it(token_by_ids):
    for s_id in sorted(k for k in token_by_ids):
        for t_id in sorted(k for k in token_by_ids[s_id]):
            yield s_id, t_id, token_by_ids[s_id][t_id]


def _soup(xml):
    return ElementTree.fromstring(xml.encode('utf-8'))


def token_offsets(xml):
    soup = _soup(xml)
    token_by_ids = _token_by_ids(soup)
    return [(tok.start, tok.end) for _, _, tok in _tok_it(token_by_ids)]


def sentence_offsets(xml):
    soup = _soup(xml)
    token_by_ids = _token_by_ids(soup)
    sent_min_max = defaultdict(lambda: (2**32, -1, ))
    for s_id, _, tok in _tok_it(token_by_ids):
        s_entry = sent_min_max[s_id]
        sent_min_max[s_id] = (min(tok.start, s_entry[0]),
                              max(tok.end, s_entry[1]), )
    return sorted((s_start, s_end) for s_start, s_end in six.itervalues(sent_min_max))


def text(xml):
    # It would be nice to have access to the original text, but this actually
    # isn't a part of the XML. Constructing it isn't that easy either, you
    # would have to assume that each "missing" character is a space, but you
    # don't really have any guarantee that this is the case...

    soup = _soup(xml)
    token_by_ids = _token_by_ids(soup)

    # Get the presumed length of the text
    max_offset = -1
    for _, _, tok in _tok_it(token_by_ids):
        max_offset = max(max_offset, tok.end)

    # Then re-construct what we believe the text to be
    text = list(' ' * max_offset)
    for _, _, tok in _tok_it(token_by_ids):
        # Also unescape any PTB escapes in the text while we are at it
        # Note: Since Stanford actually doesn't do all the escapings properly
        # this will sometimes fail! Hint: Try "*/\*".
        unesc_word = ptb_unescape(tok.word)
        text[tok.start:len(unesc_word)] = unesc_word

    return u''.join(text)


def _pos(xml, start_id=1):
    soup = _soup(xml)
    token_by_ids = _token_by_ids(soup)

    curr_id = start_id
    for s_id, t_id, tok in _tok_it(token_by_ids):
        yield s_id, t_id, TextBoundAnnotation(((tok.start, tok.end, ), ),
                                              'T%s' % curr_id, tok.pos, '')
        curr_id += 1


def pos(xml, start_id=1):
    return (a for _, _, a in _pos(xml, start_id=start_id))


def ner(xml, start_id=1):
    soup = _soup(xml)
    token_by_ids = _token_by_ids(soup)

    # Stanford only has Inside and Outside tags, so conversion is easy
    nes = []
    last_ne_tok = None
    prev_tok = None
    for _, _, tok in _tok_it(token_by_ids):
        if tok.ner != 'O':
            if last_ne_tok is None:
                # Start of an NE from nothing
                last_ne_tok = tok
            elif tok.ner != last_ne_tok.ner:
                # Change in NE type
                nes.append(
                    (last_ne_tok.start, prev_tok.end, last_ne_tok.ner, ))
                last_ne_tok = tok
            else:
                # Continuation of the last NE, move along
                pass
        elif last_ne_tok is not None:
            # NE ended
            nes.append((last_ne_tok.start, prev_tok.end, last_ne_tok.ner, ))
            last_ne_tok = None
        prev_tok = tok
    else:
        # Do we need to terminate the last named entity?
        if last_ne_tok is not None:
            nes.append((last_ne_tok.start, prev_tok.end, last_ne_tok.ner, ))

    curr_id = start_id
    for start, end, _type in nes:
        yield TextBoundAnnotation(((start, end), ), 'T%s' % curr_id, _type, '')
        curr_id += 1


def coref(xml, start_id=1):
    soup = _soup(xml)
    token_by_ids = _token_by_ids(soup)

    docs_e = soup.findall('document')
    assert len(docs_e) == 1
    docs_e = docs_e[0]
    # Despite the name, this element contains conferences (note the "s")
    corefs_e = docs_e.findall('coreference')
    if not corefs_e:
        # No coreferences to process
        raise StopIteration
    assert len(corefs_e) == 1
    corefs_e = corefs_e[0]

    curr_id = start_id
    for coref_e in corefs_e:
        if corefs_e.tag != 'coreference':
            # To be on the safe side
            continue

        # This tag is now a full corference chain
        chain = []
        for mention_e in coref_e.getiterator('mention'):
            # Note: There is a "representative" attribute signalling the most
            #   "suitable" mention, we are currently not using this
            # Note: We don't use the head information for each mention
            sentence_id = int(mention_e.find('sentence').text)
            start_tok_id = int(mention_e.find('start').text)
            end_tok_id = int(mention_e.find('end').text) - 1

            mention_id = 'T%s' % (curr_id, )
            chain.append(mention_id)
            curr_id += 1
            yield TextBoundAnnotation(
                ((token_by_ids[sentence_id][start_tok_id].start,
                  token_by_ids[sentence_id][end_tok_id].end), ),
                mention_id, 'Mention', '')

        yield EquivAnnotation('Coreference', chain, '')


def _find_sentences_element(soup):
    # Find the right portion of the XML and do some limited sanity checking
    docs_e = soup.findall('document')
    assert len(docs_e) == 1
    docs_e = docs_e[0]
    sents_e = docs_e.findall('sentences')
    assert len(sents_e) == 1
    sents_e = sents_e[0]

    return sents_e


def _dep(xml, source_element='basic-dependencies'):
    soup = _soup(xml)
    token_by_ids = _token_by_ids(soup)

    ann_by_ids = defaultdict(dict)
    for s_id, t_id, ann in _pos(xml):
        ann_by_ids[s_id][t_id] = ann
        yield ann

    curr_rel_id = 1
    for sent_e in _find_sentences_element(soup).getiterator('sentence'):
        sent_id = int(sent_e.get('id'))

        # Attempt to find dependencies as distinctly named elements as they
        #   were stored in the Stanford XML format prior to 2013.
        deps_e = sent_e.findall(source_element)
        if len(deps_e) == 0:
            # Perhaps we are processing output following the newer standard,
            #   check for the same identifier but as a type attribute for
            #   general "dependencies" elements.
            deps_e = list(e for e in sent_e.getiterator('dependencies')
                          if e.attrib['type'] == source_element)
        assert len(deps_e) == 1
        deps_e = deps_e[0]

        for dep_e in deps_e:
            if dep_e.tag != 'dep':
                # To be on the safe side
                continue

            dep_type = dep_e.get('type')
            assert dep_type is not None

            if dep_type == 'root':
                # Skip dependencies to the root node, this behaviour conforms
                #   with how we treated the pre-2013 format.
                continue

            gov_tok_id = int(dep_e.find('governor').get('idx'))
            dep_tok_id = int(dep_e.find('dependent').get('idx'))

            yield BinaryRelationAnnotation(
                'R%s' % curr_rel_id, dep_type,
                'Governor', ann_by_ids[sent_id][gov_tok_id].id,
                'Dependent', ann_by_ids[sent_id][dep_tok_id].id,
                ''
            )
            curr_rel_id += 1


def basic_dep(xml):
    return _dep(xml)


def collapsed_dep(xml):
    return _dep(xml, source_element='collapsed-dependencies')


def collapsed_ccproc_dep(xml):
    return _dep(xml, source_element='collapsed-ccprocessed-dependencies')
