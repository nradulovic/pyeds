'''
Created on Jul 24, 2017

@author: nenad
'''

import logging

from src.pyeds import fsm


class SimpleFSM(fsm.StateMachine):
    logger = logging.getLogger()
    
    def __init__(self):
        self.added_states = []
        self.out_seq = []
        super().__init__()
        
    
class CommonStateClass(fsm.State):
    def __init__(self):
        super().__init__()
        self.sm.added_states += [self.name]
        
    def on_init(self):
        self.sm.out_seq += ['{}:i'.format(self.name)]
        
    def on_entry(self):
        self.sm.out_seq += ['{}:e'.format(self.name)]
        
    def on_exit(self):
        self.sm.out_seq += ['{}:x'.format(self.name)]
        
@fsm.DeclareState(SimpleFSM)
class StateA1(CommonStateClass):
    def on_a(self, event):
        return StateA2


@fsm.DeclareState(SimpleFSM)
class StateA2(CommonStateClass):
    def on_a(self, event):
        return StateA3


@fsm.DeclareState(SimpleFSM)
class StateA3(CommonStateClass):
    def on_a(self, event):
        return StateA4


@fsm.DeclareState(SimpleFSM)
class StateA4(CommonStateClass):
    def on_a(self, event):
        return StateA5


@fsm.DeclareState(SimpleFSM)
class StateA5(CommonStateClass):
    def on_a(self, event):
        return StateA6


@fsm.DeclareState(SimpleFSM)
class StateA6(CommonStateClass):
    def on_a(self, event):
        return StateA7


@fsm.DeclareState(SimpleFSM)
class StateA7(CommonStateClass):
    def on_a(self, event):
        return StateA1
