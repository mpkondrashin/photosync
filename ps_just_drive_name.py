#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Sync folders using photo.py script and after getting sync scope
from changesrecorder
'''

import os
import sys
import subprocess as sp

import photo
import syncscope


source = '~/Pictures/photo'
source = os.path.abspath(os.path.expanduser(source.rstrip('/')))
target = '/Volumes/{}/photo'
CR_DIR = '/Users/michael/PycharmProjects/changesrecorder'
#SCOPE_DIR = 'scope'

CR = dict(
    script=os.path.join(CR_DIR, 'main.py'),
    conf=os.path.join(CR_DIR, 'changesrecorder.ini'),
    operation='peek',  # should be download for real run
)

my_ignore = [
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
                " ".join(command), exit_code, output + ' ' + err))
    return output


def download_scope_as_list():
    scope_list = download_scope().split('\n')
    return [p[len(source)+1:] for p in scope_list
                  if p.startswith(source)]

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
        photo_py=add_path('photo.py'),
        source=source,
        target=target.format(disk),
        options=' '.join('"{0}"'.format(w) for w in options_list),
        ignore='-g {}'.format(add_path('ps_ignore.txt')),
        my_ignore=' -i ' + ' -i '.join(my_ignore),
        scope=scope,
    )
    photo_sync = '{photo_py} sync {source} {target} {my_ignore} {ignore} {scope} -w warning_list.txt -r repair_all.sh {options}'.format(**parameters)
    print(photo_sync)
    rc = os.system(photo_sync)
    if rc != 0:
        print('Error: {}'.format(rc))
    return rc


def get_scope(disk=None):
    scope_list = download_scope_as_list()
    #print("scope_list\n{}\n".format(scope_list))
    scope = syncscope.Scope(disk)
    scope.add(scope_list)
    return scope


def sync_with_scope(disk, options_list):
    scope = get_scope(disk)
    total_list = scope.get_shrink()
    print("scope.get()\n{}\n".format(total_list))
    if total_list:
        scope_opts = ''.join([' -n "{}"'.format(s) for s in total_list])
    else:
        scope_opts = ''
    rc = run_sync(disk, options_list, scope_opts)
    if rc == 0:
        scope.done()


def peek_sync():
    scope = get_scope()
    print(repr(scope))


def main():
    print(os.getcwd())
    if len(sys.argv) == 1:
        print('Usage {} [-s] diskname [options]'.format(sys.argv[0]))
        print('-s -- sync without scope')
        print('-v -- view scope and exit')
        return 1
    if sys.argv[1] == '-s':
        return run_sync(sys.argv[2], sys.argv[3:])
    if sys.argv[1] == '-p':
        return peek_sync()
    else:
        return sync_with_scope(sys.argv[1], sys.argv[2:])

if __name__ == '__main__':
    sys.exit(main())
