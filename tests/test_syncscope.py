#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import unittest
import os
import sys
import shutil
import errno

my_folder = os.path.dirname(__file__)
parent_folder = os.path.abspath(os.path.join(my_folder, '..'))
sys.path.insert(0, parent_folder)

from syncscope import *


class TestPathClass(unittest.TestCase):

    def setUp(self):
        self.test_folder = os.path.join(my_folder, 'scope_test')
        try:
            shutil.rmtree(self.test_folder)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
        self.scope = self.new_scope('NONAME')

    def new_scope(self, drive):
        return Scope(
            folder=self.test_folder,
            drive=drive
        )

    def tearDown(self):
        # rm tree scope_test
        pass

    def test_000_init(self):
        #self.init_test()
        self.assertEqual(self.scope.get(), [])

    def test_010_add(self):
        paths = ['a/b', 'c/d']
        self.scope.add(paths)
        self.assertEqual(self.scope.get(), paths)

    def test_020_done(self):
        paths = ['a/b', 'c/d']
        self.scope.add(paths)
        self.scope.done()
        self.assertEqual(self.scope.get(), [])

    def test_030_add_same_path(self):
        paths = ['a/b']
        self.scope.add(paths)
        self.scope.done()
        self.scope = self.new_scope('NONAME')
        self.scope.add(paths)
        self.assertEqual(self.scope.get(), paths)

    def test_050_save_load(self):
        paths = ['a/b', 'c/d']
        self.scope.add(paths)
        self.scope = self.new_scope('NONAME')
        self.assertEqual(self.scope.get(), paths)

    def test_060_sync_second_drive(self):
        paths_a = ['a/b', 'c/d']
        self.scope.add(paths_a)
        paths_b = ['e/f', 'g/h']
        b = self.new_scope('NONAME1')
        b.add(paths_b)
        self.assertEqual(set(b.get()), set(paths_a + paths_b))

    def test_070_sync_second_time(self):
        paths_a = ['a/b', 'c/d']
        self.scope.add(paths_a)
        self.scope.done()
        self.scope = self.new_scope('NONAME')
        paths_b = ['e/f', 'g/h']
        self.scope.add(paths_b)
        self.assertEqual(set(self.scope.get()), set(paths_b))

    def test_080_sync_second_drive_after_first(self):
        paths_a = ['a/b', 'c/d']
        self.scope.add(paths_a)
        self.scope.done()
        paths_b = ['e/f', 'g/h']
        b = self.new_scope('NONAME1')
        b.add(paths_b)
        b.save()
        self.assertEqual(set(b.get()), set(paths_a + paths_b))

    def test_090_sync_third_drive(self):
        paths_a = ['a/b', 'c/d']
        self.scope.add(paths_a)
        self.scope.done()
        paths_b = ['e/f', 'g/h']
        b = self.new_scope('NONAME1')
        b.add(paths_b)
        b.done()
        paths_c = ['i/j', 'k/l']
        c = self.new_scope('NONAME2')
        c.add(paths_c)
        self.assertEqual(set(c.get()), set(paths_a + paths_b + paths_c))

    def test_100_sync_second_then_first(self):
        a = self.new_scope('NONAME')
        paths_a = ['a/b', 'c/d']
        a.add(paths_a)
        a.done()
        b = self.new_scope('NONAME1')
        paths_b = ['e/f', 'g/h']
        b.add(paths_b)
        b.done()
        c = self.new_scope('NONAME')
        paths_c = ['i/j', 'k/l']
        c.add(paths_c)
        self.assertEqual(set(c.get()), set(paths_b + paths_c))

    def test_110_cleanup(self):
        a = self.new_scope('NONAME')
        paths_a = ['a/b']
        a.add(paths_a)
        a.done()
        b = self.new_scope('NONAME1')
        paths_b = ['c/d']
        b.add(paths_b)
        b.done()
        c = self.new_scope('NONAME2')
        paths_c = ['e/f']
        c.add(paths_c)
        c.done()
        d = self.new_scope('NONAME3')
        paths_d = ['g/h']
        d.add(paths_d)
        self.assertEqual(set(d.get()), set(paths_b + paths_c + paths_d))

    def test_120_shrink(self):
        a = self.new_scope('NONAME')
        paths_a = ['a/b/c/d']
        paths_b = ['a/b']
        a.add(paths_a)
        a.add(paths_b)
        self.assertEqual(set(a.get_shrink()), set(paths_b))


if __name__ == '__main__':
    sys.exit(unittest.main())
