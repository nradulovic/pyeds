'''
Created on Jul 24, 2017

@author: nenad
'''
import unittest
import logging

from pyeds import fsm


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
    def on_a(self, event):
        self.sm.out_seq += ['{}:a'.format(self.name)]
        return StateA

    def on_b(self, event):
        self.sm.out_seq += ['{}:b'.format(self.name)]
        return StateA1

    def on_c(self, event):
        self.sm.out_seq += ['{}:c'.format(self.name)]
        return StateB


@fsm.DeclareState(SimpleHSM)
class StateA1(CommonStateClass):
    super_state = StateA

    def on_d(self, event):
        return StateA


@fsm.DeclareState(SimpleHSM)
class StateB(CommonStateClass):
    def on_a(self, event):
        return StateB

    def on_c(self, event):
        return StateA


class HsmTestCase(unittest.TestCase):
    def test_hsm_states(self):
        expected = (
            'StateA',
            'StateA1',
            'StateB',
            )
        sm = SimpleHSM()
        sm.do_terminate()
        sm.wait()
        retval = sm.states
        self.assertEqual(
            set(retval),
            set(expected),
            '{} is not as expected {}'.format(retval, expected))

    def test_hsm_state_count(self):
        expected = 3
        sm = SimpleHSM()
        sm.do_terminate()
        sm.wait()
        retval = len(sm.states)
        self.assertEqual(
            retval,
            expected,
            '{} is not as expected {}'.format(retval, expected))

    def test_hsm_state_depth(self):
        expected = 2
        sm = SimpleHSM()
        sm.do_terminate()
        sm.wait()
        retval = sm.depth
        self.assertEqual(
            retval,
            expected,
            '{} is not as expected {}'.format(retval, expected))

    def test_hsm_transitions(self):
        event_ids = (
            'a',
            'a',
            'a',
            'a',
            'a',
            'a',
            'a')
        expected = (
            'StateA:i',
            'StateA:a',
            'StateA:i',
            'StateA:a',
            'StateA:i',
            'StateA:a',
            'StateA:i',
            'StateA:a',
            'StateA:i',
            'StateA:a',
            'StateA:i',
            'StateA:a',
            'StateA:i',
            'StateA:a',
            'StateA:i'
            )
        sm = SimpleHSM()
        for event_id in event_ids:
            sm.send(fsm.Event(event_id))
        sm.do_terminate()
        sm.wait()
        retval = sm.out_seq
        self.assertEqual(
            tuple(retval),
            expected,
            '{} is not as expected {}'.format(retval, expected))


if __name__ == '__main__':
    unittest.main()
