#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

'''

1. a/b + c -> a/b, c
2. a/b + a -> a
3. a + a/b -> a

    #  #1: [a/b] + a -> [a]
    #  #2: [a/b] + c -> [a/b, c]
    #  #3: [a/b] + a/b/k -> [a/b]

This module is shared between changersrecorder and photosync projects
as link. Do not change its interface as in may break other project

'''

#import unittest
import os

Scope = dict

#import logging
#logger = logging.getLogger()


def is_empty(scope):
    return not bool(scope)


def add(scope, path):
#    logger.debug('ADD: {}'.format(path))
    if path == '':
        return False
#    p = path
    path = os.path.normpath(path)
#    print("add({},{}): Norm path: {}".format(scope, p, path))
    s = scope
    pi = iter(path.split(os.sep))
    for p in pi:
        try:
            s = s[p]
        except KeyError:
            break
    else:
        result = bool(s)
        s.clear()
        return result

    if scope and not s:
        return False
    s[p] = {}
    s = s[p]
    for q in pi:
        s[q] = {}
        s = s[q]
    return True


def iterate_paths(scope, prefix = ''):
    if not scope and prefix != '':
        yield prefix
        return
    for p, s in scope.items():
        for path in iterate_paths(s, os.path.join(prefix, p)):
            yield path


def paths(scope):
    return '\n'.join(iterate_paths(scope))


def count_paths(scope):
    return sum(1 for __ in iterate_paths(scope))


def read_from_stream(stream):
    result = {}
    for line in stream.readlines():
        line = line.strip().rstrip('/')
        add(result, line)
    return result


def read_from_file(file_name):
    with open(file_name) as f:
        return read_from_stream(f)

#import logging
#logger = logging.getLogger()


def to_text(scope):
    return '\n'.join(['/' + path for path in iterate_paths(scope)])


def write_to_stream(scope, stream):
    return stream.write(to_text(scope))


def write_to_file(scope, file_name):
    with open(file_name, 'w') as f:
        return write_to_stream(scope, f)

"""
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
        after = open(file_name).read()
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
    unittest.main()

"""
