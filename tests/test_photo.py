#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import traceback
import shutil
import fnmatch
import time


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import conf
from sync import Sync
import util
import photo
import repair

TESTS_DIR_DEFAULT = 'test'
TESTS_DIR_MUTATIONS = '../test'
TESTS_DIR = TESTS_DIR_DEFAULT if os.path.isdir(TESTS_DIR_DEFAULT) else TESTS_DIR_MUTATIONS

import stat

def stat_path(path):
    clear_uf_tracked_flag(path)
    st = os.lstat(path)
    return dict(mode=st.st_mode,
                size=st.st_size,
                flags=st.st_flags,
                mtime=int(st.st_mtime),
                nlink=st.st_nlink)

PATH_STACK = []
def chdir(folder):
    PATH_STACK.append(os.getcwd())
    os.chdir(folder)


def clear_uf_tracked_flag(path):
    UF_TRACKED = 0x40
    flags = os.lstat(path).st_flags
    if flags & UF_TRACKED:
        os.chflags(path, flags & ~UF_TRACKED)


def chdir_back():
    os.chdir(PATH_STACK.pop())


def list_dir(path):
    l1 = os.listdir(path)
    l2 = [f for f in l1
          if not any([fnmatch.fnmatch(f, pat)
                  for pat in conf.IGNORE_FILE_MASKS])]
    l3 = sorted(l2)
    return l3


def are_dir_trees_equal(dir1, dir2, mtime=True, nlink=True, flags=True):
#    print("are_dir_trees_equal({}, {})".format(dir1, dir2))
    if not os.path.isdir(dir1):
        print('{} - not directory'.format(dir1))
        return False
    if not os.path.isdir(dir2):
        print('{} - not directory'.format(dir2))
        return False
    d1 = list_dir(dir1)
#    print('A dir: {}'.format('|'.join(d1)))
    d2 = list_dir(dir2)
#    print('B dir: {}'.format('|'.join(d2)))

    if len(d1) != len(d2):
        print('length of {} and {} different.\ntest = {}\nshould be = {}'.format(dir1, dir2, d1, d2))
        #print(d1,d2)
        return False
    for a, b in zip(d1, d2):
        apath = os.path.join(dir1, a)
        bpath = os.path.join(dir2, b)
#        print('compare {} and {}'.format(apath, bpath))
        if a != b:
#            print("IN TEST " + ":".join("{:02x}".format(ord(c)) for c in a))
#            print("IN AFTER "  +":".join("{:02x}".format(ord(c)) for c in b))
            print("Files/Dirs '{}' != '{}' in dirs {} and {}".format(a, b, dir1, dir2))
            ahex = ":".join("{:02x}".format(ord(c)) for c in a)
            bhex = ":".join("{:02x}".format(ord(c)) for c in b)
            print("a = {}".format(ahex))
            print("b = {}".format(bhex))
            return False

        if os.path.isdir(apath):
            if not are_dir_trees_equal(apath, bpath, mtime, nlink):
                return False

        ast = stat_path(apath)
        bst = stat_path(bpath)
        if ast['mode'] != bst['mode']:
            print('Mode {} != {} ({:o} != {:o})'.format(apath, bpath, ast['mode'], bst['mode']))
            return False
        if not os.path.isdir(apath) and ast['size'] != bst['size']:
            print('Size {} (size = {}) != {} (size = {})'.format(apath, ast['size'], bpath, bst['size']))
            return False
        if flags and ast['flags'] != bst['flags']:
            print('Flags {} ({:X}) != {} ({:X})'.format(apath, ast['flags'], bpath, bst['flags']))
            return False
        #print('mtime: {} [{} - {}]'.format(mtime, apath, bpath))
        if mtime and ast['mtime'] != bst['mtime']:
            print('MTime {} ({}) != {} ({})'.format(apath, ast['mtime'], bpath, bst['mtime']))
#            print(os.getcwd())
#            print('MTime {} != {}'.format(ast['mtime'], bst['mtime']))
            return False
        if not os.path.isdir(apath) and nlink and ast['nlink'] != bst['nlink']:
            print('NLink {} != {}'.format(apath, bpath))
            return False
        if os.path.isfile(apath):
            if apath.endswith('.md5'):
                alines = set(open(apath).readlines())
                blines = set(open(bpath).readlines())
                if alines != blines:
                    print('Hash Content {} != {}'.format(apath, bpath))
                    return False
            else:
                if open(apath, 'rb').read() != open(bpath, 'rb').read():
                    print('Content {} != {}'.format(apath, bpath))
                    return False
        if os.path.islink(apath):
            alink = os.readlink(apath)
            blink = os.readlink(bpath)
            if alink != blink:
                print('Links differ: {} != {}'.format(alink, blink))
                return False
    return True


