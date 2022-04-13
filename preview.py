#!/usr/bin/env python3


"""
Python modules have been installed and Homebrew's site-packages is not
in your Python sys.path, so you will not be able to import the modules
this formula installed. If you plan to develop with these modules,
please run:
  mkdir -p /Users/michael/Library/Python/2.7/lib/python/site-packages
  echo 'import site; site.addsitedir("/usr/local/lib/python2.7/site-packages")' >> /Users/michael/Library/Python/2.7/lib/python/site-packages/homebrew.pth
==> Summary
/usr/local/Cellar/pyexiv2/0.3.2_1: 14 files, 684K, built in 16 seconds
MacBook-Air-Mikhail:pyexiv2-0.3.2 michael$ 
"""
#from __future__ import print_function
import os
import tempfile
import contextlib
import re
import subprocess as sp
from rawkit.raw import Raw
from PIL import Image
import libraw.errors

import util
import show
import conf
import exif


def quality_for_folder(raw_folder):
    extension = os.path.splitext(raw_folder)[1]
    if extension.lower() == ".big":
        return conf.PREVIEW_FOR_BIG_QUALITY
    else:
        return conf.PREVIEW_FOR_RAW_QUALITY


@contextlib.contextmanager
def ascii_file_name(path):
    """
    Return path to symlink for any file path
    used to avoid providing paths with none ASCII
    characters to functions that do not support it
    :param path: Path to file
    :return: path to same file with only ASCII characters
    """

    # add try:/finally:

    tmp_dir = tempfile.mkdtemp()
    link_path = os.path.join(tmp_dir, 'link')
    os.symlink(path, link_path)
    yield link_path
    os.remove(link_path)
    os.rmdir(tmp_dir)


def preview_for_raw(raw_path, preview_path):
    #    print("preview_for_raw({},{})".format(rawPath, previewPath))
    with tempfile.NamedTemporaryFile(prefix='PhotoImportArchive_', suffix='.tiff') as t:
        show.puts(".", progress=True)
        with ascii_file_name(raw_path) as ascii_raw_path: # workaround libraw bug
            try:
                with Raw(filename=ascii_raw_path) as raw: #  .decode('utf8')
                    raw.options.half_size = True
                    show.puts("o", progress=True)
                    raw.save(t.name)
            except libraw.errors.FileUnsupported as e:
                raise RuntimeError("{}: File Unsupported".format(raw_path))

        show.puts("O", progress=True)
        im = Image.open(t.name)
        show.puts("0", progress=True)
        im.thumbnail((conf.JPG_SIZE, conf.JPG_SIZE))
        show.puts("O", progress=True)
        im.save(preview_path, "JPEG", quality=conf.PREVIEW_FOR_RAW_QUALITY)
    show.puts("o", progress=True)
    exif.transfer_exif(raw_path, preview_path)
    show.puts(".", progress=True)


def preview_for_jpeg(jpg_path, preview_path):
    raw_folder, raw_file = os.path.split(jpg_path)
    show.puts("/", progress=True)
    image = Image.open(jpg_path)
    #image.seek(0)
    #print("{} size: {}".format(rawPath, image.size))
    show.puts("-", progress=True)
    thumbnail_size = conf.JPG_SIZE, conf.JPG_SIZE
    image.thumbnail(thumbnail_size) #, Image.ANTIALIAS)
    show.puts("\\", progress=True)
    exif_data = exif.get_exif(jpg_path)
    angle = exif.rotate_angle_exif(exif_data)
    show.puts("|", progress=True)
    image = image.rotate(angle)
    quality = quality_for_folder(raw_folder)
    show.puts("/", progress=True)
    image.save(preview_path, quality=quality)
    show.puts("-", progress=True)
    exif.transfer_exif(jpg_path, preview_path)
    show.puts(".", progress=True)


def ffmpeg_length(videoFile):
#   print("ffmpeg_length({})".format(videoFile))
    command = [util.ffmpeg_path(), '-i', videoFile]
    process = sp.Popen(command, stderr=sp.PIPE, stdout=sp.PIPE)#, shell=True)
    (output, err) = process.communicate()
    exit_code = process.wait()
    if exit_code != 1:
        msg = "Error running '{}' command: {} {}".format(" ".join(command), output, err)
        raise RuntimeError(msg)
    for line in err.decode('utf-8').split('\n'):
        #print("Line = " + line)
        if 'Duration' in line:
            duration = line.split(',')[0].strip()
            dur = duration.split(' ')[1]
            #  00:07:12.13,
            result = re.match('(\d\d):(\d\d):(\d\d)\.(\d\d)', dur)
            if result is None:
                raise RuntimeError("Duration format mismatch ({})".format(line))
            H = int(result.group(1))
            M = int(result.group(2))
            S = int(result.group(3))
            S100 = int(result.group(4))
            return (H*60.+M)*60.+S+S100/100.
    else:
        raise RuntimeError("Could not find video duration in {}".format(videoFile))


