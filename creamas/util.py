"""
.. py:module:: util
    :platform: Unix

Miscellaneous utility functions.
"""
import asyncio
import itertools
import re

import aiomas


def sanitize_agent_name(name):
    """Get sanitized name of the agent, used for file and directory creation.
    """
    a = re.split("[:/]", name)
    return "_".join([i for i in a if len(i) > 0])


def expose(*args, **kwargs):
    """Function which returns :func:`aiomas.expose` wrapper.

    Used by agents to indicate which functions should be callable by other agents.
    """
    return aiomas.expose(*args, **kwargs)


def create_tasks(task_coro, addrs, *args, flatten=True, **kwargs):
    """Create and schedule a set of asynchronous tasks.

    The function creates the tasks using a given list of agent addresses and
    wraps each of them in :func:`asyncio.ensure_future`. The ``*args`` and
    ``**kwargs`` are passed down to :func:`task_coro` when creating tasks for
    each address in :attr:`addrs`.

    Usage example for a method in a class derived from
    :class:`~creamas.mp.MultiEnvironment`::

        async def my_method(self, *args, **kwargs):
            async def task(addr, *args, **kwargs):
                r_manager = await self.env.connect(addr)
                return await r_manager.my_method(*args, **kwargs)

            return await util.create_tasks(task, self.addrs, *args, **kwargs)

    :param task_coro:
        Coroutine which is used for each address in :attr:`addrs`. The
        coroutine should accept an agent address as the first parameter.
    :param list addrs:
        A list of agent addresses used as the first parameters of
        :func:`task_coro`.
    :param bool flatten:
        If ``True`` the returned results are flattened into one list if the
        tasks return iterable objects. The parameter does nothing if all the
        results are not iterable.
    :returns:
        An awaitable coroutine which returns the results of tasks as a list or
        as a flattened list
    """
    tasks = []
    for agent_addr in addrs:
        task = asyncio.ensure_future(task_coro(agent_addr, *args, **kwargs))
        tasks.append(task)
    return wait_tasks(tasks, flatten)


async def wait_tasks(tasks, flatten=True):
    """Gather a list of asynchronous tasks and wait for their completion.

    :param list tasks:
        A list of *asyncio* tasks wrapped in :func:`asyncio.ensure_future`.
    :param bool flatten:
        If ``True`` the returned results are flattened into one list if the
        tasks return iterable objects. The parameter does nothing if all the
        results are not iterable.
    :returns:
        The results of tasks as a list or as a flattened list
    """
    rets = await asyncio.gather(*tasks)
    if flatten and all(map(lambda x: hasattr(x, '__iter__'), rets)):
        rets = list(itertools.chain(*rets))
    return rets


def run_or_coro(task, as_coro, loop=None):
    """A shorthand to run the task/future or return it as is.

    :param task:
        Optional. Task or Future which is run until complete. If parameter is
        ``None`` runs the event loop forever.
    :param bool as_coro:
        If ``True`` returns the given task as is, otherwise runs it in the
        event loop.
    :param loop:
        Optional. Event loop to use. If the parameter is ``None`` uses
        asyncio's base event loop.
    """
    if as_coro:
        return task
    else:
        return run(task, loop)


def run(task=None, loop=None):
    """Run the event loop forever or until the task/future *task* is finished.

    :param task:
        Optional. Task or Future which is run until complete. If parameter is
        ``None`` runs the event loop forever.
    :param loop:
        Optional. Event loop to use. If the parameter is ``None`` uses
        asyncio's base event loop.

    .. note::
        This method has the same intent as :func:`aiomas.util.run`.
    """
    if loop is None:
        loop = asyncio.get_event_loop()
    if task is None:
        return loop.run_forever()
    else:
        return loop.run_until_complete(task)


def _addr_key(addr):
    split = re.split(r'[:/]', addr)
    host, port, order = split[-3:]
    return host, int(port), int(order)


def sort_addrs(addrs):
    """Return agent addresses in a sorted order.

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

    would be sorted into the following order::

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

    :param list addrs: List of addresses to be sorted.

    :returns:
        List of addresses in a sorted order.
    """
    return sorted(addrs, key=lambda x: _addr_key(x))


def split_addrs(addrs):
    """Split addresses into dictionaries by hosts and ports.

    :param list addrs: A list of addresses.

    :returns:
        A dictionary of dictionaries, where ``dict[HOST][PORT]`` holds a list
        of all agent addresses in that environment.
    """
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
    """Get assumed environment manager's address for a given agent address.
    """
    return addr.rsplit("/", 1)[0] + "/0"


def addrs2managers(addrs):
    """Map agent addresses to their assumed managers.

    .. seealso::

        :func:`creamas.util.get_manager`
    """
    mgrs = {}
    for addr in addrs:
        mgr_addr = get_manager(addr)
        if mgr_addr not in mgrs:
            mgrs[mgr_addr] = []
        mgrs[mgr_addr].append(addr)
    return mgrs
