import time
import os
import glob

class FileWatcher(object):
    def __init__(self, directory, interval):
        self.directory = directory
        self.interval = interval
        self.last = time.time()

    def __call__(self):
        dt = self.last + self.interval - time.time()
        time.sleep(max(0, dt))

        files = glob.glob(os.path.join(self.directory, '*.h5'))
        mtimes = list(map(os.path.getmtime, files))
        new_files = [file for file,mtime in zip(files, mtimes) if mtime >= self.last]

        self.last = time.time()

        return new_files
