#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import path


class Filter(object):
    ''' Encapsulate include and exclude filtering of files to sync

    '''
    def __init__(self, include, exclude):
        if exclude is None:
            self.exclude = None
        else:
            self.exclude = [path.Path(p) for p in exclude]

        if include is None:
            self.include = None
        else:
            self.include = [path.Path(p) for p in include]

    def ignore_excuded(self, vector):
        if self.exclude is None:
            return False
        return str(vector) in self.exclude

    def ignore_not_included(self, vector):
        if self.include is None:
            return False
        return all(not vector.has_common_root_with(p) for p in self.include)

    def ignore(self, vector):
        return self.ignore_not_included(vector) or self.ignore_excuded(vector)

    def __str__(self):
        def combine(path_list):
            if path_list is None:
                return 'None'
            return ', '.join(str(p) for p in path_list)
        return "include: {}, exclude: {}".format(
            combine(self.include), combine(self.exclude))
