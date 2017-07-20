'''
Finite State Machine (FSM)

Created on Jul 7, 2017
'''

__author__ = 'Nenad Radulovic <nenad.b.radulovic@gmail.com>'

import queue
import logging
import threading


class _PathManager(object):
    def __init__(self):
        self.depth = 1
        self._states_path_map = {}
        self._exit = []
        self._enter = []
        
    def _build_state_depth(self, state):
        state_depth = []
        
        while state is not None:
            state_depth += [state]
            state = state.path_parent
            
        return state_depth

    def add(self, state, super_state):
        state.path_parent = super_state
        self._states_path_map[state] = []
        
    def build(self):
        for state in self._states_path_map.keys():
            path = self._build_state_depth(state)
            self.depth = max(self.depth, len(path))
            self._states_path_map[state] = path
            
    def generate(self, source, destination):
        # NOTE: Transition type A, most common transition
        if source == destination:
            self._enter += [destination]
            self._exit += [source]
        else:
            source_path = self._states_path_map[source]
            destination_path = self._states_path_map[destination]
            intersection = set(source_path) & set(destination_path)
            self._exit += [s for s in source_path if s not in intersection]
            self._enter += [s for s in destination_path if s not in intersection]
    
    def pend_exit(self, node):
        self._exit += [node]
        
    def reset(self):
        self._exit = []
        self._enter = []
        
    def exit(self):
        return iter(self._exit)
    
    def enter(self):
        return reversed(self._enter)


class _PathNode(object):
    path_parent = None
    
       
class ResourceManager(object):
    def __init__(self):
        self._resources = {}
        
    def add(self, resource_instance):
        self._resources[resource_instance.name] = resource_instance
        
    def get(self, resource_name):
        return self._resources[resource_name]
        
    def remove(self, resource_instance):
        for resource_key, resource in self._resources.items():
            if resource == resource_instance:
                resource.release()
                self._resources.pop(resource_key)

    def release_all(self):
        for resource in self._resources.values():
            resource.release()
        self._resources = {}
        
        
class ResourceInstance(object):
    '''ResourceInstance which is associated with current state machine
    
    Arguments are:
    *name* is the name of the resource 
    '''
    def __init__(self, name=None):
        self.name = name if name is not None else self.__class__.__name__
        producer = current_sm()
            
        class ResourceInstanceMethods(object):
            def __init__(self, producer):
                self.producer = producer
                
            def release(self):
                raise NotImplementedError('This is an abstract method.')
                
        self.ri = ResourceInstanceMethods(producer)
    
    
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
    ENTRY_EVENT = 'entry'
    EXIT_EVENT = 'exit'
    INIT_EVENT = 'init'
    NULL_EVENT = 'null'
    
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
        self._pathman = _PathManager()
        self._states_obj_map = {}
        self._ENTRY = Event(self.ENTRY_EVENT)
        self._EXIT = Event(self.EXIT_EVENT)
        self._INIT = Event(self.INIT_EVENT)
        self._NULL = Event(self.NULL_EVENT)
        self.rm = ResourceManager()
        self.state = init_state
        
        # Start the FSM   
        self.start()
        
    def _setup_fsm(self):
        # This loop will instantiate all state classes
        for state_cls in self.state_clss:
            self.logger.info(
                    '{} initializing {}'.format(self.name, state_cls.__name__))
            self._states_obj_map[state_cls] = state_cls(logger=self.logger)
            
        # This loop will setup super states of all states and build hierarchy
        for state in self._states_obj_map.values():
            self._pathman.add(
                    state, 
                    self._states_obj_map.get(state.super_state))
        self._pathman.build()
        self.logger.info(
            '{} hierarchy is {} level(s) deep'.format(
                    self.name, 
                    self._pathman.depth))
        
        # If we were called without initial state argument then implicitly set
        # the first declared state as initialization state. 
        if self.state is None:
            self.state = self._states_obj_map[self.state_clss[0]]
        else:
            # Also check if init_state is endeed a State class
            try:
                self.state = self._states_obj_map[self.state]
            except KeyError:
                raise TypeError(
                        'init_state argument \'{!r}\' is not a valid'
                        'subclass of State class'.format(self.state))
    
    def _exec_state(self, state, event):
        try:
            super_state = None
            event_handler = getattr(state, 'on_{}'.format(event.name))
        except AttributeError:
            super_state = state.path_parent
            event_handler = state.on_unhandled_event
        finally:
            new_state_cls = event_handler(event)
            # We are deliberately using if condition instead of try/except or
            # dictionary get method because we want this code to fail when a
            # user has given us wrong return value.
            if new_state_cls is not None:
                new_state = self._states_obj_map[new_state_cls]
            else:
                new_state = None
                
        return (new_state, super_state)
    
    def _release_state_resources(self, state):
        # Release any resource associated with current state
        for resource in state.resources.values():
            self.logger.debug(
                    '{} deleting resource {}'.format(self.name, resource.name))
            resource.release()
        state.resources = {}
        
    def _dispatch(self, event):
        current_state = self.state
        self._pathman.reset()
        # Loop until we find a state that will handle the event
        while True:
            new_state, super_state = self._exec_state(current_state, event)
            
            if super_state is not None:
                self._pathman.pend_exit(current_state)
                current_state = super_state
            else:
                break
        # Loop while new transitions are needed
        while new_state is not None:
            self.logger.debug(
                    '{} {} -> {}'.format(
                            self.name, 
                            current_state.name, 
                            new_state.name))
            self._pathman.generate(current_state, new_state)
            # Exit the path
            for exit_state in self._pathman.exit():
                self._exec_state(exit_state, self._EXIT)
                exit_state.rm.release_all()
            # Enter the path
            for enter_state in self._pathman.enter():
                self._exec_state(enter_state, self._ENTRY)
            self._pathman.reset()
            current_state = new_state
            new_state, super_state = self._exec_state(current_state, self._INIT)
            self.state = current_state
        event.ri.release()
        
    def run(self):
        '''Run this state machine as finite state machine with single level 
        hierarchy.
        
        This method is executed automatically by class constructor.

        '''
        # Setup FSM states
        self._setup_fsm()
        # Initialize the state machine
        self._dispatch(self._INIT)
        # Execute event loop
        while True:
            event = self._queue.get()
            # Check should we exit 
            if event is None:
                self.logger.info('{} terminating'.format(self.name))
                self._queue.task_done()
                self.on_terminate()
                return
            self.logger.debug(
                    '{} {}({})'.format(self.name, self.state.name, event.name))
            self._dispatch(event)
            self._queue.task_done()
            
    def on_terminate(self):
        self.rm.release_all()
            
    def put(self, event, block=True, timeout=None):
        '''Put an event to this state machine

        The event is put to state machine queue and then the run() method will
        be unblocked to process queued events.

        '''
        self._queue.put(event, block, timeout)
        
    def terminate(self, timeout=None):
        self._queue.put(None, timeout=timeout)
        
    def wait(self, timeout=None):
        self.join(timeout)
        
        
