'''
Annotator functionality, editing and retrieving status.

Author:     Pontus Stenetorp
Version:    2011-04-22
'''

# XXX: This module is messy, re-factor to be done

# future
from __future__ import with_statement
from __future__ import absolute_import

# standard
from os.path import join as path_join
from re import compile as re_compile

# third party
import six  # pylint disable: import-error
from six.moves import range  # pylint disable: import-error


# arat
from arat.server.annotation import (OnelineCommentAnnotation, TEXT_FILE_SUFFIX,
                                    TextAnnotations, DependingAnnotationDeleteError,
                                    EventAnnotation, EquivAnnotation, open_textfile,
                                    AnnotationsIsReadOnlyError, AttributeAnnotation,
                                    NormalizationAnnotation, SpanOffsetOverlapError,
                                    DISCONT_SEP)
from arat.server.common import ProtocolError, ProtocolArgumentError
from arat.server.annotation import TextBoundAnnotationWithText
from arat.server.document import real_directory
from arat.server.jsonwrap import loads as json_loads, dumps as json_dumps
from arat.server.message import Messager
from arat.server.projectconfig import ProjectConfiguration
from arat.server.projectconfig.commons import ENTITY_CATEGORY, EVENT_CATEGORY
from arat.server.common import AuthenticatedJsonHandler

from config import DEBUG


# Constants
MUL_NL_REGEX = re_compile(r'\n+')
###

# TODO: Couldn't we incorporate this nicely into the Annotations class?
# TODO: Yes, it is even gimped compared to what it should do when not. This
#       has been a long pending goal for refactoring.


class ModificationTracker(object):
    def __init__(self):
        self.__added = []
        self.__changed = []
        self.__deleted = []

    def __len__(self):
        return len(self.__added) + len(self.__changed) + len(self.__deleted)

    def addition(self, added):
        self.__added.append(added)

    def deletion(self, deleted):
        self.__deleted.append(deleted)

    def change(self, before, after):
        self.__changed.append((before, after))

    def _json_response_debug(self):
        msg_str = ''
        if self.__added:
            msg_str += ('Added the following line(s):\n'
                        + '\n'.join([six.text_type(a).rstrip() for a in self.__added]))
        if self.__changed:
            changed_strs = []
            for before, after in self.__changed:
                changed_strs.append('\t%s\n\tInto:\n\t%s' % (
                    six.text_type(before).rstrip(), six.text_type(after).rstrip()))
            msg_str += ('Changed the following line(s):\n'
                        + '\n'.join([six.text_type(a).rstrip() for a in changed_strs]))
        if self.__deleted:
            msg_str += ('Deleted the following line(s):\n'
                        + '\n'.join([six.text_type(a).rstrip() for a in self.__deleted]))
        if msg_str:
            Messager.info(msg_str, duration=3*len(self))
        else:
            Messager.info('No changes made')

    def json_response(self, response=None):
        if response is None:
            response = {}

        # debugging
        if DEBUG:
            self._json_response_debug()

        # highlighting
        response['edited'] = []
        # TODO: implement cleanly, e.g. add a highlightid() method to Annotation classes
        for a in self.__added:
            try:
                response['edited'].append(a.reference_id())
            except AttributeError:
                pass  # not all implement reference_id()
        for _, a in self.__changed:
            # can't mark "before" since it's stopped existing
            try:
                response['edited'].append(a.reference_id())
            except AttributeError:
                pass  # not all implement reference_id()

        # unique, preserve order
        seen = set()
        uniqued = []
        for i in response['edited']:
            s = str(i)
            if s not in seen:
                uniqued.append(i)
                seen.add(s)
        response['edited'] = uniqued

        return response

# TODO: revive the "unconfirmed annotation" functionality;
# the following currently unused bit may help
# def confirm_span(docdir, docname, span_id):
#     document = path_join(docdir, docname)

#     txt_file_path = document + '.' + TEXT_FILE_SUFFIX

#     with TextAnnotations(document) as ann_obj:
#         mods = ModificationTracker()

#         # find AnnotationUnconfirmed comments that refer
#         # to the span and remove them
#         # TODO: error checking
#         for ann in ann_obj.get_oneline_comments():
#             if ann.type_ == "AnnotationUnconfirmed" and ann.target == span_id:
#                 ann_obj.del_annotation(ann, mods)

#         mods_json = mods.json_response()
#         # save a roundtrip and send the annotations also
#         j_dic = _json_from_ann(ann_obj)
#         mods_json['annotations'] = j_dic
#         add_messages_to_json(mods_json)
#         print dumps(mods_json)


def _json_from_ann(ann_obj):
    # Returns json with ann_obj contents and the relevant text.  Used
    # for saving a round-trip when modifying annotations by attaching
    # the latest annotation data into the response to the edit
    # request.
    j_dic = {}
    txt_file_path = ann_obj.get_document() + '.' + TEXT_FILE_SUFFIX
    from arat.server.document import (_enrich_json_with_data, _enrich_json_with_base,
                                      _enrich_json_with_text)
    _enrich_json_with_base(j_dic)
    # avoid reading text file if the given ann_obj already holds it
    try:
        doctext = ann_obj.document_text
    except AttributeError:
        # no such luck
        doctext = None
    _enrich_json_with_text(j_dic, txt_file_path, doctext)
    _enrich_json_with_data(j_dic, ann_obj)
    return j_dic


