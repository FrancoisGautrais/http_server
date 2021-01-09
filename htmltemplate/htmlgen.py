from io import StringIO
import os
from .. import config
from .. import log
from ..utils import html_template_string
from ..htmltemplate.lexer import Lexer
import time
from .instructions_loader import call, InstructionContext, InstructionParseExcpetion, InstructionNotFoundExcpetion, InstructionStackException, function_exists


class MetaIncludeException(Exception):

    def __init__(self, err):
        super().__init__(err)

class FileGenIo(StringIO):

    def __init__(self, text, filename):
        StringIO.__init__(self, text)
        self.line_pos=1
        self.filename=filename
        self.line=1

    def read(self, n=None):
        c = StringIO.read(self, n)
        if c=="\n":
            self.line+=1
            self.line_pos=1
        else:
            self.line_pos+=1
        return c

    def get_location(self):
        return InstructionContext(self.filename,  self.line, self.line_pos)


class Instruction:

    def __init__(self, fd, data, revert=None, lex=None):
        self.lex=Lexer(fd, data) if not lex else lex
        self.context=fd.get_location()
        self.data=data
        self.inst=""
        self.args=[]
        raiseError=None

        try:
            if revert:
                self.inst=revert
            else:
                curr=self.lex.next()
                if curr!=Lexer.IDENT: raise InstructionParseExcpetion("Parser error: nom de fonction attendu (ident) : trouvé : '%s'" % curr)
                self.inst=self.lex.value
            if not function_exists(self.inst):
                raise InstructionNotFoundExcpetion("Fonction '%s' non définie" % self.inst)


            curr=self.lex.next()
            if curr!=Lexer.P_OUVRANTE: raise InstructionParseExcpetion("Parser error: parenthèse ouvrante '(' attendue : trouvé : '%s'" % curr)

            curr=self.lex.next()
            if curr!=Lexer.P_FERMANTE:
                curr=self._next_value()
                while curr==Lexer.VIRGULE:
                    self.lex.next()
                    curr=self._next_value()

            if curr!=Lexer.P_FERMANTE: raise InstructionParseExcpetion("Parser error: parenthèse fermante ')' attendue : trouvé : '%s'" % curr)
        except (InstructionParseExcpetion, InstructionNotFoundExcpetion)  as err:
            raiseError = InstructionStackException(["\n".join(err.args)]+[" \nFrom '%s:%s:%s' : %s"%(
                self.context.filename,str(self.context.line),str(self.context.line_pos), str( self)
            )], [self], err.type)
        if raiseError: raise  raiseError
    def __str__(self):
        strargs=list(map(lambda x: str(x), self.args))
        return self.inst+("(%s)"% ", ".join(strargs) )

    def __repr__(self):
        return self.__str__()

    def _next_value(self):
        if self.lex.current in [Lexer.INT, Lexer.FLOAT, Lexer.STRING, Lexer.NONE, Lexer.BOOL]:
            self.args.append(self.lex.value)
            self.lex.next()
        elif self.lex.current==Lexer.IDENT:
            inst = Instruction(self.lex.fd, self.data, self.lex.value, self.lex)
            self.args.append(inst.value())
            self.lex.next()
        else:
            raise InstructionParseExcpetion("Parser error: paramètre ou fin de fonction attendu (int, float, string, ident ou parenthèse fermante) : trouvé : '%s' " % self.lex.current)
        return self.lex.current


    def value(self):
        x = call(self)
        if x==None: return ""
        return x

class HtmlGen:

    def __init__(self, filename=None, isFile=True, fd=None, encoding="utf-8", cache=None):
        self.filename=filename
        self.fd=None
        self.cache=cache
        self.rawtext=(open(filename, "r", encoding=encoding) if not fd else fd).read()
        self.text=""
        self.c=""

    def close(self):
        self.close()

    def _read(self):
        self.c=self.fd.read(1)
        return self.c

    def _read_next(self, data):
        x=" "
        while x!="":
            x = self._read()
            while x!="" and x!="<":
                self.text+=x
                x=self._read()
            if x=="<":
                x=self._read()
                if x=="#":
                    return Instruction(self.fd, data)
                else: self.text+="<"+x
        return None


    def _replace_next(self, data):
        inst=self._read_next(data)
        if inst:
            self.text+=str(inst.value())
            return True
        return False

    def gen(self, data):
        self.fd=FileGenIo(html_template_string(self.rawtext, data), self.filename)
        x=True
        while x:
            x=self._replace_next(data)
        self.fd.close()
        return self.text

