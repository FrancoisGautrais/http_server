import os
import inspect
import sys

from importlib import import_module
from inspect import getmembers, isfunction

class InstructionsLoader:
    PARENT_PACKAGE=".".join(__name__.split(".")[:-1])
    def __init__(self):
        self.commands={}
        self.load()


    def load(self):
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        path = os.path.join(os.path.dirname(os.path.abspath(filename)), "instructions/")
        for x in os.listdir(path):
            file=os.path.join(path, x)
            if x[0]!="_" and (x[-3:].lower()==".py" or x[-4:].lower()==".pyc"):
                imported_module = import_module(InstructionsLoader.PARENT_PACKAGE+".instructions."+x.split(".")[0])

                functions_list = [o for o in getmembers(imported_module) if isfunction(o[1])]
                for k in functions_list:
                    if k[0].startswith("inst_"):
                        self.commands[k[0][5:]]=k[1]
        return


    def call(self, name, args, data):
        x=None
        if not name in self.commands:
            sys.stderr.write("Command '"+str(name)+"' not found\n")
        return self.commands[name](args, data)

_instance=None

def call(shell, name, args=[]):
    global _instance
    if _instance==None: _instance=InstructionsLoader()
    return _instance.call(shell, name, args)