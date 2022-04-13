#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

from os import sep as SEP
import sys
import stat
import time

import conf
import util
import preview
import hashmd5
import show
import repair
from path import Path

class Entity(object):

    def __init__(self, name,
                 parent=None,
                 mode=None,
                 size=None,
                 flags=None,
                 mtime=None,
                 nlink=None,
                 warnings=None,
                 **kwargs
                ):
        self.name = name
        assert isinstance(self.name, Path)
        self.parent = parent
        if mode is not None:
            self.mode = mode
        if size is not None:
            self.size = size
        if flags is not None:
            self.flags = flags
        if mtime is not None:
            self.mtime = mtime
        if nlink is not None:
            self.nlink = nlink
        if warnings is not None:  #  MUTE_IGNORE
            self.warnings = warnings[:]
        else:
            self.warnings = []
        self.__dict__.update(kwargs)

    @property
    def path(self):
        return self.parent.path / self.name

    @property
    def vector(self):
        return self.parent.vector / self.name

    @property
    def root(self):
        return self.parent.root

    @property
    def basename(self):
        return self.parent.path

    def only_name(self):
        return self.name.onlyname()

    @property
    def ext(self):
        return self.name.ext()

    def calculate_size(self):
        return self.size

    def __lt__(self, other):
        return self.name < other.name

    def rel_path(self, to):
        if to is self.parent:
            return self.name
        return self.parent.rel_path(to) / self.name

    def name_for_tree(self):
        if self.warnings:  #  MUTE_IGNORE
            return "{} ({}) [{}]".format(self.name,
                                         ", ".join(self.warnings),
                                         self.__class__.__name__)
        return "{} [{}]".format(self.name, self.__class__.__name__)

    def warning(self, message):
        self.warnings.append(message)

    def is_preview(self):
        # implemet all of it here with list of extensions
        return False

    def norm_ignore_extension(self):
        # Wht?
        if self.is_preview():
            return self.only_name().lower()
            #return self.only_name().decode('utf-8').lower()
        return None

    def iterate(self):
        yield self

    def genealogy(self):
        s = self.parent
        while s is not None:
            yield s
            s = s.parent

    def replace_myself(self, other):
        self.parent.replace(self, other)

    def clear_uf_tracked_flag(self):
        UF_TRACKED = 0x40
        if self.flags & UF_TRACKED:
            self.path.chflags(self.flags & ~UF_TRACKED)

    def populate(self, filter):
        pass

    def tree(self, padding=' '):
        print(padding[:-1] + '+-' + self.name_for_tree())

    def skip(self):
        return util.ignore_file(str(self.name))

    def repair_discerpancy(self, local):
        repair.remove(self.path)
        repair.copy(local.path, self.path)

    def discrepancy_with_local_file(self, local):
        self.warning("Can not overwrite by file")
        self.repair_discerpancy(local)

    def discrepancy_with_local_link(self, local):
        self.warning("Can not overwrite by link")
        self.repair_discerpancy(local)

    def discrepancy_with_local_folder(self, local):
        self.warning("Can not overwrite by folder")
        self.repair_discerpancy(local)

    def is_supported(self):
        return util.is_supported(str(self.name))

    def cleanup(self):
        return bool(self.warnings)

    def sync_case(self, remote):
        if self.name.equal(remote.name):
            return
        rename_class = self.rename_class()
        rf = rename_class(remote, self)
        remote.replace_myself(rf)
        yield rf

    def iterate_same(self, other):
        yield self, other

    def check_hash(self, remote):
        return
        yield None

    def iterate_lonely_dot_raw(self, arc):
        return
        yield None

    def copy_to_remote(self, remote):
        return
        yield None

    def remove_remote(self, remote):
        return
        yield None

    def clone(self, new_parent=None):
        entity = self.__class__(**self.__dict__)
        entity.parent = new_parent
        return entity

    def iterate_modified(self, time_stamp):
        if time_stamp < self.mtime:
            yield self.parent

    def reduce(self, scope):
        pass


