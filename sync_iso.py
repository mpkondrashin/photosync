#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import stat
import os
import sys
import shutil
import subprocess
import tempfile
import getpass
import photo

mnt = 'mnt'
truecrypt_path = '/Applications/TrueCrypt.app/Contents/MacOS/TrueCrypt'
password = 'unknown'

class TempDir(object):

    def __enter__(self):
        self.path = tempfile.mkdtemp(dir='mnt')
        return self.path

    def __exit__(self, *args):
        shutil.rmtree(self.path)
        pass


def run_command(command):
    process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    (output, err) = process.communicate()
    exitCode = process.wait()
    if exitCode != 0:
        raise RuntimeError("'{}' returned exit code {}: {}".format(
                " ".join(command), exitCode, err))
    return output


class MountContainer(object):

    def __init__(self, path, mount_point_dir, mount_point_name):
        self.path = path
        self.mount_point = os.path.join(mount_point_dir, mount_point_name)

    def __enter__(self):
        os.mkdir(self.mount_point)
        command = [truecrypt_path,
                   '--text',
                   '--mount',
                   '--keyfiles=',
                   '--protect-hidden=no',
                   '--password={}'.format(password),
                   self.path,
                   self.mount_point]
        print('Mount {}'.format(self.path))
        run_command(command)
        return self.mount_point

    def __exit__(self, *args):
        command = [truecrypt_path,
                   '--dismount',
                   self.path]
        print('Dismount {}'.format(self.path))
        run_command(command)


def sync(source, target):
    return photo.do_sync(source=source,
                       target=target,
                       noprotect=True,
                       nohash=True,
                       subdir="",
                       ignore=['.fseventsd'],
                       warnings=None,
                       yes=False,
                       content=False,
                       block_size=2*1024)


def main(source_container, target_container):
    if not os.path.isdir(mnt):
        print('{}: directory does not exist'.format(mnt))
        return
    with TempDir() as path:
        with MountContainer(source_container, path, 'source') as source:
            with MountContainer(target_container, path, 'target') as target:
                return sync(source, target)


if __name__ == '__main__':
    if len(sys.argv) != 3   :
        print('Usage: {} <source> <target>'.format(sys.argv[0]))
        sys.exit(1)
    password = getpass.getpass()
    main(sys.argv[1], sys.argv[2])


#hdiutil create -volname WhatYouWantTheDiskToBeNamed -srcfolder /path/to/the/folder/you/want/to/create -ov -format UDZO name.dmg