@contextlib.contextmanager
def ffmpeg(video_file, angle, rate):
    transpose = {0: '',
                 90: 'transpose=1, ',
                 180: 'transpose=1, transpose=1, ',
                 270: 'transpose=2, '
                 }[angle]

    command = [util.ffmpeg_path(),
               '-loglevel', 'panic',
                '-i', video_file,
                '-vf',
                "{0}scale='if(gt(a,1),{1},-1)':'if(gt(a,1),-1,{1})'".format(transpose, conf.GIF_SIZE),
                '-pix_fmt', 'pal8',
                '-r', rate,
                '-f', 'gif',
                '-']

    ffm = sp.Popen(command, stderr=sp.PIPE, stdout=sp.PIPE)
    yield ffm.stdout
    ffm.stdout.close()  # Allow ps_process to receive a SIGPIPE if grep_process exits.

"""
From https://stackoverflow.com/questions/753190/programmatically-generate-video-or-animated-gif-in-python
Not to use gifsicle:

import imageio
images = []
for filename in filenames:
    images.append(imageio.imread(filename))
imageio.mimsave('/path/to/movie.gif', images)
For longer movies, use the streaming approach:

import imageio
with imageio.get_writer('/path/to/movie.gif', mode='I') as writer:
    for filename in filenames:
        image = imageio.imread(filename)
        writer.append_data(image)
"""

def gifsicle(stream, gif_file, delay):
    with open(gif_file,'w') as gif:
        command = [util.gifsicle_path(),
                    '--optimize=3',
                    '--colors', '32',
                    '--delay={}'.format(delay)]
        # -j=4 - threads
        # --disposal METHOD
        gs = sp.Popen(command,
                    stdin=stream,
                    stderr=sp.PIPE,
                    stdout=gif)
        (output, err) = gs.communicate()
        exit_code = gs.wait()
        if exit_code != 0:
            raise RuntimeError("{}: {}: {}, {}".format(util.gifsicle_path(), exit_code, output, err))


def calculate_rate_and_delay(duration):
    rate = conf.VIDEO_PREVIEW_FRAMES/duration
    a = int(rate*1000)
    b = 1000
    duration = 30
    return "{}/{}".format(a,b), duration


def preview_for_video(video_file, gif_file):
    show.puts('-', progress=True)
    duration = ffmpeg_length(video_file)
    rate, delay = calculate_rate_and_delay(duration)
    show.puts('/', progress=True)
    exif_data = exif.get_exif(video_file)
    show.puts('-', progress=True)
    angle = exif.rotate_angle_exif(exif_data)
    with ffmpeg(video_file, angle, rate) as ff:
        show.puts('|', progress=True)
        gifsicle(ff, gif_file, delay)
        show.puts('\\', progress=True)


if __name__ == '__main__':
    with ascii_file_name('/Users/michael/PycharmProjects/photosync/requirements.txt') as p:
        os.system('ls -l {}'.format(p))
        print(p)

# Create index video movie
# ffmpeg -i 20140419_0463.MOV  -r 3 -b:v 10000 -b:a 5000 -vf "scale=320:-1" out.mov
#ffmpeg -i $1.MOV -s 320x240 -pix_fmt rgb24 -r 1/7 -f gif - | gifsicle --optimize=3 --colors 32 --delay=100 > $1-tr.gif
#ffmpeg -i $1.MOV -vf "scale=320:-1" -pix_fmt rgb24 -r 1/7 -f gif - | gifsicle --optimize=3 --colors 32 --delay=100 > $1-tr.gif


'''

def ReduceSize( jpgFile, angle, quality):
    #print("ReduceSize({}, {}, {})".format(jpgFile, angle, quality))
    image = Image.open(jpgFile)
    image = image.rotate(angle)
    thumbnailSize = 1600, 1600
    image.thumbnail(thumbnailSize)#, Image.ANTIALIAS)
    image.save(jpgFile, quality=quality)
w
'''

