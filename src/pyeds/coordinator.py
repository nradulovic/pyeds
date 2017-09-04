'''
Coordinator
===========

Coordinator provides interface for following classes:
    * Task: A class that provides simultaneous processing.
    * Timer: A time delay.
    * Queue: A data queue.

Following functions are provided:
    * current: Returns the current thread of execution.

By default the Python standard library is used for this functionality.

Module details
--------------

Created on Jul 22, 2017
'''

import collections

providers = {}
provider = None


Provider = collections.namedtuple(
    'Provider',
    ['Task', 'Timer', 'Lock', 'Queue', 'current'])


def set_provider(name):
    '''Choose the default provider.

    Args:
        * name (:obj:`str`): Name of provider.

    Raises:
        * LookupError: When a provider with given name is not registered.
    '''
    global provider

    try:
        provider = providers[name]
    except KeyError:
        raise LookupError('Coordinator \'{}\' is not registered.'.format(name))


# ****************************************************************************
# Setup Standard Python provider
# ****************************************************************************

try:
    import threading
    import queue

    class StdTask(threading.Thread):
        def __init__(self, target, name):
            super().__init__(target=target, name=name, daemon=True)

    class StdTimer(threading.Timer):
        def __init__(self, interval, handler):
            self._handler = handler
            super().__init__(interval, self.callback)

        def callback(self, *args, **kwargs):
            self._handler()

    class StdQueue(queue.Queue):
        def put(self, item, block=False, timeout=None):
            try:
                super().put(item, block, timeout)
            except queue.Full:
                raise BufferError

    providers['std'] = Provider(
        Task=StdTask,
        Timer=StdTimer,
        Lock=threading.Lock,
        Queue=StdQueue,
        current=threading.current_thread)

    if provider is None:
        set_provider('std')
except ImportError:
    pass
