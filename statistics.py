#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import stat
import os
import sys
from PIL import Image

def iterate_images_in_folder(folder):
    for f in os.listdir(folder):
        __, ext = os.path.splitext(f)
        if ext.lower() in ('.jpg', '.gif'):
            yield os.path.join(folder, f)

def iterate_folder(folder, level):
    for f in os.listdir(folder):
        path = os.path.join(folder, f)
        if os.path.isdir(path):
            if level == 1:
                for q in iterate_images_in_folder(path):
                    yield q
            else:
                for q in iterate_folder(path, level-1):
                    yield q


def statistics(folder, level):
    stat=[]
    for f in iterate_folder(folder, level):
        if '.raw' in f:
            continue
        index = int(os.path.getsize(f)/10000)
        #print("{} - {}".format(index, f))
        while len(stat) <= index:
            stat.append(0)
        if index in (0,1,2) or index >= 114:
            print("{} - {}".format(index, f))
        stat[index] += 1

    m = max(stat)
    for i, y in enumerate(stat):
        print("{}k\t{}\t{}".format(i*10, y, '#'*(int(y*120/m))))

if __name__ == "__main__":
    statistics(sys.argv[1], level=3)
    sys.exit(1)
