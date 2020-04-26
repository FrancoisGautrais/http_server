from threading import Condition, Lock

from . import log


class WaitQueue:

    def __init__(self):
        self.buffer=[]
        self.lock=Lock()
        self.cond=Condition()

    def enqueue(self, data):
        self.lock.acquire()
        self.buffer.append(data)
        self.lock.release()
        with self.cond:
            self.cond.notify()

    def wait(self):
        with self.cond:
            self.cond.wait()

    def dequeue(self):
        out="empty"
        while out=="empty":
            while len(self.buffer)==0:
                self.wait()

            self.lock.acquire()

            if len(self.buffer)>0:
                out=self.buffer.pop()
            self.lock.release()
            if out and out!="empty":
                return out