class File(Entity):

    def __init__(self, *args, **kwargs):
        # this can be removed
        super(File, self).__init__(*args, **kwargs)

    def is_protected(self):
        return util.is_protected_file_stat(mode=self.mode,
                                           flags=self.flags,
                                           nlink=self.nlink)

    def protect(self):
        pf = ProtectFile(self)
        self.replace_myself(pf)
        yield pf

    def excess_on_local(self, archive_folder):
        cf = CopyFile(self)
        archive_folder.add_entity(cf)
        yield cf

    def excess_on_archive(self):
        rm = RemoveFile(self)
        self.replace_myself(rm)
        yield rm

    def discrepancy_with_archive(self, archive):
        archive.discrepancy_with_local_file(self)

    def discrepancy_with_local_file(self, local):
        show.puts("{}".format(self.vector), progress=True)

    def update_remote(self, remote):
        delta_mtime = int(remote.mtime - self.mtime)

        if delta_mtime > 0:
            self.warning("Older by{}".format(util.time_delta(delta_mtime)))
            repair.touch(remote.path, self.path)
            return

        if delta_mtime < 0 or self.size != remote.size:
            if 160 * self.size // 100 <= remote.size and remote.is_supported():
                self.warning("Is smaller than target")
                repair.copy(self.path, remote.path)
                return
            cf = CopyFile(self)
            remote.replace_myself(cf)
            yield cf
            return

        if conf.CONTENT:
            if self.extract != remote.extract:
                cf = CopyFile(self)
                remote.replace_myself(cf)
                yield cf
                return

    def is_preview(self):
        return self.ext.lower() in ['.jpg', '.jpeg', '.gif']

    def iterate_files(self):
        yield self

    def rename_class(self):
        return RenameFile


class FileToSkip(File):

    def skip(self):
        return True
    '''
    def iterateVectors(self):
        return
        yield None
    '''

    def iterate_files(self):
        return
        yield None

    def iterate_modified(self, time_stamp):
        return
        yield None


class Link(Entity):
    #    def isProtected(self):
    #        return bool(self.flags & stat.UF_IMMUTABLE) and self.nlink > 1

    def __init__(self, *args, **kwargs):
        super(Link, self).__init__(*args, **kwargs)
        if not hasattr(self, 'link'):
            self.link = self.path.readlink()

    def excess_on_local(self, archive_folder):
        cl = CopyLink(self)  # ?!!!
        archive_folder.add_entity(cl)
        yield cl

    def excess_on_archive(self):
        rl = RemoveLink(self)
        self.replace_myself(rl)
        yield rl

    def discrepancy_with_archive(self, archive):
        archive.discrepancy_with_local_link(self)

    def discrepancy_with_local_link(self, local):
        show.puts("{}".format(self.vector), progress=True)

    def update_remote(self, remote):
        if not self.name.equal(remote.name) or self.link != remote.link: #  MUTE_IGNORE
            rl = RemoveLink(remote)
            yield rl
            cl = CopyLink(self)
            remote.replace_myself(cl)
            yield cl

    def rename_class(self):
        return RenameLink

    def iterate_files(self):
        return
        yield None

    def if_modified_since(self, time_stamp):
        return time_stamp < self.mtime

class RawFile(File):

    def preview_name(self):
        return self.name.changeext('.jpg')

    def is_preview(self):
        return True

    def check_previews(self, loc, arc, local_folder):
        if loc:
            if self.mtime > loc.mtime:
                loc.warning('is older than raw')
                if arc and arc.mtime >= loc.mtime:
                    repair.touch(loc.path, self.path)

        if arc:
            if self.mtime > arc.mtime:
                arc.warning('is older than raw')
                if loc and loc.mtime > arc.mtime:
                    repair.touch(arc.path, self.path)

        if not loc and arc:
            self.warning("Missing local index file")
            repair.copy(arc.path, (local_folder.path / arc.name).path)
            return

        if not loc and not arc:
            ir = self.preview_generator()
            local_folder.add_entity(ir)
            yield ir
            cf = CopyFile(ir)
            self.parent.parent.add_entity(cf)
            yield cf
            return

        if loc and not arc: #  MUTE_IGNORE
            # This code never executed as copy phase
            # alredy created copy of preview file
            cf = CopyFile(loc)
            self.parent.parent.add_entity(cf)
            yield cf
            return

    def preview_generator(self):
        return PreviewForRaw(self)


class VideoFile(RawFile):

    def preview_name(self):
        return self.name.changeext('.gif')

    def preview_generator(self):
        return PreviewForVideo(self)


