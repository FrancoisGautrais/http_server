import os
import inspect
import sys

from importlib import import_module
from inspect import getmembers, isfunction

import log



class InstructionContext:

    def __init__(self, filename, line, pos):
        self.filename=filename
        self.line=line
        self.line_pos=pos

class InstructionExcpetion(Exception):
    def __init__(self, message, inst=None):
        Exception.__init__(self, message)
        self.inst=inst
        self.type="Runtime Error"

class InstructionParseExcpetion(Exception):
    def __init__(self, message, inst=None):
        Exception.__init__(self, message)
        self.inst=inst
        self.type="Syntax Error"

class InstructionNotFoundExcpetion(Exception):
    def __init__(self, message, inst=None):
        Exception.__init__(self, message)
        self.inst=inst
        self.type="Function Not Found Error"

class InstructionNotCoughtExcpetion(Exception):
    def __init__(self, message, inst=None):
        Exception.__init__(self, message)
        self.inst=inst
        self.type="Unhandle Error"

class InstructionStackException(Exception):
    def __init__(self, message, inst, type):
        Exception.__init__(self, message)
        self.insts=inst
        self.type=type

depth=0
def depthstr():
    return " "+" ".join([" " for i in range(depth)])

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

    def call_from_builtin(self, name, args=[], data=None):
        if not isinstance(args, (tuple,list)):
            args=[args]
        return  self.call(fromBuiltIn=(name, args, data))

    def call(self, inst=None, fromBuiltIn=None):
        global depth
        name = inst.inst if inst else fromBuiltIn[0]
        args=inst.args  if inst else fromBuiltIn[1]
        context=inst.context if inst else InstructionContext("builtin", name,"")
        data=inst.data if inst else fromBuiltIn[2]
        x=None
        raiseError = None
        if not name in self.commands:
            sys.stderr.write("Command '"+str(name)+"' not found\n")
        depth+=1
        #log.e("%s%s(%s)" %(depthstr(), name, ",".join([ str(i)  for i in args])))

        try:
            if not name in self.commands:
                raise InstructionNotFoundExcpetion("Fonction '%s' non définie" % name)
            x= self.commands[name](args, data)
        except FileNotFoundError as err:
            raiseError = InstructionStackException(["\n".join(err.args)]+[" '%s'From '%s:%s:%s' : %s"%(
                args[0], context.filename,str(context.line),str(context.line_pos), str( inst)
            )], [inst], err.type)
        except (InstructionExcpetion, InstructionNotFoundExcpetion)  as err:
            raiseError = InstructionStackException(["\n".join(err.args)]+["From '%s:%s:%s' : %s"%(
                context.filename,str(context.line),str(context.line_pos), str( inst)
            )], [inst], err.type)
        except InstructionStackException as err:
            last = err.insts[len(err.insts)-1]
            raiseError = InstructionStackException(err.args[0]+["From '%s:%s:%s' : %s"%(
                context.filename,str(context.line),str(context.line_pos), str( inst)
            )], err.insts+[inst], err.type)
        except Exception as _err:
            err = InstructionNotCoughtExcpetion(_err.args[0])
            raiseError = InstructionStackException([_err.__class__.__name__+" : " +"\n".join(err.args[0])]+["From '%s:%s:%s' : %s"%(
                context.filename,str(context.line),str(context.line_pos), str( inst)
            )], [inst], err.type+(" (%s)" %  _err.__class__.__name__))

        if raiseError:
            raise raiseError
        depth -= 1
        return x



_instance=None

def call( inst):
    global _instance
    if _instance==None: _instance=InstructionsLoader()
    return _instance.call(inst)


def builtin_call( name, args, data):
    global _instance
    if _instance==None: _instance=InstructionsLoader()
    return _instance.call_from_builtin(name, args, data)

def function_exists( name):
    global _instance
    if _instance==None: _instance=InstructionsLoader()
    return name in _instance.commands