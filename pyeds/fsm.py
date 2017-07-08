'''
Created on Jul 7, 2017

@author: nenad
'''
from queue import Queue
from logging import getLogger
from threading import Timer, Thread, current_thread

class NStateMachine(Thread):
    state_clss = []
    logger = getLogger(None)
    entry_event = 'NENTRY'
    exit_event = 'NEXIT'
    init_event = 'NINIT'
    null_event = 'NNULL'
    
    def __init__(self, init_state=None, queue_size=64):
        super().__init__(name=self.__class__.__name__, daemon=True)
        self._queue = Queue(queue_size)
        self._states = []
        self._ENTRY_EVENT = NEvent(self.entry_event)
        self._EXIT_EVENT = NEvent(self.exit_event)
        self._INIT_EVENT = NEvent(self.init_event)
        self._NULL_EVENT = NEvent(self.null_event)
                
        self.logger.info('{} {} is initial state'. \
            format(self.name, self.state_clss[0].__name__))
        
        for state_cls in self.state_clss:
            self.logger.info('{} initializing {}'. \
                format(self.name, state_cls.__name__))
            self._states += [state_cls(state_cls.__name__, self, self.logger)]
            
        self.state = self._states[0] if init_state is None \
            else self._map_to_state(init_state)
        self._queue.put(self._INIT_EVENT)
        self.start()
        
    def _map_to_state(self, state_cls):
        return self._states[self.state_clss.index(state_cls)]
    
    def _exec_state(self, state, event):
        
        try:
            state_fn = getattr(state, event.name)
        except AttributeError:
            state_fn = state.default_handler
        new_state = state_fn(event)
        
        if new_state:
            new_state = self._map_to_state(new_state)
        return new_state
            
    def run(self):
        while True:
            event = self._queue.get()
            
            if event is None:
                self.logger.info('{} terminating'. \
                    format(self.name))
                self._queue.task_done()
                return
            
            self.logger.debug('{} {}({})'. \
                format(self.name, self.state.name, event.name))
            new_state = self._exec_state(self.state, event)
        
            while new_state:
                self.logger.debug('{} {} -> {}'. \
                    format(self.name, self.state.name, new_state.name))
                self._exec_state(self.state, self._EXIT_EVENT)
                
                for resource in self.state.resources:
                    self.logger.debug('{} deleting resource {}'. \
                        format(self.name, resource.name))
                    resource.release()
                self.state.resources = []
                self.state = new_state
                self._exec_state(self.state, self._ENTRY_EVENT)
                new_state = self._exec_state(self.state, self._INIT_EVENT)
            self._queue.task_done()
            
    def put(self, event, block = True, timeout = None):
        if not issubclass(event.__class__, NEvent):
            msg = 'The class {} is not subclass of {} class'. \
                  format(event.__class__.__name__, NEvent.__name__)
            self.logger.critical(msg)
            raise TypeError(msg)    
        self._queue.put(event, block, timeout)
        
    def release(self, timeout=None):
        self._queue.put(None, timeout=timeout)
        self.join(timeout)

class NState(object):
    
    def __init__(self, name=None, sm=None, logger=None):
        self.name = name
        self.sm = sm
        self.logger = logger
        self.resources = []
        
    def default_handler(self, event):
        self.logger.warn('{} {}({}) wasn\'t handled'.
            format(self.sm.name, self.name, event.name))
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
    def __init__(self, name = None):
        self.name = name if name else self.__class__.__name__
        self.producer = current_thread()


class NTimerAfter(object):
    def __init__(self, after, event, local=False):
        self.timeo = after
        self.event = event
        self.name = 'NTimerEvery({}, \'{}\')'.format(after, event.name)
        self.sm = current_thread()
        
        if local:
            self.sm.state.resources += [self]
        self.timer = Timer(after, self.function, [self.event])
        self.timer.start()
        
    def function(self, *args, **kwargs):
        self.sm.put(*args)
        
    def release(self):
        self.timer.cancel()
        
class NTimerEvery(NTimerAfter):
    def __init__(self, every, event, local=False):
        super().__init__(every, event, local)
        
    def function(self, *args, **kwargs):
        super().function(*args, **kwargs)
        self.timer = Timer(self.timeo, self.function, [self.event])
        self.timer.start()
        
