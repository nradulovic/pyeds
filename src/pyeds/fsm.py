'''
Finite State Machine (FSM)

Created on Jul 7, 2017
'''

__author__ = 'Nenad Radulovic <nenad.b.radulovic@gmail.com>'

import queue
import logging
import threading


class StateMachine(threading.Thread):
    '''This class implements a state machine.

    This class is a controller class of state machine.

    If init_state argument is given then that state will be initial state, 
    otherwise, the first initialized state is implicitly declared as initial
    state. The argument 'queue_size' specifies the size of event queue for this
    state machine. If this argument is -1 then unlimited queue size will be 
    used.

    '''
    logger = logging.getLogger(None)
    entry_event = 'entry'
    exit_event = 'exit'
    init_event = 'init'
    null_event = 'null'
    
    def __init__(self, init_state=None, queue_size=64):
        '''This constructor should always be called with keyword arguments. 
        
        Arguments are:

        *init_state* is a subclass of State class that implement the behaviour
        for initial state. The default value is None which means that the first 
        state that was declared will be initial state.

        *queue_size* is an integer specifying what is the maximum event queue
        size.

        If a subclass overrides the constructor, it must make sure to invoke
        the base class constructor (super().__init__) before doing anything
        else to the state machine.

        '''
        super().__init__(name=self.__class__.__name__, daemon=True)
        self._queue = queue.Queue(queue_size)
        self._states = []
        self._ENTRY_EVENT = Event(self.entry_event)
        self._EXIT_EVENT = Event(self.exit_event)
        self._INIT_EVENT = Event(self.init_event)
        self._NULL_EVENT = Event(self.null_event)
        # This for loop will instantiate all state classes
        for state_cls in self.state_clss:
            self.logger.info(
                    '{} initializing {}'.format(self.name, state_cls.__name__))
            self._states += [state_cls(
                    name=state_cls.__name__, sm=self, logger=self.logger)]
        # If we were called without initial state argument then implicitly set
        # the first declared state as initialization state. 
        if init_state is None:
            self.state = self._states[0]
        else:
            # Check if init_state is endeed a State class
            if not isinstance(init_state, State):
                raise TypeError(
                        'init_state argument \'{!r}\' is not a '
                        'subclass of State class'.format(init_state))
            self.state = self._map_to_state(init_state)
        self.logger.info(
                '{} {} is initial state'.format(self.name, self.state.name))
        self._build_hierarchy()
        # Decide do we need full HSM support or not
        if self.hierarchy_level > 1:
            self._dispatch = self._dispatch_hsm
        else:
            self._dispatch = self._dispatch_fsm
        # Start the FSM   
        self.start()
        
    def _map_to_state(self, state_cls):
        try:
            return self._states[self.state_clss.index(state_cls)]
        except ValueError:
            return None
    
    def _exec_state(self, state, event):
        event_handler = getattr(
                state, 
                'on_{}'.format(event.name), 
                state.on_unhandled_event)
        new_state = event_handler(event)
        return self._map_to_state(new_state)
    
    def _build_hierarchy(self):
        self.hierarchy_level = 1 
            
    def _release_state_resources(self):
        # Release any resource associated with current state
        for resource in self.state.resources:
            self.logger.debug(
                    '{} deleting resource {}'.format(self.name, resource.name))
            resource.release()
        self.state.resources = []
        
    def _dispatch_hsm(self, event):
        pass
    
    def _dispatch_fsm(self, event):
        new_state = self._exec_state(self.state, event)
        # Loop while new transitions are needed
        while new_state is not None:
            self.logger.debug(
                    '{} {} -> {}'. \
                    format(self.name, self.state.name, new_state.name))
            self._exec_state(self.state, self._EXIT_EVENT)
            self._release_state_resources()           
            self.state = new_state
            self._exec_state(self.state, self._ENTRY_EVENT)
            new_state = self._exec_state(self.state, self._INIT_EVENT)
            
    def run(self):
        '''Run this state machine as finite state machine with single level 
        hierarchy.
        
        This method is executed automatically by class constructor.

        '''
        # Initialize the state machine
        self._dispatch(self._INIT_EVENT)
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
            self._dispatch(event)
            self._queue.task_done()
            
    def put(self, event, block = True, timeout = None):
        '''Put an event to this state machine

        The event is put to state machine queue and then the run() method will
        be unblocked to process queued events.

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
    super_state = None
    
    def __init__(self, name=None, sm=None, logger=None):
        self.name = name
        self.sm = sm
        self.logger = logger
        self.resources = []
        
    def on_unhandled_event(self, event):
        '''Default event handler
        
        This handler gets executed in case the state does not handle the event.
        
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
        try:
            self.state_machine_cls.state_clss += [state_cls]
        except AttributeError:
            # Add new attribute if it doesn't exist
            self.state_machine_cls.state_clss = [state_cls]
        
        return state_cls
        
        
class Event(object):
    '''Event class
    
    An event is the only means of communication between state machines. Each 
    event carries name. Based on the event name a handler will be called from 
    current state class which has the same name.
    
    '''  
    def __init__(self, name = None):
        '''Using this constructor ensures that each event will be tagged with
        additional information.
        
        Arguments are:
        *name* is a string representing event name.
        '''
        self.name = name if name is not None else self.__class__.__name__
        self.producer = threading.current_thread()


class Resource(object):
    '''Resource which is associated with current state machine
    
    '''
    def __init__(self, args, is_local):
        self.name = '{}({})'.format(self.__class__.__name__, args)
        self.sm = threading.current_thread()
        if is_local:
            self.sm.state.resources += [self]
    
    
class After(Resource):
    '''Put an event to current state machine after a specified number of seconds

    Example usage:
            fsm.After(10.0, fsm.Event('blink'))

    '''
    def __init__(self, after, event, is_local=False):
        super(After, self).__init__('{}, {}'.format(after, event.name), is_local)
        self.timeo = after
        self.event = event
        self.timer = threading.Timer(after, self.function, [self.event])
        self.timer.start()
        
    def function(self, *args, **kwargs):
        self.sm.put(*args)
        
    def release(self):
        self.timer.cancel()
        
        
class Every(After):
    '''Put an event to current state machine every time a specified number of 
    seconds passes

    Example usage:
            fsm.Every(10.0, fsm.Event('blink'))

    '''
    def __init__(self, every, event, is_local=False):
        super().__init__(every, event, is_local)
        
    def function(self, *args, **kwargs):
        super().function(*args, **kwargs)
        self.timer = threading.Timer(self.timeo, self.function, [self.event])
        self.timer.start()
        
