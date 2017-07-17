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

:: 
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

::
    @fsm.DeclareState(MyFsm)
    class MyState(fsm.State):
        pass
        
Declare a new class per state.
    
Instantiating the FSM
^^^^^^^^^^^^^^^^^^^^^

To instantiate the FSM class do the following:

::
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

The first step is to declare a class which represent custom FSM.

::
    from pyeds import fsm
    
    class BlinkyFsm(fsm.StateMachine):
        pass

The second step is to start writing the states of new state machine:

::
    @fsm.DeclareState(BlinkyFsm)
    class Initialization(fsm.State):
        def NINIT(self, event):
            fsm.Every(0.5, fsm.Event('blink')
            return StateOn
            
    @fsm.DeclareState(BlinkFsm)
    class StateOn(fsm.State):
        def NENTRY(self, event):
            print('on')
            
        def blink(self, event):
            return StateOff
            
    @fsm.DeclareState(BlinkFsm)
    class StateOff(fsm.State):
        def NENTRY(self, event):
            print('off')
                
        def blink(self, event):
            return StateOn

The final step is to instantiate the FSM class defined in the first step.

::
    blinky_fsm = BlinkyFsm()

After creation the FSM is automatically put into a running state.

Source
------

Source is available at github
:: _GitHub: https:
