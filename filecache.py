import os
import time
from io import StringIO
from io import BytesIO
import magic

from . import log


from threading import Lock
_mime_lock=None

if not _mime_lock:
    _mime_lock=Lock()


class NotInitException(Exception): pass


def _mime(path):
    p=path.lower()
    if p.endswith(".html"): return "text/html"
    if p.endswith(".css"): return "text/css"
    if p.endswith(".js"): return "text/javascript"
    try:
        _mime_lock.acquire()
        x=magic.detect_from_filename(path)
        #log.info(path, ":", x)
        mi= x.mime_type
        _mime_lock.release()
        return mi
    except:
        _mime_lock.release()
        return "text/plain"


FILETYPES=[".html", ".css", ".js", ".ttf", ".woff2"]
MAX_FILE_SIZE=1024*1024 # 1 Mio
class CacheEntry:

    def __init__(self, path : str):
        self.path=path
        self.time=time.time()
        self.cached=False
        self.data=None
        self.data_str=None
        self._update()


    def _update(self):
        if self.path.endswith(".html"):
            self.mime="text/html"
        elif self.path.endswith(".css"):
            self.mime="text/css"
        elif self.path.endswith(".js"):
            self.mime="application/javascript"
        else:
            self.mime=_mime(self.path)
        self.size=os.stat(self.path).st_size
        if self.size<=MAX_FILE_SIZE:
            for x in FILETYPES:
                if self.path.endswith(x):
                    self.cached=True
                    break
        if self.cached :
            with open(self.path, "rb") as f:
                self.data=f.read()
            self.data_str=self.data.decode("utf-8", "replace")

    def open(self, mode):
        if self.cached:
            if mode=="r":
                return StringIO(self.data_str)
            else:
                return BytesIO(self.data)
        else:
            log.debug("Cache fail for '"+self.path+"'")
            return open(self.path, mode)

    def _need_invalidate(self):
        return False

    def invalidate(self):
        return self._update()

    def get(self, invalid=False):
        if self._need_invalidate() or invalid:
            self.invalidate()
        return self


class FileCache:
    _INSTANCE=None
    def __init__(self, dirs=[], bypass=True):
        self.db={}
        self.preload(dirs)
        self.bypass=bypass


    def find_total_size(self):
        acc=0
        for x in self.db:
            obj=self.db[x]
            acc+=obj.size*2
        return acc

    def _get_cached(self, path, invalidate):
        #le fichier n'est pas dans la cache
        if not path in self.db:
            x=CacheEntry(path)
            self.db[path]=x
            return x
        return self.db[path].get(invalidate)

    def preload(self, path):
        if isinstance(path, str): path=[path]
        for p in path:
            if os.path.isdir(p):
                tmp=[]
                for name in os.listdir(p):
                    tmp.append(os.path.join(p, name))
                self.preload(tmp)
            elif os.path.isfile(p):
                self._get_cached(p)

    def invalidate(self, path):
        return self._get_cached(path, True)

    def mime(self, path, invalidate=False):
        return self._get_cached(path, invalidate).mime if not self.bypass else _mime(path)

    def open(self, path, mode="r", invalidate=False, encoding="utf-8"):
        if not self.bypass:
            return self._get_cached(path, invalidate).open(mode)
        else:
            if "b" in mode:
                return open(path, mode)
            else:
                return open(path, mode, encoding=encoding)



class filecache:
    @staticmethod
    def init(dirs=[], useCache=False): FileCache._INSTANCE=FileCache(dirs, not useCache)

    @staticmethod
    def isinit(): return FileCache._INSTANCE!=None

    @staticmethod
    def preload(path):
        if not FileCache._INSTANCE: raise NotInitException()
        return FileCache._INSTANCE.preload(path)

    @staticmethod
    def invalidate(path):
        if not FileCache._INSTANCE: raise NotInitException()
        return FileCache._INSTANCE.invalidate(path)

    @staticmethod
    def mime(path, inv=False):
        if not FileCache._INSTANCE: raise NotInitException()
        return FileCache._INSTANCE.mime(path, inv)

    @staticmethod
    def open(path, mode="r", inv=False, encoding="utf-8"):
        if not FileCache._INSTANCE: raise NotInitException()
        return FileCache._INSTANCE.open(path, mode, inv, encoding)