class JpegFile(RawFile):
    """
    https://docs.python.org/2.7/library/imghdr.html

    http://stackoverflow.com/questions/266648/python-check-if-uploaded-file-is-jpg

    This one used:
    https://stackoverflow.com/questions/889333/how-to-check-if-a-file-is-a-valid-image-file

    def __init__(self, *args, **kwargs):
        super(JpegFile, self).__init__(*args, **kwargs)

        from PIL import Image
        try:
            im = Image.open(str(self.path))
            im.verify()
        except IOError as e:
            self.warning(str(e))
    """

    def preview_name(self):
        return self.name.changeext('.jpg')

    def preview_generator(self):
        return PreviewForJpeg(self)


class HashFile(File):
    # 10077522

    def __init__(self, **kwargs):
        super(HashFile, self).__init__(**kwargs)
        self.hashes = hashmd5.HashFileToDict(str(self.path)) ### no need fot 'str'

    def excess_on_local(self, archive_folder):
        for op in super(HashFile, self).excess_on_local(archive_folder):
            archive_folder.hash_md5 = op
            yield op

    def check_files(self, folder, archive_flag):
        hashes = self.hashes.copy()
#        print('CHECK_FILES {}'.format(self.path))
        for f in folder.iterate_files():
#            print("ITERATE FILES {}".format(f.name))
            if f.name == conf.HASH_FILE:
 #               print("GOT IT")
                continue
            rp = f.rel_path(folder)
            # if f.lower() not in set(k.lower() for k in hashes):
            if str(rp) in hashes:
                delta = f.mtime - self.mtime
                if delta > 0:
                    # 1
                    f.warning('is newer than {} by{}'.format(
                        conf.HASH_FILE, util.time_delta(delta)))

                # if conf.CHECK_HASH:
                    # conf.IGNORE_FILE_MASKS
                #    show.puts(str(f.path))
                #    if f.path.md5() != hashes[str(rp)]:
                #        f.warning('Hash check failed')

                del hashes[str(rp)]
            else:
                # 3
                if archive_flag:
                    rf = RemoveFile(f)
                    f.replace_myself(rf)
                    yield rf
                else:
                    f.warning('Extra file'.format(rp))

        if not archive_flag:
            for name in list(hashes):#.keys():
                esep = [e + SEP for e in conf.RAW_DIRS_EXTS]
                if any([e in name for e in esep]):
                    #                if SEP in name:
                    del hashes[name]
#        if len(self.hashes) == len(hashes):
#            folder.warning('Missing all files')
#        else:
        # for xxx in hashes:
        #    print("{}|".format(xxx))
        for f in hashes.keys():
            folder.warning('Missing file: {}'.format(f))
            repair.remove(self.path)

    def check(self, remote):
        if remote.hash_md5 is None: #  MUTE_IGNORE
            # This is second archive attached case
            # This branch is never executed as copy phase
            # runs before and remote always has hash.md5 file
            cf = CopyFile(self)
            remote.add_entity(cf)
            yield cf
        else:
            #  here to compare hash_md5 files contents!
            if self.size != remote.hash_md5.size:
                remote.hash_md5.warning(
                    'size differs from {}'.format(self.path))
                return
            elif self.mtime != remote.hash_md5.mtime:
                remote.hash_md5.warning(
                        'modification time {} differs from {}'.format(
                            time.ctime(self.mtime),
                            time.ctime(remote.hash_md5.mtime))
                    )
                return

        # for local folder it never returns any operations
        yield from self.check_files(self.parent, archive_flag=False)

        yield from self.check_files(remote, archive_flag=True)


class list_unique(object):
    #  skip при помощи norm() = None

    def __init__(self, folders, norm, dirs=True):
        self.norm = norm
        self.dirs = dirs
