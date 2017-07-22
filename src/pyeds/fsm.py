'''
Finite State Machine (FSM)

Created on Jul 7, 2017
'''

__author__ = 'Nenad Radulovic <nenad.b.radulovic@gmail.com>'

import queue
import logging
import threading


EVENT_HANDLER_PREFIX = 'on_'
ENTRY_SIGNAL = 'entry'
EXIT_SIGNAL = 'exit'
INIT_SIGNAL = 'init'


class _PathManager(object):
    def __init__(self):
        self.depth = 1
        self._state_hieararchy_map = {}
        self._state_path_map = {}
        self._state_translation_map = {}
        self._exit = []
        self._enter = []
        
    def _build_state_cls_depth(self, state_cls):
        state_cls_depth = ()
        parent = self._state_hieararchy_map[state_cls]
        
        while parent is not None:
            state_cls_depth += (parent,)
            parent = self._state_hieararchy_map[parent]
            
        return state_cls_depth

    def add(self, state_cls, parent_state_cls):
        self._state_hieararchy_map[state_cls] = parent_state_cls
        
    def build(self):
        # Build translation map
        for state_cls in self._state_hieararchy_map.keys():
            self._state_translation_map[state_cls] = state_cls()
        # Build path map
        for state_cls in self._state_hieararchy_map.keys():
            state_cls_depth = self._build_state_cls_depth(state_cls)
            self.depth = max(self.depth, len(state_cls_depth))
            self._state_path_map[self.instance_of(state_cls)] = \
                    ([self.instance_of(item) for item in state_cls_depth])
        del self._state_hieararchy_map
        # Ensure that there is at least one element in the dict so we don't get
        # KeyError elsewhere in the code
        self._state_translation_map[None] = None
        self._state_path_map[None] = None
            
    def generate(self, source, destination):
        # NOTE: Transition type A, most common transition
        if source == destination:
            self._enter += [destination]
            self._exit += [source]
        else:
            source_path = self._state_path_map[source]
            destination_path = self._state_path_map[destination]
            intersection = set(source_path) & set(destination_path)
            self._exit += [s for s in source_path if s not in intersection]
            self._enter += [s for s in destination_path if s not in intersection]
    
    def parent_of(self, state):
        return self._state_path_map[state][0]
        
    def instance_of(self, state_cls):
        return self._state_translation_map[state_cls]
        
    def pend_exit(self, node):
        self._exit += [node]
        
    def reset(self):
        self._exit = []
        self._enter = []
        
    def exit(self):
        return iter(self._exit)
    
    def enter(self):
        return reversed(self._enter)


class StateError(Exception):
    pass


class StateMachineError(Exception):
    pass

      
class ResourceManager(object):
    def __init__(self):
        self._resources = {}
        
    def put(self, resource_instance):
        self._resources[resource_instance.name] = resource_instance
        
    def get(self, resource_name):
        return self._resources[resource_name]
        
    def remove(self, resource_name):
        del self._resources[resource_name]
        
    def pop(self, resource_name):
        resource = self.get(resource_name)
        self.remove(resource_name)
        return resource

    def release_all(self):
        for resource in self._resources.values():
            resource.release()
        self._resources = {}
        
        
