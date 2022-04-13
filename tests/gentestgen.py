#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
    Pack given folder, by creating registry of files and back generating procedure

    1. Scan inventory for files
    2. Scan given folder and for each found file:
    2.1 If file does not present in inventory - put it there
    2.2 Save path, permissions, filename, flags, mtime
    2.3 Generate reproduce script


"""
import os
import stat
import sys
import hashlib
import shutil
import time

ignore = ('.DS_Store',)

UF_TRACKED = 0x40


def hex_hash(path):
    if os.path.islink(path):
        data = os.readlink(path).encode()
    elif os.path.isfile(path):
        data = open(path, 'rb').read()
    else:
        raise RuntimeError('Unknown file type: {}'.format(path))
    return hashlib.md5(data).hexdigest()


def copy(src, dst):
    if os.path.islink(src):
        linkto = os.readlink(src)
        os.symlink(linkto, dst)
    else:
        shutil.copyfile(src, dst)


def is_fifo(path):
    return stat.S_ISFIFO(os.stat(path).st_mode)


class Inventory(object):
    def __init__(self, folder):
        self.folder = folder
        self.inventory = dict()
        self.load()

    def load(self):
        if not os.path.isdir(self.folder):
            print('Folder "{}" not found. Creating empty'
                  'inventory'.format(self.folder))
            os.mkdir(self.folder)
            return

        for f in os.listdir(self.folder):
            path = os.path.join(self.folder, f)
            hh = hex_hash(path)
            self.inventory[hh] = f
            #  print('Load {} - {}'.format(hh, f))
        print('Total file in inventory: {} files'.format(len(self.inventory)))

    def file_name_for_inventory(self, file_name):
        def file_name_with_suffix_iterator():
            yield file_name
            for n in range(10000):
                name, ext = os.path.splitext(file_name)
                yield "{}[{}]{}".format(name, n, ext)

        files_in_inventory = set(f.lower() for f in os.listdir(self.folder))
        for file_name_with_suffix in file_name_with_suffix_iterator():
            if file_name_with_suffix.lower() not in files_in_inventory:
                #print("{} not in {}".format(file_name_with_suffix, files_in_inventory))
                return file_name_with_suffix
        else:
            raise RuntimeError('Inventory overloaded by filename {}'.format(file_name))

    def path(self, path):
        hh = hex_hash(path)
        try:
            return os.path.join(self.folder, self.inventory[hh])
        except KeyError:
            #print('{} not found in {}'.format(hh, self.inventory))
            inventory_file_name = self.file_name_for_inventory(os.path.basename(path))
            inventory_file_path = os.path.join(self.folder, inventory_file_name)
            print('Add to inventory {}: {}'.format(hh, path))
            copy(path, inventory_file_path)
            self.inventory[hh] = inventory_file_name
        return inventory_file_path

    def calc_size(self):
        return sum([os.path.getsize(os.path.join(self.folder,f))
                    for f in os.listdir(self.folder) if os.path.isfile(os.path.join(self.folder, f))])


HEADER ='''\
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil


def copy_file(src, dst):
    shutil.copyfile(src, dst)


def file_attrib(path, atime, mtime, mode, flags):
    os.utime(path, (atime, mtime))
    os.lchmod(path, mode)
    if flags != 0:
        os.lchflags(path, flags)


def copy_symlink(src, dst):
    os.symlink(os.readlink(src), dst)


def symlink_attrib(path, mode, flags):
    os.lchmod(path, mode)
    if flags != 0:
        os.lchflags(path, flags)


def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != 17:
            raise


def folder_attrib(path, mode, flags):
    os.chmod(path, mode)
    if flags != 0:
        os.chflags(path, flags)


def mkfifo(path, mode):
    os.mkfifo(path, mode)


def link(src, dst):
    os.link(src, dst)

operations = (
'''


def mkdir(path):
    return '    (mkdir, {{"path": "{}"}}),\n'.format(path)


def dir_stat(path, st):
    return '    (folder_attrib, {{"path": "{}", "mode": 0o{:o}, "flags": 0x{:X}}}),\n'.format(
        path, stat.S_IMODE(st.st_mode), st.st_flags
    )


def mkfile(src, dst):
    return '    (copy_file, {{"src": "{}", "dst": "{}"}}),\n'.format(src, dst)


def mkfile_stat(path, st):
    mode = stat.S_IMODE(st.st_mode)
    return '    (file_attrib, {{"path": "{}", "atime": {}, "mtime": {}, "mode": 0o{:o}, "flags": 0x{:x}}}),\n'.format(
            path, int(st.st_atime), int(st.st_mtime), mode, st.st_flags & ~UF_TRACKED

        )


def mksymlink(src, dst):
    return '    (copy_symlink, {{"src": "{}", "dst": "{}"}}),\n'.format(src, dst)


def mksymlink_stat(path, st):
    mode = stat.S_IMODE(st.st_mode)
    return '    (symlink_attrib, {{"path": "{}", "mode": 0o{:o}, "flags": 0x{:x}}}),\n'.format(
            path, mode, st.st_flags & ~UF_TRACKED
        )


def mkfifo(path, st):
    mode = stat.S_IMODE(st.st_mode)
    return '    (mkfifo, {{"path": "{}", "mode": 0o{:o}}}),\n'.format(path, mode)


def mklink(src, dst):
    return '    (link, {{"src": "{}", "dst": "{}"}}),\n'.format(src, dst)


FOOTER='''\
)


def main():
    previous_percent = -1
    for n, (op, kwarg) in enumerate(operations):
        new_percent = 100*(n+1)/len(operations)
        if new_percent != previous_percent:
            print('{:.2}%'.format(new_percent))
            previous_percent = new_percent
        op(**kwarg)


if __name__ == '__main__':
    main()
'''


def generate_generator(inventory_folder, folder, output):
    inventory = Inventory(inventory_folder)
    stack = list()
    inodes = dict()
    size = 0

    with open(output, 'w') as stream_py:
        stream_py.write(HEADER)
        for root, dirs, files in os.walk(folder, topdown=True):
            print(root)
            dirs[:] = [d for d in dirs if d != 'test']
            for d in dirs:
                path = os.path.join(root, d)
                st = os.lstat(path)
                stream_py.write(mkdir(path))
                stack.append(dir_stat(path, st))
            for f in files:
                if f in ignore:
                    continue
                path = os.path.join(root, f)
                st = os.lstat(path)
                size += st.st_size
                if stat.S_ISREG(st.st_mode):
                    if st.st_nlink > 1:
                        if st.st_ino in inodes:
                            stream_py.write(mklink(inodes[st.st_ino], path))
                            continue
                        else:
                            inodes[st.st_ino] = path
                    stream_py.write(mkfile(inventory.path(path), path))
                    stack.append(mkfile_stat(path, st))
                elif stat.S_ISLNK(st.st_mode):
                    stream_py.write(mksymlink(inventory.path(path), path))
                    stack.append(mksymlink_stat(path, st))
                elif is_fifo(path):
                    stream_py.write(mkfifo(path, st))
                else:
                    raise RuntimeError('Unknown file type: {}'.format(path))
        for l in reversed(stack):
            stream_py.write(l)
        stream_py.write(FOOTER)

    print('Processed size is {:,}'.format(size))
    print('{} size is {:,}'.format(inventory_folder, inventory.calc_size()))


def main():
    output_script = 'generate.py'
    inventory_folder = 'inventory'
    generate_generator(inventory_folder=inventory_folder, folder='test', output=output_script)
    print('"{}" folder and "{}" script are generated'.format(inventory_folder, output_script))

if __name__ == '__main__':
    main()
