# -*- coding: utf-8 -*-
'''
Per-project configuration functionality for
Arat Rapid Annotation Tool (arat)

Author:     Pontus Stenetorp    <pontus is s u-tokyo ac jp>
Author:     Sampo Pyysalo       <smp is s u-tokyo ac jp>
Author:     Illes Solt          <solt tmit bme hu>
Version:    2011-08-15
'''

# future
from __future__ import absolute_import

# standard
import re
import sys
try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache

# third party
import six
import six.moves.urllib_robotparser   # pylint: disable=import-error
import six.moves.urllib.parse   # pylint: disable=import-error
from six.moves import range

# arat
from server.annotation import open_textfile
from server.message import Messager
from server.projectconfig import constants as cst
from server.projectconfig.typehierarchynode import TypeHierarchyNode

ENTITY_CATEGORY, EVENT_CATEGORY, RELATION_CATEGORY, UNKNOWN_CATEGORY = range(4)

_PYTHON3 = (sys.version_info > (3, 0))

_CACHE_SIZE = 1000

if not _PYTHON3:
    FileNotFoundError = OSError


class InvalidProjectConfigException(Exception):
    pass


def __require_tab_separator(section):
    """
    Given a section name, returns True iff in that section of the
    project config only tab separators should be permitted.
    This exception initially introduced to allow slighlty different
    syntax for the [labels] section than others.
    """
    return section == "labels"


def __read_term_hierarchy(input_, section=None):
    """

    Output a list of TypeHierarchyNode

    >>> _input = ["# This a comment to be ignored"]
    >>> _input.append("[spans]")
    >>> _input.append("# POS tags")
    >>> _input.append("adj")
    >>> _input.append("adv")
    >>> _input.append("art")

    >>> isinstance((__read_term_hierarchy("\\n".join(_input))[0]), TypeHierarchyNode)
    True

    """

    root_nodes = []
    last_node_at_depth = {}
    last_args_at_depth = {}

    macros = {}
    for line in input_:
        # skip empties and lines starting with '#'
        if line.strip() == '' or re.match(r'^\s*#', line):
            continue

        # interpret lines of only hyphens as separators
        # for display
        if re.match(r'^\s*-+\s*$', line):
            # TODO: proper placeholder and placing
            root_nodes.append(cst.SEPARATOR_STR)
            continue

        # interpret lines of the format <STR1>=STR2 as "macro"
        # definitions, defining <STR1> as a placeholder that should be
        # replaced with STR2 whevever it occurs.
        match_obj = re.match(r'^<([a-zA-Z_-]+)>=\s*(.*?)\s*$', line)
        if match_obj:
            name, value = match_obj.groups()
            if name in cst.RESERVED_CONFIG_NAME:
                Messager.error(
                    "Cannot redefine <%s> in configuration, "
                    "it is a reserved name." % name)
                # TODO: proper exception
                raise InvalidProjectConfigException("Reserved name: "+name)
            else:
                macros["<%s>" % name] = value
            continue

        # macro expansion
        for token in macros:
            line = line.replace(token, macros[token])

        # check for undefined macros
        for match_obj in re.finditer(r'(<.*?>)', line):
            token = match_obj.group(1)
            assert token in cst.RESERVED_CONFIG_STRING, ("Error: undefined macro %s "
            "in configuration. (Note that macros are section-specific.)") % token

        # choose strict tab-only separator or looser any-space
        # separator matching depending on section
        if __require_tab_separator(section):
            match_obj = re.match(r'^(\s*)([^\t]+)(?:\t(.*))?$', line)
        else:
            match_obj = re.match(r'^(\s*)(\S+)(?:\s+(.*))?$', line)
        assert match_obj, "Error parsing line: '%s'" % line
        indent, terms, args = match_obj.groups()
        terms = [i.strip() for i in terms.split("|") if i.strip() != ""]
        if args is None or args.strip() == "":
            args = []
        else:
            args = [i.strip() for i in args.split(",") if i.strip() != ""]

        # older configs allowed space in term strings, splitting those
        # from arguments by space. Trying to parse one of these in the
        # new way will result in a crash from space in arguments.
        # The following is a workaround for the transition.
        if [i for i in args if re.search(r'\s', i)] and '\t' in line:
            # re-parse in the old way (dups from above)
            match_obj = re.match(r'^(\s*)([^\t]+)(?:\t(.*))?$', line)
            assert match_obj, "Error parsing line: '%s'" % line
            indent, terms, args = match_obj.groups()
            terms = [i.strip() for i in terms.split("|") if i.strip() != ""]
            if args is None or args.strip() == "":
                args = []
            else:
                args = [i.strip() for i in args.split(",") if i.strip() != ""]
            # issue a warning
            Messager.warning("Space in term name(s) (%s) on line \"%s\" "
                             "in config. This feature is deprecated and "
                             "support will be removed in future versions. "
                             "Please revise your configuration." % (
                                 ",".join(['"%s"' % i
                                           for i
                                           in terms
                                           if " " in i]), line), 20)

        # depth in the ontology corresponds to the number of
        # spaces in the initial indent.
        depth = len(indent)

        # expand <INHERIT> into parent arguments
        expanded_args = []
        for a in args:
            if a != '<INHERIT>':
                expanded_args.append(a)
            else:
                assert depth-1 in last_args_at_depth, \
                    "Error no parent for '%s'" % line
                expanded_args.extend(last_args_at_depth[depth-1])

        args = expanded_args

        n = TypeHierarchyNode(terms, args)
        if depth == 0:
            # root level, no children assignments
            root_nodes.append(n)
        else:
            # assign as child of last node at the depth of the parent
            assert depth-1 in last_node_at_depth, \
                "Error: no parent for '%s'" % line
            last_node_at_depth[depth-1].children.append(n)
        last_node_at_depth[depth] = n
        last_args_at_depth[depth] = args

    return root_nodes


