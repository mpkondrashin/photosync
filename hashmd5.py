#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import hashlib

import util
import show
import conf
import path
'''
def CalcHash(path):
    #   print("CalcHash({})".format(path))
    data = open(path).read()
    return hashlib.md5(data).hexdigest()

def HashFilePath(path):
    return os.path.join(path, conf.HASH_FILE)

def IsHashed(path):
    hashFile = HashFilePath(path)
    return os.path.isfile(hashFile)
'''

"""
Problems:
1.
    Problem: Hash file is older than one of hashed files
    Action: warning with list of newer files
    Solution: rehash (delete hash file)
2.
    Problem: Hash file is missing hashes of some files
    Action: warning with list of extra files
    Solution: Hash these extra files <- this could me default ation without warning
3.
    Problem: Files are missing
    Action: warning with list of missing files
    Solution: remove these lines from hash or copy from other archive

These checked in sync.py:
4.
    Problem: Hash for file does not match
    Action: warning with list of files
    Solution: rehash files/copy from other archive
5.
    Problem: Hash files are missing
    Action: create hash files
6.
    Problem: one of hash files is missing
    Action: copy/warning
    Solution: rehash

7.  Problem: Hash files are different
    Action: warning
    Solution: remove one of them - manually
"""
'''
def ListWarnings(path, subdirs):
    if not os.path.isdir(path):
        RuntimeError('{} not directory'.format(path))
    hashFile = os.path.join(path, conf.HASH_FILE)
    hashFileMTime = os.path.getmtime(hashFile)

#    if not os.path.isfile(hashFile):
#        RuntimeError('{} is missing in {}'.format(conf.HASH_FILE, path))
    hashes = HashFileToDict(hashFile)

    files = util.FilesList(path, recursive = subdirs,
                                exclude=conf.IGNORE_FILE_MASKS + [conf.HASH_FILE])
    while files:
        f = files.pop()
        fpath = os.path.join(path,f)
        if f not in hashes: # if f.lower() not in set(k.lower() for k in hashes):
            # 3
            yield 'Not hashed: {}'.format(fpath)
        else:
            delta = os.path.getmtime(fpath) - hashFileMTime
            if delta > 0:
                # 1
                yield '{} is newer by{} than {}'.format(fpath, util.time_delta(delta), conf.HASH_FILE)
            del hashes[f]
    if not subdirs:
        for f in hashes.keys():
            if os.sep in f:
                del hashes[f]
    for f in hashes.keys():
        # 2
        yield 'Missing file: {}'.format(fpath)

def IterHashErrors(path, subdirs, hashFile = None):
    if not os.path.isdir(path):
        RuntimeError('{} not directory'.format(path))
    if not hashFile:
        hashFile = HashFilePath(path)
    if not os.path.isfile(hashFile):
        RuntimeError('{} is missing in {}'.format(conf.HASH_FILE, path))
    hashFileMTime = os.path.getmtime(hashFile)

    hashes = HashFileToDict(hashFile)

    files = util.FilesList(path, recursive = subdirs,
                                exclude=conf.IGNORE_FILE_MASKS + [conf.HASH_FILE])
    while files:
        f = files.pop()
        fpath = os.path.join(path,f)
        if f not in hashes: # if f.lower() not in set(k.lower() for k in hashes):
            # 3
            yield 'Not hashed: {}'.format(fpath)
        else:
            delta = os.path.getmtime(fpath) - hashFileMTime
            if delta > 0 and hashes[f] != CalcHash(fpath):
                yield '{} modified'.format(util.ShortenPath(fpath))

#            yield '{} is newer by{} than {}'.format(fpath, util.time_delta(delta), conf.HASH_FILE)
            del hashes[f]
    if not subdirs:
        for f in hashes.keys():
            if os.sep in f:
                del hashes[f]
    for f in hashes.keys():
        # 2
        yield 'Missing file: {}'.format(fpath)

'''

#def CalcHash(data):
#    return

def HashesToFile(hashes, fileName):
    with open(fileName, 'w') as f:
        for fname, hvalue in sorted(hashes.items(), key=lambda x: x[0]):
            f.write("{}  {}\n".format(hashes[fname], fname))

#        for fname, hvalue in hashes.iteritems():
#            f.write("{}  {}\n".format(hvalue, fname))
#exiftool -n -Orientation:2   20041211_213955_1715.jpg

def HashFileToDict(hashFilePath):
    hash = dict()
    with open(hashFilePath, 'r') as hf:
        for line in hf.readlines():
            line = line.strip()
            if line == "":
                continue
            h, f = line.split(' ', 1)
            p = path.Path(f.lstrip().rstrip())
            hash[str(p)] = h
    return hash

"""
def HashFileSize(hashFilePath):
    hd = HashFileToDict(hashFilePath)
    path, __ = os.path.split(hashFilePath)
    return sum([os.path.getsize(os.path.join(path, f)) for f in hd])

"""

'''
def SupportedFile(fileName):
    if fileName == conf.HASH_FILE:
        return False
    if util.ignore_file(fileName):
        return False
    return True
'''

'''
def HashDir(path, callback = None):
    hash = dict()
    for f in util.ListFiles(path, recursive = True, dirs = False,
                            exclude = [conf.HASH_FILE] + conf.IGNORE_FILE_MASKS):
        fpath = os.path.join(path, f)
        if callback:
            callback(fpath)
        hash[f] = CalcHash(fpath)
    hashFile = HashFilePath(path)
    HashesToFile(hash, hashFile)
    return hashFile


if __name__ == "__main__":
    #HashTree(sys.argv[1])
    if sys.argv[1] == 'hash':
        HashDir(sys.argv[2])
    else:
        print('unknown command')

'''
