'''
.. py:module:: ds
    :platform: Unix

The module holds a base implementation, :py:class:`DistributedEnvironment`,
for simulations and environments where the resources span over multiple nodes
on computing clusters or other distributed systems.

.. note::

    The module needs `asyncssh <http://asyncssh.readthedocs.io/en/latest/>`_
    (>=1.6.2, developed with 1.6.2) to function. **Asyncssh** is not installed
    by default as a dependency.

'''
import asyncio
import multiprocessing
import traceback

import asyncssh
from creamas.util import run_or_coro, create_tasks
from creamas.mp import MultiEnvironment


async def ssh_exec(server, cmd, **ssh_kwargs):
    '''Execute a command on a given server using asynchronous SSH-connection.

    The method does not propagate exceptions raised during the SSH-connection,
    instead, the exceptions are caught and returned. The method will exit after
    the first exception is raised.

    :param str server: Address of the server
    :param str cmd: Command to be executed

    :param ssh_kwargs:
        Any additional SSH-connection arguments, as specified by
        :meth:`asyncssh.connect`. See `asyncssh documentation
        <http://asyncssh.readthedocs.io/en/latest/api.html#connect>`_ for
        details.

    :returns:
        (closed SSH-connection, exception)-tuple, if no exceptions are caught,
        the second value is *None*.
    '''
    ret = None
    try:
        # Setting known_hosts to None is an evil to do, but in this exercise we
        # do not care about it.
        conn = await asyncssh.connect(server, **ssh_kwargs)
        ret = await conn.run(cmd)
        conn.close()
    except:
        return (ret, traceback.format_exc())
    return (ret, None)


def ssh_exec_in_new_loop(server, cmd, **ssh_kwargs):
    '''Same as :func:`ssh_exec` but creates a new event loop and executes
    :func:`ssh_exec` in that event loop.
    '''
    task = ssh_exec(server, cmd, **ssh_kwargs)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ret = loop.run_until_complete(task)
    return ret


async def run_node(menv, log_folder):
    '''Run :class:`~creamas.mp.MultiEnvironment` until its manager's
    :meth:`~aiomas.subproc.Manager.stop` is called.

    :param menv: :class:`~creamas.mp.MultiEnvironment` to wait for.
    :param str log_folder:
        Logging folder to be passed down to
        :meth:`~creamas.mp.MultiEnvironment.destroy` after :meth:`stop` is
        called.

    This method will block the current thread until the manager's
    :meth:`~creamas.mp.MultiEnvManager.stop` is called. After the stop-message
    is received, multi-environment is destroyed.

    The method is intended to be
    used in :class:`~creamas.ds.DistributedEnvironment` scripts which spawn
    multi-environments on different nodes. That is, using this function in the
    script will block the script's further execution until the simulation has
    run its course and the nodes need to be destroyed.
    Calling :meth:`~creamas.ds.DistributedEnvironment.destroy` will
    automatically call each node manager's :meth:`stop` and therefore release
    the script.
    '''
    try:
        await menv.manager.stop_received
    except KeyboardInterrupt:
        pass
    finally:
        ret = await menv.destroy(log_folder, as_coro=True)
        return ret


