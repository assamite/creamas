"""
.. py:module:: ds
    :platform: Unix

The module holds a base implementation, :py:class:`DistributedEnvironment`,
for simulations and environments where the resources span over multiple nodes
on computing clusters or other distributed systems.

.. note::

    The module needs `asyncssh <http://asyncssh.readthedocs.io/en/latest/>`_
    to function. **Asyncssh** is not installed as a dependency by default.

"""
import asyncio
import logging
import multiprocessing

import asyncssh

from creamas.mp import MultiEnvironment
from creamas.util import create_tasks, run_or_coro


logger = logging.getLogger(__name__)


async def ssh_exec(server, cmd, timeout=10, **ssh_kwargs):
    """Execute a command on a given server using asynchronous SSH-connection.

    The connection to the server is wrapped in :func:`asyncio.wait_for` and
    given :attr:`timeout` is applied to it. If the server is not reachable
    before timeout expires, :exc:`asyncio.TimeoutError` is raised.

    :param str server: Address of the server
    :param str cmd: Command to be executed
    :param int timeout: Timeout to connect to server.

    :param ssh_kwargs:
        Any additional SSH-connection arguments, as specified by
        :func:`asyncssh.connect`. See `asyncssh documentation
        <http://asyncssh.readthedocs.io/en/latest/api.html#connect>`_ for
        details.

    :returns:
        closed SSH-connection
    """
    conn = await asyncio.wait_for(asyncssh.connect(server, **ssh_kwargs),
                                  timeout=timeout)
    ret = await conn.run(cmd)
    conn.close()
    return ret


def ssh_exec_in_new_loop(server, cmd, timeout=10, **ssh_kwargs):
    """Same as :func:`ssh_exec` but creates a new event loop and executes
    :func:`ssh_exec` in that event loop.
    """
    task = ssh_exec(server, cmd, timeout=timeout, **ssh_kwargs)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(task)


async def run_node(menv, log_folder):
    """Run :class:`~creamas.mp.MultiEnvironment` until its manager's
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
    run its course and the nodes need to be closed.
    Calling :meth:`~creamas.ds.DistributedEnvironment.close` will
    automatically call each node manager's :meth:`stop` and therefore release
    the script.
    """
    try:
        await menv.manager.stop_received
    except KeyboardInterrupt:
        pass
    finally:
        ret = await menv.close(log_folder, as_coro=True)
        return ret


class DistributedEnvironment(MultiEnvironment):
    """Distributed environment which manages several nodes containing
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
        :meth:`creamas.ds.DistributedEnvironment.close` after the simulation
        is finished. Otherwise, some rogue processes are likely to be left
        unattended on the external nodes.

    The intended order of usage is as follows::

        ds = DistributedEnvironment(*args, **kwargs)
        run(ds.spawn_nodes(spawn_cmd))
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
        ds.close()
    """
    def __init__(self, addr, env_cls, nodes, mgr_cls=None, name=None,
                 logger=None, **env_kwargs):
        """
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
            List of (server, port)-tuples which are used to make host the slave
            multi-environments. The port is the port for the SSH connection,
            default SSH-port is 22. See also
            :meth:`~creamas.ds.DistributedEnvironment.spawn_slaves`.

        :param logger:
            Optional logger for this simulation.
        """
        super().__init__(addr, env_cls, mgr_cls=mgr_cls, name=name,
                         logger=logger, **env_kwargs)
        self._nodes = nodes
        self.port = addr[1]
        self.addr = addr

    @property
    def nodes(self):
        """Environment nodes (excluding the current host).

        Altering the nodes after the initialization most probably causes
        unexpected behavior.
        """
        return self._nodes

    @property
    def addrs(self):
        """Addresses of the node managers.

        These addresses are derived from *nodes* and *ports* parameters
        given in :meth:`spawn_slaves`, and are used to communicate tasks
        (trigger agents) to the nodes. Each manager is assumed to be the
        first agent in its own managed environment.
        """
        return self._manager_addrs

    async def wait_nodes(self, timeout, check_ready=True):
        """Wait until all nodes are online (their managers accept connections)
        or timeout expires. Should be called after :meth:`spawn_nodes`.

        This is an alias for :meth:`~creamas.mp.MultiEnvironment.wait_slaves`.
        """
        return await self.wait_slaves(timeout, check_ready=check_ready)

    async def spawn_nodes(self, spawn_cmd, ports=None, **ssh_kwargs):
        """An alias for :meth:`creamas.ds.DistributedEnvironment.spawn_slaves`.
        """
        return await self.spawn_slaves(spawn_cmd, ports=ports, **ssh_kwargs)

    async def spawn_slaves(self, spawn_cmd, ports=None, **ssh_kwargs):
        """Spawn multi-environments on the nodes through SSH-connections.

        :param spawn_cmd:
            str or list, command(s) used to spawn the environment on each node.
            If *list*, it must contain one command for each node in
            :attr:`nodes`. If *str*, the same command is used for each node.

        :param ports:
            Optional. If not ``None``, must be a mapping from nodes
            (``(server, port)``-tuples) to ports which are used for the spawned
            multi-environments' master manager environments. If ``None``, then
            the same port is used to derive the master manager addresses as was
            used to initialize this distributed environment's managing
            environment (port in :attr:`addr`).

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
        """
        pool = multiprocessing.Pool(len(self.nodes))
        rets = []
        for i, node in enumerate(self.nodes):
            server, server_port = node
            port = ports[node] if ports is not None else self.port
            mgr_addr = "tcp://{}:{}/0".format(server, port)
            self._manager_addrs.append(mgr_addr)
            if type(spawn_cmd) in [list, tuple]:
                cmd = spawn_cmd[i]
            else:
                cmd = spawn_cmd
            args = [server, cmd]
            ssh_kwargs_cp = ssh_kwargs.copy()
            ssh_kwargs_cp['port'] = server_port
            ret = pool.apply_async(ssh_exec_in_new_loop,
                                   args=args,
                                   kwds=ssh_kwargs_cp,
                                   error_callback=logger.warning)
            rets.append(ret)
        self._pool = pool
        self._r = rets

    async def prepare_nodes(self, *args, **kwargs):
        """Prepare nodes (and slave environments and agents) so that they are
        ready. Should be called after :meth:`wait_nodes`.

        .. note::
            Override in the subclass for the intended functionality.
        """
        raise NotImplementedError()

    def get_slave_managers(self, as_coro=False):
        """Return all slave environment manager addresses.

        :param bool as_coro:
            If ``True`` returns awaitable coroutine, otherwise runs the calls
            to the slave managers asynchronously in the event loop.

        This method returns the addresses of the true slave environment
        managers, i.e. managers derived from :class:`~creamas.mp.EnvManager`,
        not multi-environment managers. For example, if this node environment
        has two nodes with four slave environments in each, then this method
        returns 8 addresses.
        """
        async def slave_task(addr):
            r_manager = await self.env.connect(addr)
            return await r_manager.get_slave_managers()

        tasks = create_tasks(slave_task, self.addrs)
        return run_or_coro(tasks, as_coro)
