#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import time
import unicodedata


lastTime = 0


def __terminal_ready():
    global lastTime
    if lastTime != 0 and abs(time.time() - lastTime) < 0.2:
        return False
    lastTime = time.time()
    return True


__stack = ['']
__lastLength = 0


def __del_line():
    sys.stdout.write(u"\u0008" * __lastLength)


def __str_len(text):
    return len(text)
    return len(text.decode('utf-8'))
    u_text = unicodedata.normalize('NFC', text.decode('utf-8'))
    return len(u_text)


# def __stack_len():
#    return sum([__str_len(t) for t in __stack])

def __print_stack():
    global __lastLength
    length = 0
    for t in __stack:
        length += __str_len(t)
        sys.stdout.write(t)
    delta = __lastLength - length
    if delta > 0:
        sys.stdout.write(' ' * delta)
        sys.stdout.write(u"\u0008" * delta)
    __lastLength = length
    sys.stdout.flush()


def puts(text, progress=False):
    if progress and not __terminal_ready():
        return
    __del_line()
    __stack[-1] = unicodedata.normalize('NFC', text)
#    __stack[-1] = unicodedata.normalize('NFC', text.decode('utf-8')).encode('utf-8')
    __print_stack()


def pushs(text):
    puts(text)
    __stack.append('')


def pop():
    __del_line()
    __stack.pop()
    __print_stack()
    if not __stack:
        __stack[:] = ['']


def newline():
    global __lastLength
    __lastLength = 0
    __stack[:] = ['']
    sys.stdout.write('\n')
    sys.stdout.flush()


if __name__ == '__main__':
    import unicodedata
    def norm(s,uni):
        return unicodedata.normalize(uni, s.decode('utf-8')).encode('utf-8')
    pushs('{-=#=-}')
    puts(norm('йё', 'NFC'))
    puts(norm('йёйёйё','NFD'))
    print(len(norm('йё', 'NFC')))
    print(len(norm('йё', 'NFD')))
    newline()
'''
def GetTerminalSize():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))
    return int(cr[1]), int(cr[0])
'''
