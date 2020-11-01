from io import StringIO

from .. import log
from ..filecache import filecache
from ..utils import html_template_string
from ..htmltemplate.lexer import Lexer
import time
from .instructions_loader import call, InstructionContext, InstructionParseExcpetion, InstructionNotFoundExcpetion, InstructionStackException, function_exists


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

    def __init__(self, filename=None, isFile=True, fd=None, encoding="utf-8"):
        self.filename=filename
        self.fd=None
        self.rawtext=(filecache.open(filename, "r", encoding=encoding) if not fd else fd).read()
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
