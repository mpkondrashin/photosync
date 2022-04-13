#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import unittest
import contextlib
import tempfile
import random
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sync_dmg


def mkdir(path):
    try:
        os.mkdir(path)
    except OSError as e:
        if e.errno != 17: raise


def run_cmmand(command):
    rc = os.system(command)
    if rc != 0:
        raise RuntimeError('{}: {}'.format(command, rc))


def create_dmg(dmg_path, size='1M'):
    basename = os.path.basename(dmg_path)
    volname = os.path.splitext(basename)[0]
    command = 'hdiutil create -ov -fs HFS+ -size {} -volname {} {}'.format(
        size, volname, dmg_path)
    #print(command)
    run_cmmand(command)


def attach_dmg(file_name, mount_point):
    command = "hdiutil attach {} -mountpoint {}".format(
        file_name, mount_point
    )
    #print(command)
    run_cmmand(command)


def detach_dmg(mount_point):
    command = "hdiutil detach {}".format(mount_point)
    run_cmmand(command)


'''
def create_attach_dmg(file_name, mount_point):
    create_dmg(file_name)
    mkdir(mount_point)
    attach_dmg(file_name, mount_point)

@contextlib.contextmanager
def dmg(file_name):
    tmp = tempfile.mkdtemp(prefix='tmp_test_sync_dmg_')
    create_attach_dmg(file_name, tmp)
    yield tmp
    detach_dmg(tmp)
    os.rmdir(tmp)
'''
@contextlib.contextmanager
def mount_dmg(file_name):
    tmp = tempfile.mkdtemp(prefix='tmp_test_sync_dmg_')
    attach_dmg(file_name, tmp)
    try:
        yield tmp
    finally:
        detach_dmg(tmp)
        os.rmdir(tmp)

def create_random_file(file_name, size):
    block_size = 1024*4
    with open('/dev/random', 'rb') as rfp:
        with open(file_name, 'wb') as ofp:
            for n in range(size // block_size):
                ofp.write(rfp.read(block_size))


@contextlib.contextmanager
def captured_output():
    new_out, new_err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TestSyncScope(unittest.TestCase):

    TEST_FOLDER = 'tmp_test_sync_dmg'

    LOC_DMG = os.path.join(TEST_FOLDER, 'local.dmg')
    REM_DMG = os.path.join(TEST_FOLDER, 'remote.dmg')

    def setUp(self):
        mkdir(self.TEST_FOLDER)

    def tearDown(self):
        shutil.rmtree(self.TEST_FOLDER)
        #pass

    @unittest.skip("working")
    def test_sync(self):
        create_dmg(self.LOC_DMG)
        create_dmg(self.REM_DMG)
        with mount_dmg(self.LOC_DMG) as mount_point:
            os.mkdir(os.path.join(mount_point, 'folder'))
        sync_dmg.SYNC_DEFAULT_PARAMETER['yes'] = True
        sync_dmg.main(self.LOC_DMG, self.REM_DMG, password='')
        with mount_dmg(self.REM_DMG) as mount_point:
            self.assertTrue(os.path.isdir(os.path.join(mount_point, 'folder')))

    def test_full_volume(self):
        size = 1024*1024*3 // 2
        big_file = 'bigfile.dat'
        create_dmg(self.LOC_DMG, '2M')
        create_dmg(self.REM_DMG, '1M')
        with mount_dmg(self.LOC_DMG) as mount_point:
            big_file_path = os.path.join(mount_point, big_file)
            create_random_file(big_file_path, size)
        sync_dmg.SYNC_DEFAULT_PARAMETER['yes'] = True
        with self.assertRaisesRegex(OSError, '\[Errno 28\] No space left on device'):
            sync_dmg.main(self.LOC_DMG, self.REM_DMG, password='')

        with mount_dmg(self.REM_DMG) as mount_point:
            big_file_path = os.path.join(mount_point, big_file)
            self.assertFalse(os.path.isfile(big_file_path))


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    itersuite = unittest.TestLoader().loadTestsFromTestCase(TestSyncScope)
    runner.run(itersuite)
    #sys.exit(unittest.main(buffer=True))
