'''
Created on Jul 7, 2017

@author: nenad
'''

try:
    from src.pyeds import fsm
    print('Imported PyEDS from project')
except ImportError:
    from pyeds import fsm
    
from logging import basicConfig, DEBUG, getLogger
import sys

basicConfig(level=DEBUG)

class HypotheticalMachine(fsm.StateMachine):
    logger = getLogger('app')
    foo = 0

@fsm.DeclareState(HypotheticalMachine)
class StateInitial(fsm.State):
    def on_entry(self, event):
        pass
        
    def on_exit(self, event):
        pass
        
    def on_init(self, event):
        self.sm.foo = 0
        return StateS2
    

@fsm.DeclareState(HypotheticalMachine)
class StateS(fsm.State):
    def on_entry(self, event):    
        print('S:entry')
        
    def on_exit(self, event):
        print('S:exit')
    
    def on_init(self, event):
        print('S:init')
        return StateS11
    
    def on_terminate(self, event):
        print('S:terminate')
        self.sm.release()
        sys.exit(0)
        
    def on_e(self, event):
        print('S:e')
        return StateS11
    
    def on_i(self, event):
        print('S:i[foo]:foo=0')
        if self.sm.foo != 0:
            self.sm.foo = 0
    
    
@fsm.DeclareState(HypotheticalMachine)
class StateS1(fsm.State):
    super_state = StateS
    
    def on_entry(self, event):
        print('S1:entry')
        
    def on_exit(self, event):
        print('S1:exit')
        
    def on_init(self, event):
        print('S1:init')
        return StateS11
    
    def on_a(self, event):
        print('S1:a')
        
    def on_b(self, event):
        print('S1:b')
        return StateS11
    
    def on_c(self, event):
        print('S1:c')
        return StateS2
    
    def on_d(self, event):
        print('S1:d[!foo]/foo=1')
        if self.sm.foo == 0:
            self.sm.foo = 1
            return StateS
    
    def on_f(self, event):
        print('S1:f')
        return StateS211
    
    def on_i(self, event):
        print('S1:i')
        
        
@fsm.DeclareState(HypotheticalMachine)
class StateS11(fsm.State):
    super_state = StateS1
        
    def on_entry(self, event):
        print('S11:entry')

    def on_exit(self, event):
        print('S11:exit')
        
    def on_init(self, event):
        print('S11:init')
        
    def on_d(self, event):
        print('S11:d[foo]/foo=0')
        if self.sm.foo != 0:
            self.sm.foo = 0
            return StateS1
        
    def on_g(self, event):
        print('S11:g')
        return StateS211
    
    def on_h(self, event):
        return StateS
    
    
@fsm.DeclareState(HypotheticalMachine)
class StateS2(fsm.State):
    super_state = StateS
    
    def on_entry(self, event):
        print('S2:entry')

    def on_exit(self, event):
        print('S2:exit')
        
    def on_init(self, event):
        print('S2:init')
        return StateS211
    
    def on_c(self, event):
        print('S2:c')
        return StateS1

    def on_f(self, event):
        print('S2:f')
        return StateS11
    
    
@fsm.DeclareState(HypotheticalMachine)
class StateS21(fsm.State):
    super_state = StateS2
    
    def on_entry(self, event):
        print('S21:entry')
        
    def on_exit(self, event):
        print('S21:exit')
        
    def on_init(self, event):
        print('S21:init')
        return StateS211
    
    def on_a(self, event):
        print('S21:a')
        return StateS21
    
    def on_b(self, event):
        print('S21:b')
        return StateS211
    
    def on_g(self, event):
        print('S21:g')
        return StateS11
    
@fsm.DeclareState(HypotheticalMachine)
class StateS211(fsm.State):
    super_state = StateS21

    def on_entry(self, event):
        print('S211:entry')
        
    def on_exit(self, event):
        print('S211:exit')
        
    def on_init(self, event):
        print('S211:init')

    def on_d(self, event):
        print('S211:d')
        return StateS21
    
    def on_h(self, event):
        print('S211:h')
        return StateS
        
        
def main():
    sm = HypotheticalMachine()
    
    test_input_sequence = [
        'g',
        'i',
        'a',
        'd',
        'd',
        'c',
        'e',
        'e',
        'g',
        'i',
        'i',
        'terminate'
        ]
    try:
        for signal in test_input_sequence:
            sm.put(fsm.Event(signal))
    except KeyboardInterrupt:
        sm.release()
    sm.wait()

if __name__ == '__main__':
    main()