#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import fnmatch
import errno
import stat
import hashlib
import conf
import subprocess as sp
import contextlib
import time

PROTECTED_MODE_MASK = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
PROTECTED_MODE_VALUE = 0
PROTECTED_FLAGS_MASK = stat.UF_IMMUTABLE
PROTECTED_FLAGS_VALUE = PROTECTED_FLAGS_MASK
SHADOW_ATTRIBUTES = stat.UF_APPEND | stat.UF_HIDDEN
PROTECTED_DIR_FLAGS = stat.UF_APPEND


def is_protected_file_stat(mode, flags, nlink):
    return flags & PROTECTED_FLAGS_MASK == PROTECTED_FLAGS_VALUE and \
        mode & PROTECTED_MODE_MASK == PROTECTED_MODE_VALUE and \
        nlink == 2


def is_protected_folder_stat(mode, flags):
    return flags & PROTECTED_FLAGS_MASK == PROTECTED_FLAGS_VALUE and \
           mode & PROTECTED_MODE_MASK == PROTECTED_MODE_VALUE


def protect_file(root, vector):
    #print("protect_file({}, {})".format(root, vector))
    shadow_file(root, vector)
    make_immutable(root, vector)


def protect_folder(root, vector):
#    print("protect_folder({})".format(path))
    make_immutable(root, vector)


def make_immutable(root, vector):
    """Prohibit any file change
        root / vector - path to file
    """
    path = os.path.join(root, vector)
    st = os.stat(path)
    mode = st.st_mode & ~PROTECTED_MODE_MASK | PROTECTED_MODE_VALUE
    os.chmod(path, mode)
    flags = st.st_flags & ~PROTECTED_FLAGS_MASK | PROTECTED_FLAGS_VALUE
    os.chflags(path, flags)


def is_shadow_dir(vector):
    return vector.endswith(conf.SHADOW_SUFFIX)


def shadow_path(root):
    '''Return shadow path for particular root path

    Function addes '.shadow' to last provided path component

    >>> shadow_path('/Volumes/WD/photo')
    '/Volumes/WD/photo.shadow'
    >>> shadow_path('/Volumes/WD/photo/')
    '/Volumes/WD/photo.shadow'
    '''
    return root.rstrip('/') + conf.SHADOW_SUFFIX


def shadow_file(root, vector):
    '''
    Root: /Volumes/photo
    Vector: digital/2014/01/a.raw/IMG.cr2
    Path: /Volumes/photo/digital/2014/01/a.raw/IMG.cr2
    Shadow: /Volumes/photo.shadow/digital/2014/01/a.raw/IMG.cr2
    '''
    root_shadow = shadow_path(root)
    make_dir(root_shadow, SHADOW_ATTRIBUTES)
    p = root_shadow
    for component in vector.split(os.sep)[:-1]:
        p = os.path.join(p, component)
        make_dir(p, PROTECTED_DIR_FLAGS)

    source = os.path.join(root, vector)
    link_name = os.path.join(root_shadow, vector)
    mklink(source, link_name)


def mklink(src, dst):
    """ Ignore if link exists """
    try:
        #print("link {} {}".format(source, link_name))
        os.link(src, dst)
    except OSError as e:
        if e.errno != errno.EEXIST or not os.path.isfile(dst):
            raise


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno != errno.EEXIST or not os.path.isdir(path):
            raise


def make_dir(path, flags):
    """Make directory with provided flags ignoring if it alredy exists
    path - path to direcotry
    flags - desired flags
    """
    #  print("make_dir({},{})".format(path, flags))
    try:
        os.mkdir(path)
    except OSError as e:
        if e.errno != errno.EEXIST or not os.path.isdir(path):
            raise

    if flags == 0:
        return

    try:
        os.chflags(path, flags)
    except OSError as e:
        if e.errno == 22:
            raise RuntimeError('Error os.chflags for {}. (Not Mac OS X disk?)'.format(path))
        else:
            raise


def raw_archive_folder(folder):
    return any([folder.endswith(ext) for ext in conf.RAW_DIRS_EXTS])


def read_extract(path, block_size):
    with open(path,'rb') as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        f.seek(0, os.SEEK_SET)
        if file_size < block_size * 2:
            return f.read()
        head = f.read(block_size)
        f.seek(-block_size, os.SEEK_END)
        tail = f.read(block_size)
        return head + tail


def extract_hash(path, block_size):
    data = read_extract(path, block_size)
    return hashlib.md5(data).hexdigest()


def is_ext(file_name, extensions):
    extension = os.path.splitext(file_name)[1]
    return extension.lower() in extensions


def is_raw(file_name):
    return is_ext(file_name, conf.CAMERA_RAW_EXT)


def is_image(file_name):
    return is_ext(file_name, conf.CAMERA_RAW_EXT+conf.IMG_EXT+conf.VIDEO_EXT)


def is_video(file_name):
    return is_ext(file_name, conf.VIDEO_EXT)


