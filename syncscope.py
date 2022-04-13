#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import yaml
import errno

import changes


MAX_BACKUP_DRIVES = 3


def make_existing_dir(path):
    try:
        os.mkdir(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


class Scope(object):
    #SCOPE_DIR_NAME = 'scope'
    #SCOPE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), SCOPE_DIR_NAME)

    def __init__(self, folder, drive):
        self.folder = folder
        self.drive = drive
        self.data = dict()
        self.load()

    def is_empty(self):
        return not bool(self.data)

    #@classmethod
    def scope_file_name(self):
        make_existing_dir(self.folder)
        return os.path.join(self.folder, 'scope.yml')

    def load(self):
        try:
            with open(self.scope_file_name()) as f:
                # encoding = 'utf8'
                self.data = yaml.load(f)
                print('LOAD: {}'.format(self.data))
        except IOError as e:
            if e.errno != errno.ENOENT:
                raise

    def save(self):
        with open(self.scope_file_name(), 'w') as f:
            yaml.dump(self.data, f)

    def get(self):
        return [path for path, drives in self.data.items()
                if self.drive not in drives]

    def iter_for_drive(self):
        for path, drives in self.data.items():
            if self.drive not in drives:
                yield path

    def get_shrink(self):
        sc = changes.Scope()
        for p in self.get():
            changes.add(sc, p)
        return list(changes.iterate_paths(sc))

    def add(self, paths):
        for p in paths:
            self.data[p] = set()
        self.save()

    def done(self):
        for d in self.data:
            self.data[d].add(self.drive)
            #print('[DEBUG: syncscope.py: Scope.done()] Add {} to {}'.format(d, self.drive))
        self.data = {k: v for k, v in self.data.items()
                     if len(v) < MAX_BACKUP_DRIVES}
        #print('[DEBUG: syncscope.py: Scope.done()] Result: {}'.format(self.data))
        self.save()
        return bool(self.data)

    def __repr__(self):
        all_disks_set = set()
        for path, disks in self.data.items():
            all_disks_set.update(disks)
        disks_list = list(all_disks_set)
        disks_list.sort()
        while len(disks_list) < 3:
            disks_list.append("")
        width = max(len(d) for d in disks_list)
        if width == 0:
            width = 1
        result = list()
        for path, disks_set in self.data.items():
            mark = list()
            for d in disks_list:
                 mark.append(d if d in disks_set else "")
            result.append("{:{width}} | {:{width}} | {:{width}}: {}".format(
                mark[0],mark[1], mark[2], path, width=width))
        return "\n".join(result)
