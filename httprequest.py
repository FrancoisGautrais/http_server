# coding: utf-8

import json
import io
import sys
import traceback
import os
import time

from . import utils

from . import log
from .utils import dictinit

from .socketwrapper import SocketWrapper
from .formfile import FormFile
from .htmltemplate.htmlgen import html_gen, html_meta
from .htmltemplate.instructions_loader import InstructionStackException

HTTP_OK=200
HTTP_BAD_REQUEST=400
HTTP_UNAUTHORIZED=401
HTTP_NOT_FOUND=404
HTTP_TEMPORARY_REDIRECT=307

STR_HTTP_ERROR={
    HTTP_OK: "OK",
    HTTP_UNAUTHORIZED: "Unauthorized",
    HTTP_BAD_REQUEST: "Bad request",
    HTTP_NOT_FOUND: "Not Found",
    HTTP_TEMPORARY_REDIRECT: "Temporary redirect"
}

def fromutf8(x): return bytes(x, "utf8")

_HTTP_CODE={
    100: "Continue",

    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",

    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",

    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    418: "I’m a teapot",

    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Time-out"
}

BODY_DICT="dict"
BODY_EMPTY="none"
BODY_STRING="string"
BODY_FILE="file"
BODY_BYTES="bytes"

from urllib.parse import unquote

JSON_MIME=["application/json", "application/x-javascript", "text/javascript", "text/x-javascript", "text/x-json"]
URLENCODED_MIME= [ "application/x-static-form-urlencoded", "application/x-www-form-urlencoded" ]
TEXT_MIME=["text/plain", "text/html", "text/javascript", "text/x-javascript", "text/x-json"]


def parse_urlencoded_params(string):
    out={}
    for k in string.split("&"):
        n = k.find("=")
        key = ""
        value = ""
        v = ""
        if n > 0:
            key = unquote(k[:n])
            value = unquote(k[n + 1:])
        else:
            key = unquote(k)
        if key in out:
            if not isinstance(out[key], list):
                out[key]=[out[key], value]
            else: out[key].append(value)
        else: out[key] = value
    return out

class _HTTP:

    def __init__(self):
        self._headers={}
        self.body=None
        self._body_type=BODY_EMPTY

    def body_type(self):
        return self._body_type

    def content_length(self, n:int=-1 ):
        x=self.header("Content-Length")
        return x if x else 0

    def content_type(self, x=None):
        if x:
            self.header("Content-Type", x)
            return x
        else: return self.header("Content-Type")

    def body_json(self):
        if self._body_type==BODY_DICT: return self.body
        raise Exception("Bad body format")

    def body_bytes(self):
        if self._body_type==BODY_BYTES: return self.body
        raise Exception("Bad body format")

    def body_text(self):
        if self._body_type==BODY_STRING: return self.body
        raise Exception("Bad body format")

    def body_file(self):
        if self._body_type==BODY_FILE: return self.body
        raise Exception("Bad body format")