class ResourceInstance(object):
    '''ResourceInstance which is associated with current state machine
    
    Arguments are:
    *name* is the name of the resource 
    '''
    name = ''
    '''This is a string containing State name'''
    producer = None
    '''Specifies which state machine has this state'''
    
    def __init__(self, name=None):
        self.name = name if name is not None else self.__class__.__name__
        self.producer = current_sm()

    def release(self):
        raise NotImplementedError(
                'In class {} is not implemented abstract method.'.format(
                        self.__class__.__name__))    
    
    
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
        self.rm = ResourceManager()
        self.state_cls = init_state
        
        # Start the FSM   
        self.start()
        
    def _setup_fsm(self):
        class Signal(Event):
            def execute(self, handler):
                    return handler()
        self._ENTRY = Signal(ENTRY_SIGNAL)
        self._EXIT = Signal(EXIT_SIGNAL)
        self._INIT = Signal(INIT_SIGNAL)
        
        # This loop will instantiate all state classes
        for state_cls in self.state_clss:
            self.logger.info(
                    '{} initializing {}'.format(self.name, state_cls.__name__))
            self._pathman.add(state_cls, state_cls.super_state)
            
        self._pathman.build()
        self.logger.info(
            '{} hierarchy is {} level(s) deep'.format(
                    self.name, 
                    self._pathman.depth))
        
        # If we were called without initial state argument then implicitly set
        # the first declared state as initialization state. 
        if self.state_cls is None:
            self.state = self._pathman.instance_of(self.state_clss[0])
        else:
            # Also check if init_state is endeed a State class
            try:
                self.state = self._pathman.instance_of(self.state_cls)
            except KeyError:
                raise StateMachineError(
                        'init_state argument \'{!r}\' is not a valid'
                        'subclass of State class'.format(self.state_cls))
    
    def _exec_state(self, state, event):
        try:
            super_state = None
            handler = getattr(
                    state, 
                    '{}{}'.format(EVENT_HANDLER_PREFIX, event.name))
        except AttributeError:
            super_state = self._pathman.parent_of(state)
            handler = state.on_unhandled_event
        finally:
            try:
                new_state_cls = event.execute(handler)
            except Exception as e:
                self.on_exception(e, state, event)
                # This state has caused an error, no transitions will be done
                new_state_cls = None
        try:
            new_state = self._pathman.instance_of(new_state_cls)
        except KeyError:
            raise StateMachineError(
                    'Target state \'{!r}\' is not a valid'
                    'subclass of State class'.format(new_state_cls))
                
        return (new_state, super_state)
    
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
                self._queue.task_done()
                self.on_terminate()
                self.logger.info('{} terminated'.format(self.name))
                return
            self.logger.debug(
                    '{} {}({})'.format(self.name, self.state.name, event.name))
            self._dispatch(event)
            self._queue.task_done()
            
    def send(self, event, block=True, timeout=None):
        '''Put an event to this state machine

        The event is put to state machine queue and then the run() method will
        be unblocked to process queued events.

        '''
        self._queue.put(event, block, timeout)
        
    def terminate(self, timeout=None):
        self._queue.put(None, timeout=timeout)
        
    def wait(self, timeout=None):
        self.join(timeout)
        
    def instance_of(self, state_cls):
        return self._pathman.instance_of(state_cls)
                
    def on_terminate(self):
        self.rm.release_all()
        
    def on_exception(self, e, state, event):
        raise StateError(
                e, 
                self.__class__.__module__, 
                self.name, 
                state.name, 
                event.name)
        
        
class State(ResourceInstance):
    '''This class implements a state.

    Each state is represented by a class. Every method of this class processes
    different events.

    '''
    super_state = None
    
    def __init__(self):
        # Setup resource instance
        super(State, self).__init__()
        # Add self to SM (producer) ResourceManager
        self.producer.rm.put(self)
        # Setup resource manager
        self.rm = ResourceManager()
    
    @property
    def sm(self):
        return self.producer
    
    @property
    def logger(self):
        return self.producer.logger
        
    @logger.setter
    def logger(self, logger):
        raise StateError(
                'Unable to set state machine logger, use self.sm.logger')
        
    def on_entry(self):
        pass
    
    def on_exit(self):
        pass
    
    def on_init(self):
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
        super().__init__(name)
    
    def execute(self, handler):
        return handler(self)
    
    def release(self):
        pass
    
    
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
        # Add your self to state or state machine resource manager
        if is_local:
            self.producer.state.rm.put(self)
        else:
            self.producer.rm.put(self)
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
        self.producer.put(*args)

    def release(self):
        self._timer.cancel()
        
    def cancel(self):
        '''Cancel a running timer
        '''
        self.release()
        
        
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


