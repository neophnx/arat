# -*- coding: utf-8; -*-
"""
Check annotation against declared schema.
"""

# future
from __future__ import with_statement
from __future__ import absolute_import
from __future__ import print_function

# standard
import os
from re import match as re_match
import argparse

# arat
from server import annotation
from server.projectconfig import ProjectConfiguration

# Issue types. Values should match with annotation interface.
ANNOTATION_ERROR = "ANNOTATION_ERROR"
ANNOTATION_WARNING = "ANNOTATION_WARNING"
ANNOTATION_INCOMPLETE = "ANNOTATION_INCOMPLETE"

CHECK_PASSED, FOUND_ISSUES, FILE_NOT_FOUND, ANNOATION_NOT_FOUND = list(
    range(4))


class AnnotationIssue(object):
    """
    Represents an issue noted in verification of annotations.
    """

    _next_id_idx = 1

    def __init__(self, ann_id, type_, description=""):
        self.id_ = "#%d" % AnnotationIssue._next_id_idx
        AnnotationIssue._next_id_idx += 1
        self.ann_id, self.type, self.description = ann_id, type_, description
        if self.description is None:
            self.description = ""

    def human_readable_str(self):
        """
        More concise representation
        """
        return "%s: %s\t%s" % (self.ann_id, self.type, self.description)

    def __str__(self):
        return "%s\t%s %s\t%s" % (self.id_, self.type, self.ann_id, self.description)


def event_nonum_args(event):
    """
    Given an EventAnnotatation, returns its arguments without trailing
    numbers (e.g. "Theme1" -> "Theme").
    """

    nna = {}
    for arg, aid in event.args:
        match = re_match(r'^(.*?)\d*$', arg)
        if match:
            arg = match.group(1)
        if arg not in nna:
            nna[arg] = []
        nna[arg].append(aid)
    return nna


def event_nonum_arg_count(event):
    """
    Given an EventAnnotation, returns a dictionary containing for each
    of its argument without trailing numbers (e.g. "Theme1" ->
    "Theme") the number of times the argument appears.
    """

    nnc = {}
    for arg, _ in event.args:
        m = re_match(r'^(.*?)\d*$', arg)
        if m:
            arg = m.group(1)
        nnc[arg] = nnc.get(arg, 0) + 1
    return nnc


def check_textbound_overlap(anns):
    """
    Checks for overlap between the given TextBoundAnnotations.
    Returns a list of pairs of overlapping annotations.
    """
    overlapping = []

    for anno1 in anns:
        for anno2 in anns:
            if anno1 is anno2:
                continue
            if (anno2.first_start() < anno1.last_end() and
                    anno2.last_end() > anno1.first_start()):
                overlapping.append((anno1, anno2))

    return overlapping


def verify_equivs(ann_obj, projectconf):
    """
    Check the equivs entity
    """
    issues = []

    # shortcut
    def disp(s):
        return projectconf.preferred_display_form(s)

    for eq in ann_obj.get_equivs():
        # get the equivalent annotations
        equiv_anns = [ann_obj.get_ann_by_id(eid) for eid in eq.entities]

        # all pairs of entity types in the Equiv group must be allowed
        # to have an Equiv. Create type-level pairs to avoid N^2
        # search where N=entities.
        eq_type = {}
        for e in equiv_anns:
            eq_type[e.type] = True
        type_pairs = []
        for t1 in eq_type:
            for t2 in eq_type:
                type_pairs.append((t1, t2))

        # do avoid marking both (a1,a2) and (a2,a1), remember what's
        # already included
        marked = {}

        for t1, t2 in type_pairs:
            reltypes = projectconf.relation_types_from_to(t1, t2)
            # TODO: this is too convoluted; use projectconf directly
            equiv_type_found = False
            for rt in reltypes:
                if projectconf.is_equiv_type(rt):
                    equiv_type_found = True
            if not equiv_type_found:
                # Avoid redundant output
                if (t2, t1) in marked:
                    continue
                # TODO: mark this error on the Eq relation, not the entities
                for e in equiv_anns:
                    issues.append(AnnotationIssue(e.id,
                                                  ANNOTATION_ERROR,
                                                  "Equivalence relation %s "
                                                  "not allowed between %s "
                                                  "and %s" % (eq.type,
                                                              disp(t1),
                                                              disp(t2))))
                marked[(t1, t2)] = True

    return issues