def __read_or_default(filename, default):
    """
    >>> config_filename = "data/example-data/corpora/CoNLL-ST_2006/tools.conf"
    >>> config = __read_or_default(config_filename, six.u("missed"))
    >>> six.u("Tokens") in config
    True


    >>> __read_or_default("does/not/exists/tools.conf", six.u("missed")) == six.u("missed")
    True

    """

    try:
        f = open_textfile(filename, 'r')
        r = f.read()
        f.close()
        return r
    except FileNotFoundError:
        # TODO: specific exception handling and reporting
        return default
    except IOError:
        return default


def __parse_kb_shortcuts(shortcutstr, default, source):
    shortcuts = {}
    for l in shortcutstr.split("\n"):
        l = l.strip()
        if l == "" or l[:1] == "#":
            continue
        key, type_ = re.split(r'[ \t]+', l)
        if key in shortcuts:
            Messager.warning("Project configuration: keyboard shortcut "
                             "for '%s' defined multiple times. Ignoring "
                             "all but first ('%s')" % (
                                 key, shortcuts[key]))
        else:
            shortcuts[key] = type_
    return shortcuts


def __parse_access_control(acstr, source):
    parser = six.moves.urllib_robotparser.RobotFileParser()
    parser.parse(acstr.split("\n"))
    return parser


def get_config_path(directory):
    return __read_first_in_directory_tree(directory,
                                          cst.__ANNOTATION_CONFIG_FILENAME)[1]


def __read_first_in_directory_tree(directory, filename):
    # config will not be available command-line invocations;
    # in these cases search whole tree
    from config import BASE_DIR
    from os.path import split, join
    source, result = None, None

    # check from the given directory and parents, but not above BASE_DIR
    if directory is not None:
        # TODO: this check may fail; consider "foo//bar/data"
        while BASE_DIR in directory:
            source = join(directory, filename)
            result = __read_or_default(source, None)
            if result is not None:
                break
            directory = split(directory)[0]

    return (result, source)


