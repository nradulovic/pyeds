# pyeds
Python Event Driven System

# Introduction
This package provides an easy to use system which provides boiler plate
code to write finite state machines (FSM).

# How to use it
In other to use the package some minimal initialization is needed.

The steps to create and use a FSM are the following:

  1. Import the package
  2. Declare a FSM class
  3. Declare all states classes
  4. Instantiate FSM class
  
## Blinky example
The following is an example of FSM which is called Blinky. The FSM will 
print 'on' text and 'off' text on console with 0.5 seconds of delay 
between the messages. The FSM has 2 states:

  1. State On
  2. State Off
 
    *----+
         |
     On  v                Off
    +----+----+  blink   +---------+
    |         +--------->+         |
    |         |          |         |
    |         +<---------+         |
    +---------+  blink   +---------+


First step is to import the package:

    from pyeds import fsm
    
Second step is to declare a class which represent your own FSM.

    class BlinkyFsm(fsm.StateMachine):
        pass
        
Third step is to start writting the states of your state machine:

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
            
Fourth and final step is to instantiate the FSM class defined in 
the second step.

    blinky_fsm = BlinkyFsm()
    
After creation the FSM is automatically put into a running state.
