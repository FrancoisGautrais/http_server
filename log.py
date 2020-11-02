import datetime
import sys
import threading


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
        if isinstance(level, str): level = Log.LEVEL_STR.index(level.upper())
        self.lvl=level
        self.lock=threading.Lock()
        self.filename=None

    def _log(self, lvl, s):
        if lvl>=self.lvl:
            self.lock.acquire()
            self.fd.write(_time_str()+"|"+Log.LEVEL_STR[lvl]+"| "+s+"\n")
            if self.fd!=sys.stdout:
                print(_time_str()+"|"+Log.LEVEL_STR[lvl]+"| "+s+"\n")
            self.lock.release()

    def log(self, level, *args):
       arg=[ ]
       for x in args: arg.append(str(x))
       line=" ".join(arg)
       lines=line.split("\n")
       for l in lines:
           self._log(level, l)
       if self.filename: self.fd.flush()

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

    def close(self):
        if self.filename: self.fd.close()

    @staticmethod
    def init(level=DEBUG, fd=sys.stdout):
        if isinstance(fd, str):
            Log._INSTANCE.filename=fd
            BackupLog.backup(fd)
            fd=open(fd, "w")
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

def close(): Log._INSTANCE.close()


import os


class BackupLog:

    def __init__(self, name, dir):
        self.name=name
        self.dir=dir if dir else "."

    def find_new_filename(self):
        files = os.listdir(self.dir)
        prefix = self.name + "."
        max = 0
        for name in files:
            if name.startswith(prefix):
                suffix = name[len(prefix):]
                try:
                    n = int(suffix)
                    if n > max: max = n
                except:
                    pass
        return prefix + str(max + 1)

    def copylog(self):
        try:
            oldlog = os.path.join(self.dir, self.name)
            with open(oldlog):
                pass
            filename = self.find_new_filename()
            newpathname = os.path.join(self.dir, filename)
            print(oldlog, "->",newpathname)
            os.replace(oldlog, newpathname)
            return newpathname
        except:
            return None


    @staticmethod
    def backup(name : str):
        filename = os.path.basename(name)
        dir = name[:-len(filename)]
        tmp = BackupLog(filename, dir)
        return tmp.copylog()

    @staticmethod
    def from_cmdline(args=sys.argv):
        def print_help():
            print("Usage: %s backup LOG_FILE "%args[0])
            raise Exception()

        LOG_FILE = "covid.log"

        i = 1
        current = 0
        while i < len(args):
            arg = args[i]

            if arg.startswith("--"):
                arg = arg[2:]
                print_help()
            elif arg.startswith("-"):
                arg = arg[2:]
                print_help()
            else:
                if current > 1:
                    print_help()
                if current == 0:
                    if arg != 'backup':
                        print_help()
                elif current == 1:
                    LOG_FILE = arg
                current += 1
            i += 1
        if current < 2:
            print_help()
        BackupLog.backup(LOG_FILE)

if __name__ == "__main__":
    BackupLog.from_cmdline()