def __parse_configs(configstr, source, expected_sections, optional_sections):
    # top-level config structure is a set of term hierarchies
    # separated by lines consisting of "[SECTION]" where SECTION is
    # e.g.  "entities", "relations", etc.

    # start by splitting config file lines by section, also storing
    # the label (default name or alias) used for each section.

    section = "general"
    section_lines = {section: []}
    section_labels = {}
    for l in configstr.split("\n"):
        m = re.match(r'^\s*\[(.*)\]\s*$', l)
        if m:
            section = m.group(1)

            # map and store section name/alias (e.g. "spans" -> "entities")
            section_name = cst.SECTION_ALIAS.get(section, section)
            section_labels[section_name] = section
            section = section_name

            if section not in expected_sections:
                Messager.warning("Project configuration: unexpected section "
                                 "[%s] in %s. Ignoring contents." % (
                                     section, source), 5)
            if section not in section_lines:
                section_lines[section] = []
        else:
            section_lines[section].append(l)

    # attempt to parse lines in each section as a term hierarchy
    configs = {}
    for s, sl in section_lines.items():
        try:
            configs[s] = __read_term_hierarchy(sl, s)
        except Exception as e:
            Messager.warning("Project configuration: error parsing section "
                             "[%s] in %s: %s" % (s, source, str(e)), 5)
            raise

    # verify that expected sections are present; replace with empty if not.
    for s in expected_sections:
        if s not in configs:
            if s not in optional_sections:
                Messager.warning(
                    "Project configuration: missing section [%s] in %s. "
                    "Configuration may be wrong." % (s, source), 5)
            configs[s] = []

    return (configs, section_labels)


_GET_CONFIGS_CACHE = {}


def get_configs(directory, filename, defaultstr, minconf, sections, optional_sections):
    if (directory, filename) not in _GET_CONFIGS_CACHE:
        configstr, source = __read_first_in_directory_tree(directory, filename)

        if configstr is None:
            # didn't get one; try default dir and fall back to the default
            configstr = __read_or_default(filename, defaultstr)
            if configstr == defaultstr:
                Messager.info(
                    "Project configuration: no configuration file (%s) "
                    "found, using default." % filename, 5)
                source = "[default]"
            else:
                source = filename

        # try to parse what was found, fall back to minimal config
        try:
            configs, section_labels = __parse_configs(
                configstr, source, sections, optional_sections)
        except InvalidProjectConfigException:
            Messager.warning(
                "Project configuration: Falling back to minimal default. "
                "Configuration is likely wrong.", 5)
            configs = minconf
            section_labels = dict([(a, a) for a in sections])

        # very, very special case processing: if we have a type
        # "Equiv" defined in a "relations" section that doesn't
        # specify a "<REL-TYPE>", automatically fill "symmetric" and
        # "transitive". This is to support older configurations that
        # rely on the type "Equiv" to identify the relation as an
        # equivalence.
        if 'relations' in configs:
            for r in configs['relations']:
                if r == cst.SEPARATOR_STR:
                    continue
                if (r.storage_form() == "Equiv" and
                        "<REL-TYPE>" not in r.special_arguments):
                    # this was way too much noise; will only add in after
                    # at least most configs are revised.
                    # Messager.warning('Note: "Equiv" defined in config '
                    #                 'without "<REL-TYPE>"; assuming '
                    #                 'symmetric and transitive. Consider '
                    #                 'revising config to add '
                    #                 '"<REL-TYPE>:symmetric-transitive" '
                    #                 'to definition.')
                    r.special_arguments["<REL-TYPE>"] = ["symmetric",
                                                         "transitive"]

        _GET_CONFIGS_CACHE[(directory, filename)] = (configs, section_labels)

    return _GET_CONFIGS_CACHE[(directory, filename)]


def __get_access_control(directory, filename, default_rules):

    acstr, source = __read_first_in_directory_tree(directory, filename)

    if acstr is None:
        acstr = default_rules  # TODO read or default isntead of default
        if acstr == default_rules:
            source = "[default rules]"
        else:
            source = filename
    ac_oracle = __parse_access_control(acstr, source)
    return ac_oracle


def __get_kb_shortcuts(directory, filename, default_shortcuts, min_shortcuts):

    shortcutstr, source = __read_first_in_directory_tree(directory, filename)

    if shortcutstr is None:
        shortcutstr = __read_or_default(filename, default_shortcuts)
        if shortcutstr == default_shortcuts:
            source = "[default kb_shortcuts]"
        else:
            source = filename

    kb_shortcuts = __parse_kb_shortcuts(shortcutstr, min_shortcuts, source)
    return kb_shortcuts


