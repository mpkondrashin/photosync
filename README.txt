PhotoSync — Photo Heritage Archiving
(c) 2018 by Mikhail Kondrashin mkondrashin@gmail.com


CONCEPTION
Family photos and videos are one of the most valuable digital
asset of any modern household. Value of digital assets
only rises as years go by. On the other hand, the longer
one maintains photo & video archive the more likely
that something will be lost for ever. Probability of
this un... event only rises with time. Following risks
should be considered in first place:
1. Unsupported format of archive by future software
2. Loose or malfunction of used storage
3. Loose of archive consistency
    First risk can be managed by using only open standards like
regular files and folders to store images and not to relay
on any Multimedia Managment Systems, i.e. proprietary databases
    Second risk can be obviously reduced by using several ?storages
placed distantly in space or, even better, in different ???uristdictions
    Third risk requires to use some kind of consistency check
that in case of ???failier will require to update inconsistent
storage using data from consistent ones.

Beside these static requirements, archive program should
support image/video lifecycle in some sense.
Image lifecycle is assumed to be following:
1. Image is imported from camera
2. Image is synced with external drives
3. If image is deleted locally, it is deleted on external drive also
4. Image is processed using image processing tool, like Photoshop
    and placed in some other folder
5. Full resolution image is not needed any more, so it is deleted locally
 and preserved only on external drive

DEFINITIONS
Sync - make two folders same content by copying from source (Master) folder
all files missing on target (Slave) one and removing on target folder all
files missing on source one.

Backup - periodicaly create copies of valuable files and give ability to
restore them in case loss of original ones. Some backup systems store
several versions of files in case user will need to revert on older
file versions than last backup because ruined file is ???backuped several
times before user notice it.

Archive - move unneeded currently files to less expensive storage media.
Locally some index/preview and metadate of archived files can be left to
provide user with info on what can be found on archive.

PHOTO SYNC
PhotoSync script suite provide ability to maintain photo and video
archive on several external storages. It provides following features:
1. Sync files with each of external drives using local drive as Master
2. Generate preview for locally removed full resolution images/videos
3. Generate hashes for all archived files, i.e. that have preview generated
4. Control consistency of archive. For example each archived raw file has corresponding
preview file and vice versa.

All PhotoSync operations can be implemented "manually", meaning using
widely available tools and utilities. No proprietary format files nor
databases are created.

MULTIMEDIA STORAGE STRUCTURE
PhotoSync assumes that there is on root folder for all multimedia
content. This folder contents is synced with other storage devices
(Externally attached/network drives) assuming that local drive is Master.
Exception is only for folders with following suffixes (extensions):
1. .raw — for raw images or full resolution jpegs
2. .jpg (has same meaning as .raw)
3. .big - for processed images using Photoshop/Lightroom or similar software
If one of these folders on Slave drive does not have counterpart on local (Master) drive
it is not deleted as other missing locally files or folders. It is assumed to
be "archive". So for each file in this folder that is image or video (see conf.py)
preview is generated for one level up folder locally and then copied to Same location
on Slave drive. For .big folders procedure is the same, but for still images
higher quality jpeg previews are generated.

Example (Assuming that photos is root for all images):
1. Two images IMG_0001.cr2 and IMG_0002.cr2 are imported to folder photo/my_photo_session/my_photo_session.raw
2. During next sync with each external drives this folder and two images are copied
3. IMG_0001.cr2 found to be not so good and is deleted
4. During next sync it is deleted from external drives also
5. After processing IMG_0002.cr2 is is stored in folder photo/album/album.big folder as IMG_0002.jpg
6. This folder and its contents is also synced during next syncs
7. If now folders photo/my_photo_session/my_photo_session.raw and photo/album/album.big
will be deleted, during next sync PhotoSync script will do following:
- Generate preview low res and quality image IMG_0002.jpg and place it into photo/my_photo_session
  folder on local and external drive
- Generate preview low res and good quality image IMG_0002.jpg and place it into photo/album folder
  folder on local and external drive
- Generate file hash.md5 with hashes for contents of both folders on external drive and save copy locally
- Protect folders my_photo_session.raw and album.big from deletion (only for macOS/Linux file system)


PHOTO SYNC USAGE OPTIONS
PhotoSync can be run using script photo.py. It supports following operations:
check — checks status of protection from deletion on external drive
hash - checks hashes
sync - main operation — does sync, consystency check and other archive operations
All operations support following keys:
-w (--warning) followed by file name to write all warnings to that file
-y (--yes) answer 'y' to all queries

./photo.py check <folder>
folder is root folder of photo archive on slave drive. Script will check protection from deletion. Works
only for macOS drives (probably for Linux also)

./photo.py hash <folder>
<Folder> is any folder inside photo archive tree on local or archive drive.
Script will search it for hash.md5 files and check hashes of files.
Note: It can take a long time


photo.py sync [-h] [-y] [-w file] [-r file] [-p] [-s SUBDIR]
                     [-i IGNORE] [-g IGNORE_FILE] [-n INCLUDE] [-f file] [-c]
                     [-b bytes] [-m] [-t file]
                     source target
source - root folder on local drive
