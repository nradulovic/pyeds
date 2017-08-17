'''
Created on Jul 7, 2017

@author: nenad
'''
import unittest

from pyeds import fsm

import test_events
import test_simplefsm
import test_simplehsm


class EventTestCase(unittest.TestCase):
    def test_event_class_name(self):
        class MyEvent(fsm.Event):
            pass
        my_event = MyEvent()
        self.assertEqual('my_event', my_event.name)

    def test_event_class_comlex_name(self):
        class MyEventWITHComplexName(fsm.Event):
            pass
        my_event = MyEventWITHComplexName()
        self.assertEqual('my_event_with_complex_name', my_event.name)

    def test_event_arg_name(self):
        name = 'my_name'
        my_event = fsm.Event(name)
        self.assertEqual(name, my_event.name)

    def test_event_data_set(self):
        event = fsm.Event('event')
        data = 'some data'
        self.assertEqual(
            data,
            test_events.test_event_data_set(event, data).data)

    def test_event_immutability(self):
        event = fsm.Event('event')
        self.assertRaises(
                AttributeError,
                test_events.test_event_immutability, event)


class FsmTestCase(unittest.TestCase):
    def test_fsm_states(self):
        expected = (
            'StateA1',
            'StateA2',
            'StateA3',
            'StateA4',
            'StateA5',
            'StateA6',
            'StateA7'
            )
        sm = test_simplefsm.SimpleFSM()
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
        sm = test_simplefsm.SimpleFSM()
        sm.do_terminate()
        sm.wait()
        retval = sm.added_states
        self.assertEqual(
            set(retval),
            set(expected),
            '{} is not as expected {}'.format(retval, expected))

    def test_fsm_state_count(self):
        expected = 7
        sm = test_simplefsm.SimpleFSM()
        sm.do_terminate()
        sm.wait()
        retval = len(sm.states)
        self.assertEqual(
            retval,
            expected,
            '{} is not as expected {}'.format(retval, expected))

    def test_fsm_state_depth(self):
        expected = 1
        sm = test_simplefsm.SimpleFSM()
        sm.do_terminate()
        sm.wait()
        retval = sm.depth
        self.assertEqual(
            retval,
            expected,
            '{} is not as expected {}'.format(retval, expected))

    def test_fsm_idle(self):
        expected = ['StateA1:i']
        sm = test_simplefsm.SimpleFSM()
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
        sm = test_simplefsm.SimpleFSM()
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
        sm = test_simplefsm.SimpleFSM()
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


class HsmTestCase(unittest.TestCase):
    def test_hsm_states(self):
        expected = (
            'StateA',
            'StateA1',
            'StateB',
            )
        sm = test_simplehsm.SimpleHSM()
        sm.do_terminate()
        sm.wait()
        retval = sm.states
        self.assertEqual(
            set(retval),
            set(expected),
            '{} is not as expected {}'.format(retval, expected))

    def test_hsm_state_count(self):
        expected = 3
        sm = test_simplehsm.SimpleHSM()
        sm.do_terminate()
        sm.wait()
        retval = len(sm.states)
        self.assertEqual(
            retval,
            expected,
            '{} is not as expected {}'.format(retval, expected))

    def test_hsm_state_depth(self):
        expected = 2
        sm = test_simplehsm.SimpleHSM()
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
            )
        sm = test_simplefsm.SimpleFSM()
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
