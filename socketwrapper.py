import socket
from threading import Thread
#content=open("request", "rb").read()

import traceback
import time

from . import log

class DisconnectException(Exception):

    def __init__(self):
        Exception.__init__(self)


class SocketWrapper:
    def __init__(self, llsocket):
        self._socket=llsocket
        self.sent=0
        self.buffer=bytearray()
        self._recieved=bytearray()
        self._sent=bytearray()
        self.closed=False



    def send(self, s):
        if isinstance(s, str): s = bytes(s, "utf8")
        self._sent+=s
        return self._socket.sendall(s)

    def _recv(self, n=1):
        b=self._socket.recv(n)
        self._recieved+=b
        return b

    def dump_recevied(self):
        log.error("======== dump ==============")
        log.error(self._recieved.decode(errors="replace"))
        log.error("======== end dump ==============")


    def read(self, l=1):
        base=bytearray()
        if len(self.buffer)>0:
            m=min(l, len(self.buffer))
            base=self.buffer[:m]
            self.buffer=self.buffer[m:]
            l-=m
        if l>0:
            if len==1: return self._socket.recv(1)
            bytes_recd = 0
            while bytes_recd < l:
                chunk = self._socket.recv(min(l - bytes_recd, 2048))
                if chunk == b'':
                    log.error("Connection problème here '%d' " % bytes_recd)
                    self.close()
                    #raise DisconnectException
                #    #self.dump_recevied()
                #    #raise Exception("socket connection broken, bytes left : "+str(l-bytes_recd), "chucks = ", base)
                base+=chunk
                bytes_recd = bytes_recd + len(chunk)
        return bytes(base)

    def read_str(self, len=1):
        return str(self.read(len), encoding="utf8")

    def get_ip(self):
        return self._socket.getpeername()[0]

    def readline(self, encoding="utf8"):
        out=""
        x=self.read(1)
        while x[0]!=10:
            out+=x.decode(encoding, "replace")
            x = self.read(1)
        return out

    def readc(self):
        return self.read_str()

    # put bytes before next read
    def rewind(self, b):
        self.buffer+=b

    def close(self):
        #self._socket.shutdown(socket.SHUT_WR)
        self._socket.close()
        self.closed=True

        return self._socket.close()


class ServerSocket(SocketWrapper):

    def __init__(self):
        SocketWrapper.__init__(self, socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._ip=""
        self._port=-1

    def bind(self, ip, port):
        self._ip=ip
        self._port=port
        self._socket.bind((ip, port))
        self._socket.listen(50)

    def accept(self, cb=None, args=[]):
        (clientsocket, address) = self._socket.accept()
        client = SocketWrapper(clientsocket)
        if cb: cb(client, args)

        return client



