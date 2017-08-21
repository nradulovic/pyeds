'''
Generic library
===============

This module contains definitions for generic usage.

Module details
--------------

Created on Jul 22, 2017
'''

__author__ = 'Nenad Radulovic <nenad.b.radulovic@gmail.com>'


class Immutable(object):
    '''Immutable object

    An immutable object (unchangeable object) is an object whose state cannot
    be modified after it is created.

    When trying to modify an attribute that is already set the
    ``AttributeError``  will be raised.
    '''
    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError(
                    'Can\'t set attribute \'{}\', {} object is immutable'
                    .format(name, self.__class__.__name__))
        object.__setattr__(self, name, value)
