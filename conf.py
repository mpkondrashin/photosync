#!/usr/bin/env python3
from __future__ import print_function
"""
PhotoSync (c) 2017 by Mikhail Kondrashin
Configuration module


"""
DEBUG = False
#PROTECT = True
CONTENT = False
BLOCK_SIZE = 1024*2
CHECK_HASH = False

RAW_DIRS_EXTS = ('raw', 'big', 'jpg')

HASH_FILE = 'hash.md5'
IGNORE_FILES = ['.DS_Store', 'Thumbs.db', '*backup_stop.txt', '*backup_start.txt', '._*', 'Picasa.ini']
IGNORE_FILE_MASKS = IGNORE_FILES
CAMERA_RAW_EXT = [ '.png', ".3fr", ".arw", ".bay", ".cap", ".cr2", ".crw", ".dcr", ".dcs", ".dng", ".drf",
		".eip", ".erf", ".fff", ".iiq", ".k25", ".kdc", ".mef", ".mos", ".mrw", ".nef", ".nrw", ".orf", ".pef", ".ptx", 
		".pxn", ".r3d", ".raf", ".raw", ".rw2", ".rwl", ".rwz", ".sr2", ".srf", ".tif", ".x3f" ]
CAMERA_RAW_EXT_MASK = ['*' + ext for ext in CAMERA_RAW_EXT]
JPG_EXT = [".jpg", ".jpeg"]
IMG_EXT = [".jpg", ".jpeg", ".bmp", ".eps", ".gif", ".png", ".ppm", ".psd", ".tga", ".tiff", ".tif"]#, ".dng"]
VIDEO_EXT = [".mov", ".3gp", ".mp4", ".avi"] #mpeg, mpg?
GIF_EXT = [".gif"]
OTHER_EXT = [".thm"]


#IDX_EXT = JPG_EXT + GIF_EXT
#IDX_EXT_MASK = ['*' + ext for ext in IDX_EXT]

RAW_EXT = CAMERA_RAW_EXT + JPG_EXT + VIDEO_EXT
RAW_EXT_MASK = ['*' + ext for ext in RAW_EXT]

GIFSICLE = None #'/usr/local/bin/gifsicle'
FFMPEG = None #'/usr/local/bin/ffmpeg'
EXIFTOOL = None
GIF_SIZE=320
JPG_SIZE=1600

# After changing these parameters corresponding tests should be fixed:
PREVIEW_FOR_RAW_QUALITY=60
PREVIEW_FOR_BIG_QUALITY=80

VIDEO_PREVIEW_FRAMES=10

# changing this will require to rename all shadow folders on all archive drives:
SHADOW_SUFFIX = '.shadow'