def _canonical_offset_list(offsets):
    """
    Given a list of (start, end) offsets, output the simplest equivalent
    unique form.

    :param list offsets: list of offsets
    :returns list: canonical form of input

    >>> _canonical_offset_list([(1, 2), (2, 4)])
    [(1, 4)]

    """

    offsets = sorted(set(offsets))

    if not offsets:  # empty
        return offsets

    res = []
    # removes overlap
    start0, end0 = offsets.pop(0)
    while offsets:
        start1, end1 = offsets.pop(0)
        if start1 <= end0:  # overlap
            end0 = end1
        else:
            res.append((start0, end0))
            start0, end0 = start1, end1

    res.append((start0, end0))

    return res


def _offsets_equal(offsets1, offsets2):
    """
    Given two lists of (start, end) integer offset sets, returns
    whether they identify the same sets of characters.

    :param list offsets1: list of offsets
    :param list offsets2: list of offsets
    :returns bool:
    """

    # short-circuit (expected to be the most common case)
    if offsets1 == offsets2:
        return True
    return _canonical_offset_list(offsets1) == _canonical_offset_list(offsets2)


def _text_for_offsets(text, offsets):
    """
    Given a text and a list of (start, end) integer offsets, returns
    the (catenated) text corresponding to those offsets, joined
    appropriately for use in a TextBoundAnnotation(WithText).



    :param str text:
    :param list offsets: list of offsets


    >>> _text_for_offsets("Welcome home!", [(0, 2), (8, 10)])
    'We ho'
    """
    # this makes sense only in canonical form
    offsets = _canonical_offset_list(offsets)
    if offsets and (offsets[0][0] < 0 or offsets[-1][1] >= len(text)):
        Messager.error(
            '_text_for_offsets: failed to get text for given offsets (%s)' % str(offsets))
        raise ProtocolArgumentError

    return DISCONT_SEP.join(text[i:j] for i, j in offsets)


def _edit_span(ann_obj, mods, id_, offsets, projectconf, attributes, type_,
               undo_resp=None):
    if undo_resp is None:
        undo_resp = {}

    # TODO: Handle failure to find!
    ann = ann_obj.get_ann_by_id(id_)

    if isinstance(ann, EventAnnotation):
        # We should actually modify the trigger
        tb_ann = ann_obj.get_ann_by_id(ann.trigger)
        e_ann = ann
        undo_resp['id'] = e_ann.id_
        ann_category = EVENT_CATEGORY
    else:
        tb_ann = ann
        e_ann = None
        undo_resp['id'] = tb_ann.id_
        ann_category = ENTITY_CATEGORY

    # Store away what we need to restore the old annotation
    undo_resp['action'] = 'mod_tb'
    undo_resp['offsets'] = tb_ann.spans[:]
    undo_resp['type'] = tb_ann.type_

    if not _offsets_equal(tb_ann.spans, offsets):

        # TODO: Log modification too?
        before = six.text_type(tb_ann)
        #log_info('Will alter span of: "%s"' % str(to_edit_span).rstrip('\n'))
        tb_ann.spans = offsets[:]
        tb_ann.text = _text_for_offsets(
            ann_obj.document_text, tb_ann.spans)
        #log_info('Span altered')
        mods.change(before, tb_ann)

    if ann.type_ != type_:
        if ann_category != projectconf.type_category(type_):
            # Can't convert event to entity etc. (The client should protect
            # against this in any case.)
            # TODO: Raise some sort of protocol error
            Messager.error("Cannot convert %s (%s) into %s (%s)"
                           % (ann.type_, projectconf.type_category(ann.type_),
                              type_, projectconf.type_category(type_)),
                           duration=10)

        else:
            before = six.text_type(ann)
            ann.type_ = type_

            # Try to propagate the type change
            try:
                # XXX: We don't take into consideration other anns with the
                # same trigger here!
                ann_trig = ann_obj.get_ann_by_id(ann.trigger)
                if ann_trig.type_ != ann.type_:
                    # At this stage we need to determine if someone else
                    # is using the same trigger
                    if any((event_ann
                            for event_ann in ann_obj.get_events()
                            if (event_ann.trigger == ann.trigger
                                and event_ann != ann))):
                        # Someone else is using it, create a new one
                        from copy import copy
                        # A shallow copy should be enough
                        new_ann_trig = copy(ann_trig)
                        # It needs a new id
                        new_ann_trig.id_ = ann_obj.get_new_id('T')
                        # And we will change the type_
                        new_ann_trig.type_ = ann.type_
                        # Update the old annotation to use this trigger
                        ann.trigger = six.text_type(new_ann_trig.id_)
                        ann_obj.add_annotation(new_ann_trig)
                        mods.addition(new_ann_trig)
                    else:
                        # Okay, we own the current trigger, but does an
                        # identical to our sought one already exist?
                        found = None
                        for tb_ann in ann_obj.get_textbounds():
                            if (_offsets_equal(tb_ann.spans, ann_trig.spans) and
                                    tb_ann.type_ == ann.type_):
                                found = tb_ann
                                break

                        if found is None:
                            # Just change the trigger type since we are the
                            # only users
                            before = six.text_type(ann_trig)
                            ann_trig.type_ = ann.type_
                            mods.change(before, ann_trig)
                        else:
                            # Attach the new trigger THEN delete
                            # or the dep will hit you
                            ann.trigger = six.text_type(found.id_)
                            ann_obj.del_annotation(ann_trig)
                            mods.deletion(ann_trig)
            except AttributeError:
                # It was most likely a TextBound entity
                pass

            # Finally remember the change
            mods.change(before, ann)
    return tb_ann, e_ann


