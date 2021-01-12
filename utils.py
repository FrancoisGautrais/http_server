import json
import os
import stat
import threading
import uuid
import random

import magic
import pystache
from threading import Lock
from threading import Thread
import hashlib
from hashlib import sha3_512
import base64


def path_to_list(p):
    out=[]
    p=p.split("/")
    for v in p:
        if v!='': out.append(v)
    return out


class Callback:

    def __init__(self, fct=None, obj=None, data=None):
        self.fct=fct
        self.obj=obj
        self.data=data


    def call(self, prependParams=(), appendParams=()):
        data=None
        if not self.fct: return None
        if self.data!=None:
            data=prependParams+(self.data,)+appendParams

        if self.obj:
            if data:
                return self.fct(self.obj, *data)
            else:
                x=prependParams+appendParams
                if x:
                    return self.fct(self.obj, *x)
                else:
                    return self.fct(self.obj)
        else:
            if data:
                return self.fct(*data)
            else:
                x=prependParams+appendParams
                if x:
                    return self.fct(*x)
                else:
                    return self.fct()


class ThreadWrapper(Thread):

    def __init__(self, cb : Callback):
        Thread.__init__(self)
        self.cb=cb

    def run(self):
        self.cb.call()


def start_thread(cb : Callback):
    t=ThreadWrapper(cb)
    t.start()
    return t


def html_template(path, data):
    with open(path) as file:
        return pystache.render(file.read(), data)

def html_template_string(source, data):
    return pystache.render(source, data)

def sha256(s):
    m=hashlib.sha256()
    m.update(bytes(s, "utf-8"))
    return m.digest()



def tuplist_to_dict(tuplelist):
    out={}
    for k in tuplelist:
        out[k[0]]=k[1]
    return out

def dictinit(*args):
    out={}
    for k in args:
        out.update(k)
    return k


_MIME_TO_TYPES={
    "audio" : { "*": "audio"},
    "video" : { "*": "video"},
    "image" : { "*": "image"},
    "text" : { "*": "document" },
    "application" :  {
        #Archives
        "zip,x-bzip,x-tar,x-rar-compressed,bzip2,x-tar+gzip,gzip" : "archive",

        #defaut
        "*" 				: "document"
    },
    "*" : "document"
}
MIME_TO_TYPES={}


def _init_mime():
    global _MIME_TO_TYPES
    global MIME_TO_TYPES
    out={}
    out["*"]=_MIME_TO_TYPES["*"]
    for x in _MIME_TO_TYPES:
        if x!="*":
            out[x]={}
            for k in _MIME_TO_TYPES[x]:
                if k!="*":
                    li=k.split(",")
                    val=_MIME_TO_TYPES[x][k]
                    for key in li:
                        out[x][key]=val
            out[x]["*"]=_MIME_TO_TYPES[x]["*"]
    out["*"] = _MIME_TO_TYPES["*"]
    MIME_TO_TYPES=out

_init_mime()

from threading import Lock
_mime_lock=None

if not _mime_lock:
    _mime_lock=Lock()


class NotInitException(Exception): pass


def mime(path):
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


def mime_to_type(m):
    first, second = m .split("/")
    if first in MIME_TO_TYPES:
        if second in MIME_TO_TYPES: return MIME_TO_TYPES[first][second]
        return MIME_TO_TYPES[first]["*"]
    return MIME_TO_TYPES["*"]

from urllib.parse import unquote_plus, quote_plus

def urldecode(string, encoding='utf-8', errors='replace'):
    return unquote_plus(string, encoding=encoding, errors=errors)

def urlencode(string, safe='', encoding=None, errors=None):
    return quote_plus(string, safe, encoding, errors)


def encode_dict(opt):
    out=""
    i=0
    for key in opt:
        if i>0:
            out+="&"
        if isinstance(opt[key], dict):
            val = urlencode(json.dumps(opt[key]))
        else:
            val=urlencode(opt[key])
        out+="%s=%s" % (key, val)
        i+=1
    return out

def encode_cookies(cookies):
    return  "; ".join([str(x)+"="+str(y) for x,y in cookies.items()])


def dictassign(src, *args):
    for x in args:
        for y in x:
            src[y]=x[y]
    return src

def encode_dict(opt):
    out=""
    i=0
    for key in opt:
        if i>0:
            out+="&"
        if isinstance(opt[key], dict):
            val = urlencode(json.dumps(opt[key]))
        else:
            val=urlencode(opt[key])
        out+="%s=%s" % (key, val)
        i+=1
    return out

def dictget(obj, key, default=None):
    return obj[key] if key in obj else default

def url(self, path="/", attr=None):
    url = self.config["url"] + path
    if attr:
        url += "?"
        i = 0
        for key in attr:
            if i > 0:
                url += "&"
            val = attr[key]
            url += urlencode(key) + "=" + urlencode(val)
            i += 1
    return url


_KEY_CHARACTER="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-"


def new_id( size = 32):
    n = len(_KEY_CHARACTER)
    out = ""
    for i in range(size):
        out += _KEY_CHARACTER[random.randint(0, n - 1)]
    return out




def _deepcassign(src : dict, mod : dict):
    if not isinstance(src, dict) or not isinstance(mod, dict):
        return None
    for key in mod:
        if key in src:
            if isinstance(src[key], dict):
                if isinstance(mod[key], dict):
                    src[key]=_deepcassign(src[key], mod[key])
                else:
                    src[key]=mod[key]
            else:
                if isinstance(mod[key], dict):
                    src[key]=_deepcassign({}, mod[key])
                else:
                    src[key]=mod[key]
        else:
            if isinstance(mod[key], dict):
                src[key]=_deepcassign({}, mod[key])
            else:
                src[key]=mod[key]
    return src

def deepassign(src, *args):
    for arg in args:
        src=_deepcassign(src, arg)
    return src


def file_foreach(dir, fct, recursive=False):
    for file in os.listdir(dir):
        path=os.path.join(dir, file)
        f = os.stat(path)
        fct(path,f)
        if stat.S_ISDIR(f.st_mode) and recursive:
            file_foreach(path, fct, True)


def dictassign(dest, *sources):
    for d in sources:
        for key in d:
            dest[key]=d[key]
    return dest

def dictcopy(*sources):
    return dictassign({}, *sources)


def urlencode(x):
    return parse.quote_plus(x)

def urldecode(x):
    return parse.quote_plus(x)

def password(pwd):
    x=sha3_512(pwd.encode()).digest()
    return base64.b64encode(x).decode("ascii")

def check_password(plain, encr):
    return password(plain)==encr

def new_key(size):
    out = ""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    for i in range(size):
        out += chars[random.randint(0, len(chars) - 1)]
    return out