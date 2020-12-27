'''
Created on Jul 24, 2017

@author: nenad
'''
import unittest
import logging

from pyeds import fsm


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

    def on_eventless(self, event):
        return InvalidEventlessState


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

@fsm.DeclareState(SimpleFSM)
class InvalidEventlessState(fsm.State):
    def on_entry(self):
        # This is invalid state. You can't request for transition on entry.
        return StateA1


class FsmTestCase(unittest.TestCase):
    def test_fsm_states(self):
        expected = (
            'StateA1',
            'StateA2',
            'StateA3',
            'StateA4',
            'StateA5',
            'StateA6',
            'StateA7',
            'InvalidEventlessState'
            )
        sm = SimpleFSM()
        sm.do_terminate()
        sm.wait()
        retval = sm.states
        self.assertEqual(
            set(retval),
            set(expected),
            '{} is not as expected {}'.format(retval, expected))

    def test_fsm_state_adding(self):
        expected = [
            'StateA1',
            'StateA2',
            'StateA3',
            'StateA4',
            'StateA5',
            'StateA6',
            'StateA7'
            ]
        sm = SimpleFSM()
        sm.do_terminate()
        sm.wait()
        retval = sm.added_states
        self.assertEqual(
            set(retval),
            set(expected),
            '{} is not as expected {}'.format(retval, expected))

    def test_fsm_state_count(self):
        # There are 8 states in state machine definition
        expected = 8
        sm = SimpleFSM()
        sm.do_terminate()
        sm.wait()
        retval = len(sm.states)
        self.assertEqual(
            retval,
            expected,
            '{} is not as expected {}'.format(retval, expected))

    def test_fsm_state_depth(self):
        expected = 1
        sm = SimpleFSM()
        sm.do_terminate()
        sm.wait()
        retval = sm.depth
        self.assertEqual(
            retval,
            expected,
            '{} is not as expected {}'.format(retval, expected))

    def test_fsm_idle(self):
        expected = ['StateA1:i']
        sm = SimpleFSM()
        sm.do_terminate()
        sm.wait()
        retval = sm.out_seq
        self.assertEqual(
            retval,
            expected,
            '{} is not as expected {}'.format(retval, expected))

    def test_fsm_simple_transitions(self):
        expected = [
            'StateA1:i',
            'StateA1:x',
            'StateA2:e',
            'StateA2:i',
            'StateA2:x',
            'StateA3:e',
            'StateA3:i',
            'StateA3:x',
            'StateA4:e',
            'StateA4:i',
            'StateA4:x',
            'StateA5:e',
            'StateA5:i',
            'StateA5:x',
            'StateA6:e',
            'StateA6:i',
            'StateA6:x',
            'StateA7:e',
            'StateA7:i',
            'StateA7:x',
            'StateA1:e',
            'StateA1:i'
            ]
        sm = SimpleFSM()
        event = fsm.Event('a')
        for _ in range(7):
            sm.send(event)
        sm.do_terminate()
        sm.wait()
        retval = sm.out_seq
        self.assertEqual(
            retval,
            expected,
            '{} is not as expected {}'.format(retval, expected))

    def test_fsm_missing_transitions(self):
        expected = [
            'StateA1:i',
            'StateA1:x',
            'StateA2:e',
            'StateA2:i'
            ]
        sm = SimpleFSM()
        event = fsm.Event('a')
        sm.send(event)
        event = fsm.Event('b')
        sm.send(event)
        sm.do_terminate()
        sm.wait()
        retval = sm.out_seq
        self.assertEqual(
            retval,
            expected,
            '{} is not as expected {}'.format(retval, expected))


if __name__ == '__main__':
    unittest.main()
