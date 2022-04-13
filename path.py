#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import unicodedata
import errno
#import pathlib
import shutil
import fnmatch
from contextlib import contextmanager
import hashlib
#from itertools import izip


normalize = lambda x: unicodedata.normalize('NFC', x)


class Path(object):

    def __init__(self, path):
        if isinstance(path, str):
            self.path = normalize(path)
        elif isinstance(path, bytes):
            self.path = normalize(path.decode('utf-8'))
        elif isinstance(path, Path):
            self.path = path.path
        else:
            raise ValueError('Unsupported type ({}) of path: {}'.format(type(path), path))

    def __truediv__(self, other):
        if isinstance(other, Path):
            return Path(os.path.join(self.path, other.path))
        return self / Path(other)

    def __rtruediv__(self, other):
        return Path(os.path.join(other, self.path))

    def __eq__(self, other):
        if isinstance(other, Path):
            return self.path.lower() == other.path.lower()
        return self == Path(other)

    def equal(self, other):
        if isinstance(other, Path):
            return self.path == other.path
        return self.equal(Path(other))

    def __ne__(self, other):
        if isinstance(other, Path):
            return self.path.lower() != other.path.lower()
        return self != Path(other)

    def __lt__(self, other):
        if isinstance(other, Path):
            return self.path.lower() < other.path.lower()
        return self < Path(other)

    def __str__(self):
        return self.path #.encode('utf-8')

    def __contains__(self, item):
        return item in self.path

    def has_common_root_with(self, p):
        split_a = str(self).split(os.sep)
        split_b = str(p).split(os.sep)
        return all(a == b for a, b in zip(split_a, split_b))

    def onlyname(self):
        return os.path.splitext(str(self))[0]

    def ext(self):
        return os.path.splitext(str(self))[1]

    def changeext(self, ext):
        return Path(self.onlyname() + ext)

    def split(self):
        return map(Path, os.path.split(str(self)))

    def dirname(self):
        return Path(os.path.dirname(str(self)))

    def basename(self):
        return Path(os.path.basename(str(self)))

    def listdir(self):
        for f in os.listdir(str(self)):
            yield Path(f)

#    def count_files(self):
#        return sum((len(filenames) for _, _, filenames in os.walk(str(self))))

#        count = 0
#        for dirpath, dirnames, filenames in os.walk(str(self)):
#            count += len(filenames)
#        return count


    def isdir(self):
        return os.path.isdir(str(self))

    def islink(self):
        return os.path.islink(str(self))

    def fnmatch(self, mask):
        return fnmatch.fnmatch(str(self), mask)

    def startswith(self, match):
        # convert to str first!!!
        return match(self.path.split(os.sep)[0])

    def listfiles(self, include_files=None, exclude=None):
        def lf(folder):
            root = self / folder
            for each in os.listdir(str(root)):
                if exclude:
                    if any([fnmatch.fnmatch(str(each), mask) for mask in exclude]):
                        continue
                fpath = root / each
                if fpath.isdir():
                    for f in lf(folder / each):
                        yield f
                else:
                    if include_files:
                        if all([not fnmatch.fnmatch(str(each), mask) for mask in include_files]):
                            continue
                    yield folder / each
        for each in lf(Path('')):
            yield each

    def stat(self):
        st = os.lstat(str(self))
        return dict(mode=st.st_mode,
                    size=st.st_size,
                    flags=st.st_flags,
                    mtime=int(st.st_mtime),
                    nlink=st.st_nlink)

    def size(self):
        return self.stat()['size']

    def chflags(self, flags):
        os.chflags(str(self), flags)

    @contextmanager
    def open(self, mode = 'rb'):
        f = open(str(self), mode)
        yield f
        f.close()

    def contents(self):
        with self.open() as f:
            return f.read()

    def md5(self):
        return hashlib.md5(self.contents()).hexdigest()

    def remove(self):
        os.remove(str(self))

    def remove_if_exist(self):
        try:
            self.remove()
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    def rmtree(self):
        shutil.rmtree(str(self))

    def copy2(self, target):
        try:
            shutil.copy2(str(self), str(target))
        except OSError as e:
            if e.errno == errno.EINVAL:
                #   File "/usr/local/Cellar/python/3.7.4/Frameworks/Python.framework/Versions/3.7/lib/python3.7/shutil.py", line 226, in copystat
                #     lookup("chflags")(dst, st.st_flags, follow_symlinks=follow)
                # OSError: [Errno 22] Invalid argument: '/Volumes/Elements/photo/Albums/Документы/old/Загран новый/2017.12.19 Passport [2:2].pdf'
                # Meaning archive drive has exFAT file system that does not support chflags
                # though local filesystem & OS does
                return
            print('\nError while copying {} to {}'.format(self, target))
            target.remove_if_exist()
            raise

    def makedirs(self):
        os.makedirs(str(self))

    def copystat(self, dst):
        shutil.copystat(str(self), str(dst))

    def copytree(self, dst, ignore = None, progress = None):
        # shutil.copytree(str(self), str(target))
        dst.makedirs()
        for each in self.listdir():
            if ignore is not None and ignore(str(each)):
                continue
            if progress is not None:
                progress(str(each))
            srcname = self / each
            dstname = dst / each
            if srcname.islink():
                srcname.copy_link(dstname)
            elif srcname.isdir():
                srcname.copytree(dstname, ignore, progress)
            else:
                srcname.copy2(dstname)
        self.copystat(dst)

    def readlink(self):
        return os.readlink(str(self))

    def copy_link(self, target):
        os.symlink(self.readlink(), str(target))

    def rename(self, to):
        os.rename(str(self), str(to))
