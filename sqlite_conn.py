import os
import time
import json
import sqlite3

from http_server import log

from hashlib import sha3_512
import base64
from http_server import utils


def join(x):
    if isinstance(x, str): return x
    if isinstance(x, (tuple, list)): return ";".join(x)
    return ""


def _int(x):
    if isinstance(x, (int, float, str)): return int(x)
    return -1


FCTS = [
    _int,
    str,
    str,
    join,
    _int,
    _int,
    join,
    str,
    join,
    join,
    join,
    join,
    float,
    _int,
    _int
]


def _str(x):
    return str(x).replace("'", "\\'")


def jsdef(js, key, defaut="", fct=_str):
    if isinstance(js, (tuple, list)):
        if js[key] == None:
            if not fct: return defaut
            return fct(defaut)
        if not fct: return js[key]
        return fct(js[key])
    else:
        if key in js:
            if not fct: return js[key]
            return fct(js[key])
        if not fct: return defaut
        return fct(defaut)


def format_row(row):
    out = []
    for i in range(len(row)):
        out.append(FCTS[i](row[i]))
    return tuple(out)


def translate_query(src):
    i = 0
    l = src.split(' ')
    out = ""
    while i < len(l):
        x = l[i]
        if i + 2 < len(l) and l[i + 1] == 'in':
            out += " %s like '%%%s%%' " % (l[i + 2], l[i][1:-1])
            i += 3
        else:
            out += x + " "
            i += 1

    return out


def sqvalue(x):
    if isinstance(x, str): return "'%s'" % x
    if isinstance(x, bool): return "true" if x else "false"
    if isinstance(x, int): return "%d" % x
    if isinstance(x, float): return "%f" % x
    raise Exception("Erreur type non compatible")


class SQConnector:
    FILM_SCHEM = """create table films (
	id int primary key,
    name text,
    image text,
    nationality text,
    year int,
    duration int,
    genre text,
    description text,
    director text,
    actor text,
    creator text,
    musicBy text,
    note real,
    nnote int,
    nreview int)
"""

    def __init__(self, file):
        is_init =  os.path.exists(file) or not os.path.isfile(file)
        self.conn = sqlite3.connect(file, check_same_thread=False)
        self.conn.execute("PRAGMA case_sensitive_like = false;")
        if not is_init:
            self.init_base()


    def exec(self, sql):
        c = self.conn.cursor()
        try:
            return c.execute(sql).fetchall()
        except Exception as err:
            log.error("Eror sql: %s  (%s)" % (str(err), sql))
            return None

    def onerow(self, sql):
        c = self.conn.cursor()
        return c.execute(sql).fetchone()

    def one(self, sql):
        c = self.conn.cursor()
        return c.execute(sql).fetchone()[0]

    def init_base(self):
        raise NotImplementedError()

    def table_exists(self, name):
        if isinstance(name, (tuple, list)):
            for x in name:
                if not self.table_exists(x): return False
            return True
        else:
            return self.one("select count(name) from sqlite_master where type='table' AND name='%s'" % name) > 0

    def init_user(self, username, file):
        usr = self.exec("select name from users where name='%s'" % username)
        if not len(usr):
            self.exec("insert into users (name, password) values ('%s', '%s') " % (username, utils.password("")))
            self.conn.commit()

    def commit(self):
        return self.conn.commit()




