#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Синхронизация:

1. Выявить, нет ли объектов с одинаковыми названиями, но разными типами (файл, папка, ссылка)
2. Найти все папки и файлы на source, которых нет на target и скопировать их туда
3. Проверить все файлы hash.md5 и если нужно, удалить файлы, которые не указаны в них, убедиться,
    что он модифицирован позже всех файлов в нем

4. Проверить, нет ли файлов с отичающимся регистром символов и переименовать их одинаково
5. Проверить, для всех ли raw-файлов в .raw-папках есть превью и сгенерировать их
6. Проверить, нет ли в source более новых файлов, чем в target и скопировать их
7. Найти все папки и файлы на target, которых нет на source и удалить их
8. Для всех одинкоих .raw-папках сгенерировать hash.md5, если нет
9. Защитить от удаления и модификации все незащищенные файлы в папках .raw


Найти на target все папки *.raw (*.jpg, *.big), которых нет на source (т.н. одинокие raw)
и для всех raw/jpg/video-файлов в них должны быть
preview-файлы в "над папке" на target и на source

Для всех одиноких raw: рядом raw-папкой должен быть файл hash.md5,
в который (i) будет старше всех файлов, перечисленных в нем, (ii) не будет содержать в
себе файлов, которых нет и (iii) на диске не будет файлов, которые в нем не перечисленны

Для всех одиноких raw: Сами raw-папки, а также все их содержимое
должно быть защищено от удаления или модификации

TODO:
- Недопустимо "переносить в архив", если не со всеми архивами была
  синхронизация. - "ругаться сразу(?)"

- Проверять, что пытаемся удалять защищенную папку или файл и "ругаться" сразу,
  а не давать сбой при фактическом копировании

- нужно бы защитить файлы hash.md5 от случайного удаления

- Нужна оптимизация (коагуляция) операций - одна операция на папку, а не для каждого в ней файла

- Паралельный запуск синхронизации независимых подпапок

- Добавить графический интерфейс

- Контроль mode

- Не запускать синхронизацию, если с момента старта что-то в папке photo
изменилось

Потерян в высоком разрешении: 20050526_6196-amk-od.jpg
20060314 Семинар Информзащиты. Казахстан.big - нет больших файлов

не хватает файлов с iphone:
/Volumes/WD/photo/Albums/2014/20140908-20 Манила: Missing 20140908-20 Манила.big/20140911_1956-od.jpg file
/Volumes/WD/photo/Albums/2014/20140908-20 Манила: Missing 20140908-20 Манила.big/20140911_1957-od.jpg file

нет файла /Volumes/WD/photo/Albums/2014/20140825 Франкфурт & Диценбах: Missing file: 20140825 Франкфурт & Диценбах.big/20140828_1838.jpg

Не открывается оригинал для
/Users/michael/Pictures/photo/digital/2005/10\ Октябрь/09.10.2005\ Сашина\ фотография\ для\ программы\ виртуального\ макияжа/20051009_9535.jpg

blocks = []
for block in iter(partial(f.read, 32),''):
    block.append(block)

for ...
else:

defaultdict(int)

d=dict()
d.setdefault(key, []).append(...)

d.defaults.copy()
d.update(os.environ)
d.update(command_line)

d = ChainMap(d1,d2,d3)

Results = namedtuple('Results', ['failed','ateempted'])
r = Results(1,2)

a = deque([1,2,3])
a.popleft()
a.appendleft(2)

with ignored(OSError):
    open('a')...

@contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass

with open('a','w') as f:
    with redirect_stdout(f):
        help(pow)


@contextmanager
def redirect_stdout(fileobj):
    oldstdout = sys.stdout
    sys.stdout = fileobj
    try:
        yield fileobj
    finally:
        sys.stdout = oldstdout


a/b/c/q.txt
a/b/d/P.txt
a/e/F.txt
a/e/g/H.txt

a/b/d
a/e

make __iter__ iterator with yield


параллелизм --- явное написание кода для разных потоков (a-la Scratch)
сквозная разработка --- единый код для клиента/сервера/мобильной и облачной платформы (a-la RPC)
устойчивость данных/переменных --- переменные, сохраняющие свое значение между запусками
приложения (a-la CoreData/SQL)
жизненный цикл (обновление версий) --- учет того, что у клиентов уже какая-то версия по
есть и с данными прошлый версий нужно уметь работать и код обновлять
безопасность данных (переменные для паролей/сертификатов)
мандатный доступ - у данных есть гриф


phase, name, tick

