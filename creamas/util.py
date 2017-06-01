'''
.. py:module:: util
    :platform: Unix

Miscellaneous utility functions.
'''
import asyncio
import itertools
import re


async def wait_tasks(tasks, flatten=True):
    '''Wait for a list of asynchronous tasks to finish.

    :param list tasks:
        A list of *asyncio* tasks wrapped in :func:`asyncio.ensure_future`.

    :param bool flatten:
        If ``True`` the results are flattened into one list instead of
        returning a list of lists.

    :returns: The results of tasks as a list or a list of lists.
    '''
    rets = await asyncio.gather(*tasks)
    if flatten:
        rets = list(itertools.chain(*rets))
    return rets


def _addr_key(addr):
    splitted = re.split(r'[:/]', addr)
    host, port, order = splitted[-3:]
    return (host, int(port), int(order))


def sort_addrs(addrs):
    '''Sort agent addresses.

    :param list addrs: List of addresses to be sorted.

    :returns:
        List of addresses in a sorted order.

    Agent addresses are sorted with following hierarchical criteria:
        1. by the host of an agent's environment
        2. by the port (interpreted as an integer) of an agent's environment
        3. by the order in which the agents were created in their environment

    For example, the following list of addresses::

        ['tcp://bnode:5555/0',
         'tcp://anode:5555/0',
         'tcp://anode:50/1',
         'tcp://anode:5555/2',
         'tcp://anode:50/2',
         'tcp://anode:18000/0',
         'tcp://bnode:50/0',
         'tcp://bnode:18000/0',
         'tcp://anode:18000/1',
         'tcp://anode:18000/2',
         'tcp://bnode:50/1',
         'tcp://bnode:5555/2',
         'tcp://bnode:5555/1',
         'tcp://bnode:50/2',
         'tcp://bnode:18000/2',
         'tcp://anode:50/0',
         'tcp://bnode:18000/1',
         'tcp://anode:5555/1']

    Would be sorted into following order::

        ['tcp://anode:50/0',
         'tcp://anode:50/1',
         'tcp://anode:50/2',
         'tcp://anode:5555/0',
         'tcp://anode:5555/1',
         'tcp://anode:5555/2',
         'tcp://anode:18000/0',
         'tcp://anode:18000/1',
         'tcp://anode:18000/2',
         'tcp://bnode:50/0',
         'tcp://bnode:50/1',
         'tcp://bnode:50/2',
         'tcp://bnode:5555/0',
         'tcp://bnode:5555/1',
         'tcp://bnode:5555/2',
         'tcp://bnode:18000/0',
         'tcp://bnode:18000/1',
         'tcp://bnode:18000/2']
    '''
    return sorted(addrs, key=lambda x: _addr_key(x))


def split_addrs(addrs):
    '''Split addresses into dictionaries by hosts and ports.

    :param list addrs: A list of addresses.

    :returns:
        A dictionary of dictionaries, where ``dict[HOST][PORT]`` holds a list
        of all agent addresses in that environment.
    '''
    splitted = {}
    for addr in addrs:
        host, port, _ = _addr_key(addr)
        if host not in splitted:
            splitted[host] = {}
        if port not in splitted[host]:
            splitted[host][port] = []
        splitted[host][port].append(addr)
    return splitted


def get_manager(addr):
    '''Get assumed environment manager's address for a given agent address.
    '''
    return addr.rsplit("/", 1)[0] + "/0"


def addrs2managers(addrs):
    '''Map agent addresses to their assumed managers.
    '''
    mgrs = {}
    for addr in addrs:
        mgr_addr = get_manager(addr)
        if mgr_addr not in mgrs:
            mgrs[mgr_addr] = []
        mgrs[mgr_addr].append(addr)
    return mgrs
