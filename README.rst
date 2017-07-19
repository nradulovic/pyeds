Python Event Driven System
==========================

Introduction
------------

This package provides a system allows to efficiently write finite state machines 
(FSM) by hand. The focus was to make the API as simplest as possible since no 
GUI tools are included to define a FSM.

Installation
------------

PyEDS can be installed using the standard Python tool ``pip`` with

.. code-block:: bash

    pip install pyeds
    

How to use it
-------------

The basic routine to create a state machine is the following:

1. Declare a FSM class 
2. Declare all state classes
3. Instantiate FSM class
 
Declaring a FSM class
^^^^^^^^^^^^^^^^^^^^^

FSM class is the entry point of a FSM which is used to receive events (see 
below) and do the transitions between states. Each FSM must declare it's own 
class which is a subclass of ``StateMachine``. The simplest way is to just
declare a empty class which inherits the ``StateMacine``:

.. code-block:: python

    from pyeds import fsm
    
    class MyFsm(fsm.StateMachine):
        pass
        
   
Declaring a state class
^^^^^^^^^^^^^^^^^^^^^^^

Each state is represented by different class. Every method in that class may 
handle one particular event. To declare the state, a class must be decorated 
with ``DeclareState`` decorator which state machine as an argument. This 
decorator binds the state class to a specific FSM class. Also, the new class
must be a subclass of ``State`` class:

.. code-block:: python

    @fsm.DeclareState(MyFsm)
    class MyState(fsm.State):
        pass
        
Declare a new class per state.
    
Instantiating the FSM
^^^^^^^^^^^^^^^^^^^^^

To instantiate the FSM class do the following:

.. code-block:: python

    my_fsm = MyFsm()
    
After object initialization the FSM is put into running state.

Blinky example
--------------

The following is an example of FSM which is called Blinky. The FSM will print 
'on' text and 'off' text on console with 0.5 seconds of delay between the 
messages. The FSM has 2 states:

    1. State On
    2. State Off
 
::

    *----+
         |
     On  v                Off
    +----+----+  blink   +---------+
    |         +--------->+         |
    |         |          |         |
    |         +<---------+         |
    +---------+  blink   +---------+


The event ``blink`` is used to trigger transitions between the states.

.. code-block:: python

    from pyeds import fsm


    # The first step is to declare a class which represent custom FSM.
        
    class BlinkyFsm(fsm.StateMachine):
        pass


    # The second step is to start writing the states of new state machine:

    @fsm.DeclareState(BlinkyFsm)
    class Initialization(fsm.State):
        def on_init(self, event):
            fsm.Every(0.5, fsm.Event('blink')
            return StateOn
            
            
    @fsm.DeclareState(BlinkFsm)
    class StateOn(fsm.State):
        def on_entry(self, event):
            print('on')
            
        def on_blink(self, event):
            return StateOff
            
            
    @fsm.DeclareState(BlinkFsm)
    class StateOff(fsm.State):
        def on_entry(self, event):
            print('off')
                
        def on_blink(self, event):
            return StateOn


    # The final step is to instantiate the FSM class defined in the first step.

    blinky_fsm = BlinkyFsm()

After creation the FSM is automatically put into a running state.

Event
-----

An event is a notable occurrence at a particular point in time. Events can, but
do not necessarily, cause state transitions from one state to another in state 
machines

An event can have associated parameters, allowing the event to convey not only 
the occurrence but also quantitative information about the occurrence. 

An event in PyEDS is instanced using class Event. The associated parameters with
an event are:

    1. name of the event
    2. producer of event
 
Generate an event
^^^^^^^^^^^^^^^^^

To generate a new event just instantiate Event class:

.. code-block:: python

    new_event = fsm.Event('event_name')
    
Rules about event naming
^^^^^^^^^^^^^^^^^^^^^^^^

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

.. code-block:: python

    ok_event = fsm.Event('some_event_with_long_name')
    bad_event = fsm.Event('you cannot use spaces, @, $ and % here')
    
Transition
----------

Switching from one state to another is called state transition. A transition is 
a set of actions to be executed when a condition is fulfilled or when an event 
is received.

Source
------

Source is available at github:

:: _GitHub: https://github.com/nradulovic/pyeds