class HTTPRequest(_HTTP):

    def __init__(self, socket, parse_headline=True):
        _HTTP.__init__(self)
        self.method=None
        self.start_time=time.time()
        self.total_time=-1
        self.stop_time=-1
        self.version=""
        self.url="/"
        self.path="/"
        self.query={}
        self.params={}
        self.cookies={}
        self.filename=""
        self._head_line_parsed=parse_headline
        self._socket=socket
        self.ip=self._socket

        if self._head_line_parsed:
            self._parse_command_line()

    def get_socket(self):
        return self._socket

    def is_mobile(self):
        info = self.header("User-Agent")
        if info:
            return "mobi" in info.lower()
        return False

    def get_ip(self):
        return self._socket.get_ip()

    def header(self, key : str):
        if key in self._headers:
            return self._headers[key]
        if key.lower() in self._headers:
            return self._headers[key.lower()]
        return None

    def get_total_time(self):
        return self.total_time

    def parse(self):
        self._parse_head()
        if (("Content-Type" in self._headers) and not self.header("Content-Type").startswith("multipart/form-data")) or\
            (("content-type" in self._headers) and not self.header("content-type").startswith("multipart/form-data")):
            self._parse_body()

    def is_multipart(self):
        h = self.header("Content-Type")
        return h and h.startswith("multipart/form-data")

    def multipart_next_file(self):
        ct = self.header("Content-Type")
        objct={}
        for x in ct.split(";"):
            if x.find("=")>0: objct[x[:x.find("=")].lstrip()]=x[x.find("=")+1:]
        boundary=objct["boundary"]
        f = FormFile(self._socket, boundary)
        if f.parse_head():
            return f
        return None

    def _parse_head(self):
        #parse 1st line if it is not done
        if not self._head_line_parsed :
            self._parse_command_line()

        # parse all headers
        line = self._socket.readline()[:-1]
        while len(line)>0:
            key=line[:line.find(":")]
            val=line[line.find(":")+1:].lstrip()
            self._set_header(key, val)
            line=self._socket.readline()[:-1]

    def __deepcopy__(self, memodict={}):
        return self

    def _parse_body(self):
        l=self.content_length()
        if not l:
            self._body_type=BODY_EMPTY
            self.body=bytes()

        ct = "application/octet-stream"
        cl=0
        try:
            ct = self.header("Content-Type").split(';')[0].rstrip().lower()
        except: pass

        try:
            cl = int(self.header("Content-Length"))
        except: pass

        if ct in JSON_MIME:
            self._body_type=BODY_DICT
            content=self._socket.read(cl).decode("utf8")
            if len(content)>0:
                self.body=json.loads(content)
            else: self.body=None
        elif ct in URLENCODED_MIME:
            self._body_type=BODY_DICT
            self.body=parse_urlencoded_params(self._socket.read(cl).decode("utf8"))
        elif ct in TEXT_MIME:
            self._body_type=BODY_STRING
            self.body=self._socket.read(cl).decode("utf8")
        else:
            self._body_type=BODY_BYTES
            self.body=self._socket.read(cl)

    def _set_header(self, key : str, val):
        if val and key.lower()=="cookie":
            clist = val.split(";")
            for x in clist:
                x = x.split("=")
                k = x[0].lstrip()
                v = x[1].rstrip() if len(x) > 1 else ""
                self.cookies[k] = v
        self._headers[key]= val

    def _parse_command_line(self):
        self._head_line_parsed = True

        head=self._socket.readline()[:-1].split(" ")
        self.method=head[0]
        self.url=head[1]
        self.version=head[2]

        self.path=unquote(self.url)
        n=self.url.find("?")

        if n>=0:
            self.path=unquote(self.url[:n])
            tmp=self.url[n+1:]
            self.query=parse_urlencoded_params(tmp)
            self.filename=os.path.basename(self.path)



