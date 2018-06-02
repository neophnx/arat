
# -*- coding: utf-8 -*-
"""
Created on Sat Jun  2 06:19:53 2018

@author: phnx
"""
import unittest
from tempfile import mkdtemp
from shutil import rmtree
from time import sleep
from os import listdir
from os.path import join as join_path
from datetime import timedelta

import tests_common
import backup



    

    
def _backups(dir):
    return len([f for f in listdir(dir)
        if f.endswith('.' + backup.TAR_GZ_SUFFIX)])

#TODO: Use a wrapped back-up, as it is now it is easy to mess up the paths
class BackupTest(unittest.TestCase):
    dummy_filename = 'dummy'

    def setUp(self):
        self.tmp_dir = mkdtemp()
        self.data_dir = mkdtemp()
        self.dummy_path = join_path(self.data_dir,
                BackupTest.dummy_filename)
        with open(self.dummy_path, 'w') as _:
            pass

    def tearDown(self):
        rmtree(self.tmp_dir)
        rmtree(self.data_dir)

    def test_01_empty(self):
        backup.backup(backup_dir=self.tmp_dir, data_dir=self.data_dir)
        self.assertTrue(_backups(self.tmp_dir),
                'no back-up was created upon empty backup dir')

    def test_02_no_change(self):
        backup.backup(backup_dir=self.tmp_dir, data_dir=self.data_dir)
        sleep(3)
        backup.backup(min_interval=timedelta(seconds=60),
                backup_dir=self.tmp_dir, data_dir=self.data_dir)
        self.assertTrue(_backups(self.tmp_dir) == 1,
                'additional back-up created although no file changed')

    def test_03_delay(self):
        backup.backup(backup_dir=self.tmp_dir, data_dir=self.data_dir)
        backup.backup(min_interval=timedelta(days=365),
                backup_dir=self.tmp_dir, data_dir=self.data_dir)
        self.assertTrue(_backups(self.tmp_dir) == 1,
                'additional backup created although delay had not expired')


    def test_04_expired_delay(self):
        backup.backup(backup_dir=self.tmp_dir, data_dir=self.data_dir)
        sleep(1.5)
        with open(self.dummy_path, 'w') as dummy_file:
            dummy_file.write('This is a change for a change')
        sleep(3)
        backup.backup(min_interval=timedelta(seconds=1),
                backup_dir=self.tmp_dir, data_dir=self.data_dir)
        self.assertTrue(_backups(self.tmp_dir) == 2,
                'no additional back-up was created after delay expired')


