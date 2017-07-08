'''
Created on Jul 7, 2017

@author: nenad
'''

from pyeds import fsm
from logging import basicConfig, DEBUG, getLogger
from time import sleep

basicConfig(level=DEBUG)

class MyStateMachine(fsm.StateMachine):
    logger = getLogger('app')

@fsm.DeclareState(MyStateMachine)
class StateInitial(fsm.State):
    def NENTRY(self, event):
        pass
        
    def NEXIT(self, event):
        pass
        
    def NINIT(self, event):
        return StateIdle

@fsm.DeclareState(MyStateMachine)
class StateIdle(fsm.State):
    def NENTRY(self, event):    
        fsm.After(3, fsm.Event('start'))
        fsm.After(5, fsm.Event('dummy!!!'), is_local=True)
        fsm.Every(2, fsm.Event('eveeer'))
        
    def start(self, event):
        return StateOn
    
@fsm.DeclareState(MyStateMachine)
class StateOn(fsm.State):
    def NENTRY(self, event):
        self.logger.info('ON')
        
    def on(self, event):
        return StateOn
    
    def off(self, event):
        return StateOff
    
@fsm.DeclareState(MyStateMachine)
class StateOff(fsm.State):
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
            my_state_machine.put(fsm.Event('on'))
            sleep(0.5)
            my_state_machine.put(fsm.Event('off'))
            sleep(0.5)
    except KeyboardInterrupt:
        my_state_machine.release()
        

if __name__ == '__main__':
    main()