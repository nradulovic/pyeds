.. image:: https://badge.waffle.io/nradulovic/pyeds.svg?columns=all
    :target: https://waffle.io/nradulovic/pyeds
    :alt: 'Waffle.io - Columns and their card count' 
.. image:: https://badge.fury.io/py/pyeds.svg
    :target: https://badge.fury.io/py/pyeds
.. image:: https://travis-ci.org/nradulovic/pyeds.svg?branch=master
    :target: https://travis-ci.org/nradulovic/pyeds
.. image:: https://coveralls.io/repos/github/nradulovic/pyeds/badge.svg?branch=master
    :target: https://coveralls.io/github/nradulovic/pyeds?branch=master
.. image:: https://api.codacy.com/project/badge/Grade/baa313c466c64d5d82a24e3d32a9f3a1
    :target: https://www.codacy.com/app/nradulovic/pyeds?utm_source=github.com&utm_medium=referral&utm_content=nradulovic/pyeds&utm_campaign=badger
    :alt: Codacy Badge


**Python Event Driven System**

.. contents:: Table of contents
   :local:

Introduction
============

This package provides a means to efficiently write finite state machines (FSM) 
by hand. The focus was to make the API as simple as possible since no GUI 
tools are included to define a FSM.

Installation
============

Using PIP
---------

PyEDS can be installed using the standard Python tool ``pip`` with

.. code:: console

    pip install pyeds

Installing from source
----------------------

The easiest way to install PyEDS from source is to use ``setup.py`` script 
which uses setuptools. For complete documentation about this script please
refer to setuptools manual.

To install from source issue the following command:

.. code:: console

    python setup.py install
    
Code documentation
------------------

Code documentation is bundled together with the source. The documentation
scripts use Sphinx to generate documents. 

To generate HTML documentation:

.. code:: console

    cd doc
    make html
    
This will create HTML documents in ``doc/_build/html`` directory.

The documentation can be accessed via Python interpreter, too.

.. code:: python

    >>> import pyeds
    >>> help(pyeds.fsm)

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
            fsm.Every(0.5, 'blink')
            return StateOn
            
            
    @fsm.DeclareState(BlinkyFsm)
    class StateOn(fsm.State):
        def on_entry(self):
            print('on')
            
        def on_blink(self, event):
            return StateOff
            
            
    @fsm.DeclareState(BlinkyFsm)
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
machines.

An event can have associated parameters, allowing the event to convey not only 
the occurrence but also quantitative information about the occurrence. 

An event is the only means of communication between state machines. Each event 
carries name. Based on the event name a handler will be called from current 
state class which has the same name.
    
An event in PyEDS is instanced using class ``Event``. 

The associated parameters with an event are:

- Name of the event: this is a string containing event name.
- Owner of event: specifies which state machine has generated this event.
 
Generate an event
-----------------

To generate a new event just instantiate ``Event`` class with event name as
parameter:

.. code:: python

    new_event = fsm.Event('my_special_event')

Alternative way is to first declare a new event class and instantiate this
derived class:

.. code:: python

    class MySpecialEvent(fsm.Event):
        pass
        
    new_event = MySpecialEvent() # This event is implicitly
                                 # called 'my_special_event'

In this case base ``Event`` class will implicitly take the name of the class as 
own name. This can be overridden by calling the super constructor:

.. code:: python

    # This event has the exact same name as the above one
    class DerivedEvent(fsm.Event):
        def __init__(self):
            super().__init__('my_special_event')

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
the name of events must follow the Python identifier naming rules; please refer
to https://docs.python.org/3.3/reference/lexical_analysis.html#identifiers for
more details.

.. code:: python

    ok_event = fsm.Event('some_event_with_long_name')
    bad_event = fsm.Event('you cannot use spaces, @, $ and % here')

Timers
======

Timers are used to generate time events:

- After: Means an event will be generated after elapsed time.
- Every: Means an event will be generated every period of time.
  
To generate the events use ``After`` and ``Every`` objects:

.. code:: python

    @fsm.DeclareState(BlinkyFsm)
    class Initialization(fsm.State):
        def on_init(self):
            self.blinking = fsm.Every(1.0, 'blink')
            return StateOn
    
    
This line will generate an event named `blink` every 1.0 seconds. To stop the  
timer use:

.. code:: python

    @fsm.DeclareState(BlinkyFsm)
        class StateOn(fsm.State):
            def on_entry(self):
                print('on')
                self.blinking.cancel()
    
Second approach to cancel a running timer is by using event ``timer`` attribute.
When a timer generates an event it will automatically create event attribute
called ``timer``. With this attribute you can also access the originating timer
through event. To stop the timer through an event see the example below:

.. code:: python

    @fsm.DeclareState(BlinkyFsm)
    class StateOn(fsm.State):
        def on_blink(self, event):
            event.timer.cancel() # Stop the originating timer
            return StateOff
            
State
=====

A state is a description of the status of a system that is waiting to execute 
a transition.

State machine
=============

A finite-state machine (FSM) is a mathematical model of computation. It is an 
abstract machine that can be in exactly one of a finite number of states at any
given time. The FSM can change from one state to another in response to some
external events; the change from one state to another is called a state
transition. An FSM is defined by a list of its states, its initial state, and
the conditions for each transition.

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

Other links
===========

The following is a list of links to tools used by the project:

- *Sphinx* (used to build documentation): http://www.sphinx-doc.org/en/stable/
- *setuptools* (used for installing from source): 
  https://setuptools.readthedocs.io/en/latest/