#        self.lists = sorted(folders)
        self.lists = [sorted([e for e in f.entities if norm(e) is not None],
                              key=norm #lambda f: norm(f)
                            ) for f in folders
                      ]

        self.N = len(folders)

    def end(self):
        #        return any([self.g(i) for i in range(self.N)])
        for i in range(self.N):
            if self.g(i) is not None:
                return False
        return True

    def minElement(self):
        minEl = None
        for i in range(self.N):
            if self.g(i) is None:
                continue
            otherEl = self.g(i)
            if minEl is None or self.norm(otherEl) < self.norm(minEl):
                minEl = otherEl
        return minEl

    def __iter__(self):
        self.idx = [0] * self.N
        return self

    def g(self, i):
        if self.idx[i] >= len(self.lists[i]):
            return None
        return self.lists[i][self.idx[i]]

    def skip(self, i):
        g = self.g(i)
        if g is None:
            return False
        return g.skip() or self.norm(g) is None

    def __next__(self):
        return self.next()

    def next(self):
        for i in range(self.N):
            while self.skip(i):
                self.idx[i] += 1
        if self.end(): #  MUTE_IGNORE
            raise StopIteration

        min_el = self.minElement()
        result = []
        for i in range(self.N):
            if self.g(i) is not None and \
                        self.norm(self.g(i)) == self.norm(min_el):
                result.append(self.g(i))
                self.idx[i] += 1
            else:
                result.append(None)
        return result