# final fallback for configuration; a minimal known-good config
__MINIMAL_CONFIGURATION = {
    cst.ENTITY_SECTION: [TypeHierarchyNode(["Protein"])],
    cst.RELATION_SECTION: [TypeHierarchyNode(["Equiv"],
                                             ["Arg1:Protein",
                                              "Arg2:Protein",
                                              "<REL-TYPE>:symmetric-transitive"])],
    cst.EVENT_SECTION: [TypeHierarchyNode(["Event"], ["Theme:Protein"])],
    cst.ATTRIBUTE_SECTION: [TypeHierarchyNode(["Negation"], ["Arg:<EVENT>"])],
}

# final fallback for visual configuration; minimal known-good config
__MINIMAL_VISUAL = {
    cst.LABEL_SECTION: [TypeHierarchyNode(["Protein", "Pro", "P"]),
                        TypeHierarchyNode(["Equiv", "Eq"]),
                        TypeHierarchyNode(["Event", "Ev"])],
    cst.DRAWING_SECTION: [TypeHierarchyNode([cst.VISUAL_SPAN_DEFAULT],
                                            ["fgColor:black", "bgColor:white"]),
                          TypeHierarchyNode([cst.VISUAL_ARC_DEFAULT],
                                            ["color:black"]),
                          TypeHierarchyNode([cst.VISUAL_ATTR_DEFAULT],
                                            ["glyph:*"])],
}
# final fallback for tools configuration; minimal known-good config
__MINIMAL_TOOLS = {
    cst.OPTIONS_SECTION: [],
    cst.SEARCH_SECTION: [TypeHierarchyNode(["google"],
                                           ["<URL>:http://www.google.com/search?q=%s"])],
    cst.ANNOTATORS_SECTION: [],
    cst.DISAMBIGUATORS_SECTION: [],
    cst.NORMALIZATION_SECTION: [],
}


def get_annotation_configs(directory):
    return get_configs(directory,
                       cst.__ANNOTATION_CONFIG_FILENAME,
                       cst.__DEFAULT_CONFIGURATION,
                       __MINIMAL_CONFIGURATION,
                       cst.__EXPECTED_ANNOTATION_SECTIONS,
                       cst.__OPTIONAL_ANNOTATION_SECTIONS)


def get_visual_configs(directory):
    return get_configs(directory,
                       cst.__VISUAL_CONFIG_FILENAME,
                       cst.__DEFAULT_VISUAL,
                       __MINIMAL_VISUAL,
                       cst.__EXPECTED_VISUAL_SECTIONS,
                       cst.__OPTIONAL_VISUAL_SECTIONS)


def get_tools_configs(directory):
    return get_configs(directory,
                       cst.__TOOLS_CONFIG_FILENAME,
                       cst.__DEFAULT_TOOLS,
                       __MINIMAL_TOOLS,
                       cst.__EXPECTED_TOOLS_SECTIONS,
                       cst.__OTIONAL_TOOLS_SECTIONS)


def get_entity_type_hierarchy(directory):
    return get_annotation_configs(directory)[0][cst.ENTITY_SECTION]


def get_relation_type_hierarchy(directory):
    return get_annotation_configs(directory)[0][cst.RELATION_SECTION]


def get_event_type_hierarchy(directory):
    return get_annotation_configs(directory)[0][cst.EVENT_SECTION]


def get_attribute_type_hierarchy(directory):
    return get_annotation_configs(directory)[0][cst.ATTRIBUTE_SECTION]


def get_annotation_config_section_labels(directory):
    return get_annotation_configs(directory)[1]

# TODO: use lru_cache or somethinf similar


@lru_cache(_CACHE_SIZE)
def get_labels(directory):
    l = {}
    for t in get_visual_configs(directory)[0][cst.LABEL_SECTION]:
        if t.storage_form() in l:
            Messager.warning(
                "In configuration, labels for '%s' defined more "
                "than once. Only using the last set." % t.storage_form(), -1)
        # first is storage for, rest are labels.
        l[t.storage_form()] = t.terms[1:]
    return l


@lru_cache(_CACHE_SIZE)
def get_drawing_types(directory):
    l = set()
    for n in get_drawing_config(directory):
        l.add(n.storage_form())
    return l


def get_option_config(directory):
    return get_tools_configs(directory)[0][cst.OPTIONS_SECTION]


def get_drawing_config(directory):
    return get_visual_configs(directory)[0][cst.DRAWING_SECTION]


def get_visual_option_config(directory):
    return get_visual_configs(directory)[0][cst.OPTIONS_SECTION]


