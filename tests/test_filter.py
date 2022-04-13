#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function


import os
import sys
import unittest
import tempfile
import stat


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from filter import *
from path import Path


class TestPathClass(unittest.TestCase):

    def setUp(self):
        self.a = Path('a')
        self.b = Path('b')
        self.ac = Path('a/c')

    def test_exclude(self):
        f = Filter(
            include=None,
            exclude=['a', 'z']
        )
        self.assertTrue(f.ignore(self.a))
        self.assertFalse(f.ignore(self.b))

    def test_include(self):
        f = Filter(
            include=['a', 'z'],
            exclude=None
        )
        self.assertFalse(f.ignore(self.a))
        self.assertTrue(f.ignore(self.b))

    def test_contradiction(self):
        f = Filter(
            include=['a'],
            exclude=['a']
        )
        self.assertTrue(f.ignore(self.a))

    def test_exclude_subfolder(self):
        f = Filter(
            include=['a','z'],
            exclude=['a/c', 'd/c']
        )
        self.assertFalse(f.ignore(self.a))
        self.assertTrue(f.ignore(self.ac))


if __name__ == '__main__':
    sys.exit(unittest.main())

