'''
Created on Jul 7, 2017

@author: nenad
'''

from pyfsm.fsm import NStateMachine, NState, NStateDeclare, NEvent, NTimerAfter, NTimerEvery
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
        return StateIdle

@NStateDeclare(MyStateMachine)
class StateIdle(NState):
    def NENTRY(self, event):    
        NTimerAfter(3, NEvent('start'))
        NTimerAfter(5, NEvent('dummy!!!'), local=True)
        NTimerEvery(2, NEvent('eveeer'))
        
    def start(self, event):
        return StateOn
    
@NStateDeclare(MyStateMachine)
class StateOn(NState):
    def NENTRY(self, event):
        self.logger.info('ON')
        
    def on(self, event):
        return StateOn
    
    def off(self, event):
        return StateOff
    
@NStateDeclare(MyStateMachine)
class StateOff(NState):
    def NENTRY(self, event):
        self.logger.info('OFF')
        
    def on(self, event):
        return StateOn
    
    def off(self, event):
        return StateOff

def main():
    my_state_machine = MyStateMachine()
    
    try:
        while True:
            my_state_machine.put(NEvent('on'))
            sleep(0.5)
            my_state_machine.put(NEvent('off'))
            sleep(0.5)
    except KeyboardInterrupt:
        my_state_machine.release()
        

if __name__ == '__main__':
    main()