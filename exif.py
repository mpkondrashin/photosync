#!/usr/bin/env python3
from __future__ import print_function

#import pyexiv2
import util
import subprocess
import time


def transfer_exif(from_file, to_file):
    #show.debug("transfer_exif({},{})".format(from_file, to_file))
    command = [util.exiftool_path(), '-q', '-overwrite_original', '-tagsfromfile',
               from_file, '-x', 'ThumbnailImage', '-x', 'Orientation',
               to_file]
    #  print(" ".join(command))
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    if exit_code != 0:
        raise RuntimeError("'{}' returned exit code {}: {}".format(" ".join(command), exit_code, err))


def get_exif_tag(file_name, tag):
    #show.debug("get_exif_tag({}, {})".format(file_name, tag))
    process = subprocess.Popen([util.exiftool_path(), "-n", "-s","-s","-s",  "-" + tag, file_name],
                               stdout=subprocess.PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    if exit_code != 0:
        raise RuntimeError("exiftool returned exit code {} when reading {} tag from {}: {}".format(exit_code, tag, file_name, err))
    return output


def rotate_angle(file_name):
#    show.debug("rotate_angle({})".format(fileName))
    orientation = get_exif_tag(file_name, "Orientation")
    if len(orientation) > 0:
        try:
            return {3: 180, 6: 270, 8: 90}[int(orientation)]
        except KeyError:
            return 0
    rotation = get_exif_tag(file_name, "Rotation")
    if len(rotation) > 0:
        return int(rotation)
    return 0


def rotate_angle_exif(exif):
    #show.debug("rotate_angle({})".format(exif))
    if 'Orientation' in exif:
        orientation = exif["Orientation"]
        #  if len(orientation) > 0: ...
        o = int(orientation)
        try:
            return { 3: 180, 6: 270, 8: 90 }[o]
        except KeyError:
            return 0
    elif 'Rotation' in exif:
        rotation = exif["Rotation"]
        return int(rotation)
    else:
        return 0


def get_exif(file_name):
    keys = ['-date_time_original',
            '-ContentCreateDate',
            '-FileModifyDate',
            '-Model',
            '-LensMake',
            '-Orientation',
            '-Rotation']
    #show.debug("get_exif({})".format(fileName))
    command = [util.exiftool_path(), "-n","-s","-s"] + keys + [file_name]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    if exit_code != 0:
        raise RuntimeError("exiftool returned exit code {} when executing {}: {}".format(exit_code, ' '.join(command), err))
    exif = dict()
    for l in output.decode('utf-8').split('\n'):
        for key in keys:
            tag = key[1:]
            if l.startswith(tag):
                value = l[len(tag) + 2:]
                if value == '':
                    continue
                exif[tag] = value
    exif['source'] = file_name
    return exif


def date_time_original_exif(exif):

    try: return exif['date_time_original']
    except KeyError: pass

    try: return exif['ContentCreateDate']
    except KeyError: pass

    try: return exif['FileModifyDate']
    except KeyError: pass

    return ''


def creation_time_exif(exif):
    dto = date_time_original_exif(exif)
    if dto == '':
        raise RuntimeError('DTO missing in {}'.format(exif))
    #2011:12:04 22:43:23+04:00
    return time.strptime(dto[0:19], "%Y:%m:%d %H:%M:%S")


def camera_model_exif(exif):
    try: return exif['Model'].rstrip()
    except KeyError: pass
    try: return exif['LensMake'].rstrip()
    except KeyError: pass


def date_time_original(file_name):
    #print(fileName)Plusha01
    dto = get_exif_tag(file_name, 'date_time_original')
    if dto != '':
        return dto
    ccd = get_exif_tag(file_name, 'ContentCreateDate')
    if ccd != '':
        return ccd
    return get_exif_tag(file_name, 'FileModifyDate')


def creation_time(file_name):
    dto = date_time_original(file_name)
    if dto == '':
        raise RuntimeError('{}: DTO missing'.format(file_name))
    #2011:12:04 22:43:23+04:00
    t = time.strptime(dto[0:19], "%Y:%m:%d %H:%M:%S")
    return t


def camera_model(file_name):
    model = get_exif_tag(file_name, 'Model')
    if model != '':
        return model.rstrip()
    model = get_exif_tag(file_name, 'LensMake')
    return model.rstrip()


def _RotateAngle(fileName):
    try:
        metadata = pyexiv2.metadata.ImageMetadata(fileName)
        metadata.read()
        orientationTag = metadata.__getitem__("Exif.Image.Orientation")
        angle = { 3: 180, 6: 270, 8: 90 }[orientationTag.value]
        if angle == None:
            return 0
        return angle
    except KeyError as e:
        return 0


if __name__ == '__main__':
    import sys
    e = get_exif(sys.argv[1])
    print(e)
