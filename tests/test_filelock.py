#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  2 06:47:34 2018

@author: phnx
"""
from __future__ import absolute_import
import unittest
from multiprocessing import Process
from os import rmdir
from os.path import join, isfile
from tempfile import mkdtemp
from os import (remove, read, fsync, open, close, write, getpid,
        O_CREAT, O_EXCL, O_RDWR, O_RDONLY)
from time import sleep

import tests_common
import filelock


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class TestFileLock(unittest.TestCase):
    def setUp(self):
        self._temp_dir = mkdtemp()
        self._lock_file_path = join(self._temp_dir, 'lock.file')

    def tearDown(self):
        try:
            remove(self._lock_file_path)
        except OSError:
            pass # It just didn't exist
        rmdir(self._temp_dir)

    def test_with(self):
        '''
        Tests do-with functionallity
        '''
        with filelock.file_lock(self._lock_file_path):
            sleep(1)
        sleep(0.1) # Make sure the remove is in effect
        self.assertFalse(isfile(self._lock_file_path))

    def test_exception(self):
        '''
        Tests if the lock-file does not remain if an exception occurs.
        '''
        try:
            with filelock.file_lock(self._lock_file_path):
                raise Exception('Breaking out')
        except Exception:
            pass

        self.assertFalse(isfile(self._lock_file_path))

    def test_timeout(self):
        '''
        Test if a timeout is reached.
        '''
        # Use an impossible timeout
        try:
            with filelock.file_lock(self._lock_file_path, timeout=-1):
                pass
            self.assertTrue(False, 'Should not reach this point')
        except filelock.FileLockTimeoutError:
            pass

    def test_lock(self):
        '''
        Test if a lock is indeed in place.
        '''
        def process_task(path):
            with filelock.file_lock(path):
                sleep(1)
            return 0

        process = Process(target=process_task,
                args=[self._lock_file_path])
        process.start()
        sleep(0.5) # Make sure it reaches the disk
        self.assertTrue(isfile(self._lock_file_path))
        sleep(1)

    def _fake_crash_other_process(self):
        '''
        Helper method to emulate a forced computer shutdown that leaves a
        lock-file intact.

        In theory the PID can have ended up being re-used at a later point
        but the likelihood of this can be considered to be low.
        '''
        def process_task(path):
            fd = open(path, O_CREAT | O_RDWR)
            try:
                write(fd, str(getpid()))
            finally:
                close(fd)
            return 0

        process = Process(target=process_task,
                args=[self._lock_file_path])
        process.start()
        while process.is_alive():
            sleep(0.1)
        return process.pid

    def test_crash(self):
        '''
        Test that the fake crash mechanism is working.
        '''
        pid = self._fake_crash_other_process()
        self.assertTrue(isfile(self._lock_file_path))
        self.assertTrue(pid == int(
            read(open(self._lock_file_path, O_RDONLY), 255)))#XXX: Close

    ###
    def test_pid_disallow(self):
        '''
        Test if stale-lock files are respected if disallow policy is set.
        '''
        self._fake_crash_other_process()
        try:
            with filelock.file_lock(self._lock_file_path, pid_policy=filelock.PID_DISALLOW):
                self.assertTrue(False, 'Should not reach this point')
        except filelock.FileLockTimeoutError:
            pass

    def test_pid_warn(self):
        '''
        Test if a stale lock-filk causes a warning to stderr and then is
        ignored if the warn policy is set.
        '''
        self._fake_crash_other_process()
        err_output = StringIO()
        try:
            with filelock.file_lock(self._lock_file_path, pid_policy=filelock.PID_WARN,
                    err_output=err_output):
                pass
        except filelock.FileLockTimeoutError:
            self.assertTrue(False, 'Should not reach this point')
        err_output.seek(0)
        self.assertTrue(err_output.read(), 'No output although warn set')

    def test_pid_allow(self):
        '''
        Test if a stale lock-file is ignored and un-reported if the allow
        policy has been set.
        '''
        self._fake_crash_other_process()
        err_output = StringIO()
        try:
            with filelock.file_lock(self._lock_file_path, pid_policy=filelock.PID_ALLOW,
                    err_output=err_output):
                pass
        except filelock.FileLockTimeoutError:
            self.assertTrue(False, 'Should not reach this point')
        err_output.seek(0)
        self.assertFalse(err_output.read(), 'Output although allow set')