ROOT = 'tests/tests'

def loc_arc(folder):
    loc = os.path.join(folder, 'local')
    arc = os.path.join(folder, 'archive')
    return loc, arc


def get_ignore(folder):
    try:
        keys_fname = os.path.join(folder, '..', 'keys.txt')
        k = open(keys_fname,'r').read().split()
        result = []
        while k:
            if k[0] == '-i':
                del k[0]
                result.append(k[0])
            del k[0]
        return result
    except IOError:
        return []


def get_operation(folder):
    try:
        keys_fname = os.path.join(folder, 'keys.txt')
        k = open(keys_fname,'r').read().split()
        if 'hash' in k:
            return 'hash'
        elif 'check' in k:
            return 'check'
        else:
            return 'sync'
    except IOError:
        return 'sync'


def get_noprotect(folder):
    try:
        keys_fname = os.path.join(folder, '..', 'keys.txt')
        k = open(keys_fname,'r').read().split()
        return '-p' in k
    except IOError:
        return False


def get_nohash(folder):
    try:
        keys_fname = os.path.join(folder, '..', 'keys.txt')
        k = open(keys_fname,'r').read().split()
        return '-m' in k
    except IOError:
        return False


def run_sync(folder, label):
    try:
        ignore = get_ignore(folder)
        noprotect = get_noprotect(folder)
        nohash = get_nohash(folder)
        sync = Sync(*loc_arc(folder), vector='', ignore=ignore, noprotect=noprotect, nohash=nohash)
        print('[{}] Before'.format(label))
#        sync.trees()
        # sync.source.tree()
        #print('')
        #sync.target.tree()
        sync.sync_with_local()
        print('[{}] After'.format(label))
        sync.source.tree()
        print('')
        sync.target.tree()

        print('Clean')
        sync.source.cleanup()
        sync.source.tree()
        sync.target.cleanup()
        sync.target.tree()

        if sync.list_warnings():
            return sync
        else:
            print('[{}]: Operations:'.format(label))
            sync.operations.show()
            print('[{}] Sync go'.format(label))
            sync.go()
        print('[{}] Sync Done'.format(label))
        return sync
    except Exception as e:
        print(e)
        # print(sys.exc_info()[2])
        traceback.print_exc()
    return None


def cleanup():
    util.monster_delete('test')


def prepare():
    if os.path.isdir('raise_test'):
        return 'raise_test' # os.path.join(raise_test_path, 'archive')
    cleanup()
#    if JUST_CLEAN: return
    shutil.copytree('before', 'test', symlinks=True)
    return 'test'


def cmp_options():
    if os.path.isfile('cmp.py'):
        loc = {}
        exec(compile(open('cmp.py').read(), 'cmp.py', 'exec'), loc)
        #execfile('cmp.py', loc)
        return loc['CMP']
    else:
        return {}


def check_files(label):
    cmp = cmp_options()
    tl, ta = loc_arc('test')
    sl, sa = loc_arc('after')
    rc1 = are_dir_trees_equal(tl, sl, **cmp)
    if not rc1:
        print('[{}] Failed: local dirs differ'.format(label))
    rc2 = are_dir_trees_equal(ta, sa, **cmp)
    if not rc2:
        print('[{}] Failed: archive dirs differ'.format(label))
    if rc1 and rc2:
        print('[{}] Passed'.format(label))
        return True
    return False


def check(label, test_folder, rc):
    test_folder_warning = os.path.join(test_folder,'warnings_list.txt')
    if not match_masks_file('warning.txt', test_folder_warning, rc):
        return False
    if test_folder == 'raise_test':
        return True
    if not check_files(label):
        return False
    return True


