#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from changes import *


class TestSyncScope(unittest.TestCase):
    def setUp(self):
        self.scope = {'a': {'b': {}}}

    def test_add_first_path(self):
        scope = {}
        test_path = 'a/b'
        self.assertTrue(add(scope, test_path))
        after = paths(scope)
        self.assertEqual(after, test_path)

    def test_add_path(self):
        before = paths(self.scope)
        test_path = 'c/d'
        self.assertTrue(add(self.scope, test_path))
        after = paths(self.scope)
        self.assertEqual(after,"{}\n{}".format(before, test_path))

    def test_add_upper_path(self):
        test_path = 'a'
        self.assertTrue(add(self.scope, test_path))
        after = paths(self.scope)
        self.assertEqual(after, test_path)

    def test_ignore(self):
        before = paths(self.scope)
        test_path = 'a/b/c'
        self.assertFalse(add(self.scope, test_path))
        after = paths(self.scope)
        self.assertEqual(after, before)

    def test_write_read(self):
        test_path = 'c/d'
        add(self.scope, test_path)
        before = paths(self.scope)
        file_name = 'test_write_read.txt'
        write_to_file(self.scope, file_name)
        after = paths(read_from_file(file_name))
        self.assertEqual(before, after)

    def test_write(self):
        test_path = 'c/d'
        add(self.scope, test_path)
        file_name = 'test_write.txt'
        write_to_file(self.scope, file_name)
        with open(file_name) as f:
            after = f.read()
        should_be = '/a/b\n/c/d'
        self.assertEqual(should_be, after)

    def test_same_path_twice(self):
        scope = {}
        self.assertTrue(add(scope, 't'))
        self.assertFalse(add(scope, 't'))

    def test_empty_path(self):
        scope = {}
        self.assertFalse(add(scope,''))

    def test_same_path_twice_second(self):
        scope = {}
        self.assertTrue(add(scope, 'Users/michael/Documents/python/changesrecorder/tdd/tdd_new_file/folder'))
        self.assertFalse(add(scope, 'Users/michael/Documents/python/changesrecorder/tdd/tdd_new_file/folder/subfolder'))

    def test_to_text(self):
        self.assertEqual(to_text(self.scope), '/a/b')

if __name__ == '__main__':
    sys.exit(unittest.main())
