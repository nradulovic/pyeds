'''
Created on Jul 24, 2017

@author: nenad
'''
import unittest

from pyeds import fsm


def event_data_set(event, data):
    event.data = data
    return event


def event_name_set(event):
    event.name = 'some other name'
    return event


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
            event_data_set(event, data).data)


    def test_event_immutability(self):
        event = fsm.Event('event')
        self.assertRaises(
                AttributeError,
                event_name_set, event)


if __name__ == '__main__':
    unittest.main()