class Folder(Entity):

    def __init__(self, *args, **kwargs):
        if 'entities' in kwargs: #  MUTE_IGNORE
            self.entities = kwargs['entities']
            del kwargs['entities']
        else:
            self.entities = []
        self.dot_raw = None
        self.hash_md5 = None
        super(Folder, self).__init__(*args, **kwargs)

    def is_protected(self):
        return util.is_protected_folder_stat(mode=self.mode, flags=self.flags)

    def protect(self):
        #        if self.is_protected():
        #            return
        pf = ProtectFolder(self)
        self.replace_myself(pf)
        yield pf

    def populate(self, filter):
        entities = []
        for name in self.path.listdir():
            #print('populate: got {} - {}'.format(name, type(name)))
            entity = self.fabric(name)
            if filter.ignore(entity.vector):
                continue
            show.puts(str(entity.vector), progress=True)
            entity.populate(filter)
            entities.append(entity)
        self.entities = sorted(entities)  # , key=lambda e: e.normIgnoreCase())

    def fabric(self, name):
        path = self.path / name
        params = dict(name=name, parent=self, **path.stat())
        mode = params['mode']
        if stat.S_ISDIR(mode):
            if util.raw_archive_folder(str(name)):
                folder = RawFolder(**params)
                if self.dot_raw is None:
                    self.dot_raw = folder
                else:
                    self.warning('more than one .raw/.big/.jpg folder')
                    folder.warning('extra .raw/.big/.jpg folder')
                return folder
            elif util.is_shadow_dir(str(name)):
                return FolderToSkip(**params)
            else:
                return Folder(**params)
        elif stat.S_ISREG(mode):
            if util.ignore_file(str(name)):
                return FileToSkip(**params)
            if conf.CONTENT:
                # What is faster/better/sell foot print?
                params['extract'] = util.extract_hash(
                    str(path), conf.BLOCK_SIZE)
            if util.is_raw(str(name)):
                return RawFile(**params)
            elif util.is_jpeg(str(name)):
                return JpegFile(**params)
            elif util.is_video(str(name)):
                return VideoFile(**params)
            elif name == conf.HASH_FILE:
                #print('Fabric {}'.format(params))
                self.hash_md5 = HashFile(**params)
                return self.hash_md5
            else:
                return File(**params)
        elif stat.S_ISLNK(mode):
            return Link(**params)
        else:
            f = FileToSkip(**params)
            f.warning('Unsupported file type: 0{:o}'.format(mode))
            return f

    def iterate(self):
        yield self
        for each in self.entities:
            yield from each.iterate()


    def iterate_files(self):
        for each in self.entities:
            yield from each.iterate_files()
                # print('yield', f.name)
                #ield f

    def count_files(self):
        return sum(1 for _ in self.iterate_files())

    def calculate_size(self):
        return sum(each.calculate_size() for each in self.entities)

    def add_entity(self, entity):
        if self.find(entity.name) is not None: #  MUTE_IGNORE
            raise RuntimeError(
                "{}: already in folder {}".format(entity.name, self.path))
        entity.parent = self
        self.entities = sorted(self.entities + [entity],
                               key=lambda each: each.name)

    def find(self, name):
        """
        https://www.khanacademy.org/computing/computer-science/algorithms/binary-search/a/implementing-binary-search-of-an-array
        """
        i = 0
        j = len(self.entities) - 1
        while i <= j:
            k = (i + j) // 2
            if self.entities[k].name == name: #  MUTE_IGNORE
                return self.entities[k]
            if self.entities[k].name < name:  #  MUTE_IGNORE
                i = k + 1
            else:
                j = k - 1
        return None

    def search(self, mask):
        return (each for each in self.entities if each.name.fnmatch(mask))
        #for each in self.entities:
        #    if each.name.fnmatch(mask):
        #        yield each

    def replace(self, old, new):
        i = self.entities.index(old)
        self.entities[i] = new
        new.parent = self
        # , key=lambda e: e.normIgnoreCase())
        self.entities = sorted(self.entities)

    def excess_on_archive(self):
        rf = RemoveFolder(self)
        self.replace_myself(rf)
        yield rf

    def excess_on_local(self, archive_folder):
        cf = CopyFolder(self)
        archive_folder.add_entity(cf)
        yield cf

    def tree(self, padding=' '):
        print(padding[:-1] + '+-' + self.name_for_tree())
        for each in self.entities:
            print (padding + ' |')
            if each is self.entities[-1]: #  MUTE_IGNORE
                each.tree(padding + '  ')
            else:
                each.tree(padding + ' |')

    def cleanup(self):
        self.entities = [each for each in self.entities if each.cleanup()]
        return bool(self.entities) or bool(self.warnings)

    def iterate_same(self, archive):
        yield self, archive
        for loc, arc in list_unique([self, archive], norm=lambda e: e.name):
            show.puts("{}".format(self.vector), progress=True)
            if loc is None or arc is None:  # this never happens as rename
                continue  # phase comes after copy phase
            yield from loc.iterate_same(arc)

    def discrepancy_with_local_folder(self, local):
        show.puts(str(self.vector), progress=True)
        if self.dot_raw is not None and \
                local.dot_raw is not None:
            if self.dot_raw.name != local.dot_raw.name:
                self.warning(
                    'Local has different .raw/.jpg/.big: {}'.format(
                        local.dot_raw.name))
        for loc, arc in list_unique([local, self], norm=lambda e: e.name):
            if loc is None or arc is None:
                continue
            loc.discrepancy_with_archive(arc)

    def discrepancy_with_archive(self, archive):
        archive.discrepancy_with_local_folder(self)

    def rename_class(self):
        return RenameFolder

    def check_hash(self, remote):
        show.puts("{}".format(self.vector), progress=True)
        if self.hash_md5:
            yield from self.hash_md5.check(remote)
            return
        if remote.hash_md5 is not None:
            self.warning('Missing hash.md5 file')
            repair.copy(remote.hash_md5.path, self.path)
            return
        for loc, arc in list_unique([self, remote], norm=lambda e: e.name):
            if loc is None or arc is None:
                continue
            yield from loc.check_hash(arc)


    def iterate_lonely_dot_raw(self, remote):
        if self.dot_raw is None and remote.dot_raw is not None:
            yield self, remote.dot_raw
            return
        for loc, arc in list_unique([self, remote], norm=lambda e: e.name):
            if loc is None or arc is None:
                continue
            yield from loc.iterate_lonely_dot_raw(arc)

    def copy_to_remote(self, archive):
        for src, tgt in list_unique([self, archive], norm=lambda e: e.name):
            if src:
                show.puts("{}".format(src.vector), progress=True)
                if tgt:
                    yield from src.copy_to_remote(tgt)
                else:
                    yield from src.excess_on_local(archive)

    def update_remote(self, archive):
        for src, tgt in list_unique([self, archive], norm=lambda e: e.name):
            if src and tgt:
                show.puts("{}".format(src.vector), progress=True)
                yield from src.update_remote(tgt)

    def remove_remote(self, archive):
        for src, tgt in list_unique([self, archive], norm=lambda e: e.name):
            if tgt:
                show.puts("{}".format(tgt.vector), progress=True)
                if src:
                    yield from src.remove_remote(tgt)
                else:
                    yield from tgt.excess_on_archive()

    def clone(self, new_parent=None):
        folder = super(Folder, self).clone(new_parent)
        folder.entities = [c.clone(folder) for c in self.entities]
        return folder

    def iterate_modified(self, time_stamp):
        """
        Iterate all folders that are newer than time_stamp
        newer means folder or one of its files mtime > time_stamp
        :param time_stamp: threshold value in seconds epoch
        :return: folder entites/paths

        if self.mtime > time_stamp
            return self
        if one of the files mtime > time_stamp:
            return self
        return all subfolders that thant are newer than time_stamp

        """
        result = set()
        for each in self.entities:
            for entity in each.iterate_modified(time_stamp):
                result.add(entity)

        if time_stamp < self.mtime or self in result:
            yield self
        else:
            for each in result:
                yield each

    def reduce(self, scope):
        self.entities = [e for e in self.entities if e in scope]
        for each in self.entities:
            each.reduce(scope)