def __create_span(ann_obj, mods, type_, offsets, txt_file_path,
                  projectconf, attributes):
    # For event types, reuse trigger if a matching one exists.
    found = None
    if projectconf.is_event_type(type_):
        for tb_ann in ann_obj.get_textbounds():
            try:
                if (_offsets_equal(tb_ann.spans, offsets)
                        and tb_ann.type_ == type_):
                    found = tb_ann
                    break
            except AttributeError:
                # Not a trigger then
                pass

    if found is None:
        # Get a new ID
        new_id = ann_obj.get_new_id('T')  # XXX: Cons
        # Get the text span
        with open_textfile(txt_file_path, 'r') as txt_file:
            text = txt_file.read()
            text_span = _text_for_offsets(text, offsets)

        # The below code resolves cases where there are newlines in the
        #   offsets by creating discontinuous annotations for each span
        #   separated by newlines. For most cases it preserves the offsets.
        seg_offsets = []
        for o_start, o_end in offsets:
            pos = o_start
            for text_seg in text_span.split('\n'):
                if not text_seg and o_start != o_end:
                    # Double new-line, skip ahead
                    pos += 1
                    continue
                start = pos
                end = start + len(text_seg)

                # For the next iteration the position is after the newline.
                pos = end + 1

                # Adjust the offsets to compensate for any potential leading
                #   and trailing whitespace.
                start += len(text_seg) - len(text_seg.lstrip())
                end -= len(text_seg) - len(text_seg.rstrip())

                # If there is any segment left, add it to the offsets.
                if start != end:
                    seg_offsets.append((start, end, ))

        # if we're dealing with a null-span
        if not seg_offsets:
            seg_offsets = offsets

        ann_text = DISCONT_SEP.join((text[start:end]
                                     for start, end in seg_offsets))
        ann = TextBoundAnnotationWithText(seg_offsets, new_id, type_, ann_text)
        ann_obj.add_annotation(ann)
        mods.addition(ann)
    else:
        ann = found

    if ann is not None:
        if projectconf.is_physical_entity_type(type_):
            # TODO: alert that negation / speculation are ignored if set
            event = None
        else:
            # Create the event also
            new_event_id = ann_obj.get_new_id('E')  # XXX: Cons
            event = EventAnnotation(
                ann.id_, [], six.text_type(new_event_id), type_, '')
            ann_obj.add_annotation(event)
            mods.addition(event)
    else:
        # We got a newline in the span, don't take any action
        event = None

    return ann, event


def _set_attributes(ann_obj, ann, attributes, mods, undo_resp=None):
    if undo_resp is None:
        undo_resp = {}
    # Find existing attributes (if any)
    existing_attr_anns = set((a for a in ann_obj.get_attributes()
                              if a.target == ann.id_))

    #log_info('ATTR: %s' %(existing_attr_anns, ))

    # Note the existing annotations for undo
    undo_resp['attributes'] = json_dumps(dict([(e.type_, e.value)
                                               for e in existing_attr_anns]))

    for existing_attr_ann in existing_attr_anns:
        if existing_attr_ann.type_ not in attributes:
            # Delete attributes that were un-set existed previously
            ann_obj.del_annotation(existing_attr_ann)
            mods.deletion(existing_attr_ann)
        else:
            # If the value of the attribute is different, alter it
            new_value = attributes[existing_attr_ann.type_]
            #log_info('ATTR: "%s" "%s"' % (new_value, existing_attr_ann.value))
            if existing_attr_ann.value != new_value:
                before = six.text_type(existing_attr_ann)
                existing_attr_ann.value = new_value
                mods.change(before, existing_attr_ann)

    # The remaining annotations are new and should be created
    for attr_type, attr_val in six.iteritems(attributes):
        if attr_type not in set((a.type_ for a in existing_attr_anns)):
            new_attr = AttributeAnnotation(ann.id_, ann_obj.get_new_id('A'),
                                           attr_type, '', attr_val)
            ann_obj.add_annotation(new_attr)
            mods.addition(new_attr)


def _json_offsets_to_list(offsets):
    try:
        offsets = json_loads(offsets)
    except Exception:
        Messager.error('create_span: protocol argument error: expected '
                       'offsets as JSON, but failed to '
                       'parse "%s"' % str(offsets))
        raise ProtocolArgumentError
    try:
        offsets = [(int(s), int(e)) for s, e in offsets]
    except Exception:
        Messager.error('create_span: protocol argument error: expected '
                       'offsets as list of int pairs, '
                       'received "%s"' % str(offsets))
        raise ProtocolArgumentError
    return offsets


def create_span(collection, document, offsets, type_, attributes=None,
                normalizations=None, id_=None, comment=None):
    # offsets should be JSON string corresponding to a list of (start,
    # end) pairs; convert once at this interface
    offsets = _json_offsets_to_list(offsets)

    return _create_span(collection, document, offsets, type_, attributes,
                        normalizations, id_, comment)