def verify_entity_overlap(ann_obj, projectconf):
    issues = []

    # shortcut
    def disp(s):
        return projectconf.preferred_display_form(s)

    # check for overlap between physical entities
    physical_entities = [a for a in ann_obj.get_textbounds(
    ) if projectconf.is_physical_entity_type(a.type)]
    overlapping = check_textbound_overlap(physical_entities)
    for anno1, anno2 in overlapping:
        if anno1.same_span(anno2):
            if not projectconf.spans_can_be_equal(anno1.type_, anno2.type_):
                issues.append(AnnotationIssue(anno1.id_,
                                              ANNOTATION_ERROR,
                                              "Error: %s cannot have "
                                              "identical span with %s "
                                              "%s" % (disp(anno1.type_),
                                                      disp(anno2.type_),
                                                      anno2.id_)))
        elif anno2.contains(anno1):
            if not projectconf.span_can_contain(anno1.type_, anno2.type_):
                issues.append(AnnotationIssue(anno1.id_,
                                              ANNOTATION_ERROR,
                                              "Error: %s cannot be contained "
                                              "in %s (%s)" % (disp(anno1.type_),
                                                              disp(
                                                                  anno2.type_),
                                                              anno2.id_)))
        elif anno1.contains(anno2):
            if not projectconf.span_can_contain(anno2.type_, anno1.type_):
                issues.append(AnnotationIssue(anno1.id_,
                                              ANNOTATION_ERROR,
                                              "Error: %s cannot contain %s "
                                              "(%s)" % (disp(anno1.type_),
                                                        disp(anno2.type_),
                                                        anno2.id_)))
        else:
            if not projectconf.spans_can_cross(anno1.type_, anno2.type_):
                issues.append(AnnotationIssue(anno1.id_,
                                              ANNOTATION_ERROR,
                                              "Error: annotation cannot have "
                                              "crossing span with "
                                              "%s" % anno2.id_))

    # TODO: generalize to other cases
    return issues


def verify_annotation_types(ann_obj, projectconf):
    issues = []

    event_types = projectconf.get_event_types()
    textbound_types = event_types + projectconf.get_entity_types()
    relation_types = projectconf.get_relation_types()

    # shortcut
    def disp(s):
        return projectconf.preferred_display_form(s)

    for e in ann_obj.get_events():
        if e.type not in event_types:
            issues.append(AnnotationIssue(e.id,
                                          ANNOTATION_ERROR,
                                          "Error: %s is not a known event "
                                          "type (check configuration?)"
                                          "" % disp(e.type)))

    for t in ann_obj.get_textbounds():
        if t.type not in textbound_types:
            issues.append(AnnotationIssue(t.id,
                                          ANNOTATION_ERROR,
                                          "Error: %s is not a known "
                                          "textbound type (check "
                                          "configuration?)" % disp(t.type)))

    for r in ann_obj.get_relations():
        if r.type not in relation_types:
            issues.append(AnnotationIssue(r.id,
                                          ANNOTATION_ERROR,
                                          "Error: %s is not a known relation "
                                          "type (check configuration?)"
                                          "" % disp(r.type)))

    return issues


def verify_triggers(ann_obj, projectconf):
    issues = []

    events_by_trigger = {}

    for e in ann_obj.get_events():
        if e.trigger not in events_by_trigger:
            events_by_trigger[e.trigger] = []
        events_by_trigger[e.trigger].append(e)

    trigger_by_span_and_type = {}

    for t in ann_obj.get_textbounds():
        if not projectconf.is_event_type(t.type):
            continue

        if t.id not in events_by_trigger:
            issues.append(AnnotationIssue(t.id,
                                          ANNOTATION_INCOMPLETE,
                                          "Warning: trigger %s is not "
                                          "referenced from any event" % t.id))

        spt = tuple(set(t.spans))+(t.type,)
        if spt not in trigger_by_span_and_type:
            trigger_by_span_and_type[spt] = []
        trigger_by_span_and_type[spt].append(t)

    for spt in trigger_by_span_and_type:
        trigs = trigger_by_span_and_type[spt]
        if len(trigs) < 2:
            continue
        for t in trigs:
            # We currently need to attach these to events if there are
            # any; issues attached to triggers referenced from events
            # don't get shown. TODO: revise once this is fixed.
            if t.id in events_by_trigger:
                issues.append(AnnotationIssue(events_by_trigger[t.id][0].id,
                                              ANNOTATION_WARNING,
                                              "Warning: triggers %s have "
                                              "identical span and type "
                                              "(harmless but unnecessary "
                                              "duplication)" % ",".join([x.id for x in trigs])))
            else:
                issues.append(AnnotationIssue(t.id,
                                              ANNOTATION_WARNING,
                                              "Warning: triggers %s have "
                                              "identical span and type "
                                              "(harmless but unnecessary "
                                              "duplication)" % ",".join([x.id for x in trigs])))

    return issues