class State(_PathNode, ResourceInstance):
    '''This class implements a state.

    Each state is represented by a class. Every method of this class processes
    different events.

    '''
    super_state = None
    
    def __init__(self, logger=None):
        # Setup resource instance
        super(State, self).__init__()
        # Setup resource manager
        self.rm = ResourceManager()
        self.logger = logger
        # Convinience variable 
        self.sm = self.ri.producer
        
    def entry(self):
        pass
    
    def exit(self):
        pass
    
    def init(self):
        pass
    
    def null(self):
        pass
        
    def on_unhandled_event(self, event):
        '''Unhandled event handler
        
        This handler gets executed in case the state does not handle the event.
        
        '''
        self.logger.info(
                '{} {}({}) wasn\'t handled'.
                format(self.sm.name, self.name, event.name))
        
    
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
        
        
class Event(ResourceInstance):
    '''Event class
    
    An event is the only means of communication between state machines. Each 
    event carries name. Based on the event name a handler will be called from 
    current state class which has the same name.
    
    '''  
    def __init__(self, name=None):
        '''Using this constructor ensures that each event will be tagged with
        additional information.
        
        Arguments are:
        *name* is a string representing event name.
        '''
        super(Event, self).__init__(name)
        
        # This helper method only delivers the call to self.on_release method
        self.ri.release = self.on_relase
        
    def on_relase(self):
        pass
    
    @property
    def producer(self):
        return self.ri.producer
    

class After(ResourceInstance):
    '''Put an event to current state machine after a specified number of seconds

    Example usage:
            fsm.After(10.0, fsm.Event('blink'))

    '''
    def __init__(self, after, event, name=None, is_local=False):
        if name is None:
            name = '{}.{}.{}'.format(self.__class__.__name__, event.name, after)
        # Setup resource instance
        super(After, self).__init__(name=name)
        def timer_release(self): self._timer.cancel()
        self.ri.release = timer_release
        # Add your self to state or state machine resource manager
        if is_local:
            self.ri.producer.state.rm.add(self)
        else:
            self.ri.producer.rm.add(self)
        # Save arguments
        self.timeo = after
        self.event = event
        self.start()
    
    def start(self):
        self._timer = threading.Timer(self.timeo, self.callback, [self.event])
        self._timer.start()        
        
    def callback(self, *args, **kwargs):
        '''Callback method which is called after/every timeout
        
        *args* contains event object
        '''
        self.ri.producer.put(*args)

    def cancel(self):
        '''Cancel a running timer
        '''
        self.ri.release()
        
        
class Every(After):
    '''Put an event to current state machine every time a specified number of 
    seconds passes

    Example usage:
            fsm.Every(10.0, fsm.Event('blink'))

    '''
    def __init__(self, every, event, name=None, is_local=False):
        super().__init__(every, event, name=name, is_local=is_local)
        
    def callback(self, *args, **kwargs):
        super().callback(*args, **kwargs)
        self.start()
        

def current_sm():
    return threading.current_thread()