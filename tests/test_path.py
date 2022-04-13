#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import unittest
import tempfile
import stat


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from path import *


class TestPathClass(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(suffix="", prefix='path_test_', dir='.')
        self.test_dir = os.path.join(self.temp_dir, 'Новая папка')
        os.mkdir(self.test_dir)
        self.files_list = ['a.txt', 'b.txt', 'c.txt']
        self.first_file = os.path.join(self.test_dir, self.files_list[0])
        self.second_file = os.path.join(self.test_dir, self.files_list[1])
        self.file_contents = 'Some text data\n'.encode('utf-8')
        for name in self.files_list:
            fname = os.path.join(self.test_dir, name)
            with open(fname, 'wb') as f:
                f.write(self.file_contents)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_Path_init(self):
        self.assertEqual(str(Path('A')), 'A')
        self.assertEqual(str(Path(u'A')), 'A')
        self.assertEqual(str(Path(Path('A'))), 'A')
        with self.assertRaises(ValueError):
            Path(1)

    def test_Path_div(self):
        self.assertEqual(str(Path('A') / Path('B')), 'A/B')
        self.assertEqual(str(Path('A') / 'B'), 'A/B')

    def test_Path_rdiv(self):
        self.assertEqual(str('A' / Path('B')), 'A/B')

    def test_Path_eq(self):
        self.assertTrue(Path('A') == Path('A'))
        self.assertTrue(Path('A') == Path('a'))
        self.assertTrue(Path('Й') == Path('Й'))
        self.assertTrue(Path('Й') == Path('й'))

        self.assertFalse(Path('A') == Path('B'))
        self.assertFalse(Path('Й') == Path('Ю'))

        self.assertTrue(Path('A') == 'A')
        self.assertTrue(Path('A') == 'a')
        self.assertTrue(Path('Й') == 'Й')
        self.assertTrue(Path('Й') == 'й')

        self.assertFalse(Path('A') == 'B')
        self.assertFalse(Path('Й') == 'Ю')

    def test_Path_equal(self):
        self.assertTrue(Path('A').equal(Path('A')))
        self.assertTrue(Path('A').equal('A'))
        self.assertFalse(Path('A').equal(Path('a')))
        self.assertFalse(Path('A').equal('a'))

        self.assertTrue(Path('Й').equal(Path('Й')))
        self.assertTrue(Path('Й').equal('Й'))
        self.assertFalse(Path('Й').equal(Path('й')))
        self.assertFalse(Path('Й').equal('й'))

    def test_Path_ne(self):
        self.assertFalse(Path('A') != Path('A'))
        self.assertFalse(Path('A') != Path('a'))
        self.assertFalse(Path('Й') != Path('Й'))
        self.assertFalse(Path('Й') != Path('й'))

        self.assertTrue(Path('A') != Path('B'))
        self.assertTrue(Path('Й') != Path('Ю'))

        self.assertFalse(Path('A') != 'A')
        self.assertFalse(Path('A') != 'a')
        self.assertFalse(Path('Й') != 'Й')
        self.assertFalse(Path('Й') != 'й')

        self.assertTrue(Path('A') != 'B')
        self.assertTrue(Path('Й') != 'Ю')


    def test_Path_lt(self):

        self.assertFalse(Path('A') < Path('A'))
        self.assertTrue(Path('A') < Path('B'))
        self.assertFalse(Path('Й') < Path('Й'))
        self.assertTrue(Path('Й') < Path('К'))

        self.assertFalse(Path('A') < 'A')
        self.assertTrue(Path('A') < 'B')
        self.assertFalse(Path('Й') < 'Й')
        self.assertTrue(Path('Й') < 'К')

#        self.assertFalse('A' < Path('A'))

    def test_str(self):
        self.assertEqual(str(Path('по-русски')), 'по-русски')

    def test_has_common_root_with(self):
        a = Path('a/b')
        b = Path('a/b/c')
        c = Path('q/b/c/d')
        self.assertTrue(b.has_common_root_with(a))
        self.assertTrue(a.has_common_root_with(b))
        self.assertFalse(c.has_common_root_with(b))
        self.assertFalse(b.has_common_root_with(c))

    def test_onlyname(self):
        self.assertEqual(str(Path('/some/file/name.txt').onlyname()), '/some/file/name')

    def test_ext(self):
        self.assertEqual(str(Path('/some/file/name.txt').ext()), '.txt')

    def test_changeext(self):
        self.assertEqual(str(Path('/some/file/name.txt').changeext('.jpg')), '/some/file/name.jpg')

    def test_split(self):
        a = Path('/a/b/c')
        head, tail = a.split()
        self.assertEqual(str(head), '/a/b')
        self.assertEqual(str(tail), 'c')
        self.assertEqual(head, Path('/a/b'))
        self.assertEqual(tail, Path('c'))

    def test_dirname(self):
        self.assertEqual(str(Path('/some/file/name.txt').dirname()), '/some/file')

    def test_basename(self):
        self.assertEqual(str(Path('/some/file/name.txt').basename()), 'name.txt')

    def test_listdir(self):
        l = sorted([str(f) for f in Path(self.test_dir).listdir()])
        self.assertSequenceEqual(l, self.files_list)

    def test_fnmatch(self):
        a = Path('abc.txt')
        self.assertTrue(a.fnmatch('a*.txt'))
        self.assertTrue(a.fnmatch('abc.*'))
        self.assertFalse(a.fnmatch('abC.txt'))

    def test_startswith(self):
        a = Path('a.raw/x.jpg')
        b = Path('a.big/x.jpg')
        c = Path('a.jpg/x.jpg')
        d = Path('a.dot/x.jpg')
        match = lambda n: n.endswith(('.jpg', '.big', '.raw'))
        self.assertTrue(a.startswith(match))
        self.assertTrue(b.startswith(match))
        self.assertTrue(c.startswith(match))
        self.assertFalse(d.startswith(match))

    def test_listfiles(self):
        p = Path(self.temp_dir)
        l = sorted([f for f in p.listfiles(include_files=['*.txt'], exclude=['a.*'])])
        self.assertFalse(self.files_list[0] in l[0])
        self.assertTrue(self.files_list[1] in l[0])
        self.assertTrue(self.files_list[2] in l[1])

    def test_stat(self):
        st = Path(self.first_file).stat()
        self.assertEqual(st['size'], len(self.file_contents))

    def test_size(self):
        size = Path(self.first_file).size()
        self.assertEqual(size, len(self.file_contents))

    def test_chflags(self):
        a = Path(self.first_file)
        a.chflags(stat.UF_IMMUTABLE)
        self.assertEqual(a.stat()['flags'], stat.UF_IMMUTABLE)
        a.chflags(0)


    def test_open(self):
        p = Path(self.test_dir) / Path(self.files_list[0])
        with p.open('rb') as f:
            self.assertEqual(self.file_contents, f.read())

    def test_contents(self):
        p = Path(self.test_dir) / Path(self.files_list[0])
        self.assertEqual(self.file_contents, p.contents())

    def test_md5(self):
        p = Path(self.test_dir) / Path(self.files_list[0])
        #hash = "b6943a3a70098615d976f474e50ac5bb"
        hash = hashlib.md5(self.file_contents).hexdigest()
        self.assertEqual(hash, p.md5())

    def test_remove(self):
        Path(self.first_file).remove()
        self.assertFalse(os.path.exists(self.first_file))

    def test_remove_if_exists(self):
        self.assertTrue(os.path.exists(self.first_file))
        Path(self.first_file).remove_if_exist()
        self.assertFalse(os.path.exists(self.first_file))
        Path(self.first_file).remove_if_exist()
        st = os.stat(self.second_file)
        os.chflags(self.second_file, st.st_flags | stat.UF_IMMUTABLE)
        self.assertRaises(OSError, Path(self.second_file).remove_if_exist)
        os.chflags(self.second_file, st.st_flags & ~stat.UF_IMMUTABLE)


    def test_rmtree(self):
        Path(self.test_dir).rmtree()
        self.assertFalse(os.path.exists(self.test_dir))

    def test_copy2(self):
        os.chmod(self.first_file, 0o777)
        some_file = os.path.join(self.test_dir, 'q.txt')
        Path(self.first_file).copy2(some_file)
        with open(self.first_file) as ff:
            with open(some_file) as sf:
                self.assertEqual(ff.read(), sf.read())
        st = os.stat(some_file)
        self.assertEqual(st.st_mode, os.stat(self.first_file).st_mode)

    def test_makedirs(self):
        dirs = '/A/B'
        path = self.test_dir + dirs
        Path(path).makedirs()
        self.assertTrue(os.path.isdir(path))

    def test_copystat(self):
        os.chmod(self.second_file, 0)
        Path(self.first_file).copystat(Path(self.second_file))
        first = os.stat(self.first_file)
        second = os.stat(self.second_file)
        for a, b in zip(first[:1] + first[2:], second[:1] + second[2:]):
            self.assertEqual(a, b)

    def test_copytree(self):
        target = os.path.join(self.temp_dir, 'other_dir')
        Path(self.test_dir).copytree(Path(target))
        fpath = os.path.join(target, self.files_list[0])
        self.assertTrue(os.path.isfile(fpath))

    def test_readlink(self):
        link_name = os.path.join(self.test_dir, 'some_link.txt')
        os.symlink(self.first_file, link_name)
        self.assertEqual(Path(link_name).readlink(), self.first_file)

    def test_islink(self):
        link_name = os.path.join(self.test_dir, 'some_link.txt')
        os.symlink(self.first_file, link_name)
        self.assertTrue(Path(link_name).islink())

    def test_copylink(self):
        some_link_name = os.path.join(self.test_dir, 'some_link.txt')
        os.symlink(self.first_file, some_link_name)
        other_link_name = os.path.join(self.test_dir, 'other_link.txt')
        Path(some_link_name).copy_link(other_link_name)
        self.assertTrue(os.path.islink(some_link_name))
        self.assertTrue(os.path.islink(other_link_name))
        self.assertEqual(os.readlink(some_link_name), os.readlink(other_link_name))

    def test_rename(self):
        new_name = os.path.join(self.test_dir, 'abc.txt')
        Path(self.first_file).rename(new_name)
        self.assertFalse(os.path.exists(self.first_file))
        self.assertTrue(os.path.isfile(new_name))

if __name__ == '__main__':
    sys.exit(unittest.main())

