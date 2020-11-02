import json
import threading
import uuid
import random
import pystache
from threading import Lock
from threading import Thread
import hashlib

from .filecache import filecache

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
    with filecache.open(path) as file:
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


