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
import logging
import multiprocessing
import time
import traceback

import aiomas
import asyncssh
from creamas import Environment
from creamas import util


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


class DistributedEnvironment():
    '''Distributed environment which manages several nodes containing
    multi-environments.

    This environment is used to spawn the multi-environments on the different
    servers (nodes) using SSH-connections. The spawning process assumes that
    the user can make a SSH-connection without login credentials to each
    node. The environment can then be used to wait until all the nodes are
    ready (have done their individual initialization) and do optional
    additional preparing of the nodes (e.g. adding inter-node connections
    between agents).

    After all the nodes are ready and prepared, the environment can be used
    to run an iterative (asynchronous) simulation using
    :py:meth:`DistributedEnvironment.trigger_all` which calls
    :py:meth:`~creamas.mp.MultiEnvManager.trigger_all` for each node's manager.

    .. warning::
        To free the resources on each node, it is crucial to call
        :py:meth:`DistributedEnvironment.destroy` after the simulation has been
        done. Otherwise, some rogue processes are likely to be left unattended
        on the external nodes.

    The intended order of usage is as follows::

        ds = DistributedEnvironment(*args, **kwargs)
        # 'pool' holds the process pool for SSH-connections to nodes,
        # 'r' contains the (future) return values of the connections.
        pool, r = ds.spawn_nodes(spawn_cmd)
        timeout = 30
        loop = asyncio.get_event_loop()
        nodes_ready = loop.run_until_complete(ds.wait_nodes(timeout))
        if nodes_ready:
            # All nodes are ready so we can do additional preparation
            loop.run_until_complete(ds.prepare_nodes())
            # Run the simulation
            for i in range(10):
                loop.run_until_complete(ds.trigger_all())

        # Destroy the simulation afterwards to free the resources on each node.
        ds.destroy()
    '''
    def __init__(self, host, port, nodes, logger=None):
        '''
        :param host:
            Host of the *env* property (this node). The host should not be
            present in *nodes*.

        :param port:
            Port for the managing environments on each node (incl. this node),
            e.g. 5555. This port is not checked for availability before the
            node environments are spawned.

        :param nodes:
            List of nodes (servers) which are used to host the
            multi-environments. Each node should allow SSH-connections without
            login credentials.

        :param logger:
            Optional logger for this simulation.
        '''
        self._nodes = nodes
        self.port = port
        self.addr = (host, port)
        self._env = Environment.create(self.addr, codec=aiomas.MsgPack)
        self._manager_addrs = self._make_manager_addrs()
        if logger is None:
            self.logger = logging.getLogger(__name__)
            self.logger.addHandler(logging.NullHandler())
        else:
            self.logger = logger

    @property
    def nodes(self):
        '''Environment nodes (excluding the current host).

        Altering the nodes after the initialization most probably causes
        unexpected behavior.
        '''
        return self._nodes

    @property
    def env(self):
        '''Environment used to communicate with node managers.

        The environment does not hold any agents by default, but it is easy to
        create a manager for it on your own, if the node managers need to
        be able to communicate back to this environment.
        '''
        return self._env

    @property
    def addrs(self):
        '''Addresses of node managers.

        These addresses are derived from *nodes* and *port* parameters
        given at the initialization time, and are used to communicate tasks
        (trigger agents) to the nodes. Each manager is assumed to be the
        first agent in its own managed environment.
        '''
        return self._manager_addrs

    async def connect(self, *args, **kwargs):
        '''Shortcut to ``self.env.connect``
        '''
        return await self.env.connect(*args, **kwargs)

    async def wait_nodes(self, timeout, check_ready=True):
        '''Wait until all nodes are online (their managers accept connections)
        or timeout expires. Should be called after :meth:`spawn_nodes`.

        :param int timeout:
            Timeout (in seconds) after which the method will return even though
            all the nodes are not online yet.

        :param bool check_ready:
            If ``True`` also checks if each node environment is ready.

        Node is assumed ready when its manager's :meth:`is_ready`-method
        returns ``True``.

        .. seealso::

            :meth:`creamas.core.environment.Environment.is_ready`,
            :meth:`creamas.mp.MultiEnvironment.is_ready`,
            :meth:`creamas.mp.EnvManager.is_ready`,
            :meth:`creamas.mp.MultiEnvManager.is_ready`

        '''
        self.logger.info("Waiting for nodes to become ready...")
        t = time.time()
        online = []
        while len(online) < len(self.addrs):
            for addr in self.addrs:
                if time.time() - t > timeout:
                    self.logger.info("Timeout while waiting for the nodes to "
                                     "become online.")
                    return False
                if addr not in online:
                    try:
                        r_manager = await self.env.connect(addr, timeout=1)
                        ready = True
                        if check_ready:
                            ready = await r_manager.is_ready()
                        if ready:
                            online.append(addr)
                            self.logger.info("Node {}/{} ready: {}"
                                             .format(len(online),
                                                     len(self.addrs),
                                                     addr))
                    except:
                        pass
        self.logger.info("All nodes ready in {} seconds!"
                         .format(time.time() - t))
        return True

    def _make_manager_addrs(self):
        manager_addrs = []
        for node in self.nodes:
            addr = "tcp://{}:{}/0".format(node, self.port)
            manager_addrs.append(addr)

        return manager_addrs

    def spawn_nodes(self, spawn_cmd, **ssh_kwargs):
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
        ready for the simulation. Should be called after :meth:`wait_nodes`.

        .. note::
            Override in the subclass for the intended functionality.
        '''
        raise NotImplementedError()

    async def _trigger_node(self, addr, *args, **kwargs):
        '''Trigger all agents in a node managed by the agent in
        *addr* to act.
        '''
        r_manager = await self.env.connect(addr)
        ret = await r_manager.trigger_all(*args, **kwargs)
        return ret

    async def trigger_all(self, *args, **kwargs):
        '''Trigger all agents in all the nodes to act asynchronously.

        This method makes a connection to each manager in *addrs*
        and asynchronously executes :meth:`trigger_all` in all of them.

        Given arguments and keyword arguments are passed down to each agent's
        :meth:`creamas.core.agent.CreativeAgent.act`.

        .. note::

            By design, the manager agents in each environment, i.e.
            :attr:`manager`, are excluded from acting.

        .. seealso::

            :py:meth:`creamas.core.environment.Environment.trigger_all`,
            :py:meth:`creamas.mp.MultiEnvironment.trigger_all`,
            :py:meth:`creamas.mp.MultiEnvManager.trigger_all`
        '''
        tasks = []
        for addr in self.addrs:
            task = asyncio.ensure_future(self._trigger_node
                                         (addr, *args, **kwargs))
            tasks.append(task)
        rets = await asyncio.gather(*tasks)
        return rets

    async def stop_nodes(self, timeout=1):
        '''Stop all the nodes by sending a stop-message to their managers.

        :param int timeout:
            Timeout for connecting to each manager. If a connection can not
            be made before the timeout expires, the resulting error for that
            particular manager is logged, but the stopping of other managers
            is not halted.
        '''
        for addr in self.addrs:
            try:
                r_manager = await self.env.connect(addr, timeout=timeout)
                await r_manager.stop()
            except:
                self.logger.info("Could not stop {}".format(addr))

    def destroy(self):
        '''Destroy the simulation.

        Stop the nodes and free other resources associated with the simulation.
        '''
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.stop_nodes())
        self._pool.close()
        self._pool.terminate()
        self._pool.join()
        self.env.shutdown()

    async def _get_agents(self, addr, address=True, agent_cls=None):
        r_manager = await self.env.connect(addr)
        agents = await r_manager.get_agents(address, agent_cls)
        return agents

    def get_agents(self, address=True, agent_cls=None, as_coro=False):
        '''Return all the relevant agents from all the nodes.

        The method excludes all the manager agents from the returned list.

        .. seealso::

            :meth:`creamas.Environment.get_agents`,
            :meth:`creamas.mp.MultiEnvironment.get_agents`,
            :meth:`creamas.mp.MultiEnvManager.get_agents`
        '''
        tasks = []
        for addr in self.addrs:
            task = asyncio.ensure_future(self._get_agents(addr,
                                                          address,
                                                          agent_cls))
            tasks.append(task)
        if as_coro:
            return util.wait_tasks(tasks)
        else:
            return aiomas.run(util.wait_tasks(tasks))

    async def _create_connections(self, m_addr, connection_map):
        r_manager = await self.env.connect(m_addr)
        return await r_manager.create_connections(connection_map)

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
        tasks = []
        for m_addr in self.addrs:
            task = self.ensure_future(self._create_connections(m_addr,
                                                               connection_map))
            tasks.append(task)
        if as_coro:
            return util.wait_tasks(tasks)
        else:
            return aiomas.run(util.wait_tasks(tasks))

    async def _get_connections(self, r_addr, attitudes):
        r_manager = await self.env.connect(r_addr)
        return await r_manager.get_connections(attitudes)

    def get_connections(self, attitudes, as_coro=False):
        '''Return connections from all the agents in the node environments.

        :param bool attitudes:
            If ``True``, returns also the attitudes for each connection.

        :param bool as_coro:
            If ``True`` returns a coroutine, otherwise runs the asynchronous
            calls to the node environment managers in the event loop.

        .. seealso::

            :meth:`creamas.core.environment.Environment.get_connections`
            :meth:`creamas.mp.MultiEnvironment.get_connections`
        '''
        tasks = []
        for m_addr in self.addrs:
            task = asyncio.ensure_future(self._get_connections
                                         (m_addr, attitudes))
            tasks.append(task)
        if as_coro:
            return util.wait_tasks(tasks)
        else:
            return aiomas.run(util.wait_tasks(tasks))