def get_visual_config_section_labels(directory):
    return get_visual_configs(directory)[1]


def get_search_config(directory):
    return get_tools_configs(directory)[0][cst.SEARCH_SECTION]


def get_annotator_config(directory):
    return get_tools_configs(directory)[0][cst.ANNOTATORS_SECTION]


def get_disambiguator_config(directory):
    return get_tools_configs(directory)[0][cst.DISAMBIGUATORS_SECTION]


def get_normalization_config(directory):
    return get_tools_configs(directory)[0][cst.NORMALIZATION_SECTION]


def get_tools_config_section_labels(directory):
    return get_tools_configs(directory)[1]


@lru_cache(_CACHE_SIZE)
def get_access_control(directory):
    a = __get_access_control(directory,
                             cst.__ACCESS_CONTROL_FILENAME,
                             cst.__DEFAULT_ACCESS_CONTROL)
    return a


@lru_cache(_CACHE_SIZE)
def get_kb_shortcuts(directory):

    a = __get_kb_shortcuts(directory,
                           cst.__KB_SHORTCUT_FILENAME,
                           cst.__DEFAULT_KB_SHORTCUTS,
                           {"P": "Positive_regulation"})
    return a


def __collect_type_list(node, collected):
    if node == cst.SEPARATOR_STR:
        return collected

    collected.append(node)

    for c in node.children:
        __collect_type_list(c, collected)

    return collected


def __type_hierarchy_to_list(hierarchy):
    root_nodes = hierarchy
    types = []
    for n in root_nodes:
        __collect_type_list(n, types)
    return types


@lru_cache(_CACHE_SIZE)
def get_entity_type_list(directory):
    return __type_hierarchy_to_list(get_entity_type_hierarchy(directory))


@lru_cache(_CACHE_SIZE)
def get_event_type_list(directory):
    return __type_hierarchy_to_list(get_event_type_hierarchy(directory))


@lru_cache(_CACHE_SIZE)
def get_relation_type_list(directory):
    return __type_hierarchy_to_list(get_relation_type_hierarchy(directory))


@lru_cache(_CACHE_SIZE)
def get_attribute_type_list(directory):
    return __type_hierarchy_to_list(get_attribute_type_hierarchy(directory))


@lru_cache(_CACHE_SIZE)
def get_search_config_list(directory):
    return __type_hierarchy_to_list(get_search_config(directory))


@lru_cache(_CACHE_SIZE)
def get_annotator_config_list(directory):
    return __type_hierarchy_to_list(get_annotator_config(directory))


@lru_cache(_CACHE_SIZE)
def get_disambiguator_config_list(directory):
    return __type_hierarchy_to_list(get_disambiguator_config(directory))


@lru_cache(_CACHE_SIZE)
def get_normalization_config_list(directory):
    return __type_hierarchy_to_list(get_normalization_config(directory))


_GET_NODE_BY_STORAGE_FORM_CACHE = {}


def get_node_by_storage_form(directory, term):
    if directory not in _GET_NODE_BY_STORAGE_FORM_CACHE:
        d = {}
        for e in get_entity_type_list(directory) + get_event_type_list(directory):
            t = e.storage_form()
            if t in d:
                Messager.warning(
                    "Project configuration: term %s appears multiple times, "
                    "only using last. Configuration may be wrong." % t, 5)
            d[t] = e
        _GET_NODE_BY_STORAGE_FORM_CACHE[directory] = d

    return _GET_NODE_BY_STORAGE_FORM_CACHE[directory].get(term, None)


def _get_option_by_storage_form(directory, term, config, cache):
    if directory not in cache:
        d = {}
        for n in config:
            t = n.storage_form()
            if t in d:
                Messager.warning(
                    "Project configuration: %s appears multiple times, "
                    "only using last. Configuration may be wrong." % t, 5)
            d[t] = {}
            for a in n.arguments:
                if len(n.arguments[a]) != 1:
                    Messager.warning(
                        "Project configuration: %s key %s has multiple "
                        "values, only using first. Configuration may "
                        "be wrong." % (t, a), 5)
                d[t][a] = n.arguments[a][0]

        cache[directory] = d

    return cache[directory].get(term, None)


_GET_OPTION_CONFIG_BY_STORAGE_FORM_CACHE = {}