'''
#from builtins import input
import os
import sys
import argparse

import conf
import show
from sync import Sync
import util
import hashmd5
import progress
import repair
import filter

#parser.add_argument("-s", "--shallow", help="compare only stat data", action="store_true")

def do_hash_check(root, warnings_file):
#    print(root)
    def log_it(msg):
        show.puts(msg)
        show.newline()
        show.pushs('Check: ')
        if warnings_file:
            wf.write("{}\n".format(msg))
    is_on_removable_media = util.is_on_removable_media(root)
    if not is_on_removable_media:
        print('Checking local drive — ignore absense of files in subfolders')
    import path
    root_path = path.Path(root)
    wf = None
    if warnings_file is not None:
        wf = open(warnings_file, 'w')
    have_errors = 0
    show.pushs('Scan: ')
    hash_list = []
    total_size = 0
    for hash_md5 in root_path.listfiles(include_files=[conf.HASH_FILE]):
        hash_dict = hashmd5.HashFileToDict(str(root_path / hash_md5))
        for h in hash_dict:
            if not is_on_removable_media and os.sep in h:
                #  Don't check files in subfolders
                #  if we are checking local drive
                continue
            p = root_path / hash_md5.dirname() / path.Path(h)
            try:
                size = p.size()
            except OSError as e:
                if e.errno == 2:
                    size = 0
                else:
                    raise
            hash_list.append((p, hash_dict[h], size))
            total_size += size
#            show.puts("{} hash files found. Total size = {}".format(,
#                                util.dimension(total_size)), progress=True)
            show.puts("Total size: {}".format(util.dimension(total_size)), progress=True)

    show.puts("Total size: {}".format(util.dimension(total_size)), progress=True)
    show.newline()

    show.pushs('Check: ')
    progr = progress.Progress(total_size)
    for p, hash, file_size in hash_list:
        #print(p, hash, file_size)
        #percent = size * 100 / total_size
        __, name = p.split()
        time_left = progr.time_left(file_size)
        min, sec = int(time_left / 60), int(time_left % 60)
        show.puts('{:02}:{:02} left: {}'.format(min, sec, name), progress=True)
#        show.puts('{}% ({:02}:{:02} left): {}'.format(percent, min, sec, name), progress=True)
        try:
            if p.md5() != hash:
                have_errors = 1
                log_it("Hash error: {}".format(p))
        except IOError as e:
            if e.errno != 2:
                raise
            have_errors = 1
            log_it("Missing: {}".format(p))
    show.puts('done')
    show.newline()
    return have_errors


def do_sync(argv):
    source = os.path.abspath(os.path.expanduser(argv['source'].rstrip('/')))
    target = os.path.abspath(os.path.expanduser(argv['target'].rstrip('/')))

    conf.CONTENT = argv['content']
    conf.BLOCK_SIZE = int(argv['block_size'])

    def combine_list_arg(arg_list, arg_files):
        if arg_list or arg_files:
            return arg_list + list(util.remove_prefix(util.cat(arg_files), source))
        return None

    include = combine_list_arg(argv['include'], argv['include_file'])
    exclude = combine_list_arg(argv['ignore'], argv['ignore_file'])

    filter_include_ignore = filter.Filter(include=include, exclude=exclude)

    sync = Sync(source,
                target,
                argv['subdir'],
                _filter=filter_include_ignore,
                noprotect=argv['noprotection'],
                nohash=argv['nohash'])


    #print("BEFORE SYNC")
    #sync.source.tree()
    #print('')
    #sync.target.tree()
    sync.sync_with_local()
    #print("AFTER SYNC AND CLEANUP")

    sync.source.cleanup()
#    sync.source.tree()
    sync.target.cleanup()
#    sync.target.tree()

    if argv['repair'] is not None:
        repair.shell_script(argv['repair'])

    wf = None
    if argv['warnings'] is not None:
        wf = open(argv['warnings'], 'w')
    if sync.list_warnings(wf):
        if wf is not None:
            print('Warning written to {} file'.format(argv['warnings']))
        return 1

    if len(sync.operations) > 0:
        print('Operations:')
        sync.operations.show()

    oc = sync.operations_count()
    if oc == 0:
        print('Nothing to sync')
        return 0

    print('Total {} operations'.format(oc))

    #try: input = raw_input
    #except NameError: pass

    if not argv['yes']:
        while True:
            answer = input('Proceed? [y/N/t]: ')
            #answer = eval(input('Proceed? [y/N/t]: '))
            if answer.lower() == 't':
                sync.source.tree()
                sync.target.tree()
                continue
            elif answer.lower() == 'y':
                break
            else:
                print("Operation aborted")
                return 100

    print('Sync go')
    sync.go()
    print('Sync Done')
    return 0


def do_check(target, warnings_file = None):#, subdir, ignore, warnings, yes):
    spath = target + '.shadow'
    wf = None
    if warnings_file is not None:
        wf = open(warnings_file, 'w')
    if not os.path.isdir(spath):
        err = "{}: does not exist".format(spath)
        print(err)
        if wf:
            wf.write("{}\n".format(err))
        return 1
    flags = os.stat(spath).st_flags
    if flags != util.SHADOW_ATTRIBUTES:
        err = "{}: wrong attributes".format(spath)
        print(err)
        if wf:
            wf.write("{}\n".format(err))

    show.pushs('Check: ')
    unprotected = 0
    for root, dirs, files in os.walk(spath):
        st = os.stat(root)
        show.puts(root, progress=True)
        if st.st_flags & util.PROTECTED_DIR_FLAGS == 0:
            show.pop()
            err = 'Not protected folder: {}'.format(root)
            show.puts(err)
            if wf:
                wf.write("{}\n".format(err))
            show.newline()
            show.pushs('Check: ')
            unprotected += 1

        for fname in files:
            if util.ignore_file(fname):
                continue
            fpath = os.path.join(root, fname)
            show.puts(fpath, progress=True)
            st = os.stat(fpath)
            if not util.is_protected_file_stat(mode=st.st_mode,
                                               flags=st.st_flags,
                                               nlink=st.st_nlink):
                show.pop()
                err = 'Not protected file: {}'.format(fpath)
                show.puts(err)
                if wf:
                    wf.write("{}\n".format(err))
                show.newline()
                show.pushs('Check: ')
                unprotected += 1
    if unprotected:
        show.puts('{} unprotected files and folders found'.format(unprotected))
    else:
        show.puts('done')
    show.newline()
    return unprotected
    # noinspection InjectedReferences


def parse_args(arguments = None):
    parser = argparse.ArgumentParser(description='Sync Photo Archive')
    subparsers = parser.add_subparsers(help='Action')

    parser_check = subparsers.add_parser('check', help='Check shadow copy files')
    parser_check.set_defaults(action='check')
    parser_check.add_argument('target', type=str, help='Target directory')
    parser_check.add_argument("-y", "--yes", help="Yes to all questions", action="store_true")
    parser_check.add_argument("-w", "--warnings",	metavar='file', help="file to write warnings")

    parser_hash = subparsers.add_parser('hash', help='Check hash.md5 files')
    parser_hash.set_defaults(action='hash')
    parser_hash.add_argument('target', type=str, help='Target directory')
    parser_hash.add_argument("-y", "--yes", help="Yes to all questions", action="store_true")
    parser_hash.add_argument("-w", "--warnings",	metavar='file', help="file to write warnings")

    parser_sync = subparsers.add_parser('sync', help='Sync with external drive')
    parser_sync.set_defaults(action='sync')
    parser_sync.add_argument("-y", "--yes", help="Yes to all questions", action="store_true")
    parser_sync.add_argument("-w", "--warnings",	metavar='file', help="file to write warnings")
    parser_sync.add_argument("-r", "--repair",	metavar='file', help="file to write repair script")
    #parser_sync.add_argument("-d", "--debug",help="debug mode", action="store_true")
    #parser_sync.add_argument("-f", "--fat", metavar='fat', help="sync with FAT file system")
    parser_sync.add_argument("-p", "--noprotection", help="do not protect", action="store_true")
    parser_sync.add_argument("-s", "--subdir", default="", help="Sync only subdir")
    parser_sync.add_argument("-i", "--ignore", default=[], action='append', help="ignore this path")
    parser_sync.add_argument("-g", "--ignore-file", default=[], action='append', help="ignore paths from file")
    parser_sync.add_argument("-n", "--include", default=[], action='append', help="sync only this folder")
    parser_sync.add_argument("-f", "--include-file", metavar='file', default=[], action='append', help="include only paths from file")
    parser_sync.add_argument("-c", "--content", help="compare files content", action="store_true")
    parser_sync.add_argument("-b", "--block-size", metavar='bytes', default=2*1024, help="block size to compare")
    parser_sync.add_argument("-m", "--nohash", help="do not calc hash", action="store_true")
    parser_sync.add_argument("-t", "--time",	metavar='file', help="time stamp file")
#    parser_sync.add_argument('action', choices=['sync', 'hash', 'check'], help='Action')
    parser_sync.add_argument('source', type=str, help='Source directory')
    parser_sync.add_argument('target', type=str, help='Target directory')

#    parser.add_argument("-y", "--yes", help="Yes to all questions", action="store_true")
#    parser.add_argument("-w", "--warnings",	metavar='file', help="file to write warnings")

    if arguments is not None:
        return parser.parse_args(arguments)
    return parser.parse_args()


import traceback

class TracePrints(object):
    def __init__(self):
        self.stdout = sys.stdout

    def write(self, s):
        self.stdout.write("Writing %r\n" % s)
        traceback.print_stack(file=self.stdout)


def main():
    util.check_external_programs()
    args = parse_args()
#    check_environment()

    if args.action == 'sync':
        return do_sync(vars(args))
    elif args.action == 'check':
        return do_check(os.path.abspath(os.path.expanduser(args.target.rstrip('/'))),
                        warnings_file=args.warnings)
    elif args.action == 'hash':
        return do_hash_check(os.path.abspath(os.path.expanduser(args.target.rstrip('/'))),
                             warnings_file=args.warnings)
    else:
        print('Not implemented')
        return 50


if __name__ == '__main__':
    rc = main()
    print("RC = ", rc)
    sys.exit(rc)