def is_jpeg(file_name):
    return is_ext(file_name, conf.JPG_EXT)


def is_other(file_name):
    return is_ext(file_name, conf.OTHER_EXT)


def is_supported(file_name):
    return any(f(file_name) for f in (is_raw, is_video, is_jpeg, is_other))


def dimension1000(x):
    for d in ['B ', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']:
        if x < 1000:
            return str(x) + ' ' + d
        x //= 1000


def dimension(x):
    if x < 1000:
        return str(x) + ' Byte'
    x /= 1000.
    for d in ['KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']:
        if x < 1000.:
            s = str(x)[:3]
            if s[2] == '.':
                s = s[:2]
            return s + ' ' + d
        x /= 1000.


def time_delta(x):
    #def p(x):
    x = int(x)
    p = lambda x: "" if x == 1 else "s"
#    if x >= 24*60*60*30:
#        y = x // (24*60*60*30)
#        return  " {} month{}".format(y, p(y))
#    if x >= 24*60*60*7:
#        y = x // (24*60*60*7)
#        return  " {} week{}".format(y, p(y))
    if x >= 24*60*60:
        y = x // (24*60*60)
        return  " {} day{}".format(y, p(y))
    if x >= 60*60:
        y = x // (60*60)
        return " {} hour{}".format(y, p(y))
    if x >= 60:
        y = x // 60
        return " {} min".format(y)
    return " {} second{}".format(x, p(x))


def time_delta_full(x):
    def p(n):
        if n % 10 == 1:
            return ""
        return "s"
    res = ""
    if x >= 24*60*60:
        y = x / (24*60*60)
        res += " {} day{}".format(y, p(y))
        x %= 60*60*24
    if x >= 60*60:
        y = x / (60*60)
        res += " {} hour{}".format(y, p(y))
        x %= 60*60
    if x >= 60:
        y = x / 60
        res += " {} min".format(y)
        x %= 60
    if x > 0:
        res += " {} sec".format(x)
    return res




def which(program):
    def is_executable(file_path):
        return os.path.isfile(file_path) and os.access(file_path, os.X_OK)

    def search_third_party(file_name):
        base_folder = os.path.dirname(os.path.abspath(__file__))
        folder = os.path.join(base_folder,"thirdparty", "root")
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f == file_name:
                    file_path = os.path.join(root, f)
                    if is_executable(file_path):
                        return file_path
                    return None
        return None

    def search_path(file_name):
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, file_name)
            if is_executable(exe_file):
                return exe_file
        return None

    file_path, file_name = os.path.split(program)
    if file_path:
        if is_executable(program):
            return program
    else:
        result = search_third_party(file_name)
        if result is not None:
            return result
        result = search_path(file_name)
        if result is not None:
            return result
    return None


#from functools import wraps

def memoize(function):
    memo = {}
    #@wraps(function)
    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = function(*args)
            memo[args] = rv
            return rv
    return wrapper


@memoize
def get_path(program, url):
    path = which(program)
    if path is None:
        msg = '{} can not be found in PATH\n{}'.format(program, url)
        raise RuntimeError(msg)
    return path


from functools import partial
gifsicle_path = partial(get_path, 'gifsicle', 'https://www.lcdf.org/gifsicle/')
ffmpeg_path = partial(get_path, 'ffmpeg', 'https://www.ffmpeg.org/')
exiftool_path = partial(get_path, 'exiftool', 'https://www.sno.phy.queensu.ca/~phil/exiftool/')

#def __gifsicle_path():
#    url = 'https://www.lcdf.org/gifsicle/'
#    return get_path('gifsicle', url)

#def ffmpeg_path():
#    url = 'https://www.ffmpeg.org/'
#    return get_path('ffmpeg', url)


#def exiftool_path():
#    url = 'https://www.sno.phy.queensu.ca/~phil/exiftool/'
#    return get_path('exiftool', url)


def check_external_programs():
    gifsicle_path()
    ffmpeg_path()
    exiftool_path()


def move_to_raw(path):
    dname, fname = os.path.split(path)
    base_dir, dir_name = os.path.split(dname)
    raw_dir = os.path.join(dname, dir_name + ".raw")
    if not os.path.isdir(raw_dir):
        print("os.mkdir({})".format(raw_dir))
        os.mkdir(raw_dir)
    new_path = os.path.join(raw_dir, fname)
    print("os.rename({},{})".format(path, new_path))
    os.rename(path, new_path)


def move_folder_to_raw(path):
    for f in os.listdir(path):
        if is_supported(f):
            p = os.path.join(path, f)
            if os.path.isfile(p):
                move_to_raw(p)


def lower_extension(path):
    for f in os.listdir(path):
        src = os.path.join(path, f)
        if not os.path.isfile(src):
            continue
        fname, fext = os.path.splitext(f)
        low = fext.lower()
        if fext == low:
            continue
        name = fname + low
        dst = os.path.join(path, name)
        print("os.rename({},{})".format(src, dst))
        os.rename(src, dst)


