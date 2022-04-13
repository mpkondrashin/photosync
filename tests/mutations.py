#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function
"""
This code should not work after moving it into tests subfodler
"""
import sys
import os
import subprocess
import shutil

MUTE_DIR='mute'
MUTATION_IGNORE_MARK = '#  MUTE_IGNORE'
FIRST_LINE = 0

def iterate_scripts(folder):
    for s in os.listdir(folder):
        if os.path.splitext(s)[1] == '.py':
            if s != 'exif.py':
                continue
            yield s




def iterate_mutations(bak, script):
    for prefix, seek_for, change_to in rules:
        content = open(bak).readlines()
        for n, line in enumerate(content):
#            mute_line = re.sub(seek_for, line, change_to)
            #print(mute_line)
            mute_line = mutate(prefix, seek_for, change_to, line)
            if mute_line is None:
                continue
            mute_content = content[:n] + [mute_line] + content[n+1:]
            open(script, 'w').write(''.join(mute_content))
            descr ="Line {}:\nWAS: {}\nMUTE:{}".format(n + 1, line.strip(), mute_line.strip())
            print(descr)
            yield descr


class backup(object):

    def __init__(self, script):
        self.script = script

    def backup(self):
        os.rename(self.script, self.backup_name())
        return self.backup_name()

    def backup_name(self):
        return self.script + '.bak'

    def restore(self):
        try:
            os.remove(self.script)
        except OSError as e:
            if e.errno != 2:
                raise
        os.rename(self.backup_name(), self.script)

#import subprocess32
import subprocess32

def run_test(script):
    # print('SP',script, os.getcwd())
    command = ['python', script]
    try:
        output = subprocess32.check_output(command,
                        stderr=subprocess32.STDOUT, timeout=20)  # , shell=True)
        #print(output)
    except subprocess32.CalledProcessError as e:
        #print("CalledProcessError{}".format(e.output))
        if os.path.isfile('failed_rule.txt'):
            print(open('failed_rule.txt').read())
        else:
            print('Missing failed_rule.txt')
        return False
    except subprocess32.TimeoutExpired as e:
        fname = 'timeout-mutations-output.txt'
        print('Timeout! (check {} file for output)'.format(fname))
        open(fname,'w').write(e.output)
        return False
    return True


import inspect
import importlib

def list_modules(module_name):
    root_dir = os.getcwd()
    list = []
    def scan_modules(module_name):
#        print('APPEND', module_name)
        list.append(module_name)
        module = importlib.import_module(module_name)
        all_modules = inspect.getmembers(module, inspect.ismodule)
        for name, m in all_modules:
            if m.__name__ in list:
                continue
            if not hasattr(m, '__file__'):
                continue
            if os.path.dirname(m.__file__) != root_dir:
                continue
#            print('NEW LOCAL MODULE', m.__file__)
            scan_modules(m.__name__)
        all_classes = inspect.getmembers(module, inspect.isclass)
        for name, c in all_classes:
            if c.__module__ in list:
                continue
#            print('CLASS MODULE', c)
            #class_members = inspect.getfile(c)
            if os.path.dirname(inspect.getfile(c)) != root_dir:
                continue
            #print('CLASS MEMBERS', class_members)
            scan_modules(c.__module__)
    scan_modules(module_name)
    return [m + '.py' for m in list]

def minify(files_list, folder):
    command = ['pyminifier', '-d', folder] + files_list
    process = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)  # , shell=True)
    (output, err) = process.communicate()
    print("{}\n\n{}".format(output, err))


def prepare(script):
    #shutil.rmtree(MUTE_DIR, ignore_errors=True)
    if not os.path.isdir(MUTE_DIR):
        os.mkdir(MUTE_DIR)
    modules = list_modules(os.path.splitext(script)[0])
    print('Modules found: {}'.format(', '.join(modules)))
#    minify(modules, MUTE_DIR)
    for s in modules:
        shutil.copy2(s, MUTE_DIR)



rules = [
#     ('', '==', '!=')
#    ('', '!=', '==')
#     (r'if',r'>', r'>=')
#    (r'if', r'<', r'<=')
    ('', 'if ', 'if False and ')
]

def mutate(prefix, seek_for, change_to, line):
    if MUTATION_IGNORE_MARK in line:
        return None
    comment = line.find('#')
    if comment == -1:
        comment = len(line)
    start = 0
    if prefix != '':
        start = line.find(prefix, 0, comment)
        if start == -1:
            return None
        start += len(prefix)
    position = line.find(seek_for, start, comment)  # coult be second position!!!
    if position == -1:
        return None
    if line.find(change_to, start, comment) == position:
        # We have the changed code alredy, i.e. change '<' to '<=' in line that has '<='
        return None
    return line[:position] + change_to + line[position + len(seek_for):]


def inspect_script_backup(main_script, script, bak):
    print("INSPECT: {}".format(script))
    content = open(bak).readlines()
    for n, line in enumerate(content):
        if n < FIRST_LINE:
            continue
        comment = line.find('#')
        if comment == -1: comment = len(line)
        for prefix, seek_for, change_to in rules:
            mute_line = mutate(prefix, seek_for, change_to, line)
            if mute_line is None:
                continue
            mute_content = content[:n] + [mute_line] + content[n + 1:]
            open(script, 'w').write(''.join(mute_content))
            descr = "{0}[{1}] was:  {2}\n{0}[{1}] mute: {3}".format(script, n + 1, line.strip(), mute_line.strip())
            print(descr)
            if run_test(main_script):
                print('SCRIPT: {}'.format(script))
                print('GOT IT!')
                return 0
            else:
                pass



def inspect_script(main_script, script):
    bkp = backup(script)
    inspect_script_backup(main_script, script, bkp.backup())
    bkp.restore()


def main():
    if len(sys.argv) < 2:
        print("Usage: {} script\nscript - script to lunch".format(sys.argv[0]))
        return 1
    script = sys.argv[1]
    if len(sys.argv) == 3:
        global FIRST_LINE
        FIRST_LINE = int(sys.argv[2])
    prepare(script)
    os.chdir(MUTE_DIR)
    for s in iterate_scripts('.'):
        if s == script:
            print('skip', script)
            continue
        inspect_script(script, s)

if __name__ == '__main__':
    sys.exit(main())