class HtmlMetaIncludeGen:

    def __init__(self,base,  filename, cache, encoding="utf-8", data=None, debug=False):
        self.filename=filename
        self.debug=debug
        self.encoding=encoding
        self.base=base
        self.dirname=os.path.dirname(self.filename)
        if not self.dirname: self.dirname="."
        if data:
            self.file=data
        else:
            if not cache or not cache.has(filename):
                fd=open(filename, "r", encoding=encoding)
                self.file=fd.read()
            else:
                self.file=cache[filename]

    def from_base_dir(self, path):
        base="/".join([".."]*(len(self.dirname.split("/"))-1))
        return os.path.join(base, self.base, path)


    def read(self, path):
        if(isinstance(path, bytes)): path=path.decode(self.encoding)
        if path and len(path) and path[0]=="/":
            path=self.from_base_dir(path[1:])
        else:
            path=os.path.join(self.dirname, path)

        with open(path) as f:
            return f.read()

    def _find_filename(self, line, prefix):
        pattern='%s="'%prefix
        start=line.find(pattern)
        if start<0: return None
        start+=len(pattern)
        end=line.find('"', start)
        if end<0: return None
        return line[start:end]


    def _other_find_filename(self, line):
        totest=["data-include", "src", "href"]
        for pat in totest:
            x=self._find_filename(line, pat)
            if x: return x
        return None

    def get_filepos(self, i):
        tmp = self.file[:i - 1].split("\n")
        line = 1 + len(tmp)
        col = len(tmp[-1])
        return "%s:%d:%d" % (self.filename, line, col)

    def process_other_include(self, input):
        out=[]
        lines=input.split("\n")
        for i in range(len(lines)):
            line=lines[i]
            if 'data-include' in line:
                start=None
                end = None
                if ('<link' in line or '<style' in line)  and ('src="' in line or 'href="' in line):
                    start="<style>"
                    end="</style>"
                if '<script' in line and ('src="' in line or 'href="' in line):
                    start="<script>"
                    end="</script>"
                if start and end:
                    path = self._other_find_filename(line)
                    if path:
                        data=self.read(path)
                        if data is not None:
                            out.append(start)
                            out.append(data)
                            out.append(end)
                        else:
                            raise MetaIncludeException("Erreur:%s:%d impossible de trouver le fichier '%s'"%(self.filename,i, path))
                    else:
                        out.append(line)
                else:
                    out.append(line)
            else:
                out.append(line)
        return "\n".join(out)

    def gen(self):
        out=""
        pattern='<#include("'
        i=0
        l=len(self.file)

        while i<l:
            start=self.file.find(pattern, i)+len(pattern)
            if start<len(pattern):
                return (out+self.file[i:]) if self.debug else self.process_other_include(out+self.file[i:])

            tmp=self.file.find("\")>", start)
            out+=self.file[i:start-len(pattern)]
            if i<0:

                raise Exception("MetaIncludeGen:%s '>' manquant"% self.get_filepos(i-1))
            out+=self.read(self.file[start:tmp])
            i=tmp+3


        return out if self.debug else self.process_other_include(out)



def html_meta(base, filename, cache=None, encoding="utf-8", debug=False):
    return HtmlMetaIncludeGen(base, filename, cache, debug=debug).gen()

def html_meta_data(base, filename, data, cache=None, encoding="utf-8", debug=False):
    return HtmlMetaIncludeGen(base, filename, cache, encoding, data, debug=debug).gen()


def html_gen(filename, data):
    t=time.time()
    x = HtmlGen(filename=filename)
    out=x.gen(data)
    t= "%.3f ms" % ((time.time()-t)*1000)
    #log.debug("html_gen('"+filename+"') : ", t)
    return out

def html_gen_fd(fd, data, filename):
    x = HtmlGen(fd=fd, filename=filename)
    content=x.gen(data)
    return content
