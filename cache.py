from . import utils
from threading import Lock


class _CacheEntry:
    def __init__(self):
        self.data=None
        self.mime=None

    @staticmethod
    def from_file(path):
        ce = _CacheEntry()
        with open(path, "rb") as f:
            ce.data=f.read()
        ce.mime=utils.mime(path)
        return ce

    @staticmethod
    def from_data(data, mime):
        ce = _CacheEntry()
        ce.data=data
        ce.mime=mime
        return ce


class Cache:

    def __init__(self):
        self.db={}
        self.lock=Lock()


    def cache_file(self, path):
        ce = _CacheEntry.from_file(path)
        self.lock.acquire()
        self.db[path]=ce
        self.lock.release()
        return ce

    def cache_data(self, path, data, mime):
        self.lock.acquire()
        ce = _CacheEntry.from_data(data, mime)
        self.db[path]=ce
        self.lock.release()
        return ce

    def __getitem__(self, item):
        if item in self.db:
            return self.db[item].data
        return None

    def mime(self, item):
        if item in self.db:
            return self.db[item].mime
        return None

    def get(self, item):
        if item in self.db:
            return self.db[item]
        return None


    def has(self, item):
        return item in self.db