class FolderToSkip(Folder):

    def __init__(self, *args, **kwargs):
        super(Folder, self).__init__(*args, **kwargs)
        self.entities = []

    def skip(self):
        return True

    def populate(self, filter):
        pass

    def iterate(self):
        return # iter(())
        yield None

    def iterate_files(self):
        return
        yield None

    def cleanup(self):
        pass

    def iterate_modified(self, time_stamp):
        return
        yield None


class RootFolder(Folder):

    def __init__(self, root, *args, **kwargs):
        self._root = root
        metadata = dict(**self._root.stat())
        metadata.update(kwargs)
        super(RootFolder, self).__init__(*args, **metadata)

    @property
    def root(self):
        return self._root

    @property
    def path(self):
        return self.root / self.name

    @property
    def vector(self):
        return self.name

    def iterate_warnings(self):
        for each in self.iterate():
            for w in each.warnings:
                yield each.path, w

    def list_warnings(self, title=None, tee=None):
        have_warnings_flag = False
        for path, warn in self.iterate_warnings():
            if title: #  MUTE_IGNORE
                print(title)
                title = ""
            have_warnings_flag = True
            msg = '{}: {}\n'.format(path, warn)
            sys.stdout.write(msg)
            if tee:
                tee.write(msg)
        return have_warnings_flag

    def have_warnings(self):
        return any(True for __ in self.iterate_warnings())

    def name_for_tree(self):
        if self.warnings: #  MUTE_IGNORE
            return "{} ({}) [{}]".format(
                self.path,
                ", ".join(self.warnings),
                self.__class__.__name__)
        return "{} [{}]".format(self.path, self.__class__.__name__)


class RawFolder(Folder):

    def populate(self, filter):
        super(RawFolder, self).populate(filter)

        if any([isinstance(s, RawFolder) for s in self.genealogy()]):
                self.warning('Nested .raw folder')

        for a, b in zip(self.entities, self.entities[1:]):
            if util.is_image(str(a.name)) and util.is_image(str(b.name)) and \
                    a.only_name() == b.only_name():
                self.warning(
                    "Two files with same name are not supported" +
                    " - {} and {}".format(a.name, b.name))
                if util.is_raw(str(a.name)) and util.is_jpeg(str(b.name)):
                    #  another option is to ignore jpg with same name as raw,
                    #   so it will not be backed up and will not used to generate preview
                    repair.remove(b.path)
                elif util.is_jpeg(str(a.name)) and util.is_raw(str(b.name)):
                    repair.remove(a.path)
                break

    def warn_and_repair(self, preview):
        preview.warning("Missing raw file for this index")
        if preview.name.fnmatch('*-[0-9][0-9].*'):
            only_name = preview.name.onlyname()[:-3]
            mask = '{}*'.format(only_name)
            if any(True for _ in self.search(mask)):
                new_name = only_name + preview.name.ext()
                repair.rename(preview.path, new_name)
        else:
            repair.remove(preview.path)

    def check_raw(self, local_folder):
        # lonely .raw folder
        #print("check_raw({})".format(local_folder))
        #show.puts("{}".format(self.vector), progress=True)
        has_files = False
        for loc, arc, raw in list_unique(
                [local_folder, self.parent, self],
                norm=lambda e: e.norm_ignore_extension()):
            #print("check_raw loc arc raw")
            has_files = True
            if raw:
                yield from raw.check_previews(loc, arc, local_folder)
                continue
            else:  # not raw
                if loc:
                    self.warn_and_repair(loc)
                if arc:
                    self.warn_and_repair(arc)
        #print("check_raw x")
        if not has_files:
            self.warning('Empty .raw folder')
            repair.remove(self.path)

    def check_protection(self):
        for each in self.iterate():
            if each.is_protected():
                continue
            yield from each.protect()

    def is_preview(self):
        r = super(RawFolder, self).is_preview()
        return r

    def excess_on_archive(self):
        return
        yield None

    def gen_hash(self, local):
        if self.parent.hash_md5 is not None:
            return
        hfg = HashFileGenerator(self.parent)
        self.parent.add_entity(hfg)
        yield hfg
        cf = CopyFile(hfg)
        local.add_entity(cf)
        yield cf