def get_option_config_by_storage_form(directory, term):
    config = get_option_config(directory)
    return _get_option_by_storage_form(directory, term, config,
                                       _GET_OPTION_CONFIG_BY_STORAGE_FORM_CACHE)


_GET_VISUAL_OPTION_CONFIG_BY_STORAGE_FORM_CACHE = {}


def get_visual_option_config_by_storage_form(directory, term):
    config = get_visual_option_config(directory)
    return _get_option_by_storage_form(directory, term, config,
                                       _GET_VISUAL_OPTION_CONFIG_BY_STORAGE_FORM_CACHE)

# access for settings for specific options in tools.conf
# TODO: avoid fixed string values here, define vars earlier


def options_get_validation(directory):
    v = get_option_config_by_storage_form(directory, 'Validation')
    return 'none' if v is None else v.get('validate', 'none')


def options_get_tokenization(directory):
    v = get_option_config_by_storage_form(directory, 'Tokens')
    return 'whitespace' if v is None else v.get('tokenizer', 'whitespace')


def options_get_ssplitter(directory):
    v = get_option_config_by_storage_form(directory, 'Sentences')
    return 'regex' if v is None else v.get('splitter', 'regex')


def options_get_annlogfile(directory):
    v = get_option_config_by_storage_form(directory, 'Annotation-log')
    return '<NONE>' if v is None else v.get('logfile', '<NONE>')

# access for settings for specific options in visual.conf


def visual_options_get_arc_bundle(directory):
    v = get_visual_option_config_by_storage_form(directory, 'Arcs')
    return 'none' if v is None else v.get('bundle', 'none')


def visual_options_get_text_direction(directory):
    v = get_visual_option_config_by_storage_form(directory, 'Text')
    return 'ltr' if v is None else v.get('direction', 'ltr')


def get_drawing_config_by_storage_form(directory, term):
    cache = get_drawing_config_by_storage_form.__cache
    if directory not in cache:
        d = {}
        for n in get_drawing_config(directory):
            t = n.storage_form()
            if t in d:
                Messager.warning(
                    "Project configuration: term %s appears multiple times, "
                    "only using last. Configuration may be wrong." % t, 5)
            d[t] = {}
            for a in n.arguments:
                # attribute drawing can be specified with multiple
                # values (multi-valued attributes), other parts of
                # drawing config should have single values only.
                if len(n.arguments[a]) != 1:
                    if a in cst.ATTR_DRAWING_ATTRIBUTES:
                        # use multi-valued directly
                        d[t][a] = n.arguments[a]
                    else:
                        # warn and pass
                        Messager.warning("Project configuration: expected "
                                         "single value for %s argument %s, "
                                         "got '%s'. Configuration may be "
                                         "wrong." %
                                         (t, a, "|".join(n.arguments[a])))
                else:
                    d[t][a] = n.arguments[a][0]

        # TODO: hack to get around inability to have commas in values;
        # fix original issue instead
        for t in d:
            for k in d[t]:
                # sorry about this
                if not isinstance(d[t][k], list):
                    d[t][k] = d[t][k].replace("-", ",")
                else:
                    for i in range(len(d[t][k])):
                        d[t][k][i] = d[t][k][i].replace("-", ",")

        default_keys = [cst.VISUAL_SPAN_DEFAULT,
                        cst.VISUAL_ARC_DEFAULT,
                        cst.VISUAL_ATTR_DEFAULT]
        for default_dict in [d.get(dk, {}) for dk in default_keys]:
            for k in default_dict:
                for t in d:
                    d[t][k] = d[t].get(k, default_dict[k])

        # Kind of a special case: recognize <NONE> as "deleting" an
        # attribute (prevents default propagation) and <EMPTY> as
        # specifying that a value should be the empty string
        # (can't be written as such directly).
        for t in d:
            todelete = [k for k in d[t] if d[t][k] == '<NONE>']
            for k in todelete:
                del d[t][k]

            for k in d[t]:
                if d[t][k] == '<EMPTY>':
                    d[t][k] = ''

        cache[directory] = d

    return cache[directory].get(term, None)


get_drawing_config_by_storage_form.__cache = {}


