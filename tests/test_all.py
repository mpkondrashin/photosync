#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import subprocess as sp
import fnmatch

def my_folder():
    return os.path.abspath(os.path.dirname(__file__))


def run_test(script):
    print('TEST: {}'.format(script))
    command = ['python', script]
    process = sp.Popen(command, stderr=sp.PIPE, stdout=sp.PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    return (exit_code, output + err)


def main():
    result = []
    mf = my_folder()
    for f in os.listdir(mf):
        if f == os.path.basename(__file__):
            continue
        if fnmatch.fnmatch(f, 'test_*.py'):
            rc, output = run_test(os.path.join(mf, f))
            if rc != 0:
                print(output)
            result.append((rc, f))
    for rc, f in result:
        print('RESULT for {}: {}'.format(f, rc))
    return any([rc != 0 for rc, __ in result])


if __name__ == '__main__':
    sys.exit(main())