def _set_normalizations(ann_obj, ann, normalizations, mods, undo_resp=None):
    if undo_resp is None:
        undo_resp = {}
    # Find existing normalizations (if any)
    existing_norm_anns = set((a for a in ann_obj.get_normalizations()
                              if a.target == ann.id_))

    # Note the existing annotations for undo
    undo_resp['normalizations'] = json_dumps([(n.refdb, n.refid, n.reftext)
                                              for n in existing_norm_anns])

    # Organize into dictionaries for easier access
    old_norms = dict([((n.refdb, n.refid), n) for n in existing_norm_anns])
    new_norms = dict([((n[0], n[1]), n[2]) for n in normalizations])

    #Messager.info("Old norms: "+str(old_norms))
    #Messager.info("New norms: "+str(new_norms))

    # sanity check
    for refdb, refid, _ in normalizations:
        # TODO: less aggressive failure
        assert refdb is not None and refdb.strip() != '', "Error: client sent empty norm DB"
        assert refid is not None and refid.strip() != '', "Error: client sent empty norm ID"
        # (the reference string is allwed to be empty)

    # Process deletions and updates of existing normalizations
    for old_norm_id, old_norm in old_norms.items():
        if old_norm_id not in new_norms:
            # Delete IDs that were referenced previously but not anymore
            ann_obj.del_annotation(old_norm)
            mods.deletion(old_norm)
        else:
            # If the text value of the normalizations is different, update
            # (this shouldn't happen on a stable norm DB, but anyway)
            new_reftext = new_norms[old_norm_id]
            if old_norm.reftext != new_reftext:
                old = six.text_type(old_norm)
                old_norm.reftext = new_reftext
                mods.change(old, old_norm)

    # Process new normalizations
    for new_norm_id, new_reftext in new_norms.items():
        if new_norm_id not in old_norms:
            new_id = ann_obj.get_new_id('N')
            # TODO: avoid magic string value
            norm_type = u'Reference'
            new_norm = NormalizationAnnotation(new_id, norm_type,
                                               ann.id_, new_norm_id[0],
                                               new_norm_id[1],
                                               u'\t'+new_reftext)
            ann_obj.add_annotation(new_norm)
            mods.addition(new_norm)

# helper for _create methods


def _parse_attributes(attributes):
    if attributes is None:
        _attributes = {}
    else:
        try:
            _attributes = json_loads(attributes)
        except ValueError:
            # Failed to parse, warn the client
            Messager.warning((u'Unable to parse attributes string "%s" for '
                              u'"createSpan", ignoring attributes for request and '
                              u'assuming no attributes set') % (attributes, ))
            _attributes = {}

        # XXX: Hack since the client is sending back False and True as values...
        # These are __not__ to be sent, they violate the protocol
        for _del in [k for k, v in _attributes.items() if v == False]:
            del _attributes[_del]

        # These are to be old-style modifiers without values
        for _revalue in [k for k, v in _attributes.items() if v == True]:
            _attributes[_revalue] = True
        ###
    return _attributes

# helper for _create_span


def _parse_span_normalizations(normalizations):
    if normalizations is None:
        _normalizations = {}
    else:
        try:
            _normalizations = json_loads(normalizations)
        except ValueError:
            # Failed to parse, warn the client
            Messager.warning((u'Unable to parse normalizations string "%s" for '
                              u'"createSpan", ignoring normalizations for request and '
                              u'assuming no normalizations set') % (normalizations, ))
            _normalizations = {}

    return _normalizations

# Helper for _create functions


def _set_comments(ann_obj, ann, comment, mods, undo_resp=None):
    if undo_resp is None:
        undo_resp = {}
    # We are only interested in id;ed comments
    try:
        ann.id_
    except AttributeError:
        return None

    # Check if there is already an annotation comment
    for com_ann in ann_obj.get_oneline_comments():
        if (com_ann.type_ == 'AnnotatorNotes'
                and com_ann.target == ann.id_):
            found = com_ann

            # Note the comment in the undo
            undo_resp['comment'] = found.tail[1:]
            break
    else:
        found = None

    if comment:
        if found is not None:
            # Change the comment
            # XXX: Note the ugly tab, it is for parsing the tail
            before = six.text_type(found)
            found.tail = u'\t' + comment
            mods.change(before, found)
        else:
            # Create a new comment
            new_comment = OnelineCommentAnnotation(
                ann.id_, ann_obj.get_new_id('#'),
                # XXX: Note the ugly tab
                u'AnnotatorNotes', u'\t' + comment)
            ann_obj.add_annotation(new_comment)
            mods.addition(new_comment)
    else:
        # We are to erase the annotation
        if found is not None:
            ann_obj.del_annotation(found)
            mods.deletion(found)

# Sanity check, a span can't overlap itself


def _offset_overlaps(offsets):
    for i in range(len(offsets)):
        i_start, i_end = offsets[i]
        for j in range(i + 1, len(offsets)):
            j_start, j_end = offsets[j]
            if (
                    # i overlapping or in j
                    (j_start <= i_start < j_end) or (j_start < i_end < j_end)
                    or
                    # j overlapping or in i
                    (i_start <= j_start < i_end) or (i_start < j_end < i_end)
            ):
                return True
    # No overlap detected
    return False

# TODO: ONLY determine what action to take! Delegate to Annotations!


