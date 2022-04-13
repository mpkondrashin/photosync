#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Import
Read file
Transform date (location?)
copy
'''

import sys
import argparse
import shutil
import os
import conf
import show
import util
import exif

parser = argparse.ArgumentParser(description='Import Photo')
#parser.add_argument("-l", "--list-only",help="List actions instead of import", action="store_true")
parser.add_argument("-d", "--debug",help="debug mode", action="store_true")
parser.add_argument("-l", "--label",help="Label import")
parser.add_argument('source', type=str, help='Source directory')
parser.add_argument('target', type=str, help='Target directory')
args = parser.parse_args()

SOURCE = args.source.rstrip('/') #path[0]
TARGET = args.target.rstrip('/') #path[1]
LABEL = 'label_missing' #args.label


def iterate_source(folder):
    for root, dirs, files in os.walk(folder, topdown=True):
        for name in files:
            if util.is_supported(name):
                yield root, name


def path_for_file(folder, file_name, label):
    path = os.path.join(folder, file_name)
    exif_data = exif.get_exif(path)
    ct = exif.creation_time_exif(exif_data)
    model = exif.camera_model_exif(exif_data)
    if model:
        model = " ({})".format(model)
    else:
        model = ""
    # 2016/02 февраль/22.02.2016 <name> (K-r)/22.02.2016 <name>.raw/20162022_1234.CR2
    month_names = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                   'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']
    fname, ext = os.path.splitext(file_name)
    dig_list = []
    for ch in fname:
        if ch.isdigit():
            dig_list.append(ch)
        if ch == '.':
            break
    digits = ''.join(dig_list)
    fmt = "{Y}/{M:02d} {mn}/{D:02d}.{M:02d}.{Y} {label}{model}/{D:02d}.{M:02d}.{Y} {label}.raw/{Y}{M:02d}{D:02d}_{digits}{ext}"
    new_path = fmt.format(Y=ct.tm_year, M=ct.tm_mon, D=ct.tm_mday, H=ct.tm_hour,
                    m=ct.tm_min, s=ct.tm_sec, wd=ct.tm_wday, yd=ct.tm_yday, mn=month_names[ct.tm_mon-1],
                    model=model, label=label, digits=digits, ext=ext)
    return new_path


def copy_file(src, dst):
    util.mkdir_p(os.path.dirname(dst))
    shutil.copy2(src, dst)
    return
    block_size = 102400
    with open(src, 'rb') as s, open(dst, 'wb') as d:
            while True:
                block = s.read(block_size)
                if block:
                    #print('.')
                    d.write(block)
                else:
                    break


print('Scan {} directory'.format(SOURCE))
srcList = list(iterate_source(SOURCE))

print("Found %d files to import" % len(srcList))

answer = input('Proceed? [y/N]: ')
# answer = eval(input('Proceed? [y/N/t]: '))
if answer.lower() != 'y':
    print("Operation aborted")
    sys.exit(1)


totalSize = 0
srcList2 = []
for d, f in srcList:
    fp = os.path.join(d, f)
    size = os.stat(fp).st_size
    totalSize += size
    srcList2.append((d, f, size))

print("Import {}".format(util.dimension(totalSize)))
for i, (folder, file_name, size) in enumerate(srcList2):
    percent = 100 * (i+1) // len(srcList)
    target = path_for_file(folder, file_name, LABEL)
    targetPath = os.path.join(TARGET, target)
    sourcePath = os.path.join(folder, file_name)
    #print("{}".format(targetPath))
    #print('{}'.format(exif.get_exif(os.path.join(dir, fileName))))
    show.puts ("{:3}%: {} ({})".format(percent, file_name, util.dimension(size)))
    copy_file(sourcePath, targetPath)
    #print('{} -> {}'.format(os.path.join(dir, fileName), os.path.join(TARGET, target)))
show.puts('done')
show.newline()
