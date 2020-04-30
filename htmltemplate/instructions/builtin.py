from urllib import parse
from ...filecache import filecache
from ..htmlgen import html_gen_fd
import  copy
import json

def custom_deepcopy(x):
    cp = {}
    for key in x:
        if key.startswith("_"):
            cp[key]=x[key]
        else:
            cp[key]=copy.deepcopy(x[key])
    return cp




def inst_include(args, data):
    x=custom_deepcopy(data)
    with filecache.open(args[0]) as f:
        if len(args)>1:
            x.update(args[1])
        return html_gen_fd(f, x)

def inst_get(args, data):
    acc=data
    for x in args:
        acc=acc[x]
    return acc
#
# set(k ,k2, .., kn, value)
#
def inst_set(args, data):
    inst_get(args[:-2], data)[args[-2]]=args[-1]


def inst_ismobile(args, data):
    return data["_request"].is_mobile()

def inst_ifmobile(args, data):
    if data["_request"].is_mobile():
        return args[0]

def inst_ifnmobile(args, data):
    if not data["_request"].is_mobile():
        return args[0]

def inst_cat(args, data):
    acc=""
    for x in args:
        acc+=str(x)
    return  acc

def inst_kv(args, data):
    return (args[0], args[1])

def inst_list(args, data):
    return args

def inst_objl(args, data):
    out={}
    i=0
    while i+1<len(args):
        out[args[i]]=args[i+1]
        i+=2
    return out

def inst_escape(args, data):
    return args[0].replace("\n", "\\n")

def inst_None(args, data): return None

def inst_true(args, data): return True

def inst_false(args, data): return False

def inst_bloc(args, data):
    return args[-1]

def inst_object(args, data):
    obj={}
    for x in args:
        obj[x[0]]=x[1]
    return obj


def inst_if(args, data):
    x = args[0]
    if x: return args[1]
    elif len(args)>2: return args[2]
    return ""

def inst_not(args, data):
    return not args[0]

def inst_eq(args, data): return not args[0] == args[1]
def inst_diff(args, data): return not args[0] != args[1]
def inst_inf(args, data): return not args[0] < args[1]
def inst_infeq(args, data): return not args[0] <= args[1]
def inst_sup(args, data): return not args[0] > args[1]
def inst_supeq(args, data): return not args[0] >= args[1]


def inst_mobile(args, data):
    x = data["user"]["mobile"]
    if x:
        return args[0]
    elif len(args) > 1:
        return args[1]

def inst_desktop(args, data):
    x = not data["user"]["mobile"]
    if x:
        return args[0]
    elif len(args) > 1:
        return args[1]

def inst_json(args, data):
    x=args[0]
    if isinstance(x, dict):
        out={}
        for k in x:
            if x[k]==None or isinstance(x[k], (int, float, bool, tuple, list, dict, str, set)):
                out[k]=x[k]
    else:
        out=x
    return json.dumps(out)

def inst_replace(args, data):
    return args[0].replace(args[1], args[2])

def inst_add(args, data):
    acc=0
    for x in args:
        acc+=int(x)
    return acc

def inst_lower(args, data):
    return args[0].lower()


def inst_minToStr(args, data):
    n=args[0]
    out=""
    h=int(n/60)
    m=str(n%60)
    if len(m)==1: m="0"+m
    if h>0: return str(h)+"h"+m
    else: return m+" minutes"

def inst_jsbool(args, data):
    return "true" if args[0] else "false"

def inst_urlencode(args, data): return parse.quote(args[0])

def inst_urldecode(args, data): return parse.unquote(args[0])

def inst_escapequote(args, data):
    return args[0].replace("\"", "\\\"")

