# -*- coding: utf-8 -*-
"""
Created on Thu Jun 14 00:34:42 2018

@author: phnx
"""

import re

from arat.server.projectconfig import commons as com
from arat.server.projectconfig import constants as cst
from arat.server.message import Messager


class ProjectConfiguration(object):
    def __init__(self, directory):
        # debugging (note: latter test for windows paths)
        if directory[:1] != "/" and not re.search(r'^[a-zA-Z]:\\', directory):
            Messager.debug(
                "Project config received relative directory ('%s'), "
                "configuration may not be found." % directory, duration=-1)
        self.directory = directory

    def mandatory_arguments(self, atype):
        """
        Returns the mandatory argument types that must be present for
        an annotation of the given type.
        """
        node = com.get_node_by_storage_form(self.directory, atype)
        if node is None:
            Messager.warning(
                "Project configuration: unknown event type %s. "
                "Configuration may be wrong." % atype)
            return []
        return node.mandatory_arguments()

    def multiple_allowed_arguments(self, atype):
        """
        Returns the argument types that are allowed to be filled more
        than once for an annotation of the given type.
        """
        node = com.get_node_by_storage_form(self.directory, atype)
        if node is None:
            Messager.warning(
                "Project configuration: unknown event type %s. "
                "Configuration may be wrong." % atype)
            return []
        return node.multiple_allowed_arguments()

    def argument_maximum_count(self, atype, arg):
        """
        Returns the maximum number of times that the given argument is
        allowed to be filled for an annotation of the given type.
        """
        node = com.get_node_by_storage_form(self.directory, atype)
        if node is None:
            Messager.warning(
                "Project configuration: unknown event type %s. "
                "Configuration may be wrong." % atype)
            return 0
        return node.argument_maximum_count(arg)

    def argument_minimum_count(self, atype, arg):
        """
        Returns the minimum number of times that the given argument is
        allowed to be filled for an annotation of the given type.
        """
        node = com.get_node_by_storage_form(self.directory, atype)
        if node is None:
            Messager.warning(
                "Project configuration: unknown event type %s. "
                "Configuration may be wrong." % atype)
            return 0
        return node.argument_minimum_count(arg)

    def arc_types_from(self, from_ann):
        return self.arc_types_from_to(from_ann)

    def relation_types_from(self, from_ann, include_special=False):
        """
        Returns the possible relation types that can have an
        annotation of the given type as their arg1.
        """
        return [r.storage_form()
                for r
                in com.get_relations_by_arg1(self.directory,
                                             from_ann,
                                             include_special)]

    def relation_types_to(self, to_ann, include_special=False):
        """
        Returns the possible relation types that can have an
        annotation of the given type as their arg2.
        """
        return [r.storage_form()
                for r
                in com.get_relations_by_arg2(self.directory,
                                             to_ann,
                                             include_special)]

    def relation_types_from_to(self, from_ann, to_ann, include_special=False):
        """
        Returns the possible relation types that can have the
        given arg1 and arg2.
        """
        types = []

        t1r = com.get_relations_by_arg1(
            self.directory, from_ann, include_special)
        t2r = com.get_relations_by_arg2(
            self.directory, to_ann, include_special)

        for r in t1r:
            if r in t2r:
                types.append(r.storage_form())

        return types

    def overlap_types(self, inner, outer):
        """
        Returns the set of annotation overlap types that have been
        configured for the given pair of annotations.
        """
        # TODO: this is O(NM) for relation counts N and M and goes
        # past much of the implemented caching. Might become a
        # bottleneck for annotations with large type systems.
        t1r = com.get_relations_by_arg1(self.directory, inner, True)
        t2r = com.get_relations_by_arg2(self.directory, outer, True)

        types = []
        for r in (s for s in t1r
                  if s.storage_form() in cst.SPECIAL_RELATION_TYPES):
            if r in t2r:
                types.append(r)

        # new-style overlap configuration ("<OVERLAP>") takes precedence
        # over old-style configuration ("ENTITY-NESTING").
        ovl_types = set()

        ovl = [r for r in types
               if r.storage_form() == cst.TEXTBOUND_OVERLAP_TYPE]
        nst = [r for r in types
               if r.storage_form() == cst.ENTITY_NESTING_TYPE]

        if ovl:
            if nst:
                Messager.warning('Warning: both '+cst.TEXTBOUND_OVERLAP_TYPE +
                                 ' and '+cst.ENTITY_NESTING_TYPE+' defined for ' +
                                 '('+inner+','+outer+') in config. ' +
                                 'Ignoring latter.')
            for r in ovl:
                if cst.OVERLAP_TYPE_ARG not in r.special_arguments:
                    Messager.warning('Warning: missing '+cst.OVERLAP_TYPE_ARG +
                                     ' for '+cst.TEXTBOUND_OVERLAP_TYPE +
                                     ', ignoring specification.')
                    continue
                for val in r.special_arguments[cst.OVERLAP_TYPE_ARG]:
                    ovl_types |= set(val.split('|'))
        elif nst:
            # translate into new-style configuration
            ovl_types = set(['contain'])
        else:
            ovl_types = set()

        undefined_types = [t for t in ovl_types if
                           t not in ('contain', 'equal', 'cross', '<ANY>')]
        if undefined_types:
            Messager.warning('Undefined '+cst.OVERLAP_TYPE_ARG+' value(s) ' +
                             str(undefined_types)+' for ' +
                             '('+inner+','+outer+') in config. ')
        return ovl_types

    def span_can_contain(self, inner, outer):
        """
        Returns True if the configuration allows the span of an
        annotation of type inner to (properly) contain an annotation
        of type outer, False otherwise.
        """
        ovl_types = self.overlap_types(inner, outer)
        if 'contain' in ovl_types or '<ANY>' in ovl_types:
            return True
        ovl_types = self.overlap_types(outer, inner)
        if '<ANY>' in ovl_types:
            return True
        return False

    def spans_can_be_equal(self, t1, t2):
        """
        Returns True if the configuration allows the spans of
        annotations of type t1 and t2 to be equal, False otherwise.
        """
        ovl_types = self.overlap_types(t1, t2)
        if 'equal' in ovl_types or '<ANY>' in ovl_types:
            return True
        ovl_types = self.overlap_types(t2, t1)
        if 'equal' in ovl_types or '<ANY>' in ovl_types:
            return True
        return False

    def spans_can_cross(self, t1, t2):
        """
        Returns True if the configuration allows the spans of
        annotations of type t1 and t2 to cross, False otherwise.
        """
        ovl_types = self.overlap_types(t1, t2)
        if 'cross' in ovl_types or '<ANY>' in ovl_types:
            return True
        ovl_types = self.overlap_types(t2, t1)
        if 'cross' in ovl_types or '<ANY>' in ovl_types:
            return True
        return False

    def all_connections(self, include_special=False):
        """
        Returns a dict of dicts of lists, outer dict keyed by
        entity/event type, inner dicts by role/relation type, and
        lists containing entity/event types, representing all possible
        connections between annotations. This function is provided to
        optimize access to the entire annotation configuration for
        passing it to the client and should never be used to check for
        individual connections. The caller must not change the
        contents of the returned collection.
        """

        # TODO: are these uniques really necessary?
        entity_types = com.unique_preserve_order(self.get_entity_types())
        event_types = com.unique_preserve_order(self.get_event_types())
        all_types = com.unique_preserve_order(entity_types + event_types)

        connections = {}

        # TODO: it might be possible to avoid copies like
        # entity_types[:] and all_types[:] here. Consider the
        # possibility.

        for t1 in all_types:
            assert t1 not in connections, "INTERNAL ERROR"
            connections[t1] = {}

            processed_as_relation = {}

            # relations

            rels = com.get_relations_by_arg1(
                self.directory, t1, include_special)

            for r in rels:
                a = r.storage_form()

                conns = connections[t1].get(a, [])

                # magic number "1" is for 2nd argument
                args = r.arguments[r.arg_list[1]]

                if "<ANY>" in args:
                    connections[t1][a] = all_types[:]
                else:
                    for t2 in args:
                        if t2 == "<ENTITY>":
                            conns.extend(entity_types)
                        elif t2 == "<EVENT>":
                            conns.extend(event_types)
                        else:
                            conns.append(t2)
                    connections[t1][a] = com.unique_preserve_order(conns)

                processed_as_relation[a] = True

            # event arguments

            n1 = com.get_node_by_storage_form(self.directory, t1)

            for a, args in n1.arguments.items():
                if a in processed_as_relation:
                    Messager.warning(
                        "Project configuration: %s appears both as role "
                        "and relation. Configuration may be wrong." % a)
                    # won't try to resolve
                    continue

                assert a not in connections[t1], "INTERNAL ERROR"

                # TODO: dedup w/above
                if "<ANY>" in args:
                    connections[t1][a] = all_types[:]
                else:
                    conns = []
                    for t2 in args:
                        if t2 == "<EVENT>":
                            conns.extend(event_types)
                        elif t2 == "<ENTITY>":
                            conns.extend(entity_types)
                        else:
                            conns.append(t2)
                    connections[t1][a] = com.unique_preserve_order(conns)

        return connections

    def arc_types_from_to(self, from_ann, to_ann="<ANY>", include_special=False):
        """
        Returns the possible arc types that can connect an annotation
        of type from_ann to an annotation of type to_ann.
        If to_ann has the value \"<ANY>\", returns all possible arc types.
        """

        from_node = com.get_node_by_storage_form(self.directory, from_ann)

        if from_node is None:
            Messager.warning(
                "Project configuration: unknown textbound/event type %s. "
                "Configuration may be wrong." % from_ann)
            return []

        if to_ann == "<ANY>":
            relations_from = com.get_relations_by_arg1(
                self.directory, from_ann, include_special)
            # TODO: consider using from_node.arg_list instead of .arguments for order
            return com.unique_preserve_order([role for role in from_node.arguments] + [r.storage_form() for r in relations_from])

        # specific hits
        types = from_node.keys_by_type.get(to_ann, [])

        if "<ANY>" in from_node.keys_by_type:
            types += from_node.keys_by_type["<ANY>"]

        # generic arguments
        if self.is_event_type(to_ann) and '<EVENT>' in from_node.keys_by_type:
            types += from_node.keys_by_type['<EVENT>']
        if self.is_physical_entity_type(to_ann) and '<ENTITY>' in from_node.keys_by_type:
            types += from_node.keys_by_type['<ENTITY>']

        # relations
        types.extend(self.relation_types_from_to(from_ann, to_ann))

        return com.unique_preserve_order(types)

    def attributes_for(self, ann_type):
        """
        Returs a list of the possible attribute types for an
        annotation of the given type.
        """
        attrs = []
        for attr in com.get_attribute_type_list(self.directory):
            if attr == cst.SEPARATOR_STR:
                continue

            if 'Arg' not in attr.arguments:
                Messager.warning(
                    "Project configuration: config error: attribute '%s' "
                    "lacks 'Arg:' specification." % attr.storage_form())
                continue

            types = attr.arguments['Arg']

            if ((ann_type in types) or ('<ANY>' in types) or
                (self.is_event_type(ann_type) and '<EVENT>' in types) or
                (self.is_physical_entity_type(ann_type) and '<ENTITY>' in types)
                or
                    (self.is_relation_type(ann_type) and '<RELATION>' in types)):
                attrs.append(attr.storage_form())

        return attrs

    def get_labels(self):
        return com.get_labels(self.directory)

    def get_kb_shortcuts(self):
        return com.get_kb_shortcuts(self.directory)

    def get_access_control(self):
        return com.get_access_control(self.directory)

    def get_attribute_types(self):
        return [t.storage_form() for t in com.get_attribute_type_list(self.directory)]

    def get_event_types(self):
        return [t.storage_form() for t in com.get_event_type_list(self.directory)]

    def get_relation_types(self):
        return [t.storage_form() for t in com.get_relation_type_list(self.directory)]

    def get_equiv_types(self):
        # equivalence relations are those relations that are symmetric
        # and transitive, i.e. that have "symmetric" and "transitive"
        # in their "<REL-TYPE>" special argument values.
        return [t.storage_form() for t in com.get_relation_type_list(self.directory)
                if "<REL-TYPE>" in t.special_arguments and
                "symmetric" in t.special_arguments["<REL-TYPE>"] and
                "transitive" in t.special_arguments["<REL-TYPE>"]]

    def get_relations_by_type(self, _type):
        return com.get_relations_by_storage_form(self.directory, _type)

    def get_labels_by_type(self, _type):
        return com.get_labels_by_storage_form(self.directory, _type)

    def get_drawing_types(self):
        return com.get_drawing_types(self.directory)

    def get_drawing_config_by_type(self, _type):
        return com.get_drawing_config_by_storage_form(self.directory, _type)

    def get_search_config(self):
        search_config = []
        for r in com.get_search_config_list(self.directory):
            if '<URL>' not in r.special_arguments:
                Messager.warning(
                    'Project configuration: config error: missing <URL> '
                    'specification for %s search.' % r.storage_form())
            else:
                search_config.append(
                    (r.storage_form(), r.special_arguments['<URL>'][0]))
        return search_config

    def _get_tool_config(self, tool_list):
        tool_config = []
        for r in tool_list:
            if '<URL>' not in r.special_arguments:
                Messager.warning(
                    'Project configuration: config error: missing <URL> '
                    'specification for %s.' % r.storage_form())
                continue
            if 'tool' not in r.arguments:
                Messager.warning(
                    'Project configuration: config error: missing tool '
                    'name ("tool") for %s.' % r.storage_form())
                continue
            if 'model' not in r.arguments:
                Messager.warning(
                    'Project configuration: config error: missing model '
                    'name ("model") for %s.' % r.storage_form())
                continue
            tool_config.append((r.storage_form(),
                                r.arguments['tool'][0],
                                r.arguments['model'][0],
                                r.special_arguments['<URL>'][0]))
        return tool_config

    def get_disambiguator_config(self):
        tool_list = com.get_disambiguator_config_list(self.directory)
        return self._get_tool_config(tool_list)

    def get_annotator_config(self):
        # TODO: "annotator" is a very confusing term for a web service
        # that does automatic annotation in the context of a tool
        # where most annotators are expected to be human. Rethink.
        tool_list = com.get_annotator_config_list(self.directory)
        return self._get_tool_config(tool_list)

    def get_normalization_config(self):
        norm_list = com.get_normalization_config_list(self.directory)
        norm_config = []
        for n in norm_list:
            if 'DB' not in n.arguments:
                # optional, server looks in default location if None
                n.arguments['DB'] = [None]
            if '<URL>' not in n.special_arguments:
                Messager.warning(
                    'Project configuration: config error: missing <URL> '
                    'specification for %s.' % n.storage_form())
                continue
            if '<URLBASE>' not in n.special_arguments:
                # now optional, client skips link generation if None
                n.special_arguments['<URLBASE>'] = [None]
            norm_config.append((n.storage_form(),
                                n.special_arguments['<URL>'][0],
                                n.special_arguments['<URLBASE>'][0],
                                n.arguments['DB'][0]))
        return norm_config

    def get_entity_types(self):
        return [t.storage_form() for t in com.get_entity_type_list(self.directory)]

    def get_entity_type_hierarchy(self):
        return com.get_entity_type_hierarchy(self.directory)

    def get_relation_type_hierarchy(self):
        return com.get_relation_type_hierarchy(self.directory)

    def get_event_type_hierarchy(self):
        return com.get_event_type_hierarchy(self.directory)

    def get_attribute_type_hierarchy(self):
        return com.get_attribute_type_hierarchy(self.directory)

    def _get_filtered_attribute_type_hierarchy(self, types):
        from copy import deepcopy
        # TODO: This doesn't property implement recursive traversal
        # and filtering, instead only checking the topmost nodes.
        filtered = []
        for t in self.get_attribute_type_hierarchy():
            if t.storage_form() in types:
                filtered.append(deepcopy(t))
        return filtered

    def attributes_for_types(self, types):
        """
        Returns list containing the attribute types that are
        applicable to at least one of the given annotation types.
        """
        # list to preserve order, dict for lookup
        attribute_list = []
        seen = {}
        for t in types:
            for a in self.attributes_for(t):
                if a not in seen:
                    attribute_list.append(a)
                    seen[a] = True
        return attribute_list

    def get_entity_attribute_type_hierarchy(self):
        """
        Returns the attribute type hierarchy filtered to include
        only attributes that apply to at least one entity.
        """
        attr_types = self.attributes_for_types(self.get_entity_types())
        return self._get_filtered_attribute_type_hierarchy(attr_types)

    def get_relation_attribute_type_hierarchy(self):
        """
        Returns the attribute type hierarchy filtered to include
        only attributes that apply to at least one relation.
        """
        attr_types = self.attributes_for_types(self.get_relation_types())
        return self._get_filtered_attribute_type_hierarchy(attr_types)

    def get_event_attribute_type_hierarchy(self):
        """
        Returns the attribute type hierarchy filtered to include
        only attributes that apply to at least one event.
        """
        attr_types = self.attributes_for_types(self.get_event_types())
        return self._get_filtered_attribute_type_hierarchy(attr_types)

    def preferred_display_form(self, t):
        """
        Given a storage form label, returns the preferred display form
        as defined by the label configuration (labels.conf)
        """
        labels = com.get_labels_by_storage_form(self.directory, t)
        if labels is None or len(labels) < 1:
            return t
        return labels[0]

    def is_physical_entity_type(self, t):
        if t in self.get_entity_types() or t in self.get_event_types():
            return t in self.get_entity_types()
        # TODO: remove this temporary hack
        if t in com.very_likely_physical_entity_types:
            return True
        return t in self.get_entity_types()

    def is_event_type(self, t):
        return t in self.get_event_types()

    def is_relation_type(self, t):
        return t in self.get_relation_types()

    def is_equiv_type(self, t):
        return t in self.get_equiv_types()

    def is_configured_type(self, t):
        return (t in self.get_entity_types() or
                t in self.get_event_types() or
                t in self.get_relation_types())

    def type_category(self, t):
        """
        Returns the category of the given type t.
        The categories can be compared for equivalence but offer
        no other interface.
        """
        if self.is_physical_entity_type(t):
            return com.ENTITY_CATEGORY
        elif self.is_event_type(t):
            return com.EVENT_CATEGORY
        elif self.is_relation_type(t):
            return com.RELATION_CATEGORY
        else:
            # TODO: others
            return com.UNKNOWN_CATEGORY
