
from .socketwrapper import SocketWrapper

from os import  path
from . import log

class FormFile:

    def __init__(self, soc : SocketWrapper, boundary : str):
        self.soc=soc
        self.boundary=bytes("--"+boundary, "ascii")
        self.filename=""
        self.name=""
        self.mime=""
        self.attrs={}
        self.has_next=False

    def parse_head(self):
        bound=self.soc.readline()
        if bound.endswith("--\r") : return False
        head=self.soc.readline()[:-1]
        head+="\n"+self.soc.readline()[:-1]
        head=head.split("\n")
        for h in head:
            tmp=h.split(":")
            key = tmp[0]
            val = tmp[1][1:]
            if val.find(";")>0:
                v={}
                for k in val.split(";"):
                    k=k.lstrip()
                    if k.find("=")>0:
                      v[k[:k.find("=")]]=k[k.find("=")+1:]
                    else: v[k]=None
                val=v
            self.attrs[key]=val
        self.soc.readline()
        self.name=self.attrs["Content-Disposition"]["name"][1:-1]
        self.filename=self.attrs["Content-Disposition"]["filename"][1:-1]
        return True
    NO_BOUND=0
    SIMPLE_BOUND=1
    END_BOUND=2
    #
    #
    #
    def is_bound(self):
        tmp = self.soc.read(len(self.boundary))
        self.soc.rewind(tmp)
        if tmp != self.boundary:
            return FormFile.NO_BOUND
        if self.soc.read(2) == bytes("\r\n", "ascii"): return FormFile.SIMPLE_BOUND
        self.soc.read(2)
        return FormFile.END_BOUND

    def parse_content(self):
        x=self.soc.read(1)
        out=x
        while True:
            x=self.soc.read(1)
            if x==bytes("\n", "ascii"):
                bound=self.is_bound()
                out+=x
                if bound==FormFile.END_BOUND:
                    self.has_next=False
                    return out
                elif bound == FormFile.SIMPLE_BOUND:
                    self.has_next=True
                    return out
            else: out+=x


    def save(self, p, forcePath=False):
        out=path.normpath(p+("" if forcePath else "/"+self.filename))

        # si 'out" est un dossier => filename = "" => Pas de fichier
        if self.filename=="":
            while True:
                self.soc.read(1)
                bound=self.is_bound()
                if bound == FormFile.END_BOUND:
                    self.has_next=False
                    return False
                elif bound == FormFile.SIMPLE_BOUND:
                    self.has_next=True
                    return True
        log.debug("Writing file to '"+out+"'")
        with open(out, "wb") as f:
            x=self.soc.read(1)
            while True:
                f.write(x)
                x=self.soc.read(1)
                if x==bytes("\n", "ascii"):
                    bound=self.is_bound()

                    if bound==FormFile.END_BOUND:
                        self.has_next=False
                        return False
                    elif bound == FormFile.SIMPLE_BOUND:
                        self.has_next=True
                        return True