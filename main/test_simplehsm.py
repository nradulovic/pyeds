'''
Created on Jul 24, 2017

@author: nenad
'''

import logging

from src.pyeds import fsm


class SimpleHSM(fsm.StateMachine):
    logger = logging.getLogger()

    def __init__(self):
        self.out_seq = []
        super().__init__()
        

class CommonStateClass(fsm.State):
        
    def on_init(self):
        self.sm.out_seq += ['{}:i'.format(self.name)]
        
    def on_entry(self):
        self.sm.out_seq += ['{}:e'.format(self.name)]
        
    def on_exit(self):
        self.sm.out_seq += ['{}:x'.format(self.name)]
        

@fsm.DeclareState(SimpleHSM)
class StateA(CommonStateClass):
    def on_a(self):
        self.sm.out_seq += ['{}::a'.format(self.name)]
        return StateA
    
    def on_b(self):
        self.sm.out_seq += ['{}::b'.format(self.name)]
        return StateA1
    
    def on_c(self):
        self.sm.out_seq += ['{}::c'.format(self.name)]
        return StateB


@fsm.DeclareState(SimpleHSM)
class StateA1(CommonStateClass):
    super_state = StateA
    
    def on_d(self):
        return StateA
    
    
@fsm.DeclareState(SimpleHSM)
class StateB(CommonStateClass):
    def on_a(self):
        return StateB
    
    def on_c(self):
        return StateA