def __directory_relations_by_arg_num(directory, num, atype, include_special=False):
    assert num >= 0 and num < 2, "INTERNAL ERROR"

    rels = []

    entity_types = set([t.storage_form()
                        for t in get_entity_type_list(directory)])
    event_types = set([t.storage_form()
                       for t in get_event_type_list(directory)])

    for r in get_relation_type_list(directory):
        # "Special" nesting relations ignored unless specifically
        # requested
        if r.storage_form() in cst.SPECIAL_RELATION_TYPES and not include_special:
            continue

        if len(r.arg_list) != 2:
            # Don't complain about argument constraints for unused relations
            if not r.unused:
                Messager.warning("Relation type %s has %d arguments in "
                                 "configuration (%s; expected 2). Please fix "
                                 "configuration." % (
                                     r.storage_form(),
                                     len(r.arg_list),
                                     ",".join(r.arg_list)))
        else:
            types = r.arguments[r.arg_list[num]]
            for type_ in types:
                # TODO: there has to be a better way
                if (type_ == atype or
                        type_ == "<ANY>" or
                        atype == "<ANY>" or
                        (type_ in entity_types and atype == "<ENTITY>") or
                        (type_ in event_types and atype == "<EVENT>") or
                        (atype in entity_types and type_ == "<ENTITY>") or
                        (atype in event_types and type_ == "<EVENT>")):
                    rels.append(r)
                    # TODO: why not break here?

    return rels


def get_relations_by_arg1(directory, atype, include_special=False):
    cache = get_relations_by_arg1.__cache
    cache[directory] = cache.get(directory, {})
    if (atype, include_special) not in cache[directory]:
        cache[directory][(atype, include_special)] = __directory_relations_by_arg_num(
            directory, 0, atype, include_special)
    return cache[directory][(atype, include_special)]


get_relations_by_arg1.__cache = {}


def get_relations_by_arg2(directory, atype, include_special=False):
    cache = get_relations_by_arg2.__cache
    cache[directory] = cache.get(directory, {})
    if (atype, include_special) not in cache[directory]:
        cache[directory][(atype, include_special)] = __directory_relations_by_arg_num(
            directory, 1, atype, include_special)
    return cache[directory][(atype, include_special)]


get_relations_by_arg2.__cache = {}


def get_relations_by_storage_form(directory, rtype, include_special=False):
    cache = get_relations_by_storage_form.__cache
    cache[directory] = cache.get(directory, {})
    if include_special not in cache[directory]:
        cache[directory][include_special] = {}
        for r in get_relation_type_list(directory):
            if (r.storage_form() in cst.SPECIAL_RELATION_TYPES and
                    not include_special):
                continue
            if r.unused:
                continue
            if r.storage_form() not in cache[directory][include_special]:
                cache[directory][include_special][r.storage_form()] = []
            cache[directory][include_special][r.storage_form()].append(r)
    return cache[directory][include_special].get(rtype, [])


get_relations_by_storage_form.__cache = {}


def get_labels_by_storage_form(directory, term):
    cache = get_labels_by_storage_form.__cache
    if directory not in cache:
        cache[directory] = {}
        for l, labels in get_labels(directory).items():
            # recognize <EMPTY> as specifying that a label should
            # be the empty string
            labels = [lab if lab != '<EMPTY>' else ' ' for lab in labels]
            cache[directory][l] = labels
    return cache[directory].get(term, None)


get_labels_by_storage_form.__cache = {}

# fallback for missing or partial config: these are highly likely to
# be entity (as opposed to an event or relation) types.
# TODO: remove this workaround once the configs stabilize.
very_likely_physical_entity_types = [
    'Protein',
    'Entity',
    'Organism',
    'Chemical',
    'Two-component-system',
    'Regulon-operon',
    # for more PTM annotation
    'Protein_family_or_group',
    'DNA_domain_or_region',
    'Protein_domain_or_region',
    'Amino_acid_monomer',
    'Carbohydrate',
    # for AZ corpus
    'Cell_type',
    'Drug_or_compound',
    'Gene_or_gene_product',
    'Tissue',
    # 'Not_sure',
    # 'Other',
    'Other_pharmaceutical_agent',
]

# helper; doesn't really belong here
# TODO: shouldn't we have an utils.py or something for stuff like this?


def unique_preserve_order(iterable):
    seen = set()
    uniqued = []
    for i in iterable:
        if i not in seen:
            seen.add(i)
            uniqued.append(i)
    return uniqued
