**Python Event Driven System**

.. contents:: Table of contents
   :backlinks: top
   :local:

Introduction
============

This package provides a system allows to efficiently write finite state machines 
(FSM) by hand. The focus was to make the API as simplest as possible since no 
GUI tools are included to define a FSM.

Installation
============

PyEDS can be installed using the standard Python tool ``pip`` with

.. code-block:: console

    pip install pyeds

How to use it
=============

The basic routine to create a state machine is the following:
 1) Declare a FSM class 
 2) Declare all state classes
 3) Instantiate FSM class
 
Declaring a FSM class
---------------------

FSM class is the entry point of a FSM which is used to receive events (see 
below) and do the transitions between states. Each FSM must declare it's own 
class which is a subclass of ``StateMachine``. The simplest way is to just
declare an empty class which inherits the class ``StateMachine``:

.. code:: python

    from pyeds import fsm
    
    class MyFsm(fsm.StateMachine):
        pass
   
Declaring a state class
-----------------------

Each state is represented by different class. Every method in that class may 
handle one particular event. To declare the state, a class must be decorated 
with ``DeclareState`` decorator which require state machine as an argument. 
This decorator binds the state class to the specific FSM class. Also, the new 
state class must be a subclass of ``State`` class:

.. code:: python

    @fsm.DeclareState(MyFsm)
    class MyState(fsm.State):
        pass
        
Declare a new class per state.
    
Instantiating the FSM
---------------------

To instantiate the FSM class do the following:

.. code:: python

    my_fsm = MyFsm()
    
After object initialization the FSM is put into running state.

Blinky example
==============

The following is an example of FSM which is called Blinky. The FSM will print 
'on' text and 'off' text on console with 0.5 seconds of delay between the 
messages. 

The Blinky FSM has 2 states:
 - State On
 - State Off
 
::

    o----+
         |
     On  v                Off
    +----+----+  blink   +---------+
    |         +--------->+         |
    |         |          |         |
    |         +<---------+         |
    +---------+  blink   +---------+


The event ``blink`` is used to trigger transitions between the states.

