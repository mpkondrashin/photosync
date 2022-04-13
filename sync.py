#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import contextlib

from entity import *
import path


@contextlib.contextmanager
def note_time():
    time_start = time.time()
    yield
    delta = int(time.time() - time_start)
    show.puts(f'{delta} seconds elapsed')
    show.newline()


class Operations(list):
    def __init__(self):
        super(Operations, self).__init__([])

    def show(self):
        for o in self:
            print(o.operation_name())
        #            print("{}: {}".format(de.__class__.__name__, de.path))

    def go(self, sync):
        #show.pushs('Sync: ')
        total_time = sum([o.time_estimate() for o in self])
        if total_time == 0: total_time = 1  #  MUTE_IGNORE
        cur_time = 0
        for o in self:
            percent = cur_time * 100 // total_time
            show.pushs('{}% {}'.format(percent, o.operation_name()))
            cur_time += o.time_estimate()
            o.go(sync)
            show.pop()


class Sync(object):

    def __init__(self, sourceDir, targetDir, vector, _filter,
                 noprotect, nohash):#, time_stamp):
        print("Sync(sourceDir={}, targetDir={}, vector={}, filter=({}), noprotect={}, nohash={}".format(
            sourceDir, targetDir, vector, _filter, noprotect, nohash))

        self.operations = Operations()

        self.source = RootFolder(name=path.Path(vector), root=path.Path(sourceDir))
        self.target = RootFolder(name=path.Path(vector), root=path.Path(targetDir))
        self.filter = _filter

        self.phases = [
            ('Scan archive drive', self.phase_populate_target),
            ('Scan local drive', self.phase_populate_source),
            ('Statistics', self.phase_statistics),
            ('Check for discrepancy', self.phase_discrepancy),
            ('Check for new files', self.phase_copy),
            ('Check hash.md5 files', self.phase_hash),
            ('Check case', self.phase_rename),
            ('Preview phase', self.phase_preview),
            ('Check for updated files', self.phase_update),
            ('Check for files to remove', self.phase_remove),
        ]
        if not nohash:
            self.phases += [
                ('Generate hash phase', self.phase_gen_hash)
            ]

        if not noprotect:
            self.phases += [
                ('Protect phase', self.phase_protect)
            ]

        self.log_file = None

    def have_warnings(self):
        return self.source.have_warnings() or self.target.have_warnings()

#    def count_source_files(self):
#        return self.source.count_files()

    def sync_with_local(self):
        phase_duration = []
        for n, (name, phase) in enumerate(self.phases):
            show.pushs('{:2}. {}: '.format(n+1, name))
            time_start = time.time()
            operations_count_before = self.operations_count()
            phase()
            new_operations = self.operations_count() - operations_count_before
            time_end = time.time()
            time_delta = time_end - time_start
            if self.have_warnings():
                show.puts('have warnings')
                show.newline()
                return
            #show.puts('done')
            #show.puts('done ({} files in{})'.format(count, util.time_delta(time_delta)))
            show.pushs('completed in{}'.format(util.time_delta(time_delta)))
            phase_duration.append((time_delta, phase.__name__))
            if new_operations > 0: #  MUTE_IGNORE
                show.pushs('. {} operation(s)'.format(new_operations))
            show.newline()
#            self.source.tree()
#            print('')
#            self.target.tree()

        total_time = sum(d[0] for d in phase_duration)
        for duration, name in phase_duration:
            print("{}: {:.2f}%".format(name, duration*100./total_time))

    def phase_populate_source(self):
        self.source.populate(self.filter)
        ### print('')
        ### self.source.tree()
        ### print('')

    def phase_populate_target(self):
#        print('\n'.join(self.include))
        self.target.populate(self.filter)
        # self.target.tree()

    def phase_statistics(self):
        source_count = self.source.count_files()
        target_count = self.target.count_files()
        show.pushs('Source files: {}, Target files: {}: '.format(source_count, target_count))

    def phase_discrepancy(self):
        self.source.discrepancy_with_archive(self.target)

    def phase_copy(self):
        self.operations += self.source.copy_to_remote(self.target)

    def phase_update(self):
        self.operations += self.source.update_remote(self.target)

    def phase_remove(self):
        self.operations += self.source.remove_remote(self.target)

    def phase_hash(self):
        self.operations += self.source.check_hash(self.target)

    def phase_rename(self):
        for loc, arc in self.source.iterate_same(self.target):
            self.operations += loc.sync_case(arc)

    def phase_preview(self):
        for loc, raw in self.source.iterate_lonely_dot_raw(self.target):
            self.operations += raw.check_raw(loc)

    def phase_gen_hash(self):
        for loc, raw in self.source.iterate_lonely_dot_raw(self.target):
            show.puts("{}".format(raw.vector), progress=True)
            self.operations += raw.gen_hash(loc)

    def phase_protect(self):
        for __, raw in self.source.iterate_lonely_dot_raw(self.target):
            self.operations += raw.check_protection()

    def go(self, protect=True):
        show.pushs('sync phase: ')
        ### TEMP
        if '/Volumes/' in str(self.target.path): #  MUTE_IGNORE
            log_file_name = os.path.join(os.path.dirname(__file__), 'log.csv')
            self.log_file = open(os.path.abspath(log_file_name), 'a')
        with note_time():
            self.operations.go(self)
        ### TEMP:
        if self.log_file is not None:  #  MUTE_IGNORE
            self.log_file.close()

        show.puts('done')
        show.newline()

        # нестеров поляков лутков
    def operations_count(self):
        return len(self.operations)

    '''
    def statistics(self):
        s = self.source.statistics()
        s += self.target.statistics()
        return s
    '''
    def list_warnings(self, tee=None):
        rc_source = self.source.list_warnings('Local Warnings:', tee)
        rc_target = self.target.list_warnings('Archive Warnings:', tee)
        return rc_source or rc_target

