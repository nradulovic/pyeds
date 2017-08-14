'''
Finite State Machine (FSM)

Created on Jul 7, 2017
'''

__author__ = 'Nenad Radulovic <nenad.b.radulovic@gmail.com>'

import logging

from . import coordinator
from . import lib


EVENT_HANDLER_PREFIX = 'on_'
ENTRY_SIGNAL = 'entry'
EXIT_SIGNAL = 'exit'
INIT_SIGNAL = 'init'


class _PathManager(object):
    def __init__(self):
        self.depth = 0
        self._hierarchy_map = {}
        self._path_map = {}
        self._translation_map = {}
        self._exit = []
        self._enter = []

    def _build_node_cls_depth(self, node_cls):
        node_cls_depth = ()
        parent = self._hierarchy_map[node_cls]

        while parent is not None:
            node_cls_depth += (parent,)
            parent = self._hierarchy_map[parent]

        return node_cls_depth

    def add_cls(self, node_cls, parent_node_cls):
        self._hierarchy_map[node_cls] = parent_node_cls

    def build(self):
        # Build translation map
        for node_cls in self._hierarchy_map.keys():
            self._translation_map[node_cls] = node_cls()
        # Build path map
        for node_cls in self._hierarchy_map.keys():
            node_cls_depth = self._build_node_cls_depth(node_cls)
            self.depth = max(self.depth, len(node_cls_depth))
            self._path_map[self.instance_of(node_cls)] = \
                tuple([self.instance_of(i) for i in node_cls_depth] + [None])
        # We don't need hierarchy map anymore
        del self._hierarchy_map
        # Ensure that there is at least None element in the dict so we don't
        # get KeyError elsewhere in the code
        self._translation_map[None] = None
        self._path_map[None] = [None]
        # Correction for hierarchy depth
        self.depth += 1

    def states(self):
        nodes = ()
        for node in self._translation_map.values():
            if node is not None:
                nodes += (node.name,)
        return nodes

    def generate(self, source, destination):
        src_path = (source,) + self._path_map[source]
        dst_path = (destination,) + self._path_map[destination]
        intersection = set(src_path) & set(dst_path)
        self._exit += [s for s in src_path if s not in intersection]
        self._enter += [s for s in dst_path if s not in intersection]

    def parent_of(self, node):
        return self._path_map[node][0]

    def instance_of(self, node_cls):
        return self._translation_map[node_cls]

    def pend_exit(self, node):
        self._exit += [node]

    def reset(self):
        self._exit = []
        self._enter = []

    def exit_iterator(self):
        return iter(self._exit)

    def enter_iterator(self):
        return reversed(self._enter)


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
    *name* is the name of the resource.
    '''
    def __init__(self, name=None):
        # Try to setup the name of this resource instance
        if not hasattr(self, 'name'):
            self.name = name if name is not None else self.__class__.__name__
        self.producer = current_sm()

    def release(self):
        raise NotImplementedError(
            'Abstract method \'release\' in class \'{}\'.'.format(
                self.__class__.__name__))


class StateMachine(object):
    '''This class implements a state machine.

    This class is a controller class of state machine.

    If init_state_cls argument is given then that state will be initial state,
    otherwise, the first declared (registered) state is implicitly declared as
    initial state.
    '''
    init_state_cls = None
    '''Initial state class'''
    logger = logging.getLogger(None)
    '''Logger instance used by the state machine'''
    should_autostart = True
    '''Should machine start at initialization'''

    def __init__(self, queue_size=64, name=None):
        '''This constructor should always be called with keyword arguments.

        Arguments are:

        *queue_size* is an integer specifying what is the maximum event queue
        size. When this argument is not given it defaults to 64. If this
        argument is -1 then unlimited queue size will be used.

        *name* is a string specifying the state machine name. When this
        argument is not given then the class name is taken as the state machine
        name.

        If a subclass overrides the constructor, it must make sure to invoke
        the base class constructor (super().__init__) before doing anything
        else to the state machine.
        '''
        self._name = name if name is not None else self.__class__.__name__
        self._queue = coordinator.Queue(queue_size)
        self._pm = _PathManager()
        self._thread = coordinator.Thread(
                target=self.event_loop,
                name=self.name)
        self._thread.sm = self
        self.rm = ResourceManager()
        if self.should_autostart:
            self._thread.start()

    def _setup_fsm(self):
        class Signal(Event):
            def execute(self, handler):
                return handler()
        self._ENTRY = Signal(ENTRY_SIGNAL)
        self._EXIT = Signal(EXIT_SIGNAL)
        self._INIT = Signal(INIT_SIGNAL)
        if not hasattr(self, 'state_clss'):
            raise AttributeError('{} has no states'.format(self.name))
        # This loop will add all state classes to path manager
        for state_cls in self.state_clss:
            self.logger.info(
                    '{} adding {}'.format(self.name, state_cls.__name__))
            self._pm.add_cls(state_cls, state_cls.super_state)
        # Instantiate added state classes and build path
        self._pm.build()
        self.logger.info(
            '{} hierarchy is {} level(s) deep, {} state(s)'.format(
                self.name, self._pm.depth, len(self._pm.states())))
        # If we were called without initial state argument then implicitly set
        # the first declared state as initialization state.
        if self.init_state_cls is None:
            self.init_state_cls = self.state_clss[0]
        # Also check if init_state_cls is endeed a State class
        try:
            self._state = self._pm.instance_of(self.init_state_cls)
        except KeyError:
            raise LookupError(
                    'init_state_cls argument \'{!r}\' '
                    'is not a registered state'.format(self.init_state_cls))
        self.logger.info(
                '{} {} is initial state'.format(
                        self.name, self._state.name))

    def _exec_state(self, state, event):
        handler_name = '{}{}'.format(EVENT_HANDLER_PREFIX, event.name)
        try:
            super_state = None
            handler = getattr(state, handler_name)
        except AttributeError:
            super_state = self._pm.parent_of(state)
            handler = state.on_unhandled_event
        finally:
            try:
                new_state_cls = event.execute(handler)
            except Exception as e:
                self.on_exception(e, state, event, 'State exception')
                # This state has caused an error, no transitions will be done
                new_state_cls = None
        try:
            new_state = self._pm.instance_of(new_state_cls)
        except KeyError:
            raise LookupError(
                    'Target state \'{!r}\' '
                    'is not a registered state'.format(new_state_cls))
        return (new_state, super_state)

    def _dispatch(self, event):
        current_state = self._state
        self._pm.reset()
        # Loop until we find a state that will handle the event
        while True:
            new_state, super_state = self._exec_state(current_state, event)
            if super_state is not None:
                self._pm.pend_exit(current_state)
                current_state = super_state
            else:
                break
        # Loop while new transitions are needed
        while new_state is not None:
            self.logger.debug(
                '{} {} -> {}'.format(
                    self.name, current_state.name, new_state.name))
            self._pm.generate(current_state, new_state)
            # Exit the path
            for exit_state in self._pm.exit_iterator():
                self._exec_state(exit_state, self._EXIT)
                exit_state.rm.release_all()
            # Enter the path
            for enter_state in self._pm.enter_iterator():
                self._exec_state(enter_state, self._ENTRY)
            self._pm.reset()
            current_state = new_state
            new_state, super_state = self._exec_state(
                current_state, self._INIT)
            self._state = current_state
        event.release()

    @property
    def depth(self):
        '''The depth of state machine states hierarchy'''
        return self._pm.depth

    @property
    def states(self):
        '''List of names of registered states'''
        return self._pm.states()

    @property
    def state(self):
        '''Current state instance'''
        return self._state

    @property
    def name(self):
        '''String containing the state machine name'''
        return self._name

    def instance_of(self, state_cls):
        '''Get the instance of state class'''
        return self._pm.instance_of(state_cls)

    def event_loop(self):
        '''Event loop
        '''
        # Initialize states and build hierarchy
        self._setup_fsm()
        # Initialize the state machine
        self._dispatch(self._INIT)
        self.on_start()
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
                '{} {}({})'.format(self.name, self._state.name, event.name))
            self._dispatch(event)
            self._queue.task_done()

    def send(self, event, block=True, timeout=None):
        '''Send an event to the state machine

        The event is put to state machine queue and then the event_loop()
        method will process the queued event.
        '''
        self._queue.put(event, block, timeout)

    def wait(self, timeout=None):
        '''Wait until the state machine terminates'''
        self._thread.join(timeout)

    def do_start(self):
        '''Explicitly start the state machine'''
        self._thread.start()

    def do_terminate(self, timeout=None):
        '''Pend termination of the state machine.

        After calling this method the state machine may still run. Use
        ``wait()`` to wait for state machine until it terminates.
        '''
        self._queue.put(None, timeout=timeout)

    def on_start(self):
        '''Gets called by state machine just before the machine starts'''
        pass

    def on_terminate(self):
        '''Gets called by state machine just before the termination'''
        self.rm.release_all()

    def on_exception(self, e, state, event, msg):
        '''Gets called when unhandled exception has occured'''
        raise RuntimeError(
                e,
                msg,
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

    def release(self):
        pass

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
        self.logger.debug(
                '{} {}({}) wasn\'t handled'.
                format(self.sm.name, self.name, event.name))


class DeclareState(object):
    '''This is a decorator class which binds a state with a state machine.

    Use this decorator class to bind states to a state machine.

    '''
    def __init__(self, state_machine_cls):
        assert state_machine_cls is not StateMachine, \
            'Make specific state machine class from {}'.format(
                StateMachine.__name__)
        assert issubclass(state_machine_cls, StateMachine), \
            'The class {} is not subclass of {} class'.format(
                state_machine_cls.__name__, StateMachine.__name__)
        self.state_machine_cls = state_machine_cls

    def __call__(self, state_cls):
        assert issubclass(state_cls, State), \
            'The class {} is not subclass of {} class'.format(
                state_cls.__name__, State.__name__)
        try:
            self.state_machine_cls.state_clss += [state_cls]
        except AttributeError:
            # Add new attribute if it doesn't exist
            self.state_machine_cls.state_clss = [state_cls]
        return state_cls


class Event(lib.Immutable, ResourceInstance):
    '''Event

    An event is a notable occurrence at a particular point in time. Events can,
    but do not necessarily, cause state transitions from one state to another
    in state machines.

    An event can have associated parameters, allowing the event to convey not
    only the occurrence but also quantitative information about the occurrence.

    An event is the only means of communication between state machines. Each
    event carries name. Based on the event name a handler will be called from
    current state class which has the same name.
    '''
    def __init__(self, name=None):
        '''Using this constructor ensures that each event will be tagged with
        additional information.

        Arguments are:

        *name* is a string representing event name. When this argument is not
        given then the class name is taken as the event name.
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
            name = '{}.{}.{}'.format(
                self.__class__.__name__, event.name, after)
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
        self._timer = coordinator.Timer(
            self.timeo, self.callback, [self.event])
        self._timer.start()

    def callback(self, *args, **kwargs):
        '''Callback method which is called after/every timeout

        *args* contains event object
        '''
        self.producer.send(*args)

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
    current = coordinator.current_thread()
    try:
        return current.sm
    except AttributeError:
        return None