def _relation_labels_match(rel, rel_conf):
    if len(rel_conf.arg_list) != 2:
        # likely misconfigured relation, can't match
        return False
    return (rel.arg1l == rel_conf.arg_list[0] and
            rel.arg2l == rel_conf.arg_list[1])


def verify_relations(ann_obj, projectconf):
    issues = []

    # shortcut
    def disp(s):
        return projectconf.preferred_display_form(s)

    # TODO: rethink this function.
    for r in ann_obj.get_relations():
        a1 = ann_obj.get_ann_by_id(r.arg1)
        a2 = ann_obj.get_ann_by_id(r.arg2)
        match_found = False

        # check for argument order a1, a2
        if r.type in projectconf.relation_types_from_to(a1.type_, a2.type_):
            # found for argument order a1, a2; check labels
            conf_rels = projectconf.get_relations_by_type(r.type)
            if any(c for c in conf_rels if _relation_labels_match(r, c)):
                match_found = True
        if match_found:
            continue

        # no match for argument order a1, a2; try a2, a1
        # temp inversion for check
        r.arg1, r.arg2, r.arg1l, r.arg2l = r.arg2, r.arg1, r.arg2l, r.arg1l
        if r.type in projectconf.relation_types_from_to(a2.type_, a1.type_):
            conf_rels = projectconf.get_relations_by_type(r.type)
            if any(c for c in conf_rels if _relation_labels_match(r, c)):
                match_found = True
        r.arg1, r.arg2, r.arg1l, r.arg2l = r.arg2, r.arg1, r.arg2l, r.arg1l
        if match_found:
            continue

        # not found for either argument order
        issues.append(AnnotationIssue(r.id,
                                      ANNOTATION_ERROR,
                                      "Error: %s relation %s:%s %s:%s not "
                                      "allowed" % (disp(r.type),
                                                   r.arg1l,
                                                   disp(a1.type_),
                                                   r.arg2l,
                                                   disp(a2.type_))))

    return issues


def verify_missing_arguments(ann_obj, projectconf):
    """
    Checks for events having too few mandatory arguments.
    """
    issues = []

    # shortcut
    def disp(s):
        return projectconf.preferred_display_form(s)

    for e in ann_obj.get_events():
        nonum_arg_counts = event_nonum_arg_count(e)
        for m in projectconf.mandatory_arguments(e.type):
            c = nonum_arg_counts.get(m, 0)
            amin = projectconf.argument_minimum_count(e.type, m)
            amax = projectconf.argument_maximum_count(e.type, m)
            if c < amin:
                # insufficient, pick appropriate string and add issue
                if amin == 1:
                    countstr = "one %s argument " % disp(m)
                else:
                    countstr = "%d %s arguments " % (amin, disp(m))
                if amin == amax:
                    countstr = "exactly " + countstr
                else:
                    countstr = "at least " + countstr
                issues.append(AnnotationIssue(e.id,
                                              ANNOTATION_INCOMPLETE,
                                              "Incomplete: " + countstr + "required for event"))

    return issues


def verify_disallowed_arguments(ann_obj, projectconf):
    """
    Checks for events with arguments they are not allowed to
    have.
    """
    issues = []

    # shortcut
    def disp(s):
        return projectconf.preferred_display_form(s)

    for e in ann_obj.get_events():
        allowed = projectconf.arc_types_from(e.type)
        eargs = event_nonum_args(e)
        for a in eargs:
            if a not in allowed:
                issues.append(AnnotationIssue(e.id,
                                              ANNOTATION_ERROR,
                                              "Error: %s cannot take a %s "
                                              "argument" % (disp(e.type),
                                                            disp(a))))
            else:
                for rid in eargs[a]:
                    r = ann_obj.get_ann_by_id(rid)
                    if a not in projectconf.arc_types_from_to(e.type, r.type):
                        issues.append(AnnotationIssue(e.id,
                                                      ANNOTATION_ERROR,
                                                      "Error: %s argument %s "
                                                      "cannot be of type "
                                                      "%s" % (disp(e.type),
                                                              disp(a),
                                                              disp(r.type))))

    return issues


