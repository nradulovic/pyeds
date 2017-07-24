'''
Created on Jul 23, 2017

@author: nenad
'''

import threading
import queue

class Thread(threading.Thread):
    def __init__(self, target=None, name=None):
        super().__init__(target=target, name=name, daemon=True)

class Timer(threading.Timer):        
    pass

class Queue(queue.Queue):
    pass

def current_thread():
    return threading.current_thread()