class Operation(object):

    def go(self, sync):
        if sync.log_file is None:
            self.run()
            return
        with util.log_time(sync.log_file,
                self.__class__.__name__,
                self.size, self.path):
            self.run()

    def run(self):
        pass

    def cleanup(self):
        return True

    def time_estimate(self):
        return


class CopyFile(File, Operation):

    def __init__(self, source_entity):
        super(CopyFile, self).__init__(**source_entity.__dict__)
        self.source = source_entity

    def run(self):
        self.source.clear_uf_tracked_flag()
        # in case we want to deal more accurate with
        # upper/lower case, we need to create separate operations
        # "UpdateFile" or "OverwriteFile" that would do more granular
        self.path.remove_if_exist()
        self.source.path.copy2(self.path)

    def name_for_tree(self):
        p = super(CopyFile, self).name_for_tree()
        return "{} - copy of {}".format(p, self.source.path)

    def operation_name(self):
        return "Copy file: {}".format(self.source.vector)

    def time_estimate(self):
        return self.size * 200


class RemoveFile(File, Operation):

    def __init__(self, entity):
        super(RemoveFile, self).__init__(**entity.__dict__)
        return
#  to get folder with symlinks to all files to be removed
#        p = '/Users/michael/Pictures/photo/Software/Scripts/PhotoSync/remove'
#        import os
#        os.symlink(str(self.path), str(p / self.name))

    def run(self):
        self.path.remove()  # should work for both files and links

    def operation_name(self):
        return "Remove file: {}".format(self.vector)

    def iterate(self):
        return
        yield None

    def iterate_files(self):
        return
        yield None

    def skip(self):
        return True

    def time_estimate(self):
        return 1


class CopyFolder(Folder, Operation):

    def __init__(self, source_entity):
        super(CopyFolder, self).__init__(**source_entity.clone().__dict__)
        for each in self.entities:
            each.parent = self
        self.source = source_entity
        self.total_size = self.source.calculate_size()

    def run(self):

        def progress(path):
            show.puts(": {}".format(path), progress=True)

        def ignore(path):
            return util.ignore_file(str(path))

        self.source.path.copytree(self.path, ignore=ignore, progress=progress)

    def name_for_tree(self):
        p = super(CopyFolder, self).name_for_tree()
        return "{} - copy".format(p)

    def operation_name(self):
        return "Copy folder: {}".format(self.vector)

    def time_estimate(self):
        return self.total_size * 200


class RemoveFolder(Folder, Operation):

    def __init__(self, entity):
        super(RemoveFolder, self).__init__(**entity.__dict__)

    def run(self):
        self.path.rmtree()

    def skip(self):
        return True

    def operation_name(self):
        return "Remove folder: {}".format(self.vector)

    def time_estimate(self):
        return 1


class CopyLink(Link, Operation):

    def __init__(self, source_entity):
        super(CopyLink, self).__init__(**source_entity.__dict__)
        self.source = source_entity

    def run(self):
        self.source.path.copy_link(self.path)

    def name_for_tree(self):
        p = super(CopyLink, self).name_for_tree()
        return "{} - copy".format(p)

    def operation_name(self):
        return "Copy link: {}".format(self.source.vector)

    def time_estimate(self):
        return 1


class RemoveLink(Link, Operation):

    def __init__(self, entity):
        super(RemoveLink, self).__init__(**entity.__dict__)

    def run(self):
        self.path.remove()  # should work for both files and links

    def skip(self):
        return True

    def operation_name(self):
        return "Remove link: {}".format(self.vector)

    def iterate_files(self):  # This is not used currently
        return
        yield None

    def time_estimate(self):
        return 1


class RenameFile(File, Operation):

    def __init__(self, entity, source_entity):
        super(RenameFile, self).__init__(**entity.__dict__)
        self.source = source_entity

    def run(self):
        self.path.rename(self.basename / self.source.name)

    def name_for_tree(self):
        p = super(RenameFile, self).name_for_tree()
        return "{} - renamed to {}".format(p, self.source.name)

    def operation_name(self):
        return "Rename file: {} -> {}".format(self.vector, self.source.name)

    def time_estimate(self):
        return 1


