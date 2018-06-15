# -*- coding: utf-8 -*-
"""
Created on Thu Jun 14 00:09:40 2018

@author: phnx
"""

# Magic string to use to represent a separator in a config
SEPARATOR_STR = "SEPARATOR"


# names of files in which various configs are found
__ACCESS_CONTROL_FILENAME = 'acl.conf'
__ANNOTATION_CONFIG_FILENAME = 'annotation.conf'
__VISUAL_CONFIG_FILENAME = 'visual.conf'
__TOOLS_CONFIG_FILENAME = 'tools.conf'
__KB_SHORTCUT_FILENAME = 'kb_shortcuts.conf'

# annotation config section name constants
ENTITY_SECTION = "entities"
RELATION_SECTION = "relations"
EVENT_SECTION = "events"
ATTRIBUTE_SECTION = "attributes"

# aliases for config section names
SECTION_ALIAS = {
    "spans": ENTITY_SECTION,
}

__EXPECTED_ANNOTATION_SECTIONS = (
    ENTITY_SECTION, RELATION_SECTION, EVENT_SECTION, ATTRIBUTE_SECTION)
__OPTIONAL_ANNOTATION_SECTIONS = []

# visual config section name constants
OPTIONS_SECTION = "options"
LABEL_SECTION = "labels"
DRAWING_SECTION = "drawing"

__EXPECTED_VISUAL_SECTIONS = (OPTIONS_SECTION, LABEL_SECTION, DRAWING_SECTION)
__OPTIONAL_VISUAL_SECTIONS = [OPTIONS_SECTION]

# tools config section name constants
SEARCH_SECTION = "search"
ANNOTATORS_SECTION = "annotators"
DISAMBIGUATORS_SECTION = "disambiguators"
NORMALIZATION_SECTION = "normalization"

__EXPECTED_TOOLS_SECTIONS = (OPTIONS_SECTION, SEARCH_SECTION,
                             ANNOTATORS_SECTION, DISAMBIGUATORS_SECTION, NORMALIZATION_SECTION)
__OTIONAL_TOOLS_SECTIONS = (OPTIONS_SECTION, SEARCH_SECTION,
                            ANNOTATORS_SECTION, DISAMBIGUATORS_SECTION, NORMALIZATION_SECTION)

# special relation types for marking which spans can overlap
# ENTITY_NESTING_TYPE used up to version 1.3, now deprecated
ENTITY_NESTING_TYPE = "ENTITY-NESTING"
# TEXTBOUND_OVERLAP_TYPE used from version 1.3 onward
TEXTBOUND_OVERLAP_TYPE = "<OVERLAP>"
SPECIAL_RELATION_TYPES = set([ENTITY_NESTING_TYPE,
                              TEXTBOUND_OVERLAP_TYPE])
OVERLAP_TYPE_ARG = '<OVL-TYPE>'

# visual config default value names
VISUAL_SPAN_DEFAULT = "SPAN_DEFAULT"
VISUAL_ARC_DEFAULT = "ARC_DEFAULT"
VISUAL_ATTR_DEFAULT = "ATTRIBUTE_DEFAULT"

# visual config attribute name lists
SPAN_DRAWING_ATTRIBUTES = ['fgColor', 'bgColor', 'borderColor']
ARC_DRAWING_ATTRIBUTES = ['color', 'dashArray', 'arrowHead', 'labelArrow']
ATTR_DRAWING_ATTRIBUTES = ['glyphColor',
                           'box', 'dashArray', 'glyph', 'position']

# fallback defaults if config files not found
__DEFAULT_CONFIGURATION = """
[entities]
Protein

[relations]
Equiv    Arg1:Protein, Arg2:Protein, <REL-TYPE>:symmetric-transitive

[events]
Protein_binding|GO:0005515    Theme+:Protein
Gene_expression|GO:0010467    Theme:Protein

[attributes]
Negation    Arg:<EVENT>
Speculation    Arg:<EVENT>
"""

__DEFAULT_VISUAL = """
[labels]
Protein | Protein | Pro | P
Protein_binding | Protein binding | Binding | Bind
Gene_expression | Gene expression | Expression | Exp
Theme | Theme | Th

[drawing]
Protein    bgColor:#7fa2ff
SPAN_DEFAULT    fgColor:black, bgColor:lightgreen, borderColor:black
ARC_DEFAULT    color:black
ATTRIBUTE_DEFAULT    glyph:*
"""

__DEFAULT_TOOLS = """
[search]
google     <URL>:http://www.google.com/search?q=%s
"""

__DEFAULT_KB_SHORTCUTS = """
P    Protein
"""

__DEFAULT_ACCESS_CONTROL = """
User-agent: *
Allow: /
Disallow: /hidden/

User-agent: guest
Disallow: /confidential/
"""

# Reserved strings with special meanings in configuration.
RESERVED_CONFIG_NAME = ["ANY", "ENTITY", "RELATION", "EVENT", "NONE",
                        "EMPTY", "REL-TYPE",
                        "URL", "URLBASE", "GLYPH-POS",
                        "DEFAULT", "NORM", "OVERLAP", "OVL-TYPE", "INHERIT"]
# TODO: "GLYPH-POS" is no longer used, warn if encountered and
# recommend to use "position" instead.
RESERVED_CONFIG_STRING = ["<%s>" % _n for _n in RESERVED_CONFIG_NAME]