class HTTPResponse(_HTTP):
    def __init__(self, req, code=200):
        _HTTP.__init__(self)
        self.version = "HTTP/1.1"
        self.code=code
        self.request= req
        self.msg=STR_HTTP_ERROR[code]
        self._set_cookies={}


    def header(self, key : str, val):
        self._headers[key]=val

    def end(self, data, contentType=None):
        if contentType:
            self.content_type(contentType)

        self.body=data
        if isinstance(data, str):
            self._body_type=BODY_STRING
        elif isinstance(data, bytes):
            self._body_type=BODY_BYTES
        elif isinstance(data, (dict, list)):
            self._body_type=BODY_DICT
        elif isinstance(data, io.BufferedIOBase):
            self._body_type=BODY_FILE
        else:
            self._body_type=BODY_EMPTY


    def serve_file_meta(self, base, path : str, cache=None, debug=False):
        if not cache or not cache.has(path):
            if not os.path.isfile(path):
                log.error("Le fichier '"+str(path)+"' est introuvable")
                self.serve404()
                return None
            m=utils.mime(path)
        else:
            m=cache.mime(path)

        self.content_type(m)
        self.header("Content-Length", str(os.stat(path).st_size))
        self.end(html_meta(base, path, cache=cache, debug=debug))



    def serve_file_gen(self, path : str, data={}):
        if not os.path.isfile(path):
            log.error("Le fichier '"+str(path)+"' est introuvable")
            self.serve404()
            return None
        m=utils.mime(path)
        self.content_type(m)
        self.header("Content-Length", str(os.stat(path).st_size))
        data["_request"] = self.request
        data["_response"] = self
        if m!="application/octet-stream":
            try:
                self.end(html_gen(path, data))
            except InstructionStackException as err:
                out="""<html>
                    <head>
                      <meta charset="UTF-8">
                    </head><body><h1>%s</h1><ul>""" % err.type
                i=0
                l=len(err.args[0])
                for line in reversed(err.args[0]):
                    out+="<li style=\"color: #ff0000;\">%s</li>" % (line if i<l-1 else ('<b>%s</b>'%line))
                    i+=1
                self.code=500;
                self.end(out+"</ul></body></html>")
        else:
            self.serve_file(path)

    def serve_file(self, path: str, urlReq=None, forceDownload=False, data={}, contenlength=None, cache=None):
        fd = None
        if cache and not cache.has(path): cache=None

        try:
            if not cache:
                fd = open(path, "rb")
        except Exception as err:
            self.code = HTTP_NOT_FOUND
            self.msg = STR_HTTP_ERROR[HTTP_NOT_FOUND]
            self.content_type("text/plain")
            if urlReq:
                self.end(str(urlReq) + " not found")
            else:
                self.end("File not found : " + str(err))
            return

        # self._isStreaming=True
        self.content_type(utils.mime(path))
        if not contenlength:
            self.header("Content-Length", str(os.stat(path).st_size))
        else:
            self.header("Content-Length", str(contenlength))

        if forceDownload:
            self.header("Content-Disposition", "attachment; filename=\"" + \
                        os.path.basename(path) + "\"")
        if cache:
            self.end(cache[path], cache.mime(path))
        else:
            self.end(fd)
        # self.end(open(path, "rb"))

    def serve_file_data(self, data, mime : str, filename : str,  forceDownload=False):
        if isinstance(data, str) : data=data.encode("utf-8")
        if isinstance(data, (dict, list, tuple)): data=json.dumps(data).encode("ascii")
        if not isinstance(data, bytes):
            raise Exception("serve_file_data data doit etre bytes ou str")
        self.content_type(mime)
        self.header("Content-Length", str(len(data)))

        if forceDownload:
            self.header("Content-Disposition", "attachment; filename=\"" + \
                        filename+ "\"")
        self.end(data)

    def serve_large_file(self, path: str, contenlength=None):
        fd = None
        try:
            fd = open(path, "rb")
        except Exception as err:
            self.code = HTTP_NOT_FOUND
            self.msg = STR_HTTP_ERROR[HTTP_NOT_FOUND]
            self.content_type("text/plain")

        # self._isStreaming=True
        self.content_type(utils.mime(path))
        if not contenlength:
            self.header("Content-Length", str(os.stat(path).st_size))
        else:
            self.header("Content-Length", str(contenlength))

        self.header("Content-Disposition", "attachment; filename=\"" + \
                        os.path.basename(path) + "\"")
        self.end(fd)
        # self.end(open(path, "rb"))

    def _set_json_response(self, httpcode : int, code : int , msg : str, js):
        self.header("Content-Type", "application/json")
        self.code = httpcode
        self.msg = STR_HTTP_ERROR[httpcode]
        self.end(bytes(json.dumps({"code": code, "message": msg, "data": js}), "utf8"))

    def ok(self, code : int, msg : str, js):
        self._set_json_response(HTTP_OK, code, msg, js)

    def unauthorized(self, code : int, msg : str, js):
        self._set_json_response(HTTP_UNAUTHORIZED, code, msg, js)

    def bad_request(self, code : int, msg : str, js):
        self._set_json_response(HTTP_BAD_REQUEST, code, msg, js)

    def not_found(self, code : int, msg : str, js):
        self._set_json_response(HTTP_NOT_FOUND, code, msg, js)

    def temporary_redirect(self, url : str):
        self.code = HTTP_TEMPORARY_REDIRECT
        self.msg = STR_HTTP_ERROR[HTTP_TEMPORARY_REDIRECT]
        self.header("Location", url)
        self.end("")

    def set_cookie(self, name, value, options={}):
        self._set_cookies[name]={
            "name" : name,
            "value" : value,
            "options" : options
        }

    def clear_cookie(self, name):
        self.set_cookie(name, "deleted", {
            "path" : "/",
            "expires" : "Thu, 01 Jan 1970 00:00:00 GMT"
        })

    def write(self, soc : SocketWrapper):
        out=None
        typ=self.body_type()
        if typ==BODY_DICT:
            out=bytes(json.dumps(self.body), "utf8")
        elif typ==BODY_BYTES:
            out=self.body
        elif typ==BODY_STRING:
            out=bytes(self.body, "utf8")
        elif typ==BODY_FILE:
            out=self.body
        else: out=bytes()
        self.header("Connection", "close")
        if typ!=BODY_FILE:
            self.header("Content-Length", len(out))

        try:
            soc.send(fromutf8(self.version + " " + str(self.code) + " " + self.msg + "\r\n"))
            for k in self._headers:
                soc.send(fromutf8(k + ": " + str(self._headers[k]) + "\r\n"))
            for key in self._set_cookies:
                cookie = self._set_cookies[key]
                tmp="Set-Cookie: %s=%s" % (cookie["name"], cookie["value"])
                tmp2="; ".join(list(map(lambda y: "%s=%s" % (y, cookie["options"][y]),  cookie["options"])))
                if tmp2: tmp+="; "+tmp2
                soc.send(fromutf8(tmp+"\r\n"))
            soc.send(fromutf8("\r\n"))
            if typ!=BODY_FILE:
                soc.send(out)
            else:
                chunk=1024*1024
                left=int(self._headers["Content-Length"])
                while left>0:
                    buffer=out.read(chunk)
                    left-=len(buffer)
                    soc.send(buffer)
                out.close()
        except IOError as err:
            log.critical("Erreur d'écriture:", err," (envoyé: ",soc.sent," octets)")

    def no_cache(self):
        self.header("Cache-Control", "max-age=0, no-cache, no-store, must-revalidate")
        self.header("Pragma", "no-cache")
        self.header("Expires", "Wed, 11 Jan 1984 05:00:00 GMT")

    def serv(self, code, headers={}, data={}, file=None, filegen=None):
        for h in headers: self.header(h, headers[h])
        self.code=code
        self.msg=_HTTP_CODE[code]
        if file:
            self.serve_file(file)
        elif filegen:
            self.serve_file_gen(filegen, data)
        else:
            self.end(data)

    def serveJson(self, data, code=200, headers={}):
        headers=headers.copy()
        self.content_type("application/json")
        return self.serv(code, headers, data)

    def serve100(self, header={}, data={}, file=None, filegen=None ): self.serv(100, header, data, file, filegen)

    def serve200(self, header={}, data={}, file=None, filegen=None ): self.serv(200, header, data, file, filegen)
    def serve201(self, header={}, data={}, file=None, filegen=None ): self.serv(201, header, data, file, filegen)
    def serve202(self, header={}, data={}, file=None, filegen=None ): self.serv(202, header, data, file, filegen)
    def serve204(self, header={}, data={}, file=None, filegen=None ): self.serv(204, header, data, file, filegen)

    def serve300(self, header={}, data={}, file=None, filegen=None ): self.serv(300, header, data, file, filegen)
    def serve301(self, url, header={}, data={}, file=None, filegen=None ):
        self.serv(301, dictinit(header, {"Location": url }), data, file, filegen)

    def serve302(self, url, header={}, data={}, file=None, filegen=None):
        self.serv(302, dictinit(header, {"Location": url}), data, file, filegen)

    def serve304(self, header={}, data={}, file=None, filegen=None ): self.serv(304, header, data, file, filegen)

    def serve400(self, header={}, data={}, file=None, filegen=None ): self.serv(400, header, data, file, filegen)
    def serve401(self, header={}, data={}, file=None, filegen=None ): self.serv(401, header, data, file, filegen)
    def serve403(self, header={}, data={}, file=None, filegen=None ): self.serv(403, header, data, file, filegen)
    def serve404(self, header={}, data={}, file=None, filegen=None ): self.serv(404, header, data, file, filegen)
    def serve405(self, header={}, data={}, file=None, filegen=None ): self.serv(405, header, data, file, filegen)
    def serve418(self, header={}, data={}, file=None, filegen=None ): self.serv(418, header, data, file, filegen)

    def serve500(self, header={}, data={}, file=None, filegen=None ): self.serv(500, header, data, file, filegen)
    def serve501(self, header={}, data={}, file=None, filegen=None ): self.serv(501, header, data, file, filegen)
    def serve502(self, header={}, data={}, file=None, filegen=None ): self.serv(502, header, data, file, filegen)
    def serve503(self, header={}, data={}, file=None, filegen=None ): self.serv(503, header, data, file, filegen)
    def serve504(self, header={}, data={}, file=None, filegen=None ): self.serv(504, header, data, file, filegen)

    #
    #  ==== Utils methods
    #
    def serv_json(self, httpcode, code, msg, data=None):
        self.serv(httpcode, {"Content-Type", "application/json"}, {
            "code": code,
            "message": msg,
            "data": data
        })

    def serv_json_ok(self, data=None):
        self.serv(200, {"Content-Type": "application/json"}, {
            "code": 0,
            "message": "Success",
            "data": data
        })


    def serv_json_bad_request(self, data=None):
        self.serv(400, {"Content-Type": "application/json"}, {
            "code": 400,
            "message": "Bad Request",
            "data": data
        })

    def serv_json_unauthorized(self, data=None):
        self.serv(401, {"Content-Type": "application/json"}, {
            "code": 401,
            "message": "Unauthorised",
            "data": data
        })

    def serv_json_forbidden(self, data=None):
        self.serv(403, {"Content-Type": "application/json"}, {
            "code": 403,
            "message": "Forbidden",
            "data": data
        })

    def serv_json_not_found(self, data=None):
        self.serv(404, {"Content-Type": "application/json"}, {
            "code": 404,
            "message": "Ressource not found",
            "data": data
        })

    def serv_json_method_not_allowed(self, data=None):
        self.serv(405, {"Content-Type": "application/json"}, {
            "code": 405,
            "message": "Method Not Allowed",
            "data": data
        })

    def serv_json_teapot(self, data=None):
        self.serv(418, {"Content-Type": "application/json"}, {
            "code": 418,
            "message": "I’m a teapot",
            "data": data
        })