class RenameFolder(Folder, Operation):

    def __init__(self, entity, source_entity):
        super(RenameFolder, self).__init__(**entity.__dict__)
        self.source = source_entity

    def run(self):
        self.path.rename(self.basename / self.source.name)

    def name_for_tree(self):
        p = super(RenameFolder, self).name_for_tree()
        return "{} - renamed to {}".format(p, self.source.name)

    def operation_name(self):
        return "Rename folder: {} -> {}".format(self.vector, self.source.name)

    def time_estimate(self):
        return 1


class RenameLink(File, Operation):

    def __init__(self, entity, source_entity):
        super(RenameLink, self).__init__(**entity.__dict__)
        self.name = source_entity.name
        self.source = source_entity

    def run(self):
        self.path.remove()
        self.source.path.copy_link(self.basename / self.source.name)

    def name_for_tree(self):
        p = super(RenameLink, self).name_for_tree()
        return "{} - renamed to {}".format(p, self.source.name)

    def operation_name(self):
        return "Rename link: {} -> {}".format(self.vector, self.source.name)

    def time_estimate(self):
        return 1


class PreviewForRaw(JpegFile, Operation):

    def __init__(self, raw):
        self.raw = raw
        super(PreviewForRaw, self).__init__(
            name=raw.preview_name(),
            mode=raw.mode,
            mtime=int(time.time()),
            size=100000,
            flags=0,
            nlink=0,
            extract=''
        )

    def run(self):
        preview.preview_for_raw(str(self.raw.path), str(self.path))
        #show.pop()

    def name_for_tree(self):
        p = super(PreviewForRaw, self).name_for_tree()
        return "{} - preview from {}".format(p, self.raw.path)

    def operation_name(self):
        return "Рreview for: {} ".format(self.raw.vector)

    def time_estimate(self):
        return self.raw.size * 200


class PreviewForVideo(PreviewForRaw):

    def run(self):
        preview.preview_for_video(str(self.raw.path), str(self.path))
        #show.pop()

    def time_estimate(self):
        return self.raw.size * 1350


class PreviewForJpeg(PreviewForRaw):

    def run(self):
        preview.preview_for_jpeg(str(self.raw.path), str(self.path))
        #show.pop()

    def time_estimate(self):
        return self.raw.size * 300


class ProtectFile(File, Operation):

    def __init__(self, entity):
        super(ProtectFile, self).__init__(**entity.__dict__)

    def run(self):
        util.protect_file(str(self.root), str(self.vector))

    def name_for_tree(self):
        p = super(ProtectFile, self).name_for_tree()
        return "{} (protected)".format(p)

    def operation_name(self):
        return "Protect file: {}".format(self.vector)

    def time_estimate(self):
        return 1


class HashFileGenerator(File, Operation):

    def __init__(self, folder):
        super(HashFileGenerator, self).__init__(
            name=Path(conf.HASH_FILE),
            parent=folder,
            mode=0o644,
            size=100,
            flags=0,
            mtime=int(time.time()),
            nlink=1)
        self.total_size = self.parent.calculate_size()

    def run(self):
        h = dict()
        for f in self.parent.path.listfiles(exclude=[conf.HASH_FILE] +
                                            conf.IGNORE_FILE_MASKS):
            show.puts(": {}".format(f), progress=True)
            h[str(f)] = (self.parent.path / f).md5()
        hashmd5.HashesToFile(h, str(self.path))

    def name_for_tree(self):
        p = super(HashFileGenerator, self).name_for_tree()
        return "{} (to be generated)".format(p)

    def operation_name(self):
        return "Generate hash for {}".format(self.parent.vector)

    def time_estimate(self):
        return self.total_size * 4


class ProtectFolder(RawFolder, Operation):

    def __init__(self, entity):
        super(ProtectFolder, self).__init__(**entity.__dict__)

    def run(self):
        util.protect_folder(str(self.root), str(self.vector))

    def name_for_tree(self):
        p = super(ProtectFolder, self).name_for_tree()
        return "{} (protected)".format(p)

    def operation_name(self):
        return "Protect folder: {}".format(self.vector)

    def cleanup(self):
        super(RawFolder, self).cleanup()
        return True

    def time_estimate(self):
        return self.count_files() * 1