class DistributedEnvironment(MultiEnvironment):
    '''Distributed environment which manages several nodes containing
    multi-environments, a subclass of :class:`~creamas.mp.MultiEnvironment`.

    This environment spawns its slave multi-environments on the different
    servers (nodes) using SSH-connections. The spawning process assumes that
    the user can make a SSH-connection without login credentials to each
    node. The environment can then be used to wait until all the nodes are
    ready (have done their individual initialization) and do optional
    additional preparing of the nodes (e.g. adding inter-node connections
    between agents).

    After all the nodes are ready and prepared, the environment can be used
    to run an iterative (asynchronous) simulation using
    :meth:`DistributedEnvironment.trigger_all` which calls
    :meth:`~creamas.mp.MultiEnvManager.trigger_all` for each node's manager.

    .. warning::
        To free the resources on each node, it is crucial to call
        :meth:`creamas.ds.DistributedEnvironment.destroy` after the simulation
        has been done. Otherwise, some rogue processes are likely to be left
        unattended on the external nodes.

    The intended order of usage is as follows::

        ds = DistributedEnvironment(*args, **kwargs)
        # 'pool' holds the process pool for SSH-connections to nodes,
        # 'r' contains the (future) return values of the connections.
        pool, r = ds.spawn_nodes(spawn_cmd)
        timeout = 30
        loop = asyncio.get_event_loop()
        task = ds.wait_nodes(timeout, check_ready=True)
        nodes_ready = loop.run_until_complete(task)
        if nodes_ready:
            # All nodes are ready so we can do additional preparation
            loop.run_until_complete(ds.prepare_nodes())
            # Run the simulation
            for i in range(10):
                loop.run_until_complete(ds.trigger_all())

        # Destroy the simulation afterwards to free the resources on each node.
        ds.destroy()
    '''
    def __init__(self, addr, env_cls, nodes, mgr_cls=None, name=None,
                 logger=None, **env_kwargs):
        '''
        :param addr:
            ``(HOST, PORT)`` address for the *env* property (this node). The
            ``host`` should not be present in *nodes*.

        :param env_cls:
            Class for the master environment, used to make connections to the
            slave environments. Must be a subclass of
            :py:class:`~creamas.core.environment.Environment`.

        :param mgr_cls:
            Class for the master environment's manager.

        :param str name: Name of the environment. Will be shown in logs.

        :param nodes:
            List of nodes (servers) which are used to host the slave
            multi-environments. See
            :meth:`~creamas.ds.DistributedEnvironment.spawn_slaves`.

        :param logger:
            Optional logger for this simulation.
        '''
        super().__init__(addr, env_cls, mgr_cls=mgr_cls, name=name,
                         logger=logger, **env_kwargs)
        self._nodes = nodes
        self.port = addr[1]
        self.addr = addr
        self._manager_addrs = self._make_manager_addrs()

    @property
    def nodes(self):
        '''Environment nodes (excluding the current host).

        Altering the nodes after the initialization most probably causes
        unexpected behavior.
        '''
        return self._nodes

    @property
    def addrs(self):
        '''Addresses of node managers.

        These addresses are derived from *nodes* and *port* parameters
        given at the initialization time, and are used to communicate tasks
        (trigger agents) to the nodes. Each manager is assumed to be the
        first agent in its own managed environment.
        '''
        return self._manager_addrs

    def _make_manager_addrs(self):
        manager_addrs = []
        for node in self.nodes:
            addr = "tcp://{}:{}/0".format(node, self.port)
            manager_addrs.append(addr)

        return manager_addrs

    async def wait_nodes(self, timeout, check_ready=True):
        '''Wait until all nodes are online (their managers accept connections)
        or timeout expires. Should be called after :meth:`spawn_nodes`.

        This is an alias for :meth:`~creamas.mp.MultiEnvironment.wait_slaves`.
        '''
        return await self.wait_slaves(timeout, check_ready=check_ready)

    async def spawn_nodes(self, spawn_cmd, **ssh_kwargs):
        '''An alias for :meth:`creamas.ds.DistributedEnvironment.spawn_slaves`.
        '''
        return await self.spawn_slaves(spawn_cmd, **ssh_kwargs)

    async def spawn_slaves(self, spawn_cmd, **ssh_kwargs):
        '''Spawn multi-environments on the nodes through SSH-connections.

        :param spawn_cmd:
            str or list, command(s) used to spawn the environment on each node.
            If *list*, it must contain one command for each node in
            :attr:`nodes`. If *str*, the same command is used for each node.

        :param ssh_kwargs:
            Any additional SSH-connection arguments, as specified by
            :meth:`asyncssh.connect`. See `asyncssh documentation
            <http://asyncssh.readthedocs.io/en/latest/api.html#connect>`_ for
            details.

        Nodes are spawned by creating a multiprocessing pool where each node
        has its own subprocess. These subprocesses then use SSH-connections
        to spawn the multi-environments on the nodes. The SSH-connections in
        the pool are kept alive until the nodes are stopped, i.e. this
        distributed environment is destroyed.

        .. warning::
            The spawning process of the nodes assumes that the manager agent of
            each multi-environment (on each node) is initialized in the port
            given by the parameter *port* at the distributed environment's
            initialization time.
        '''
        pool = multiprocessing.Pool(len(self.nodes))
        rets = []
        for i, node in enumerate(self.nodes):
            if type(spawn_cmd) in [list, tuple]:
                cmd = spawn_cmd[i]
            else:
                cmd = spawn_cmd
            args = [node, cmd]
            ret = pool.apply_async(ssh_exec_in_new_loop, args=args,
                                   kwds=ssh_kwargs)
            rets.append(ret)
        self._pool = pool
        self._r = rets
        return pool, rets

    async def prepare_nodes(self, *args, **kwargs):
        '''Prepare nodes (and slave environments and agents) so that they are
        ready. Should be called after :meth:`wait_nodes`.

        .. note::
            Override in the subclass for the intended functionality.
        '''
        raise NotImplementedError()

    def create_connections(self, connection_map, as_coro=False):
        '''Create agent connections from the given connection map.

        :param dict connection_map:
            A map of connections to be created. Dictionary where keys are
            agent addresses and values are lists of (addr, attitude)-tuples
            suitable for
            :meth:`~creamas.core.agent.CreativeAgent.add_connections`.

        The connection map is passed as is to all the node managers which then
        take care of creating connections in their slave environments.
        '''
        async def slave_task(addr, connection_map):
            r_manager = await self.env.connect(addr)
            return await r_manager.create_connections(connection_map)

        tasks = create_tasks(slave_task, self.addrs, connection_map)
        return run_or_coro(tasks, as_coro)
