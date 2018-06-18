# -*- coding: utf-8; -*-

'''
Annotation statistics generation.

Author:     Pontus Stenetorp    <pontus is s u-tokyo ac jp>
Version:    2011-04-21
'''

# future
from __future__ import with_statement
from __future__ import absolute_import

# standard
from logging import info as log_info
from os import listdir
from os.path import isfile, getmtime
from os.path import join as path_join

# third party
from six.moves.cPickle import UnpicklingError  # pylint: disable=import-error, no-name-in-module
from six.moves.cPickle import dump as pickle_dump  # pylint: disable=import-error, no-name-in-module
from six.moves.cPickle import load as pickle_load  # pylint: disable=import-error, no-name-in-module


# arat
import config
from server import constants
from server.annotation import Annotations
from server.message import Messager
from server.projectconfig.commons import get_config_path, options_get_validation
from server.projectconfig import ProjectConfiguration
from server.verify_annotations import verify_annotation


# Constants
STATS_CACHE_FILE_NAME = '.stats_cache'
###


def _get_stat_cache_by_dir(directory):
    return path_join(directory, STATS_CACHE_FILE_NAME)


# TODO: Quick hack, prettify and use some sort of csv format

def _store_cache_stat(docstats, cache_file_path, directory):
    """
    Cache the statistics
    """
    try:
        with open(cache_file_path, 'wb') as cache_file:
            pickle_dump(docstats, cache_file,
                        protocol=constants.PICKLE_PROTOCOL)
    except IOError as exception:
        Messager.warning(
            "Could not write statistics cache file to directory %s: %s" % (directory, exception))


def _generate_stats(directory, base_names, stat_types, cache_file_path):
    """
    Generate the document statistics from scratch
    """
    log_info('generating statistics for "%s"' % directory)
    docstats = []
    for docname in base_names:
        with Annotations(path_join(directory, docname),
                         read_only=True) as ann_obj:
            tb_count = len([a for a in ann_obj.get_entities()])
            rel_count = (len([a for a in ann_obj.get_relations()]) +
                         len([a for a in ann_obj.get_equivs()]))
            event_count = len([a for a in ann_obj.get_events()])

            if options_get_validation(directory) == 'none':
                docstats.append([tb_count, rel_count, event_count])
            else:
                # verify and include verification issue count
                projectconf = ProjectConfiguration(directory)
                issues = verify_annotation(ann_obj, projectconf)
                issue_count = len(issues)
                docstats.append(
                    [tb_count, rel_count, event_count, issue_count])

    _store_cache_stat(docstats, cache_file_path, directory)

    return stat_types, docstats


def _need_regeneration(directory, cache_file_path, cache_mtime):
    """
    Check if cache is invalid and regeneration required
    """
    return (not isfile(cache_file_path)
            # Has config.py been changed?
            or getmtime(config.__file__) > cache_mtime
            # Any file has changed in the dir since the cache was generated
            or any(True for f in listdir(directory)
                   if (getmtime(path_join(directory, f)) > cache_mtime
                       # Ignore hidden files
                       and not f.startswith('.')))
            # The configuration is newer than the cache
            or getmtime(get_config_path(directory)) > cache_mtime)


def get_statistics(directory, base_names, use_cache=True):
    """
    Check if we have a cache of the costly satistics generation
    Also, only use it if no file is newer than the cache itself
    """
    cache_file_path = _get_stat_cache_by_dir(directory)

    try:
        cache_mtime = getmtime(cache_file_path)
    except OSError as exception:
        if exception.errno == 2:
            cache_mtime = -1
        else:
            raise

    try:
        if _need_regeneration(directory, cache_file_path, cache_mtime):
            generate = True
            docstats = []
        else:
            generate = False
            try:
                with open(cache_file_path, 'rb') as cache_file:
                    docstats = pickle_load(cache_file)
                if len(docstats) != len(base_names):
                    Messager.warning(
                        'Stats cache %s was incomplete; regenerating' % cache_file_path)
                    generate = True
                    docstats = []
            except UnpicklingError:
                # Corrupt data, re-generate
                Messager.warning(
                    'Stats cache %s was corrupted; regenerating' % cache_file_path, -1)
                generate = True
            except EOFError:
                # Corrupt data, re-generate
                generate = True
    except OSError as exception:
        Messager.warning(
            'Failed checking file modification times for stats cache check; regenerating')
        generate = True

    if not use_cache:
        generate = True

    # "header" and types
    stat_types = [("Entities", "int"), ("Relations", "int"), ("Events", "int")]

    if options_get_validation(directory) != 'none':
        stat_types.append(("Issues", "int"))

    if generate:
        stat_types, docstats = _generate_stats(
            directory, base_names, stat_types, cache_file_path)

    return stat_types, docstats
