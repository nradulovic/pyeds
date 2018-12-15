'''
Finite State Machine (FSM)
--------------------------

A finite-state machine (FSM) is a mathematical model of computation. It is an
abstract machine that can be in exactly one of a finite number of states at any
given time. The FSM can change from one state to another in response to some
external events; the change from one state to another is called a state
transition. An FSM is defined by a list of its states, its initial state, and
the conditions for each transition.

Event
-----

An event is a notable occurrence at a particular point in time. Events can, but
do not necessarily, cause state transitions from one state to another in state
machines.

An event can have associated parameters, allowing the event to convey not only
the occurrence but also quantitative information about the occurrence.

An event in PyEDS is instanced using class :obj:`Event`.

State
-----

A state is a description of the status of a system that is waiting to execute
a transition.

State transition
----------------

Switching from one state to another is called state transition. A transition is
a set of actions to be executed when a condition is fulfilled or when an event
is received.

Module details
--------------

Created on Jul 7, 2017
'''

__author__ = 'Nenad Radulovic <nenad.b.radulovic@gmail.com>'

import re
import logging

from . import coordinator
from . import lib


EVENT_HANDLER_PREFIX = 'on_'
'''This is default event handler prefix.

This string is prefixed with event name to form event handler name which will
be called to process the event.
'''


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


class Resource(object):
    '''Resource which is associated with an object.

    Args:
        * category (:obj:`str`, *optional*): Is the category of the resource.
          The default value is `obj`.
        * name (:obj:`str`, *optional*): Is the name of the resource. The
          default value is ``None`` which means that the name will be defined
          by resource class name.
        * owner (:obj:`object`, *optional*): Object which is the owner of the
          resource. The default value is ``None``.
        * is_unique (:obj:`bool`, *optional*): Defines if this resource should
          be unique in Resource management. By being unique means that a
          resource in a given *category* is the only resource with the
          specified *name*. The default value is ``False``.
        * releaser (:obj:`function`): A function which will be called when this
          resource is being removed.

    Attributes:
        * resources (:obj:`dict`): Dictionary contains all resources managed by
          Resource. It contains additional information like *category* and
          *name* for fast fetching of resource objects.
    '''
    resources = {}

    def __init__(
            self,
            category='obj',
            name=None,
            owner=None,
            is_unique=False,
            releaser=None):
        name = name or self.__class__.__name__
        self.category = category
        self.name = name
        self.owner = owner
        self.is_unique = is_unique
        self._releaser = releaser
        Resource._lock = coordinator.provider.Lock()

    @classmethod
    def _build_filter_map(cls):
        filter_map = {}
        for category, names in cls.resources.items():
            for name, instances in names.items():
                for instance in instances:
                    filter_map[instance] = (category, name, instance.owner)
        return filter_map

    @classmethod
    def add_resource(cls, resource):
        '''Add a resource to resource management.

        Args:
            * resource (:obj:'Resource'): Add derived class of ``Resource`` to
              resource management.

        Raises:
            * ValueError: When this resource is not a unique resource and
              *is_unique* is ``True``.
        '''
        with cls._lock:
            if resource.category not in cls.resources:
                cls.resources[resource.category] = {}
            if resource.name not in cls.resources[resource.category]:
                cls.resources[resource.category][resource.name] = []
            cls.resources[resource.category][resource.name] += [resource]
            instances = len(cls.resources[resource.category][resource.name])
        if resource.is_unique and instances > 1:
            raise ValueError('{} is not unique resource'.format(resource.name))

    @classmethod
    def get_resources(cls, category, name):
        '''Get resources specified by category and name.

        Args:
            * category (:obj:`str`): Is the category of the resource.
            * name (:obj:`str`): Is the name of the resource.

        Returns:
            * :obj:`list` of :obj:`Resource`: A list containing all resources
              that match *category* and *name* constraints.
        '''
        try:
            return cls.resources[category][name]
        except KeyError:
            return []

    @classmethod
    def filter_resources(cls, category=None, owner=None, name=None):
        '''Get resources filtered by category, owner and name.

        Args:
            * category (:obj:`str`, *optional*): Is the category of the
              resource. Default is ``None`` which means to match any category.
            * owner (:obj:`object`, *optional*): Object which is the owner of
              the resource. Default is ``None`` which means to match any owner.
            * name (:obj:`str`, *optional*): Is the name of the resource.
              Default is ``None`` which means to match any name.

        Returns:
            * :obj:`list` of :obj:`Resource`: A list containing all resources
              that match *category*, *owner* and *name* constraints.
        '''
        retval = []
        for instance, info in cls._build_filter_map().items():
            i_category, i_name, i_owner = info
            if category is not None:
                if i_category != category:
                    continue
            if owner is not None:
                if i_owner != owner:
                    continue
            if name is not None:
                if i_name != name:
                    continue
            retval += [instance]
        return retval

    @classmethod
    def remove_resource(cls, resource):
        '''Remove a resource from resource management.

        In the process of removal the resource releaser method will be called
        if it was specified in the constructor initialization.

        Args:
            * resource (:obj:`Resource`): A resource to be removed from
              resource management.

        Raises:
            * LookupError: When a resource is not registered to resource
              management.
        '''
        with cls._lock:
            resources = cls.get_resources(resource.category, resource.name)
            for idx, resource in enumerate(resources):
                if resource is resource:
                    if resource._releaser is not None:
                        resource._releaser()
                    del cls.resources[resource.category][resource.name][idx]
                    if not cls.resources[resource.category][resource.name]:
                        del cls.resources[resource.category][resource.name]
                    if not cls.resources[resource.category]:
                        del cls.resources[resource.category]
                    return
        raise LookupError('{} is not registered'.format(resource.name))

    @classmethod
    def remove_all_resources(cls, owner):
        '''Remove all resources associated with an owner.

        Args:
            * owner (:obj:`object`): Object which is the owner of the resource.
        '''
        for resource in cls.filter_resources(owner=owner):
            cls.remove_resource(resource)


