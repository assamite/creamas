'''
.. py:module:: ds
    :platform: Unix

The module holds a base implementation, :py:class:`DistributedEnvironment`,
for simulations and environments where the resources span over multiple nodes
on computing clusters or other distributed systems.
'''
import asyncio
import logging
import multiprocessing
import time
import traceback

import aiomas
import asyncssh
from creamas import Environment


async def ssh_exec(server, cmd, logger=None):
    '''Execute a command on a given server using asynchronous SSH-connection.

    The method does not propagate exceptions raised during the SSH-connection,
    instead they are logged by *logger* as errors. The method will exit after
    the first exception is raised.

    :param str server: Address of the server
    :param str cmd: Command to be executed
    :param logger:
        Optional, logger for errors during the command execution.
    '''
    if logger is not None:
        logger.debug("Executing cmd='{}' on {}".format(cmd, server))
    ret = None
    try:
        # Setting known_hosts to None is an evil to do, but in this exercise we
        # do not care about it.
        conn = await asyncssh.connect(server, known_hosts=None)
        ret = await conn.run(cmd)
        conn.close()
    except:
        if logger is not None:
            logger.error("Error while executing cmd='{}' on server={}\n{}"
                         .format(cmd, server, traceback.format_exc()))
        return ret
    return ret


def ssh_exec_in_new_loop(server, cmd, logger=None):
    '''Same as :func:`ssh_exec` but creates a new event loop and executes
    :func:`ssh_exec` in that event loop.
    '''
    task = ssh_exec(server, cmd, logger)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(task)


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

        This simulation does not hold manager on its own by default, but it is
        easy to create one on your own, if you need the node manager's to be
        able to communicate back to this simulation.
        '''
        return self._env

    @property
    def manager_addrs(self):
        '''Addresses of node managers.

        These addresses are derived from *nodes* and *port* parameters
        given at the initialization time, and are used to communicate tasks
        (trigger agents) to the nodes. Each manager is assumed to be the
        first agent in its own manager environment.
        '''
        return self._manager_addrs

    async def wait_nodes(self, timeout):
        '''Wait until all nodes are ready or timeout expires. Should be called
        after :meth:`spawn_nodes`.

        Node is assumed ready when its managers :py:meth:`is_ready`-method
        returns True.

        :param int timeout:
            Timeout (in seconds) after which the method will return even though
            all the nodes are not ready yet.
        '''
        self.logger.info("Waiting for nodes to become ready...")
        t = time.time()
        online = []
        while len(online) < len(self.manager_addrs):
            if time.time() - t > timeout:
                self.logger.info("Timeout while waiting for the nodes to "
                                 "become online.")
                return False
            for addr in self.manager_addrs:
                if addr not in online:
                    try:
                        r_manager = await self.env.connect(addr, timeout=1)
                        ready = await r_manager.is_ready()
                        if ready:
                            online.append(addr)
                            self.logger.info("Node {}/{} ready: {}"
                                             .format(len(online),
                                                     len(self.manager_addrs),
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

    def spawn_nodes(self, spawn_cmd):
        '''Spawn all multi-environments on the nodes.

        :param int spawn_cmd:
            str or list, command(s) used to spawn the environment on each node.
            If list, the parameter must contain one command for each node in
            *nodes*, if str the same command is used for each node.

        .. warning::
            The spawning process of nodes assumes that in each node the manager
            environment of the multi-environment is initialized in the port
            given by the parameter *menv_port* at the object's initialization
            time.
        '''
        pool = multiprocessing.Pool(len(self.nodes))
        rets = []
        for i, node in enumerate(self.nodes):
            if type(spawn_cmd) in [list, tuple]:
                cmd = spawn_cmd[i]
            else:
                cmd = spawn_cmd
            args = [node, cmd, self.logger]
            ret = pool.apply_async(ssh_exec_in_new_loop, args=args)
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

    async def _trigger_node(self, addr):
        '''Trigger all agents in a node managed by the agent in
        *addr* to act.
        '''
        r_manager = await self.env.connect(addr)
        ret = await r_manager.trigger_all()
        return ret

    async def trigger_all(self):
        '''Trigger all agents in all the nodes to act asynchronously.

        This method makes a connection to each manager in *manager_addrs*
        and asynchronously executes :meth:`trigger_all` in all of them.

        .. seealso::

            :py:meth:`creamas.core.environment.Environment.trigger_all`,
            :py:meth:`creamas.mp.MultiEnvironment.trigger_all`,
            :py:meth:`creamas.mp.MultiEnvManager.trigger_all`
        '''
        tasks = []
        for addr in self.manager_addrs:
            task = asyncio.ensure_future(self._trigger_node(addr))
            tasks.append(task)
        ret = await asyncio.gather(*tasks)
        return ret

    async def stop_nodes(self, timeout=1):
        '''Stop all the nodes by sending a stop-message to their managers.

        :param int timeout:
            Timeout for connecting to each manager. If a connection can not
            be made before the timeout expires, the resulting error for that
            particular manager is logged, but the stopping of other managers
            is not halted.
        '''
        for addr in self.manager_addrs:
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
