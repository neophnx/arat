'''
json wrapper to be used instead of a direct call.

Author:     Pontus Stenetorp    <pontus is s u-tokyo ac jp>
Version:    2011-04-21
'''

# use ultrajson if set up
from __future__ import absolute_import

try:
    # ultrajson doesn't have encoding

    from ujson import dumps as dumps
    from ujson import loads as loads


except ImportError:

    # fall back to native json, available since 2.6
    from json import dumps as dumps
    from json import loads as loads

    # Wrap the loads and dumps to expect utf-8
#    from functools import partial
#    dumps = partial(dumps, encoding='utf-8')  # , ensure_ascii=False)
#    loads = partial(loads, encoding='utf-8')  # , ensure_ascii=False)