def verify_extra_arguments(ann_obj, projectconf):
    """
    Checks for events with excessively many allowed arguments.
    """
    issues = []

    # shortcut
    def disp(s):
        return projectconf.preferred_display_form(s)

    for e in ann_obj.get_events():
        nonum_arg_counts = event_nonum_arg_count(e)
        multiple_allowed = projectconf.multiple_allowed_arguments(e.type)
        for a in [m for m in nonum_arg_counts if nonum_arg_counts[m] > 1]:
            amax = projectconf.argument_maximum_count(e.type, a)
            if a not in multiple_allowed:
                issues.append(AnnotationIssue(e.id,
                                              ANNOTATION_ERROR,
                                              "Error: %s cannot take multiple "
                                              "%s arguments" % (disp(e.type), disp(a))))
            elif nonum_arg_counts[a] > amax:
                issues.append(AnnotationIssue(
                    e.id, ANNOTATION_ERROR, "Error: %s can take at most %d %s arguments" % (disp(e.type), amax, disp(a))))

    return issues


def verify_attributes(ann_obj, projectconf):
    """
    Checks for instances of attributes attached to annotations that
    are not allowed to have them.
    """
    issues = []

    # shortcut
    def disp(s):
        return projectconf.preferred_display_form(s)

    for a in ann_obj.get_attributes():
        tid = a.target
        t = ann_obj.get_ann_by_id(tid)
        allowed = projectconf.attributes_for(t.type)

        if a.type not in allowed:
            issues.append(AnnotationIssue(t.id, ANNOTATION_ERROR,
                                          "Error: %s cannot take a %s attribute" % (disp(t.type), disp(a.type))))

    return issues


def verify_annotation(ann_obj, projectconf):
    """
    Verifies the correctness of a given AnnotationFile.
    Returns a list of AnnotationIssues.
    """
    issues = []

    issues += verify_annotation_types(ann_obj, projectconf)

    issues += verify_equivs(ann_obj, projectconf)

    issues += verify_entity_overlap(ann_obj, projectconf)

    issues += verify_triggers(ann_obj, projectconf)

    issues += verify_relations(ann_obj, projectconf)

    issues += verify_missing_arguments(ann_obj, projectconf)

    issues += verify_disallowed_arguments(ann_obj, projectconf)

    issues += verify_extra_arguments(ann_obj, projectconf)

    issues += verify_attributes(ann_obj, projectconf)

    return issues


def argparser():

    parser = argparse.ArgumentParser(
        description="Verify BioNLP Shared Task annotations.")
    parser.add_argument("-v", "--verbose", default=False,
                        action="store_true", help="Verbose output.")
    parser.add_argument("-q", "--quiet", default=False,
                        action="store_true", help="Quiet output.")
    parser.add_argument("files", metavar="FILE",
                        nargs="+", help="Files to verify.")
    return parser


def main(argv=None):

    if argv is None:
        argv = sys.argv
    arg = argparser().parse_args(argv[1:])

    retcode = CHECK_PASSED
    for fn in arg.files:
        try:
            projectconf = ProjectConfiguration(os.path.dirname(fn))
            # remove ".a2" or ".rel" suffixes for Annotations to prompt
            # parsing of .a1 also.
            # (TODO: temporarily removing .ann also to work around a
            # bug in TextAnnotations, but this should not be necessary.)
            nosuff_fn = fn.replace(".a2", "").replace(
                ".rel", "").replace(".ann", "")
            with annotation.TextAnnotations(nosuff_fn) as ann_obj:
                issues = verify_annotation(ann_obj, projectconf)
                for i in issues:
                    if not arg.quiet:
                        print("%s:\t%s" % (fn, i.human_readable_str()))
                    retcode = FOUND_ISSUES
        except annotation.AnnotationFileNotFoundError:
            if not arg.quiet:
                print("%s:\tFailed check: file not found" %
                      fn, file=sys.stderr)
            retcode = FILE_NOT_FOUND
        except annotation.AnnotationNotFoundError as e:
            if not arg.quiet:
                print("%s:\tFailed check: %s" % (fn, e), file=sys.stderr)
            retcode = ANNOATION_NOT_FOUND
    if not arg.quiet and arg.verbose:
        print("Check complete.", file=sys.stderr)

    return retcode


if __name__ == "__main__":
    import sys
    sys.exit(main())
