'''
Created on Jul 22, 2017

@author: nenad
'''

class Immutable(object):
    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError(
                    'Can\'t set attribute \'{}\', {} object is immutable'
                    .format(name, self.__class__.__name__))
        object.__setattr__(self, name, value)