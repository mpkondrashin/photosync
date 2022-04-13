#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import stat
import os
import sys
import shutil
import subprocess as sp
import tempfile
import getpass
import contextlib

import photo

#password = 'unknown'

SYNC_DEFAULT_PARAMETER = dict(
    content=False,
    block_size=2048,
    include=[],
    include_file=[],
    ignore=['.fseventsd', '.Trashes', '.TemporaryItems'],
    ignore_file=[],
    subdir="",
    noprotection=True,
    nohash=True,
    repair=None,
    yes=False,
    warnings=None
)


@contextlib.contextmanager
def temp_dir():
    path = tempfile.mkdtemp()  #dir='mnt')
    try:
        yield path
    finally:
        shutil.rmtree(path)


def run_command(command, input=None):
    #print("run_command({})".format(" ".join(command)))
    process = sp.Popen(command, stderr=sp.PIPE, stdout=sp.PIPE, stdin=sp.PIPE)
    if input:
        input = input.encode('utf-8')
    (output, err) = process.communicate(input=input)
    exit_code = process.wait()
    if exit_code != 0:
        raise RuntimeError("'{}' returned exit code {}: {}".format(
                " ".join(command), exit_code, err))
    return output


@contextlib.contextmanager
def mount_container(dmg_path, password):
    with temp_dir() as mount_point:
        command = [
            'hdiutil', 'attach', '-stdinpass', '-mountpoint', mount_point, dmg_path
        ]
        run_command(command, input=password)
        try:
            yield mount_point
        finally:
            print('detach {}'.format(dmg_path))
            command = [
                'hdiutil', 'detach', mount_point
            ]
            run_command(command)


def sync(source, target):
    parameters = SYNC_DEFAULT_PARAMETER
    parameters['source'] = source
    parameters['target'] = target
    return photo.do_sync(parameters)


def main(source_container, target_container, password=None):
    """    if not os.path.isdir(mount_point):
        print('{}: directory does not exist'.format(mount_point))
        return
    """
    try:
        if password is None:
            password = getpass.getpass()
        with mount_container(source_container, password) as source:
            with mount_container(target_container, password) as target:
                return sync(source, target)
    except RuntimeError as e:
        print("{}".format(e))
        return 5


if __name__ == '__main__':
    if len(sys.argv) != 3   :
        print('Usage: {} <source> <target>'.format(sys.argv[0]))
        sys.exit(1)
    sys.exit(main(sys.argv[1], sys.argv[2]))