def _create_span(collection, document, offsets, type_, attributes=None,
                 normalizations=None, id_=None, comment=None):

    if _offset_overlaps(offsets):
        raise SpanOffsetOverlapError(offsets)

    directory = collection
    undo_resp = {}

    _attributes = _parse_attributes(attributes)
    _normalizations = _parse_span_normalizations(normalizations)

    #log_info('ATTR: %s' %(_attributes, ))

    real_dir = real_directory(directory)
    document = path_join(real_dir, document)

    projectconf = ProjectConfiguration(real_dir)

    txt_file_path = document + '.' + TEXT_FILE_SUFFIX

    with TextAnnotations(document) as ann_obj:
        # bail as quick as possible if read-only
        if ann_obj.read_only:
            raise AnnotationsIsReadOnlyError(ann_obj.get_document())

        mods = ModificationTracker()

        if id_ is not None:
            # We are to edit an existing annotation
            tb_ann, e_ann = _edit_span(ann_obj, mods, id_, offsets, projectconf,
                                       _attributes, type_, undo_resp=undo_resp)
        else:
            # We are to create a new annotation
            tb_ann, e_ann = __create_span(ann_obj, mods, type_,
                                          offsets, txt_file_path,
                                          projectconf, _attributes)

            undo_resp['action'] = 'add_tb'
            if e_ann is not None:
                undo_resp['id'] = e_ann.id_
            else:
                undo_resp['id'] = tb_ann.id_

        # Determine which annotation attributes, normalizations,
        # comments etc. should be attached to. If there's an event,
        # attach to that; otherwise attach to the textbound.
        if e_ann is not None:
            # Assign to the event, not the trigger
            target_ann = e_ann
        else:
            target_ann = tb_ann

        # Set attributes
        _set_attributes(ann_obj, target_ann, _attributes, mods,
                        undo_resp=undo_resp)

        # Set normalizations
        _set_normalizations(ann_obj, target_ann, _normalizations, mods,
                            undo_resp=undo_resp)

        # Set comments
        if tb_ann is not None:
            _set_comments(ann_obj, target_ann, comment, mods,
                          undo_resp=undo_resp)

        if tb_ann is not None:
            mods_json = mods.json_response()
        else:
            # Hack, probably we had a new-line in the span
            mods_json = {}
            Messager.error(
                'Text span contained new-line, rejected', duration=3)

        if undo_resp:
            mods_json['undo'] = json_dumps(undo_resp)
        mods_json['annotations'] = _json_from_ann(ann_obj)
        return mods_json


from arat.server.annotation import BinaryRelationAnnotation


def _create_equiv(ann_obj, projectconf, mods, origin, target, type_, attributes,
                  old_type, old_target):

    # due to legacy representation choices for Equivs (i.e. no
    # unique ID), support for attributes for Equivs would need
    # some extra work. Getting the easy non-Equiv case first.
    if attributes is not None:
        Messager.warning('_create_equiv: attributes for Equiv annotation not '
                         'supported yet, please tell the devs if you need '
                         'this feature (mention "issue #799").')
        attributes = None

    ann = None

    if old_type is None:
        # new annotation

        # sanity
        assert old_target is None, '_create_equiv: incoherent args: old_type is None, old_target is not None (client/protocol error?)'

        ann = EquivAnnotation(type_, [six.text_type(origin.id_),
                                      six.text_type(target.id_)], '')
        ann_obj.add_annotation(ann)
        mods.addition(ann)

        # TODO: attributes
        assert attributes is None, "INTERNAL ERROR"  # see above
    else:
        # change to existing Equiv annotation. Other than the no-op
        # case, this remains TODO.
        assert projectconf.is_equiv_type(
            old_type), 'attempting to change equiv relation to non-equiv relation, operation not supported'

        # sanity
        assert old_target is not None, '_create_equiv: incoherent args: old_type is not None, old_target is None (client/protocol error?)'

        if old_type != type_:
            Messager.warning(
                '_create_equiv: equiv type change not supported yet, please tell the devs if you need this feature (mention "issue #798").')

        if old_target != target.id_:
            Messager.warning(
                '_create_equiv: equiv reselect not supported yet, please tell the devs if you need this feature (mention "issue #797").')

        # TODO: attributes
        assert attributes is None, "INTERNAL ERROR"  # see above

    return ann


def _create_relation(ann_obj, projectconf, mods, origin, target, type_,
                     attributes, old_type, old_target, undo_resp=None):
    if undo_resp is None:
        undo_resp = {}
    attributes = _parse_attributes(attributes)

    if old_type is not None or old_target is not None:
        assert type_ in projectconf.get_relation_types(), (
            ('attempting to convert relation to non-relation "%s" ' % (target.type_, )) +
            ('(legit types: %s)' % (six.text_type(projectconf.get_relation_types()), )))

        sought_target = (old_target
                         if old_target is not None else target.id_)
        sought_type = (old_type
                       if old_type is not None else type_)
        sought_origin = origin.id_

        # We are to change the type, target, and/or attributes
        found = None
        for ann in ann_obj.get_relations():
            if (ann.arg1 == sought_origin and ann.arg2 == sought_target and
                    ann.type_ == sought_type):
                found = ann
                break

        if found is None:
            # TODO: better response
            Messager.error('_create_relation: failed to identify target relation (type %s, target %s) (deleted?)' % (
                str(old_type), str(old_target)))
        elif found.arg2 == target.id_ and found.type_ == type_:
            # no changes to type or target
            pass
        else:
            # type and/or target changed, mark.
            before = six.text_type(found)
            found.arg2 = target.id_
            found.type_ = type_
            mods.change(before, found)

        target_ann = found
    else:
        # Create a new annotation
        new_id = ann_obj.get_new_id('R')
        # TODO: do we need to support different relation arg labels
        # depending on participant types? This doesn't.
        rels = projectconf.get_relations_by_type(type_)
        rel = rels[0] if rels else None
        assert rel is not None and len(rel.arg_list) == 2
        a1l, a2l = rel.arg_list
        ann = BinaryRelationAnnotation(
            new_id, type_, a1l, origin.id_, a2l, target.id_, '\t')
        mods.addition(ann)
        ann_obj.add_annotation(ann)

        target_ann = ann

    # process attributes
    if target_ann is not None:
        _set_attributes(ann_obj, ann, attributes, mods, undo_resp)
    elif attributes != None:
        Messager.error('_create_relation: cannot set arguments: failed to identify target relation (type %s, target %s) (deleted?)' % (
            str(old_type), str(old_target)))

    return target_ann


