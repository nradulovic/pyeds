'''
Created on Jul 23, 2017

@author: nenad
'''

import queue
import threading


class Thread(threading.Thread):
    def __init__(self, target=None, name=None):
        super().__init__(target=target, name=name, daemon=True)


class Timer(threading.Timer):
    pass


class Queue(queue.Queue):
    def put(self, item, block=False, timeout=None):
        try:
            super().put(item, block, timeout)
        except queue.Full:
            raise BufferError


def current_thread():
    return threading.current_thread()
