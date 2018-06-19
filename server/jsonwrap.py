'''
json wrapper to be used instead of a direct call.

Author:     Pontus Stenetorp    <pontus is s u-tokyo ac jp>
Version:    2011-04-21
'''

# in order to reduce code maintenance
# always use ultrajson
from ujson import dumps, loads# pylint: disable=E0611, W0611
