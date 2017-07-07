'''
Created on Jul 7, 2017

@author: nenad
'''
from queue import Queue
from logging import getLogger
from threading import Thread

class NStateMachine(object):
    state_clss = []
    state_inst = []
    logger = getLogger(None)
    
    def __init__(self, init_state = None, queue_size = 16):
        self._queue = Queue(queue_size)
        self._state = init_state
        self._thread = Thread(target=self.__runnable)
        self._should_run = True
        
        self.logger.info('{} {} is initial state'. \
                         format(self.__class__.__name__, \
                                self.state_clss[0].__name__))
        
        for state_cls in self.state_clss:
            self.logger.info('{} initializing {}'. \
                             format(self.__class__.__name__, state_cls.__name__))
            instance = state_cls()
            instance.logger = self.logger
            instance.state_machine = self
            self.state_inst += [instance]
            
        self._state = self.state_inst[0]
        self._queue.put(_INIT_EVENT)
        self._thread.start()
        
    def _exec_state(self, state, event):
        
        try:
            state_fn = getattr(state, event.name)
        except AttributeError:
            state_fn = state.default_handler
        new_state = state_fn(event)
        
        if new_state:
            new_state = self.state_inst[self.state_clss.index(new_state)]
        return new_state
            
    def __runnable(self):
        while self._should_run:
            event = self._queue.get()
            self.logger.debug('{} {}({})'. \
                format(self.__class__.__name__, self._state.__class__.__name__,
                       event.name))
            new_state = self._exec_state(self._state, event)
        
            while new_state:
                self.logger.debug('{} {} -> {}'. \
                    format(self.__class__.__name__, 
                           self._state.__class__.__name__,
                           new_state.__class__.__name__))
                self._exec_state(self._state, _EXIT_EVENT)
                self._state = new_state
                self._exec_state(self._state, _ENTRY_EVENT)
                new_state = self._exec_state(self._state, _INIT_EVENT)
                
    def put(self, event):
        assert issubclass(event.__class__, NEvent), \
            'The class {} is not subclass of {} class'. \
            format(event.name, NEvent.__name__)
        self._queue.put(event)


class NState(object):
    
    def __init__(self):
        self.logger = None
        self.state_machine = None
        
    def default_handler(self, event):
        self.logger.debug('{} {}({}) wasn\'t handled'.
                          format(self.state_machine.__class__.__name__,
                                 self.__class__.__name__,
                                 event.name))
        return None
    
    
class NStateDeclare(object):
    def __init__(self, state_machine_cls):
        assert not state_machine_cls is NStateMachine, \
            'Make specific state machine class from {}'. \
            format(NStateMachine.__name__)
            
        assert issubclass(state_machine_cls, NStateMachine), \
            'The class {} is not subclass of {} class'. \
            format(state_machine_cls.__name__, NStateMachine.__name__)
        self.state_machine_cls = state_machine_cls
            
    def __call__(self, state_cls):
        assert issubclass(state_cls, NState), \
            'The class {} is not subclass of {} class'. \
            format(state_cls.__name__, NState.__name__)
        self.state_machine_cls.state_clss += [state_cls]
        
        return state_cls
        
        
class NEvent(object):
    def __init__(self, name = None, producer = None):
        self.name = name if name else self.__class__.__name__
        self.producer = producer

_ENTRY_EVENT = NEvent('NENTRY')
_EXIT_EVENT = NEvent('NEXIT')
_INIT_EVENT = NEvent('NINIT')