def _create_argument(ann_obj, projectconf, mods, origin, target, type_,
                     attributes, old_type, old_target):
    try:
        arg_tup = (type_, six.text_type(target.id_))

        # Is this an addition or an update?
        if old_type is None and old_target is None:
            if arg_tup not in origin.args:
                before = six.text_type(origin)
                origin.add_argument(type_, six.text_type(target.id_))
                mods.change(before, origin)
            else:
                # It already existed as an arg, we were called to do nothing...
                pass
        else:
            # Construct how the old arg would have looked like
            old_arg_tup = (type_ if old_type is None else old_type,
                           target if old_target is None else old_target)

            if old_arg_tup in origin.args and arg_tup not in origin.args:
                before = six.text_type(origin)
                origin.args.remove(old_arg_tup)
                origin.add_argument(type_, six.text_type(target.id_))
                mods.change(before, origin)
            else:
                # Collision etc. don't do anything
                pass
    except AttributeError:
        # The annotation did not have args, it was most likely an entity
        # thus we need to create a new Event...
        new_id = ann_obj.get_new_id('E')
        ann = EventAnnotation(
            origin.id_,
            [arg_tup],
            new_id,
            origin.type_,
            ''
        )
        ann_obj.add_annotation(ann)
        mods.addition(ann)

    # No addressing mechanism for arguments at the moment
    return None


def reverse_arc(collection, document, origin, target, type_, attributes=None):
    directory = collection
    # undo_resp = {} # TODO
    real_dir = real_directory(directory)
    # mods = ModificationTracker() # TODO
    projectconf = ProjectConfiguration(real_dir)
    document = path_join(real_dir, document)
    with TextAnnotations(document) as ann_obj:
        # bail as quick as possible if read-only
        if ann_obj.read_only:
            raise AnnotationsIsReadOnlyError(ann_obj.get_document())

        if projectconf.is_equiv_type(type_):
            Messager.warning('Cannot reverse Equiv arc')
        elif not projectconf.is_relation_type(type_):
            Messager.warning('Can only reverse configured binary relations')
        else:
            # OK to reverse
            found = None
            # TODO: more sensible lookup
            for ann in ann_obj.get_relations():
                if (ann.arg1 == origin and ann.arg2 == target and
                        ann.type_ == type_):
                    found = ann
                    break
            if found is None:
                Messager.error('reverse_arc: failed to identify target relation (from %s to %s, type %s) (deleted?)' % (
                    str(origin), str(target), str(type_)))
            else:
                # found it; just adjust this
                found.arg1, found.arg2 = found.arg2, found.arg1
                # TODO: modification tracker

        json_response = {}
        json_response['annotations'] = _json_from_ann(ann_obj)
        return json_response

# TODO: undo support


def create_arc(collection, document, origin, target, type_, attributes=None,
               old_type=None, old_target=None, comment=None):
    directory = collection
    undo_resp = {}

    real_dir = real_directory(directory)

    mods = ModificationTracker()

    projectconf = ProjectConfiguration(real_dir)

    document = path_join(real_dir, document)

    with TextAnnotations(document) as ann_obj:
        # bail as quick as possible if read-only
        # TODO: make consistent across the different editing
        # functions, integrate ann_obj initialization and checks
        if ann_obj.read_only:
            raise AnnotationsIsReadOnlyError(ann_obj.get_document())

        origin = ann_obj.get_ann_by_id(origin)
        target = ann_obj.get_ann_by_id(target)

        ann = None

        # if there is a previous annotation and the arcs aren't in
        # the same category (e.g. relation vs. event arg), process
        # as delete + create instead of update.
        if old_type is not None and (
                projectconf.is_relation_type(old_type) !=
                projectconf.is_relation_type(type_) or
                projectconf.is_equiv_type(old_type) !=
                projectconf.is_equiv_type(type_)):
            _delete_arc_with_ann(origin.id_, old_target, old_type, mods,
                                 ann_obj, projectconf)
            old_target, old_type = None, None

        if projectconf.is_equiv_type(type_):
            ann = _create_equiv(ann_obj, projectconf, mods, origin, target,
                                type_, attributes, old_type, old_target)

        elif projectconf.is_relation_type(type_):
            ann = _create_relation(ann_obj, projectconf, mods, origin, target,
                                   type_, attributes, old_type, old_target)
        else:
            _create_argument(ann_obj, projectconf, mods, origin, target,
                             type_, attributes, old_type, old_target)

        # process comments
        if ann is not None:
            _set_comments(ann_obj, ann, comment, mods,
                          undo_resp=undo_resp)
        elif comment is not None:
            Messager.warning(
                'create_arc: non-empty comment for None annotation (unsupported type for comment?)')

        mods_json = mods.json_response()
        mods_json['annotations'] = _json_from_ann(ann_obj)
        return mods_json

# helper for delete_arc


def _delete_arc_equiv(origin, target, type_, mods, ann_obj):
    # TODO: this is slow, we should have a better accessor
    for eq_ann in ann_obj.get_equivs():
        # We don't assume that the ids only occur in one Equiv, we
        # keep on going since the data "could" be corrupted
        if (six.text_type(origin) in eq_ann.entities and
            six.text_type(target) in eq_ann.entities and
                type_ == eq_ann.type_):
            before = six.text_type(eq_ann)
            eq_ann.entities.remove(six.text_type(origin))
            eq_ann.entities.remove(six.text_type(target))
            mods.change(before, eq_ann)

        if len(eq_ann.entities) < 2:
            # We need to delete this one
            try:
                ann_obj.del_annotation(eq_ann)
                mods.deletion(eq_ann)
            except DependingAnnotationDeleteError:
                # TODO: This should never happen, dep on equiv
                raise

    # TODO: warn on failure to delete?

