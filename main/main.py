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
    def on_entry(self, event):
        pass
        
    def on_exit(self, event):
        pass
        
    def on_init(self, event):
        return StateIdle

@fsm.DeclareState(MyStateMachine)
class StateIdle(fsm.State):
    def on_entry(self, event):    
        fsm.After(3, fsm.Event('start'))
        fsm.After(5, fsm.Event('dummy!!!'), is_local=True)
        fsm.Every(2, fsm.Event('eveeer'))
        
    def on_start(self, event):
        return StateOn
    
@fsm.DeclareState(MyStateMachine)
class StateOn(fsm.State):
    def on_entry(self, event):
        self.logger.info('ON')
        
    def on_on(self, event):
        return StateOn
    
    def on_off(self, event):
        return StateOff
    
@fsm.DeclareState(MyStateMachine)
class StateOff(fsm.State):
    def on_entry(self, event):
        self.logger.info('OFF')
        
    def on_on(self, event):
        return StateOn
    
    def on_off(self, event):
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