.. code:: python

    from pyeds import fsm


    # The first step is to declare a class which represent custom FSM.
        
    class BlinkyFsm(fsm.StateMachine):
        pass


    # The second step is to start writing the states of new state machine:

    @fsm.DeclareState(BlinkyFsm)
    class Initialization(fsm.State):
        def on_init(self):
            fsm.Every(0.5, fsm.Event('blink')
            return StateOn
            
            
    @fsm.DeclareState(BlinkFsm)
    class StateOn(fsm.State):
        def on_entry(self):
            print('on')
            
        def on_blink(self, event):
            return StateOff
            
            
    @fsm.DeclareState(BlinkFsm)
    class StateOff(fsm.State):
        def on_entry(self):
            print('off')
                
        def on_blink(self, event):
            return StateOn


    # The final step is to instantiate the FSM class defined in the first step.

    blinky_fsm = BlinkyFsm()

After creation the FSM is automatically put into a running state.

Event
=====

An event is a notable occurrence at a particular point in time. Events can, but
do not necessarily, cause state transitions from one state to another in state 
machines

An event can have associated parameters, allowing the event to convey not only 
the occurrence but also quantitative information about the occurrence. 

An event in PyEDS is instanced using class ``Event``. 

The associated parameters with an event are:
 - name of the event
 - producer of event
 
Generate an event
-----------------

To generate a new event just instantiate ``Event`` class with event name as
parameter:

.. code:: python

    new_event = fsm.Event('my_special_event')

Alternative way is to first declare a new event class and instantiate this
derive class:

.. code:: python

    class MySpecialEvent(fsm.Event):
        pass
        
    new_event = MySpecialEvent() # This event is implicitly called 'my_special_event'

In this case base ``Event`` class will implicitly take the name of the class as 
own name. This can be overriden by calling the super constructor:

.. code:: python

    # This event has the exact same name as the above one
    class MySecondEvent(fsm.Event):
        def __init__(self):
            super().__init__('my_special_event')

    # Another way of creating event with same name as above events
    class MyThirdEvent(fsm.Event):
        name = 'my_special_event'

Event class attributes and methods
----------------------------------

Attributes:
 - ``self.name`` - this is a string containing event name
 - ``self.producer`` - specifies which state machine has generated this event.
 
Methods:
 - ``release(self)`` - this method is called by state machine when it has 
   finished the processing of the event
 - ``execute(self, handler)`` - this method is called by state machine and it 
   is used to modify how an event handler is called.

Rules about event naming
------------------------

When an event is created and sent to a state machine it's name is used to decide
which method in current state instance should be invoked. The state machine 
takes the name of the event, it prepends text ``on_`` to the name string and 
then it looks up to event handler method.

Example: If an event named ``toggle`` is created and sent to a state machine, 
the target state machine will lookup for a method named ``on_toggle`` in the 
current state instance. 

Since the event name directly impacts which state instance method will be called
the name of events must follow the Python identifier naming rules. 

A Python identifier starts with a letter A to Z or a to z or an underscore (_) 
followed by zero or more letters, underscores and digits (0 to 9). Python does 
not allow punctuation characters such as @, $, and % within identifiers. 

.. code:: python

    ok_event = fsm.Event('some_event_with_long_name')
    bad_event = fsm.Event('you cannot use spaces, @, $ and % here')

State
=====

A state is a description of the status of a system that is waiting to execute 
a transition.

State attributes and methods
----------------------------

Attributes:
 - ``self.name`` - this is a string containing state name
 - ``self.producer`` - specifies which state machine has this state
 - ``self.sm`` - the same as ``self.producer`` but shorter
 - ``self.logger`` - this is the logger which is used by state machine
 - ``self.rm`` - this is ResourceManager for this state
 - ``super_state`` - this is a class attribute that specifies super 
   state class
 
Methods:
 - ``release(self)`` - this method is called by state machine just before
   state machine termination
 - ``on_entry(self)`` - this method is called by state machine when it has
   entered the state
 - ``on_exit(self)`` - this method is called by state machine when it has
   exited the state
 - ``on_init(self)`` - this method is called by state machine when it has
   entered the state and now needs to initialize the state
 - ``on_unhandled_event`` - this method is called by state machine when
   no event handlers where found for this state
   
State machine
=============

State machine attributes and methods
------------------------------------

Attributes:
 - ``self.name`` - this is a string containing Sstate machine name
 - ``self.logger`` - this is the logger which is used by state machine
 - ``self.rm`` - this is ResourceManager for this state machine
 - ``self.state`` - current state of this machine
 
Methods:
 - ``run(self)`` - this is state machine dispatch method
 - ``put(self, event)`` - this method puts an event to state machine wait
   queue
 - ``terminate(self)`` - pend termination of the state machine. After 
   exiting this method the state machine may still run. Use ``self.wait``
   to wait for FSM termination
 - ``wait(self)`` - wait for FSM to terminate
 - ``instance_of`` - get the instance of a state class
 - ``on_terminate`` - gets called by state machine just before termination
 - ``on_exception`` - gets called when unhandled exception has occured
 
State transition
================

Switching from one state to another is called state transition. A transition is 
a set of actions to be executed when a condition is fulfilled or when an event 
is received.

Transitions are started by returning target state class in an event handler.

.. code:: python
 
    def on_some_event(self, event):
        do_some_stuff()
        return SomeOtherState # Note: return a class object, not instance object

Hierarchical Finite State Machines (HFSM)
=========================================

Please, refer to Wikipedia article for further explanation: 
 - https://en.wikipedia.org/wiki/UML_state_machine#Hierarchically_nested_states 

Source
======

Source is available at github:
 - https://github.com/nradulovic/pyeds
