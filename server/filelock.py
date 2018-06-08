#!/usr/bin/env python


'''
Provides a stylish pythonic file-lock:

>>>    with('file.lock'):
...        pass

Inspired by: http://code.activestate.com/recipes/576572/

Is *NIX specific due to being forced to use ps (suggestions on how to avoid
this are welcome).

But with added timeout and PID check to spice it all up and avoid stale
lock-files. Also includes a few unittests.

Author:     Pontus Stenetorp    <pontus stenetorp se>
Version:    2009-12-26


Copyright (c) 2009, 2011, Pontus Stenetorp <pontus stenetorp se>

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

Copyright (C) 2008 by Aaron Gallagher

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

# future
from __future__ import with_statement
from __future__ import absolute_import
from __future__ import print_function

# standard
from contextlib import contextmanager
import os
import errno
import sys
from time import time, sleep

# Constants
# Disallow ignoring a lock-file although the PID is inactive
PID_DISALLOW = 1
# Ignore a lock-file if the noted PID is not running, but warn to stderr
PID_WARN = 2
# Ignore a lock-file if the noted PID is not running
PID_ALLOW = 3
###


class FileLockTimeoutError(Exception):
    '''
    Raised if a file-lock can not be acquired before the timeout is reached.
    '''

    def __init__(self, timeout):
        Exception.__init__(self)
        self.timeout = timeout

    def __str__(self):
        return 'Timed out when trying to acquire lock, waited (%d)s' % (
            self.timeout)


def _pid_exists(pid):
    """Check whether pid exists in the current process table.
    UNIX only.
    """
    if pid < 0:
        return False
    if pid == 0:
        # According to "man 2 kill" PID 0 refers to every process
        # in the process group of the calling process.
        # On certain systems 0 is a valid PID but we have no way
        # to know that in a portable fashion.
        raise ValueError('invalid PID 0')
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True


@contextmanager
def file_lock(path, wait=0.1, timeout=1,
              pid_policy=PID_DISALLOW, err_output=sys.stderr):
    '''
    Use the given path for a lock-file containing the PID of the process.
    If another lock request for the same file is requested, different policies
    can be set to determine how to handle it.

    Arguments:
    path - Path where to place the lock-file or where it is in place

    Keyword arguments:
    wait - Time to wait between attempts to lock the file
    timeout - Duration to attempt to lock the file until a timeout exception
        is raised
    pid_policy - A PID policy as found in the module, valid are PID_DISALLOW,
        PID_WARN and PID_ALLOW
    err_output - Where to print warning messages, for testing purposes
    '''
    start_time = time()
    while True:
        if time() - start_time > timeout:
            raise FileLockTimeoutError(timeout)
        try:
            file_desc = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.write(file_desc, str(os.getpid()).encode("ascii"))
            os.fsync(file_desc)
            break
        except OSError as exception:
            if exception.errno == errno.EEXIST:
                if pid_policy == PID_DISALLOW:
                    pass  # Standard, just do nothing
                elif pid_policy == PID_WARN or pid_policy == PID_ALLOW:
                    file_desc = os.open(path, os.O_RDONLY)
                    pid = int(os.read(file_desc, 255).decode(
                        'ascii', "replace"))
                    os.close(file_desc)
                    if not _pid_exists(pid):
                        # Stale lock-file
                        if pid_policy == PID_WARN:
                            print("Stale lock-file '%s', deleting" %
                                  path, file=err_output)
                        os.remove(path)
                        continue
                else:
                    assert False, 'Invalid pid_policy argument'
            else:
                raise
        sleep(wait)
    try:
        yield file_desc
    finally:
        os.close(file_desc)
        os.remove(path)
