import time
import warnings
from collections import defaultdict
import os
import h5py
import numpy as np

import larpix.format.rawhdf5format as rh5
import larpix.format.hdf5format as h5
from larpix.format.pacman_msg_format import parse
from larpix import PacketCollection

class FileParser(object):
    def __init__(self, max_msgs, clean_up_interval):
        self.max_msgs = max_msgs
        self.clean_up_interval = clean_up_interval

        self._curr_index = defaultdict(int)
        self._last_updated = defaultdict(lambda : time.time())

    def __call__(self, datafiles):
        datafile_fh = list()
        for file in datafiles:
            try:
                self._remove_temp_file(file)
                datafile_fh.append(self._load_raw_hdf5(file))
            except Exception as e:
                warnings.warn('could not load {} as raw hdf5! \nError: {}'.format(file, e), RuntimeWarning)
                datafile_fh.append(dict(packets=np.empty((0,))))

            self._last_updated[file] = time.time()

        self._clean_up()

        return datafile_fh

    def _load_raw_hdf5(self, filename):
        length = rh5.len_rawfile(filename)
        end = min(length, self.max_msgs+self._curr_index[filename])
        rd = rh5.from_rawfile(filename, start=self._curr_index[filename], end=end)
        pkts = list()
        for io_group,msg in zip(rd['msg_headers']['io_groups'], rd['msgs']):
            pkts.extend(parse(msg, io_group=io_group))
        self._curr_index[filename] = length
        h5.to_file(self._temp_filename(filename), pkts)
        return h5py.File(self._temp_filename(filename), 'r')

    def _temp_filename(self, filename):
        return '{}.dqm.h5'.format(os.path.basename(filename[:-3]))

    def _remove_temp_file(self, filename):
        if os.path.exists(self._temp_filename(filename)):
            os.remove(self._temp_filename(filename))

    def _clean_up(self):
        to_clean = []
        for filename,last in self._last_updated.items():
            if time.time() > last + self.clean_up_interval:
                to_clean.append(filename)
        for filename in to_clean:
            del self._last_updated[filename]
            del self._curr_index[filename]