def ignore_file(path):
    file_name = os.path.split(path)[1]
    for mask in conf.IGNORE_FILES:
        if fnmatch.fnmatch(file_name.lower(), mask.lower()):
            return True
    return False


def monster_delete(path):
    try:
        st = os.lstat(path)
    except OSError as e:
        if e.errno == errno.ENOENT:
            return
        raise
    protective_flags = stat.UF_APPEND | stat.UF_HIDDEN | stat.UF_IMMUTABLE
    os.lchflags(path, st.st_flags & ~protective_flags )
    os.lchmod(path, st.st_mode | stat.S_IWUSR)
    if stat.S_ISDIR(st.st_mode):
        for f in os.listdir(path):
            monster_delete(os.path.join(path, f))
        os.rmdir(path)
    else:
        os.unlink(path)


def file_system(path):
    command = ['df', path]
    process = sp.Popen(command, stderr=sp.PIPE, stdout=sp.PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    if exit_code != 0:
        raise RuntimeError("Error {} on {} command: {} {}".format(
            exit_code, ' '.join(command), output, err))
    return output.decode('utf-8').split('\n')[1].split()[0]


def is_removable(filesystem):
    command = ['diskutil', 'list', filesystem]
    process = sp.Popen(command, stderr=sp.PIPE, stdout=sp.PIPE)  # , shell=True)
    (output, err) = process.communicate()
    exit_code = process.wait()
    if exit_code != 0:
        raise RuntimeError("Error {} on {} command: {}".format(
            exit_code, ' '.join(command), output + err))
    first_line = output.decode('utf-8').split('\n')[0]
    left_bracket = first_line.find('(')
    right_bracket = first_line.find(')', left_bracket)
    properties = first_line[left_bracket + 1:right_bracket].split(', ')
    return 'external' in properties


def is_on_removable_media(path):
    system = file_system(path)
    return is_removable(system)


def cat(files):
    for file_name in files:
        yield from file_to_list(file_name)


def file_to_list(file_name):
    with open(file_name) as f:
        for l in f: #.readlines():
            l = l.strip()
            if l != '':
                yield l
#        contents = [l.strip() for l in f.readlines()]
#        return [l for l in contents if l != '']


def __remove_prefix(paths, prefix):
    result = []
    for p in paths:
        if os.path.isabs(p):
            if p.startswith(prefix):
                result.append(p[len(prefix):])
        else:
            result.append(p)
    return result


def remove_prefix(paths, prefix):
    for p in paths:
        if os.path.isabs(p):
            if p.startswith(prefix):
                yield p[len(prefix)+1:]
        else:
            yield p


@contextlib.contextmanager
def log_time(file_object, *argv):
    time_start = time.time()
    yield
    time_finish = time.time()
    delta = time_finish - time_start
    str_argv = list(map(str, argv))

    file_object.write("{};{};{}\n".format(time_start, delta, ';'.join(str_argv)))

"""
Unused:

def SameContent(source, target, block_size):
    with open(source, 'r') as s:
        with open(target, 'r') as t:
            if block_size == -1:
                return s.read() == t.read()
            if s.read(block_size) != t.read(block_size):
                return False
            s.seek(-block_size, 2) #  seek from end
            t.seek(-block_size, 2)
            return s.read(block_size) == t.read(block_size)


def test_SameContent(block_size):
    with open('a_util_SameContent.txt','w') as a:
        a.write('a' * block_size)
        a.write('b' * block_size)
        a.write('c' * block_size)
    with open('b_util_SameContent.txt','w') as a:
        a.write('a' * (block_size-1))
        a.write('x')
        a.write('b' * block_size)
        a.write('c' * block_size)
    if SameContent('a_util_SameContent.txt', 'b_util_SameContent.txt', block_size):
        print('error 1')
    with open('c_util_SameContent.txt','w') as a:
        a.write('a' * block_size)
        a.write('b' * (block_size-1))
        a.write('x')
        a.write('c' * block_size)
    if not SameContent('a_util_SameContent.txt', 'c_util_SameContent.txt', block_size):
        print('error 2')
    with open('d_util_SameContent.txt','w') as a:
        a.write('a' * block_size)
        a.write('b' * block_size)
        a.write('x')
        a.write('c' * (block_size-1))
    if SameContent('a_util_SameContent.txt', 'd_util_SameContent.txt', block_size):
        print('error 3')

def StringHead(path, length):
		u = unicode(path,"utf-8")
		f = u[:length]
		return f.encode("utf-8")

def StringTail(path, length):
		u = unicode(path,"utf-8")
		f = u[-length:]
		return f.encode("utf-8")

def ShortPath(path, length):
	if len(path) < length:
		return path #"%%-%ds" % length % path
	head = (length-3)//2
	tail = length-3-head;
	#print("%d\n" % half)
#	print("ShortPath: {}, {}, {}".format(len(path), length, len(StringHead(path,head) + "..." + StringTail(path, tail))))
	return StringHead(path,head) + "..." + StringTail(path, tail)
"""
