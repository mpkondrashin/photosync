#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import time
import os
import fnmatch
import errno
import stat
#import unicodedata
import hashlib
import conf

f = open('performance.csv', 'w')
f.write("total;current;start;now;delta;performance;self.total - self.current;left\n")


class Progress(object):
    def __init__(self, total):
        self.total = total
        self.current = 0
        self.start = time.time()

    def time_left(self, amount):
        self.current += amount
        now = time.time()
        delta = now - self.start
        performance = self.current/delta
        if performance == 0:
            performance = 1
        left = (self.total - self.current)/performance
        f.write("{};{};{};{};{};{};{};{}\n".format(self.total,
            self.current,
            self.start, now, delta, performance, self.total - self.current, left))
        return int(left)
