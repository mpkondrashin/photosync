#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
find . -type f -name \*.py -exec sed -i.bak 's|/usr/bin/env python3|/usr/bin/env python33|g' {} +
Sync folders using photo.py script and after getting sync scope
from changesrecorder
'''


import os
import sys
import subprocess as sp

import photo
import syncscope
import changes
import util

source = '~/Pictures/photo'
source = os.path.abspath(os.path.expanduser(source.rstrip('/')))
#target = '/Volumes/{}/photo'
CR_DIR = '/Users/michael/PycharmProjects/changesrecorder'
CR_DIR = '../changesrecorder'
SCOPE_DIR_NAME = 'scope'
SCOPE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), SCOPE_DIR_NAME)


CR = dict(
    script=os.path.join(CR_DIR, 'main.py'),
    conf=os.path.join(CR_DIR, 'changesrecorder.ini'),
    operation='download',  # should be 'download' and not 'peek' for real run
)

__my_ignore = [
    'Software/Scripts/PhotoSync/test',
    'Software/Scripts/PhotoSync/inventory',
    'Software/Scripts/PhotoSync/log.csv',
    'Software/Scripts/PhotoSync/warning_list.txt',
    'Software/Scripts/PhotoSync/.idea',
    'Software/Scripts/PhotoSync/GTG_TEST',
    'Software/Scripts/PhotoSync/repair_all.sh',
    'Software/Scripts/PhotoSync/scope',
    'Software/Scripts/PhotoSync/performance.csv',
]


def download_scope():
    command = [
        os.path.join(CR_DIR, 'main.py'),
        '--config',
        os.path.join(CR_DIR, 'changesrecorder.ini'),
        'download',  # should be 'download' for real run
        '-',
    ]
    process = sp.Popen(command, stderr=sp.PIPE, stdout=sp.PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    if exit_code != 0:
        raise RuntimeError("'{}' returned exit code {}: {}".format(
                " ".join(command), exit_code, output.decode('utf-8') + ' ' + err.decode('utf-8')))
    return output.decode('utf-8')


def download_scope_as_list(text):
    for p in text.split('\n'):
        if p.startswith(source):
            yield p[len(source)+1:]


def fix_scope_list(scope_list):
    for path in scope_list:
        if util.raw_archive_folder(path):
            yield os.path.dirname(path)
        else:
            yield path


def run_sync_2(disk, options_list, scope=''):
    """./photo.py sync /Users/michael/Pictures/photo /Volumes/WD/photo  -i Software/Scripts/PhotoSync/test -i Software/Scripts/PhotoSync/inventory -i Software/Scripts/PhotoSync/log.csv -i Software/Scripts/PhotoSync/warning_list.txt -i Software/Scripts/PhotoSync/.idea -i Software/Scripts/PhotoSync/GTG_TEST -i Software/Scripts/PhotoSync/repair_all.sh -i Software/Scripts/PhotoSync/scope -i Software/Scripts/PhotoSync/performance.csv -g ps_ignore.txt  -w warning_list.txt -r repair_all.sh "-p"
{'repair': 'repair_all.sh',
'nohash': False,
'target': '/Volumes/WD/photo',
 'warnings': 'warning_list.txt',
 'ignore_file': ['ps_ignore.txt'],
 'noprotection': True,
 'ignore': ['Software/Scripts/PhotoSync/test', ...],
 'source': '/Users/michael/Pictures/photo',
 'include_file': [],
 'include': [],
 'subdir': '',
 'time': None,
 'content': False,
 'yes': False,
 'block_size': 2048,
 'action': 'sync'}
"""


def add_path(file_name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)


def run_sync(disk, options_list, scope=''):
    parameters = dict(
        python=add_path('venv/bin/python'),
        photo_py=add_path('photo.py'),
        source=source,
        target=disk,
        options=' '.join('"{0}"'.format(w) for w in options_list),
        ignore='-g {}'.format(add_path('ps_ignore.txt')),
        #my_ignore=' -i ' + ' -i '.join(my_ignore),
        scope=scope,
    )
    photo_sync = '{python} {photo_py} sync {source} {target} {ignore} {scope} -w warning_list.txt -r repair_all.sh {options}'.format(**parameters)
    print(photo_sync)
    rc = os.system(photo_sync) // 256
    #print('RC: {}'.format(rc))
    if rc != 0:
        print('Error: {}'.format(rc))
    return rc


def get_scope(disk=None):
    text = download_scope()
    scope_list = list(download_scope_as_list(text))
#    print("scope_list\n{}\n".format(scope_list))
    scope_list_fixed = list(fix_scope_list(scope_list))
#    print("scope_list_fixed\n{}\n".format(scope_list_fixed))
    scope = syncscope.Scope(SCOPE_DIR, disk)
#    print("scope\n{}\n".format(scope))
    scope.add(scope_list_fixed)
#    print("combined\n{}\n".format(scope))
    return scope


def sync_with_scope(target_folder, options_list):
    #print("{}: sync_with_scope".format(__file__))
    disk = get_disk(target_folder)
    print('sync_with_scope: disk: {}'.format(disk))
    scope = get_scope(disk)
    print('Scope:\n{!r}'.format(scope))
    total_list = scope.get_shrink()
    if not total_list:
        answer = input('No changes since previous sync. Sync all? [Y/n]: ')
        if answer.lower() == 'n':
            return 2
    #print("scope.get()\n{}\n".format(total_list))
    if total_list:
        print("=== Sync scope ===\n{}\n==================".format(
            '\n'.join(total_list)
        ))
    if total_list:
        scope_opts = ''.join([' -n "{}"'.format(s) for s in total_list])
    else:
        scope_opts = ''
    #print("{}: about to run_sync".format(__file__))
    rc = run_sync(target_folder, options_list, scope_opts)
    #print("{}: run_sync rc = {}".format(__file__, rc))
    if rc == 0:
        #print("SAVING SCOPE")
        if not scope.done():
            print('Sync scope is empty')

    print('Scope after:\n{!r}'.format(scope))
    return rc


def peek_sync():
    scope = get_scope()
    print(repr(scope))


def get_disk(path):
    print('get_disk({})'.format(path))
    return os.path.basename(os.path.dirname(path))


def main():
#    print(os.getcwd())
    if len(sys.argv) == 1:
        print('Usage {} [-s] <path to photo> [options]'.format(sys.argv[0]))
        print('-s -- sync without scope')
        print('-v -- view scope and exit')
        return 1
    if sys.argv[1] == '-s':
        return run_sync(sys.argv[2], sys.argv[3:])
    if sys.argv[1] == '-v':
        return peek_sync()
    else:
        return sync_with_scope(sys.argv[1], sys.argv[2:])


if __name__ == '__main__':
    sys.exit(main())
