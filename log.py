import datetime
import sys

def _padding(x, n=2):
    s=str(x)
    while len(s)<n:
        s="0"+s
    return s

def _time_str():
    x=datetime.datetime.today()
    return _padding(x.day)+"/"+_padding(x.month)+"/"+str(x.year)+" "+_padding(x.hour)+":"+_padding(x.minute)+":"+_padding(x.second)+"."+_padding(x.microsecond,6)

class Log:
    DEBUG=0
    INFO=1
    WARN=2
    ERROR=3
    CRITICAL=4
    LEVEL_STR=["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
    _INSTANCE=None

    def __init__(self, level, fd):
        self.fd=fd
        self.lvl=level

    def _log(self, lvl, s):
        if lvl>=self.lvl: self.fd.write(_time_str()+"|"+Log.LEVEL_STR[lvl]+"| "+s+"\n")

    def log(self, level, *args):
       arg=[ ]
       for x in args: arg.append(str(x))
       line=" ".join(arg)
       lines=line.split("\n")
       for l in lines:
           self._log(level, l)

    def debug(self, *args): return self.log(Log.DEBUG, *args)
    def d(self, *args): return self.log(Log.DEBUG, *args)

    def info(self, *args): return self.log(Log.INFO, *args)
    def i(self, *args): return self.log(Log.INFO, *args)

    def warn(self, *args): return self.log(Log.WARN, *args)
    def w(self, *args): return self.log(Log.WARN, *args)

    def error(self, *args): return self.log(Log.ERROR, *args)
    def e(self, *args): return self.log(Log.ERROR, *args)

    def critical(self, *args): return self.log(Log.CRITICAL, *args)
    def c(self, *args): return self.log(Log.CRITICAL, *args)


    @staticmethod
    def init(level=DEBUG, fd=sys.stdout):
        Log._INSTANCE = Log(level, fd)



if not Log._INSTANCE:
    Log.init()

def log(lvl, *args): Log._INSTANCE.log(lvl, *args)

def debug(*args): log(Log.DEBUG, *args)
def d(*args): log(Log.DEBUG, *args)

def info(*args): log(Log.INFO, *args)
def i(*args): log(Log.INFO, *args)

def warn(*args): log(Log.WARN, *args)
def w(*args): log(Log.WARN, *args)

def error(*args): log(Log.ERROR, *args)
def e(*args): log(Log.ERROR, *args)

def critical(*args): log(Log.CRITICAL, *args)
def c(*args): log(Log.CRITICAL, *args)