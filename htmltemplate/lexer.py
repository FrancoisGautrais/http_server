
class Lexer:
    NONE="none"
    STRING="string"
    IDENT="ident"
    NONE="None"
    BOOL="bool"
    INT="int"
    FLOAT="float"
    P_OUVRANTE="("
    P_FERMANTE=")"
    END=">"
    BEGIN="<"
    SHARP="#"
    EOF=""
    VIRGULE=","

    IDENT_FIRST="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_"
    IDENT_AFTER="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_0123456789"
    NUMBERS_FIRST="-0123456789"
    NUMBERS_AFTER="0123456789"

    def __init__(self, fd, data):
        self.c=""
        self.data=data
        self.fd=fd
        self.current=Lexer.NONE
        self.string=""
        self.value=""
        self.read()

    def read(self):
        self.c=self.fd.read(1)

        return self.c;

    def cis(self, x):
        return self.c in x

    def _read_str(self):
        end=self.c
        self.read()
        while self.c!=end and self.c!="":
            self.string+=self.c
            self.read()
        self.read()
        self.value=self.string
        self.current=Lexer.STRING

    def _read_ident(self):
        self.string=self.c
        self.read()
        while self.cis(Lexer.IDENT_AFTER) and self.c!="":
            self.string+=self.c
            self.read()
        if self.string=="None":
            self.value=None
            self.current=Lexer.NONE
        elif self.string.lower()=="true" or self.string.lower()=="false":
            self.value=self.string.lower()=="true"
            self.current=Lexer.BOOL
        else:
            self.value=self.string
            self.current=Lexer.IDENT

    def _read_numbers(self):
        self.string=self.c
        self.read()
        while self.cis(Lexer.NUMBERS_AFTER) and self.c!="":
            self.string+=self.c
            self.read()
        if self.c==".":
            self.string+="."
            self.read()
            while self.cis(Lexer.NUMBERS_AFTER) and self.c != "":
                self.string += self.c
                self.read()
            self.current=Lexer.FLOAT
            self.value=float(self.string)
        else:
            self.current=Lexer.INT
            self.value=int(self.string)

    def _set_special(self, type, string):
        self.string=string
        self.value=string
        self.current=type
        self.read()

    def next(self):

        while self.c in [" ", "\t", "\n"]:
            self.c=self.fd.read(1)
        self.string=""
        if self.cis(Lexer.IDENT_FIRST):  self._read_ident()
        elif self.cis(Lexer.NUMBERS_FIRST):  self._read_numbers()
        elif self.c=="\"": self._read_str()
        elif self.c=="\'": self._read_str()
        elif self.c==")": self._set_special(Lexer.P_FERMANTE, self.c)
        elif self.c=="(": self._set_special(Lexer.P_OUVRANTE, self.c)
        elif self.c==",": self._set_special(Lexer.VIRGULE, self.c)
        elif self.c==">": self._set_special(Lexer.END, self.c)
        elif self.c=="#": self._set_special(Lexer.SHARP, self.c)
        elif self.c=="<": self._set_special(Lexer.BEGIN, self.c)
        elif self.c=="": self._set_special(Lexer.EOF, "")
        else:
            raise Exception("Lexer error '"+self.c+"' unexpected")
        return self.current