class StateMachine(Resource):
    '''This class implements a state machine.

    This class is a controller class of state machine.

    State machine instance is the entry point of a state machine which is used
    to receive events and do the transitions between states. Each state machine
    must declare it's own subclass of :class:`StateMachine`. The simplest way
    is to just declare an empty class which inherits the class
    :class:`StateMachine`::

        from pyeds import fsm

        class MyFsm(fsm.StateMachine):
            pass

    Args:
        * queue_size (:obj:`int`, *optional*): Is an integer specifying what is
          the maximum event queue size. If this argument is -1 then unlimited
          queue size will be used. Default is 64.
        * name (:obj:`str`, *optional*): Is a string specifying the state
          machine name. The default value is ``None`` which means that the
          class name is taken as the state machine name.

    Attributes:
        * init_state_cls (:obj:`State`, *optional*): Initial state class. If
          *init_state_cls* attribute is set then that state will be initial
          state. Default is ``None`` which means the first declared
          (registered) state is initial state.
        * logger (:obj:`Logger`, *optional*): Logger instance used by the state
          machine. Default is to use ``logging.getLogger(None)``.
        * should_autostart (:obj:`bool`, *optional*): Should machine start at
          initialization? Default is ``True``.

    Raises:
        * AttributeError: If this state machine has no states declared with
          :obj:`DeclareState` decorator.
        * ValueError: If init_state_cls is not a declared state of this state
          machine.

    Note:
        The subclass must call the constructor method.
    '''
    init_state_cls = None
    logger = logging.getLogger(None)
    should_autostart = True

    def __init__(self, queue_size=64, name=None):
        # Ensure that state machine has state classes
        if not hasattr(self, 'state_clss'):
            raise AttributeError('{} has no states'.format(self.name))
        # If an explicit initialization state is given then ensure that
        # init_state is a registered state
        if self.init_state_cls is not None:
            if self.init_state_cls not in self.state_clss:
                raise ValueError(
                    'init_state_cls argument \'{!r}\' '
                    'is not a registered state'.format(self.init_state_cls))
        super().__init__(
            category='state machine',
            name=name,
            is_unique=True,
            releaser=self.on_terminate)
        self._queue = coordinator.provider.Queue(queue_size)
        self._pm = _PathManager()
        self._thread = coordinator.provider.Task(self.event_loop, self.name)
        self._thread.sm = self
        if self.init_state_cls is None:
            self.init_state_cls = self.state_clss[0]
        if self.should_autostart:
            self._thread.start()

    def _setup_fsm(self):
        class Signal(Event):
            def execute(self, handler):
                return handler()
        # This will make the owner of these signals this state machine
        self._ENTRY = Signal('entry')
        self._EXIT = Signal('exit')
        self._INIT = Signal('init')
        for state_cls in self.state_clss:
            self._pm.add_cls(state_cls, state_cls.super_state)
        self._pm.build()
        # Set the state to initial state
        self._state = self._pm.instance_of(self.init_state_cls)
        # Add itself to Resource
        Resource.add_resource(self)
        # Log info about state machine
        self.logger.debug('{} registered states {}'.format(
            self.name, self.states))
        self.logger.debug('{} hierarchy: {} level(s) deep, {} state(s)'.format(
            self.name, self._pm.depth, len(self._pm.states())))
        self.logger.info('{} {} is initial state'.format(
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
        new_state = self._pm.instance_of(new_state_cls)
        return (new_state, super_state)

    def _dispatch(self, event):
        self.logger.debug('{} {}({})'.format(
            self.name, self._state.name, event.name))
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
            self.logger.debug('{} {} -> {}'.format(
                self.name, current_state.name, new_state.name))
            self._pm.generate(current_state, new_state)
            # Exit the path
            for exit_state in self._pm.exit_iterator():
                self._exec_state(exit_state, self._EXIT)
                Resource.remove_all_resources(exit_state)
            # Enter the path
            for enter_state in self._pm.enter_iterator():
                self._exec_state(enter_state, self._ENTRY)
            self._pm.reset()
            current_state = new_state
            new_state, _ = self._exec_state(current_state, self._INIT)
            self._state = current_state

    @property
    def depth(self):
        ''':obj:`int`: The depth of state machine states hierarchy
        '''
        return self._pm.depth

    @property
    def states(self):
        ''':obj:`list` of :obj:`str`: List of names of registered states
        '''
        return self._pm.states()

    @property
    def state(self):
        ''':obj:`State`: Instance of current state
        '''
        return self._state

    def instance_of(self, state_cls):
        '''Get the instance of state class

        Args:
            * state_cls (:class:`State`): State class

        Returns:
            * :obj:`State`: Instance of *state_cls* class.

        Raises:
            * LookupError: If *state_cls* is not a registered state of the
              state machine.
        '''
        try:
            return self._pm.instance_of(state_cls)
        except KeyError:
            raise LookupError(
                'State \'{!r}\' is not a registered state'.format(state_cls))

    def event_loop(self):
        '''Event loop

        This method executes the event looper.

        Raises:
            * LookupError: If a state returns invalid transition class.
        '''
        # Initialize the states and build hierarchy
        self._setup_fsm()
        self._dispatch(self._INIT)
        self.on_start()
        # Execute event loop
        while True:
            event = self._queue.get()
            # Check should we exit
            if event is None:
                self._queue.task_done()
                Resource.remove_all_resources(self)
                Resource.remove_resource(self)
                self.logger.info('{} terminated'.format(self.name))
                return
            self._dispatch(event)
            try:
                Resource.remove_resource(event)
            except LookupError:
                pass
            self._queue.task_done()

    def send(self, event, block=True, timeout=None):
        '''Send an event to the state machine.

        The event is put to state machine queue and then the event_loop()
        method will process the queued event.

        Args:
            * event (:obj:`Event`): Event object to send to this machine.
            * block (:obj:`bool`, *optional*): If event queue is full should
              this method block? Default is ``True`` which means the method
              will block.
            * timeout (:obj:`float`, *optional*): If *block* is ``True`` then
              wait up to *timeout* seconds. This argument is disregarded when
              *block* is ``False``. Default is ``None`` which means to block
              indefinitely.

        Raises:
            * BufferError: Raised when queue buffer is full and timeout has
              passed (if given), otherwise, it raises it immediately when full.
        '''
        Resource.add_resource(event)
        self._queue.put(event, block, timeout)

    def wait(self, timeout=None):
        '''Wait until the state machine terminates.

        Args:
            * timeout (:obj:`float`, *optional*): How many seconds to wait for
              termination. The default is ``None`` which means to wait
              indefinitely.
        '''
        self._thread.join(timeout)

    def do_start(self):
        '''Explicitly start the state machine

        If attribute *should_autostart* is ``False`` then after the creating
        the class the state machine will start executing only after calling
        this function.
        '''
        self._thread.start()

    def do_terminate(self, timeout=None):
        '''Pend termination of the state machine.

        Put a special event into to queue buffer which will signal the state
        machine to terminate.

        Args:
            * timeout (:obj:`float`, *optional*): When specified it will wait
              up to *timeout* seconds. Default is ``None`` which means to block
              indefinitely.

        Raises:
            * BufferError: Raised when queue buffer is full and timeout has
              passed (if given), otherwise, it raises it immediately when full.

        Note:
            After calling this method the state machine may still run. Use
            ``wait()`` to wait for state machine until it terminates.
        '''
        self._queue.put(None, timeout=timeout)

    def on_start(self):
        '''Gets called by state machine just before the machine starts'''
        pass

    def on_terminate(self):
        '''Gets called by state machine just before the termination'''
        pass

    def on_exception(self, exc, state, event, msg):
        '''Gets called when un-handled state exception has occurred

        Args:
            * exc (:obj:`Exception`): Holds state exception.
            * state (:obj:`State`): State instance where the exception
              originates.
            * event (:obj:`Event`): Event which was processed in the state.
            * msg (:obj:`str`): Message associated with the exception.
        '''
        raise RuntimeError(
            exc,
            msg,
            self.__class__.__module__,
            self.name,
            state.name,
            event.name)


class State(Resource):
    '''This class implements a state.

    Each state is represented by a class derived from this class. Every method
    in state class may handle one particular event. To declare the state, a
    class must be decorated with :obj:`DeclareState` decorator which requires
    a subclass of :obj:`StateMachine` as an argument. This decorator binds the
    state class to the specific FSM class. Also, the new state class must be a
    subclass of :obj:`State` class::

        @fsm.DeclareState(MyFsm)
        class MyState(fsm.State):
            pass

    Event handler has the following signature::

        def on_event_name(self, event):

    Where *on_event_name* corresponds to event name. Event handler gets the
    event (:obj:`Event`) which has caused this call.

    Transitions are started by returning target state class in an event
    handler::

        def on_some_event(self, event):
            do_some_stuff()
            return SomeOtherState # Note: return a class object,
                                  # not instance object

    Objects created in the current state may be local or non-local to the
    state. When an object is local it will exist only while the state machine
    is in the current state. When state machine transitions to any state (
    including the current one) all object local to current state will be
    deleted.

    Attributes:
        * super_state (:class:`State`): The super state of this state. By
          default is set to ``None`` which means that this state has no super
          state.
    '''
    super_state = None

    def __init__(self):
        # Setup resource instance
        super().__init__(category='state', owner=current())
        Resource.add_resource(self)

    @property
    def sm(self):
        ''':obj:`StateMachine`: The state machine who is owner of this state.
        '''
        return self.owner

    @property
    def logger(self):
        ''':obj:`Logger`: Logger of the state machine.
        '''
        return self.sm.logger

    def set_local(self, resource):
        '''Set a resource as local to this state.

        Local object exist only while the state machine is in current state.

        Args:
            * resource (:obj:`Resource`): Resource which will be local to this
              state.
        '''
        resource.owner = self

    def on_entry(self):
        '''State "entry" event handler

        This handler gets called by dispatcher when state machine enters this
        state.

        Note:
            This event handler does not have event argument.
        '''
        pass

    def on_exit(self):
        '''State "exit" event handler

        This handler gets called by dispatcher when state machine exits this
        state.

        Note:
            This event handler does not have event argument.
        '''
        pass

    def on_init(self):
        '''State "initialization" event handler

        This handler gets called by dispatcher when state machine enters this
        state and wants to initialize it.

        Note:
            This event handler does not have event argument.
        '''
        pass

    def on_unhandled_event(self, event):
        '''Un-handled event handler

        This handler gets executed in case the state does not handle the event.
        By default this handler only logs the un-handled event.

        Args:
            * event (:obj:`Event`): Event which is not handled.
        '''
        self.logger.debug('{} {}({}) wasn\'t handled'.format(
                self.sm.name, self.name, event.name))


class DeclareState(object):
    '''This is a decorator which declares a state for a state machine.

    Use this decorator class to declare states for a state machine.

    Args:
        * state_machine_cls (subclass of :class:`StateMachine`): A state
          machine for which the state is declared for.

    Raises:
        * AssertError:
            - When *state_machine_cls* is class :class:`StateMachine`
            - When *state_machine_cls* is not a subclass of
              :class:`StateMachine`
            - When decorated class is class :class:`State`
            - When decorated class is not a subclass of :class:`State`
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
        assert state_cls is not State, \
            'Make specific state class from {}'.format(State.__name__)
        assert issubclass(state_cls, State), \
            'The class {} is not subclass of {} class'.format(
                state_cls.__name__, State.__name__)
        try:
            self.state_machine_cls.state_clss += [state_cls]
        except AttributeError:
            # Add new attribute if it doesn't exist
            self.state_machine_cls.state_clss = [state_cls]
        return state_cls


class Event(lib.Immutable, Resource):
    '''Event

    An event is the only means of communication between state machines. Each
    event carries name. Based on the event name a handler will be called from
    current state class which has the same name.

    When an event is created and sent to a state machine it's name is used to
    decide which method in current state instance should be invoked. The state
    machine takes the name of the event, it prepends text ``on_`` to the name
    string and then it looks up to event handler method.

    Example:
        If an event named ``toggle`` is created and sent to a state machine,
        the target state machine will lookup for a method named ``on_toggle``
        in the current state instance.

    Since the event name directly impacts which state instance method will be
    called the name of events must follow the Python identifier naming rules.

    The associated parameters with an event are:
        * Name of the event: as given to constructor or implicitly defined
          using class name.
        * Owner of event: state machine which generated this event or ``None``
          if the event was generated outside a state machine context.

    Args:
        * name (:obj:`str`, *optional*): Name of the event. When not given the
          event will take the name of the derived Event class and convert it to
          appropriate format.
    '''
    _ename_regex = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')

    def __init__(self, name=None):
        name = name or self.format_name(self.__class__.__name__)
        super().__init__(category='event', name=name, owner=current())

    def format_name(self, name):
        '''Resource, format the name.

        Used by resource instance to format the name of Event. It will convert
        Event names from `CamelCase` to `camel_case` format.

        Example::

            class MySpecialEvent(fsm.Event):
                pass

            new_event = MySpecialEvent() # This event is implicitly
                                         # called 'my_special_event'

        Args:
            * name (:obj:`str`): Unformatted name of the Event.

        Returns:
            * :obj:`str`: Formatted name of the Event.
        '''
        return self._ename_regex.sub(r'_\1', name).lower()

    def execute(self, handler):
        '''Event handler executor

        This method is called by state machine dispatcher to execute event
        handler in a state.

        By default it just delivers itself to event handler::

            return handler(self)
        '''
        return handler(self)

    def send(self, state_machine=None):
        '''Send this event to state machine.

        Args:
            * state_machine (:obj:`None`): Send the event to the state machine
              who created this event. This argument is invalid in case when the
              owner of event is not a state machine.
            * state_machine (:obj:`StateMachine`): State machine object.
            * state_machine (:obj:`str`): State machine name.
            * state_machine (:obj:`Channel`): Event channel.

        Raises:
            * ValueError: When *state_machine* argument is not supported.
            * LookupError: When *state_machine* argument is :obj:`str` and
              there is no state machine with that name.
        '''
        if state_machine is None:
            self.owner.send(self)
        elif isinstance(state_machine, StateMachine):
            state_machine.send(self)
        elif isinstance(state_machine, str):
            state_machine = Resource.get_resources(
                'state_machine', state_machine)
            state_machine.send(self)
        else:
            raise ValueError('state_machine arg {!r} is invalid'.format(
                    state_machine))


class After(Resource):
    '''Send an event to current state machine after a specified number of
    seconds.

    This is a timer object that will send the specified event after period of
    elapsed time. The timer will start counting at the time of creation.

    Args:
        * every (:obj:`float`): Time period in seconds.
        * event_name (:obj:`str`): Name of event.

    Example:
        In order to send the event called 'blink' to itself after 10 seconds
        do::

            fsm.After(10.0, 'blink')
    '''
    def __init__(self, after, event_name):
        name = '{}.{}.{}'.format(self.__class__.__name__, event_name, after)
        # Setup resource instance
        super().__init__(
            category='timer',
            name=name,
            owner=current(),
            releaser=self.cancel)
        # Save arguments
        self.timeo = after
        self.event_name = event_name
        self.start()

    def handler(self):
        '''Timeout handler method.
        '''
        event = Event(self.event_name)
        event.timer = self
        self.owner.send(event)

    def start(self):
        '''Start the timer.

        Use this method to start a cancelled timer or a timer that has been
        expired.
        '''
        self._timer = coordinator.provider.Timer(self.timeo, self.handler)
        self._timer.start()

    def cancel(self):
        '''Cancel a running timer
        '''
        self._timer.cancel()


class Every(After):
    '''Send an event to current state machine every time a specified number of
    seconds passes.

    This is a timer object that will send the specified event every period of
    elapsed time. The timer will start counting at the time of creation.

    Args:
        * every (:obj:`float`): Time period in seconds.
        * event_name (:obj:`str`): Name of event.

    Example:
        In order to send the event called 'blink' to itself every 10 seconds
        do::

            fsm.Every(10.0, 'blink')
    '''
    def __init__(self, every, event_name):
        super().__init__(every, event_name)

    def handler(self):
        '''Timeout handler method.
        '''
        super().handler()
        self.start()


def current():
    '''Returns the currently executing state machine.

    Returns:
        * :obj:`StateMachine`: Which state machine is currently executing.
        * :obj:`None`: When this function is called outside of a state machine
          code context.
    '''
    current = coordinator.provider.current()
    try:
        return current.sm
    except AttributeError:
        pass