# helper for delete_arc


def _delete_arc_nonequiv_rel(origin, target, type_, mods, ann_obj):
    # TODO: this is slow, we should have a better accessor
    for ann in ann_obj.get_relations():
        if ann.type_ == type_ and ann.arg1 == origin and ann.arg2 == target:
            ann_obj.del_annotation(ann)
            mods.deletion(ann)

    # TODO: warn on failure to delete?

# helper for delete_arc


def _delete_arc_event_arg(origin, target, type_, mods, ann_obj):
    event_ann = ann_obj.get_ann_by_id(origin)
    # Try if it is an event
    arg_tup = (type_, six.text_type(target))
    if arg_tup in event_ann.args:
        before = six.text_type(event_ann)
        event_ann.args.remove(arg_tup)
        mods.change(before, event_ann)
    else:
        # What we were to remove did not even exist in the first place
        # TODO: warn on failure to delete?
        pass


def _delete_arc_with_ann(origin, target, type_, mods, ann_obj, projectconf):
    origin_ann = ann_obj.get_ann_by_id(origin)

    # specifics of delete determined by arc type (equiv relation,
    # other relation, event argument)
    if projectconf.is_relation_type(type_):
        if projectconf.is_equiv_type(type_):
            _delete_arc_equiv(origin, target, type_, mods, ann_obj)
        else:
            _delete_arc_nonequiv_rel(origin, target, type_, mods, ann_obj)
    elif projectconf.is_event_type(origin_ann.type_):
        _delete_arc_event_arg(origin, target, type_, mods, ann_obj)
    else:
        Messager.error('Unknown annotation types for delete')


def delete_arc(collection, document, origin, target, type_):
    directory = collection

    real_dir = real_directory(directory)

    mods = ModificationTracker()

    projectconf = ProjectConfiguration(real_dir)

    document = path_join(real_dir, document)

    with TextAnnotations(document) as ann_obj:
        # bail as quick as possible if read-only
        if ann_obj.read_only:
            raise AnnotationsIsReadOnlyError(ann_obj.get_document())

        _delete_arc_with_ann(origin, target, type_, mods, ann_obj, projectconf)

        mods_json = mods.json_response()
        mods_json['annotations'] = _json_from_ann(ann_obj)
        return mods_json

    # TODO: error handling?

# TODO: ONLY determine what action to take! Delegate to Annotations!


def delete_span(collection, document, id_):
    directory = collection

    real_dir = real_directory(directory)

    document = path_join(real_dir, document)

    with TextAnnotations(document) as ann_obj:
        # bail as quick as possible if read-only
        if ann_obj.read_only:
            raise AnnotationsIsReadOnlyError(ann_obj.get_document())

        mods = ModificationTracker()

        # TODO: Handle a failure to find it
        # XXX: Slow, O(2N)
        ann = ann_obj.get_ann_by_id(id_)
        try:
            # Note: need to pass the tracker to del_annotation to track
            # recursive deletes. TODO: make usage consistent.
            ann_obj.del_annotation(ann, mods)
            try:
                trig = ann_obj.get_ann_by_id(ann.trigger)
                try:
                    ann_obj.del_annotation(trig, mods)
                except DependingAnnotationDeleteError:
                    # Someone else depended on that trigger
                    pass
            except AttributeError:
                pass
        except DependingAnnotationDeleteError as e:
            Messager.error(e.html_error_str())
            return {
                'exception': True,
            }

        mods_json = mods.json_response()
        mods_json['annotations'] = _json_from_ann(ann_obj)
        return mods_json


class AnnotationSplitError(ProtocolError):
    def __init__(self, message):
        self.message = message
        ProtocolError.__init__(self)

    def __str__(self):
        return self.message

    def json(self, json_dic):
        json_dic['exception'] = 'annotationSplitError'
        Messager.error(self.message)
        return json_dic