def match_masks_file(masks_file_name, file_name, rc):
    def load_as_list(file_name):
        try:
            data = open(file_name, 'r').read().strip().split('\n')
            return [w for w in data if w != '']
        except IOError as e:
            return []

    we_list = load_as_list(masks_file_name)
    if we_list:
        if rc == 0:
            print("Return Code == 0, but expected warnings list is not empty")
            return False

    wg_list = load_as_list(file_name)

    for wg in range(len(wg_list)):
        for we in range(len(we_list)):
            if we_list[we] is None:
                continue
            if we_list[we][0] == '#':
                we_list[we] = None
                continue
            if fnmatch.fnmatch(wg_list[wg], we_list[we]):
                print('"{}" - found'.format(we_list[we]))
                wg_list[wg] = None
                we_list[we] = None
                break

    wg_list = [w for w in wg_list if w is not None]
    we_list = [w for w in we_list if w is not None]

    for g in wg_list:
        print('Extra warning: {}'.format(g))

    for e in we_list:
        print('Missing warning: {}'.format(e))

    return not bool(wg_list) and not bool(we_list)


def test_sync(args, label):
    test_folder = prepare()
    chdir(test_folder)
    rc = photo.do_sync(vars(args))

    """    rc = photo.do_sync(
            source=os.path.abspath(os.path.expanduser(args.source[0].rstrip('/'))),
            target=os.path.abspath(os.path.expanduser(args.target.rstrip('/'))),
            noprotect=args.noprotection,
            nohash=args.nohash,
            subdir=args.subdir,
            ignore=args.ignore,
            include=args.include,
            warnings=args.warnings,
            repair_script=args.repair,
            yes=args.yes,
            content=args.content,
            block_size=args.block_size)
    """
    if args.repair is not None and os.path.isfile(args.repair):
        print('{} found - executing'.format(args.repair))
        os.system('sh {}'.format(args.repair))
        repair.init()
    chdir_back()
    rc = check(label, test_folder, rc)
    if rc:
        pass
#        cleanup()
    return rc


def test_hash(args, label):
    rc = photo.do_hash_check(os.path.abspath(os.path.expanduser(args.target.rstrip('/'))),
                             warnings_file=args.warnings)
    return match_masks_file('warning.txt', args.warnings, rc)


def test_check( args, label):
    rc = photo.do_check(args.target, warnings_file=args.warnings)
    return match_masks_file('warning.txt', args.warnings, rc)


def test(path, args_list, label):
    print("[{}] Start".format(label))
    args = photo.parse_args(args_list)
    chdir(path)
    if args.action == 'sync':
        rc = test_sync(args, label)
    elif args.action == 'hash':
        rc = test_hash(args, label)
    elif args.action == 'check':
        rc = test_check(args, label)
    chdir_back()
    print("[{}] End".format(label))
    return rc


def list_test_dirs(path):
    l = sorted(os.listdir(path))
    for d in l:
        p = os.path.join(path, d)
        if not os.path.isdir(p):
            continue
        args = []
        args_txt = os.path.join(p, 'args.txt')
        if os.path.isfile(args_txt):
            args = open(args_txt).read().split()
        if d[0:3] == 'TDD':
            yield p, args
        else:
            for each, a in list_test_dirs(p):
                yield each, args + a


def run_tests(num=None, skip=[]):
    result = []
    total = 0
    errors = 0
    n = 0
    for p, args in list_test_dirs(TESTS_DIR):
        n += 1
        label = p.replace('_', ' ')
        total += 1
        start_time = time.time()
        if num is not None and total not in num or total in skip:
            r = 'skiped'
            smile = ':|'
            duration = '-----'
        else:
            rc = test(p, args, label)
            duration = "{: 2.2f}".format(time.time() - start_time)
            if rc:
                r = "passed"
                smile = ':)'
            else:
                errors += 1
                r = "failed " + '*' * 40
                smile = ':('
                msg = "[{}] {} {} - {}".format(duration, smile, label, r)
                open('failed_rule.txt', 'w').write(msg)
        msg = "[{}] {} {} - {}".format(duration, smile, label , r)
        result.append( msg )
#        if errors > 0:
#            open('failed_rule.txt','w').write(msg)
        if TESTS_DIR == TESTS_DIR_MUTATIONS and errors > 0:
            break

    print('Tests:')
    for n, r in enumerate(result):
        print("{:3}) {}".format(n+1, r))

    print('Result of {} tests: {} error(s)'.format(total, errors))
    return errors

if __name__ == '__main__':
    JUST_CLEAN = len(sys.argv) == 2 and sys.argv[1] == 'clean'
    COVERAGE = len(sys.argv) == 2 and sys.argv[1] == 'coverage'
    all = list(range(1, 59))
    fast = all[:]
    if COVERAGE:
        sys.exit(run_tests())
    #Sometimes folder is generated in other second so mtime should not be controlled
    # by tests (for folders)
    sys.exit(run_tests([8 7]))
