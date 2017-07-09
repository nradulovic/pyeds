'''
Created on Jul 7, 2017

@author: nenad
'''

__all__ = ['StateMachine', 'State', 'DeclareState', 'Event', 'After', 'Every']
__version__ = '0.1'
__author__ = 'Nenad Radulovic'

from queue import Queue
from logging import getLogger
from threading import Timer, Thread, current_thread


class StateMachine(Thread):
    '''This class implements a state machine.

    This class is a controller class of state machine.

    If init_state argument is given then that state will be initial state, 
    otherwise, the first initialized state is implicitly declared as initial
    state. The argument 'queue_size' specifies the size of event queue for this
    state machine. If this argument is -1 then unlimited queue size will be 
    used.

    '''
    state_clss = []
    logger = getLogger(None)
    entry_event = 'NENTRY'
    exit_event = 'NEXIT'
    init_event = 'NINIT'
    null_event = 'NNULL'
    
    def __init__(self, init_state=None, queue_size=64):
        '''This constructor should always be called with keyword arguments. 
        Arguments are:

        *init_state* is a subclass of State class that implement the behaviour
        for a specific state. The default value is None which means that the
        first state that was initialized will be initial state.

        *queue_size* is an integer specifying what is the maximum event queue
        size.

        If a subclass overrides the constructor, it must make sure to invoke
        the base class constructor (super().__init__) before doing anything
        else to the state machine.

        '''
        super().__init__(name=self.__class__.__name__, daemon=True)
        self._queue = Queue(queue_size)
        self._states = []
        self._ENTRY_EVENT = Event(self.entry_event)
        self._EXIT_EVENT = Event(self.exit_event)
        self._INIT_EVENT = Event(self.init_event)
        self._NULL_EVENT = Event(self.null_event)
        # This for loop will instantiate all state classes
        for state_cls in self.state_clss:
            self.logger.info(
                    '{} initializing {}'.format(self.name, state_cls.__name__))
            self._states += [state_cls(state_cls.__name__, self, self.logger)]
        # NOTE:
        # If we were called without initial state argument then implicitly 
        # declare the first state as initialization state. 
        if init_state is None:
            self.state = self._states[0]
        else:
            self.state = self._map_to_state(init_state)
        self.logger.info(
                '{} {} is initial state'.format(self.name, self.state.name))
        # Put a INIT event and start the FSM   
        self._queue.put(self._INIT_EVENT)
        self.start()
        
    def _map_to_state(self, state_cls):
        try:
            return self._states[self.state_clss.index(state_cls)]
        except ValueError:
            return None
    
    def _exec_state(self, state, event):
        try:
            new_state = getattr(state, event.name)(event)
        except AttributeError:
            new_state = state.default_handler(event)
        return self._map_to_state(new_state)
            
    def run(self):
        '''Run this state machine
        
        This method is executed automatically by class constructor.

        '''
        # Overridden run() method of Thread class
        while True:
            event = self._queue.get()
            # Check should we exit 
            if event is None:
                self.logger.info('{} terminating'.format(self.name))
                self._queue.task_done()
                return
            self.logger.debug(
                    '{} {}({})'.format(self.name, self.state.name, event.name))
            new_state = self._exec_state(self.state, event)
            # Loop while new transitions are needed
            while new_state is not None:
                self.logger.debug(
                        '{} {} -> {}'. \
                        format(self.name, self.state.name, new_state.name))
                self._exec_state(self.state, self._EXIT_EVENT)
                # Release any resource associated with current state
                for resource in self.state.resources:
                    self.logger.debug(
                            '{} deleting resource {}'. \
                            format(self.name, resource.name))
                    resource.release()
                self.state.resources = []
                self.state = new_state
                self._exec_state(self.state, self._ENTRY_EVENT)
                new_state = self._exec_state(self.state, self._INIT_EVENT)
            self._queue.task_done()
            
    def put(self, event, block = True, timeout = None):
        '''Put an event to this state machine

        The event is put to state machine queue and then the run() method is
        invoked to process queued events.

        '''
        if not issubclass(event.__class__, Event):
            msg = 'The class {} is not subclass of {} class'. \
                    format(event.__class__.__name__, Event.__name__)
            self.logger.exception(msg)
            raise TypeError(msg)    
        self._queue.put(event, block, timeout)
        
    def release(self, timeout=None):
        self._queue.put(None, timeout=timeout)
        self.join(timeout)


class State(object):
    '''This class implements a state.

    Each state is represented by a class. Every method of this class processes
    different events.

    '''
    def __init__(self, name=None, sm=None, logger=None):
        self.name = name
        self.sm = sm
        self.logger = logger
        self.resources = []
        
    def default_handler(self, event):
        '''Default event handler
        
        This handler gets executed in case the state does not handle an event.
        
        '''
        self.logger.warn(
                '{} {}({}) wasn\'t handled'.
                format(self.sm.name, self.name, event.name))
        return None
    
    
class DeclareState(object):
    '''This is a decorator class which binds a state with a state machine.

    Use this decorator class to bind states to a state machine.

    '''
    def __init__(self, state_machine_cls):
        assert state_machine_cls is not StateMachine, \
                'Make specific state machine class from {}'. \
                format(StateMachine.__name__)
        assert issubclass(state_machine_cls, StateMachine), \
                'The class {} is not subclass of {} class'. \
                format(state_machine_cls.__name__, StateMachine.__name__)
        self.state_machine_cls = state_machine_cls
            
    def __call__(self, state_cls):
        assert issubclass(state_cls, State), \
                'The class {} is not subclass of {} class'. \
                format(state_cls.__name__, State.__name__)
        self.state_machine_cls.state_clss += [state_cls]
        
        return state_cls
        
        
class Event(object):
    def __init__(self, name = None):
        self.name = name if name is not None else self.__class__.__name__
        self.producer = current_thread()


class After(object):
    """Put an event after a specified number of seconds:

            t = fsm.After(10.0, fsm.Event('event_name'))

    """
    def __init__(self, after, event, is_local=False):
        self.timeo = after
        self.event = event
        self.name = '{}({}, \'{}\')'.format(
                self.__class__.__name__, after, event.name)
        self.sm = current_thread()
        if is_local:
            self.sm.state.resources += [self]
        self.timer = Timer(after, self.function, [self.event])
        self.timer.start()
        
    def function(self, *args, **kwargs):
        self.sm.put(*args)
        
    def release(self):
        self.timer.cancel()
        
        
class Every(After):
    def __init__(self, every, event, local=False):
        super().__init__(every, event, local)
        
    def function(self, *args, **kwargs):
        super().function(*args, **kwargs)
        self.timer = Timer(self.timeo, self.function, [self.event])
        self.timer.start()
        
