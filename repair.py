#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import time
import os


first_template = """#!/bin/sh
# PhotoSync utility Repair script
# (c) 2017 by Mikhail Kondrashin mkondrashin@gmail.com
# Generated on {}
#
# BE CAREFUL! DO NOT RUN THIS SCRIPT IF YOU ARE NOT SURE
#
"""


__repair_lines = []


last_line ="""
echo "Done"
"""


def shell_script(file_name):
    first_line = first_template.format(time.ctime(time.time()))
    script = '\n'.join(__repair_lines)
    if script != '':
        open(file_name, 'w').write(first_line + script + last_line)
    else:
        try:
            os.remove(file_name)
        except OSError as e:
            if e.errno != 2:
                raise


def init():
    global __repair_lines
    __repair_lines = []


def __append(line):
    if line in __repair_lines:
        return
    __repair_lines.append(line)


def remove(path):
    __append('echo "rm {}"\nrm -d "{}"'.format(path.basename(), path))


def rename(path, new_name):
    __append('echo "mv {}"\nmv "{}" "{}/{}"'.format(path.basename(),
                                                    path, path.dirname(), new_name))


def copy(src, tgt):
    __append('echo "cp {}"\ncp -p -R "{}" "{}"'.format(src.basename(), src, tgt))


def touch(src, tgt):
    __append('echo "touch {}"\ntouch -r "{}" "{}"'.format(src.basename(), src, tgt))

