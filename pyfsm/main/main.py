'''
Created on Jul 7, 2017

@author: nenad
'''

from pyfsm.fsm import NStateMachine, NState, NStateDeclare, NEvent
from logging import basicConfig, DEBUG, getLogger
from time import sleep

basicConfig(level=DEBUG)

class MyStateMachine(NStateMachine):
    logger = getLogger('app')

@NStateDeclare(MyStateMachine)
class StateInitial(NState):
    def NENTRY(self, event):
        pass
        
    def NEXIT(self, event):
        pass
        
    def NINIT(self, event):
        pass
        
        return StateIdle

@NStateDeclare(MyStateMachine)
class StateIdle(NState):
    def on(self, event):
        return StateOn
    
    def off(self, event):
        return StateOff
    
@NStateDeclare(MyStateMachine)
class StateOn(NState):
    def on(self, event):
        self.logger.info('ON')
        return StateOn
    
    def off(self, event):
        return StateOff
    
@NStateDeclare(MyStateMachine)
class StateOff(NState):
    def on(self, event):
        self.logger.info('OFF')
        return StateOn
    
    def off(self, event):
        return StateOff

def main():
    my_state_machine = MyStateMachine()
    
    while True:
        my_state_machine.put(NEvent('on'))
        sleep(0.5)
        my_state_machine.put(NEvent('off'))
        sleep(0.5)
        

if __name__ == '__main__':
    main()