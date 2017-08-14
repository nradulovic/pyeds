'''
Created on Jul 24, 2017

@author: nenad
'''


def test_event_data_set(event, data):
    event.data = data
    return event


def test_event_immutability(event):
    event.name = 'some other name'
    return event