def split_span(collection, document, args, id_):
    directory = collection

    real_dir = real_directory(directory)
    document = path_join(real_dir, document)
    # TODO don't know how to pass an array directly, so doing extra catenate and split
    tosplit_args = json_loads(args)

    with TextAnnotations(document) as ann_obj:
        # bail as quick as possible if read-only
        if ann_obj.read_only:
            raise AnnotationsIsReadOnlyError(ann_obj.get_document())

        mods = ModificationTracker()

        ann = ann_obj.get_ann_by_id(id_)

        # currently only allowing splits for events
        if not isinstance(ann, EventAnnotation):
            raise AnnotationSplitError(
                "Cannot split an annotation of type %s" % ann.type_)

        # group event arguments into ones that will be split on and
        # ones that will not, placing the former into a dict keyed by
        # the argument without trailing numbers (e.g. "Theme1" ->
        # "Theme") and the latter in a straight list.
        split_args = {}
        nonsplit_args = []
        import re
        for arg, aid in ann.args:
            m = re.match(r'^(.*?)\d*$', arg)
            if m:
                arg = m.group(1)
            if arg in tosplit_args:
                if arg not in split_args:
                    split_args[arg] = []
                split_args[arg].append(aid)
            else:
                nonsplit_args.append((arg, aid))

        # verify that split is possible
        for a in tosplit_args:
            acount = len(split_args.get(a, []))
            if acount < 2:
                raise AnnotationSplitError(
                    "Cannot split %s on %s: only %d %s arguments (need two or more)" % (ann.id_, a, acount, a))

        # create all combinations of the args on which to split
        argument_combos = [[]]
        for a in tosplit_args:
            new_combos = []
            for aid in split_args[a]:
                for c in argument_combos:
                    new_combos.append(c + [(a, aid)])
            argument_combos = new_combos

        # create the new events (first combo will use the existing event)
        from copy import deepcopy
        new_events = []
        for i, arg_combo in enumerate(argument_combos):
            # tweak args
            if i == 0:
                ann.args = nonsplit_args[:] + arg_combo
            else:
                newann = deepcopy(ann)
                # TODO: avoid hard-coding ID prefix
                newann.id_ = ann_obj.get_new_id("E")
                newann.args = nonsplit_args[:] + arg_combo
                ann_obj.add_annotation(newann)
                new_events.append(newann)
                mods.addition(newann)

        # then, go through all the annotations referencing the original
        # event, and create appropriate copies
        for a in ann_obj:
            soft_deps, hard_deps = a.get_deps()
            refs = soft_deps | hard_deps
            if ann.id_ in refs:
                # Referenced; make duplicates appropriately

                if isinstance(a, EventAnnotation):
                    # go through args and make copies for referencing
                    new_args = []
                    for arg, aid in a.args:
                        if aid == ann.id_:
                            for newe in new_events:
                                new_args.append((arg, newe.id_))
                    a.args.extend(new_args)

                elif isinstance(a, AttributeAnnotation):
                    for newe in new_events:
                        newmod = deepcopy(a)
                        newmod.target = newe.id_
                        # TODO: avoid hard-coding ID prefix
                        newmod.id_ = ann_obj.get_new_id("A")
                        ann_obj.add_annotation(newmod)
                        mods.addition(newmod)

                elif isinstance(a, BinaryRelationAnnotation):
                    # TODO
                    raise AnnotationSplitError(
                        "Cannot adjust annotation referencing split: not implemented for relations! (WARNING: annotations may be in inconsistent state, please reload!) (Please complain to the developers to fix this!)")

                elif isinstance(a, OnelineCommentAnnotation):
                    for newe in new_events:
                        newcomm = deepcopy(a)
                        newcomm.target = newe.id_
                        # TODO: avoid hard-coding ID prefix
                        newcomm.id_ = ann_obj.get_new_id("#")
                        ann_obj.add_annotation(newcomm)
                        mods.addition(newcomm)
                elif isinstance(a, NormalizationAnnotation):
                    for newe in new_events:
                        newnorm = deepcopy(a)
                        newnorm.target = newe.id_
                        # TODO: avoid hard-coding ID prefix
                        newnorm.id_ = ann_obj.get_new_id("N")
                        ann_obj.add_annotation(newnorm)
                        mods.addition(newnorm)
                else:
                    raise AnnotationSplitError(
                        "Cannot adjust annotation referencing split: not implemented for %s! (Please complain to the lazy developers to fix this!)" % a.__class__)

        mods_json = mods.json_response()
        mods_json['annotations'] = _json_from_ann(ann_obj)
        return mods_json


def set_status(directory, document, new_status=None):
    real_dir = real_directory(directory)

    with TextAnnotations(path_join(real_dir, document)) as ann:
        # Erase all old status annotations
        status = None
        for status in ann.get_statuses():
            ann.del_annotation(status)

        if status is not None:
            # XXX: This could work, not sure if it can induce an id collision
            new_status_id = ann.get_new_id('#')
            ann.add_annotation(OnelineCommentAnnotation(
                new_status, new_status_id, 'STATUS', ''
            ))

    json_dic = {
        'status': new_status
    }
    return json_dic


def get_status(directory, document):
    with TextAnnotations(path_join(directory, document),
                         read_only=True) as ann:

        # XXX: Assume the last one is correct if we have more
        #       than one (which is a violation of protocol anyway)
        statuses = [c for c in ann.get_statuses()]
        if statuses:
            status = statuses[-1].target
        else:
            status = None

    json_dic = {
        'status': status
    }
    return json_dic


class CreateSpanHandler(AuthenticatedJsonHandler):
    """
    Add a span to a document
    """

    def _post(self, collection, document, offsets, type_, attributes=None,
              normalizations=None, id_=None, comment=None):
        response = create_span(collection, document, offsets, type_, attributes,
                               normalizations, id_, comment)
        return response


class DeleteSpanHandler(AuthenticatedJsonHandler):
    """
    Delete a span from a document
    """

    def _post(self, collection, document, id_, type_, offsets):
        response = delete_span(collection, document, id_)

        return response


class SplitSpanHandler(AuthenticatedJsonHandler):
    """
    Split a span from a document
    """

    def _post(self, collection, document, args, id_):
        response = split_span(collection, document, args, id_)

        return response


class CreateArcHandler(AuthenticatedJsonHandler):
    """
    Add an arc to a document
    """

    def _post(self, collection, document, origin, target, type_,
              attributes=None, old_type=None, old_target=None, comment=None):
        response = create_arc(collection, document, origin, target, type_,
                              attributes, old_type, old_target, comment)
        return response


class DeleteArcHandler(AuthenticatedJsonHandler):
    """
    Delete an arc of a document
    """

    def _post(self, collection, document, origin, target, type_,
              attributes=None, old_type=None, old_target=None, comment=None):
        response = delete_arc(collection, document, origin, target, type_)
        return response


class ReverseArcHandler(AuthenticatedJsonHandler):
    """
    Reverse an arc of a document
    """

    def _post(self, collection, document, origin, target, type_,
              attributes=None, old_type=None, old_target=None, comment=None):
        raise NotImplementedError
#        response = reverse_arc (collection, document, origin, target, type_,
#                              attributes, old_type, old_target, comment)
#        return response
