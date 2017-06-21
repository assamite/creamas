"""
.. py:module:: mp
    :platform: Unix

This module contains multiprocessing implementation for
:class:`~creamas.core.environment.Environment`,
:class:`~creamas.mp.MultiEnvironment`.

A :class:`~creamas.mp.MultiEnvironment` holds several
:class:`~creamas.core.environment.Environment` slaves, which are spawned on
their own processes, and uses managers to obtain much of the same functionality
as the single processor environment. See :class:`~creamas.mp.EnvManager` and
:class:`~creamas.mp.MultiEnvManager` for details.

.. warning::
    This functionality is currently largely untested. However, it *seems* to
    work as intended and may be used in
    :class:`~creamas.core.simulation.Simulation`.
"""
import asyncio
import logging
import multiprocessing
import time

import aiomas
from aiomas.agent import _get_base_url

from creamas.core.environment import Environment
from creamas.util import run_or_coro, create_tasks


logger = logging.getLogger(__name__)
TIMEOUT = 5


class EnvManager(aiomas.subproc.Manager):
    """A manager for :class:`~creamas.core.environment.Environment`, subclass
    of :class:`aiomas.subproc.Manager`.

    Managers are used in environments which need to be able to execute
    commands originating from outside sources, e.g. in slave environments
    inside a multiprocessing environment.

    A manager can spawn other agents into its environment, and can execute
    other tasks relevant to the environment. The manager should always be the
    first agent created to the environment.

    .. note::
        You should not need to create managers directly, instead pass the
        desired manager class to an instance of
        :class:`~creamas.mp.MultiEnvironment` at its initialization time.
    """
    def __init__(self, environment):
        super().__init__(environment)
        self._host_manager = None

    @property
    def env(self):
        return self.container

    @aiomas.expose
    def set_host_manager(self, addr):
        """Set host (or master) manager for this manager.

        :param addr:
            Address for the host manager.
        """
        self._host_manager = addr

    @aiomas.expose
    def host_manager(self):
        """Get address of the host manager.
        """
        return self._host_manager

    @aiomas.expose
    async def report(self, msg, timeout=5):
        """Report message to the host manager.
        """
        try:
            host_manager = await self.env.connect(self.host_manager,
                                                  timeout=timeout)
        except:
            raise ConnectionError("Could not reach host manager ({})."
                                  .format(self.host_manager))
        ret = await host_manager.handle(msg)
        return ret

    @aiomas.expose
    def handle(self, msg):
        """Handle message, override in subclass if needed.
        """
        pass

    @aiomas.expose
    def get_agents(self, addr=True, agent_cls=None, as_coro=False):
        """Get agents from the managed environment.

        This is a managing function for the
        :py:meth:`~creamas.environment.Environment.get_agents`. Returned
        agent list excludes the environment's manager agent (this agent) by
        design.
        """
        return self.env.get_agents(addr=addr, agent_cls=agent_cls)

    @aiomas.expose
    def set_log_folder(self, log_folder):
        self.env.log_folder = log_folder

    @aiomas.expose
    def artifacts(self):
        """Return artifacts from the managed environment.
        """
        return self.env.artifacts

    @aiomas.expose
    def create_connections(self, connection_map):
        """Create connections for agents in the environment.

        This is a managing function for
        :meth:`~creamas.core.environment.Environment.create_connections`.
        """
        return self.env.create_connections(connection_map)

    @aiomas.expose
    def get_connections(self, data=False):
        """Get connections from the agents in the environment.

        This is a managing function for
        :meth:`~creamas.core.environment.Environment.get_connections`.
        """
        return self.env.get_connections(data=data)

    @aiomas.expose
    async def get_artifacts(self):
        """Get all artifacts from the host environment.

        :returns: All the artifacts in the environment.
        """
        host_manager = await self.env.connect(self._host_manager,
                                              timeout=TIMEOUT)
        artifacts = await host_manager.get_artifacts()
        return artifacts

    @aiomas.expose
    def close(self, folder=None):
        """Implemented for consistency. This basic implementation does nothing.
        """
        pass

    @aiomas.expose
    async def trigger_all(self, *args, **kwargs):
        """Trigger all agents in the managed environment to act once.

        This is a managing function for
        :meth:`~creamas.core.environment.Environment.trigger_all`.
        """
        return await self.env.trigger_all(*args, **kwargs)

    @aiomas.expose
    async def is_ready(self):
        """Check if the managed environment is ready.

        This is a managing function for
        :py:meth:`~creamas.environment.Environment.is_ready`.
        """
        return self.env.is_ready()

    @aiomas.expose
    async def spawn_n(self, agent_cls, n, *args, **kwargs):
        """Spawn :attr:`n` agents to the managed environment.

        This is a convenience function so that one does not have to repeatedly
        make connections to the environment to spawn multiple agents with the
        same parameters.

        See :meth:`aiomas.subproc.Manager.spawn` for details.
        """
        rets = []
        for _ in range(n):
            ret = await self.spawn(agent_cls, *args, **kwargs)
            rets.append(ret)
        return rets


class MultiEnvManager(aiomas.subproc.Manager):
    """A manager for :class:`~creamas.mp.MultiEnvironment`, subclass of
    :class:`aiomas.subproc.Manager`.

    A Manager can spawn other agents into its slave environments, and can
    execute other tasks relevant to the whole environment. The manager should
    always be the first (and usually only) agent created for the
    multi-environment's managing environment. The actual simulation agents
    should be created to the slave environments, typically using
    multi-environment's or its manager's functionality.

    .. note::
        You should not need to create managers directly, instead pass the
        desired manager class to an instance of
        :class:`~creamas.mp.MultiEnvironment` at its initialization time.
    """
    def __init__(self, environment):
        super().__init__(environment)

    @property
    def env(self):
        return self.container

    @aiomas.expose
    def handle(self, msg):
        """Handle message from a slave manager.

        **This is a dummy method which should be overridden in a subclass.**
        """
        pass

    @aiomas.expose
    async def spawn(self, agent_cls, *args, addr=None, **kwargs):
        """Spawn an agent to the environment.

        This is a managing function for
        :meth:`~creamas.mp.MultiEnvironment.spawn`.

        .. note::

            Since :class:`aiomas.rpc.Proxy` objects do not seem to handle
            (re)serialization, only the address of the spawned agent is
            returned.
        """
        _, addr = await self.menv.spawn(agent_cls, *args, addr=addr, **kwargs)
        return addr

    @aiomas.expose
    async def spawn_n(self, agent_cls, n, *args, addr=None, **kwargs):
        """Same as :meth:`~creamas.mp.MultiEnvManager.spawn`, but spawn
        :attr:`n` agents with same initialization parameters.

        This is a managing function for
        :meth:`~creamas.mp.MultiEnvironment.spawn_n`.

        .. note::

            Since :class:`aiomas.rpc.Proxy` objects do not seem to handle
            (re)serialization, only the addresses of the spawned agents are
            returned.
        """
        ret = await self.menv.spawn_n(agent_cls, n, *args, addr=addr, **kwargs)
        return [r[1] for r in ret]

    @aiomas.expose
    async def get_agents(self, addr=True, agent_cls=None):
        """Get addresses of all agents in all the slave environments.

        This is a managing function for
        :meth:`creamas.mp.MultiEnvironment.get_agents`.

        .. note::

            Since :class:`aiomas.rpc.Proxy` objects do not seem to handle
            (re)serialization, ``addr`` and ``agent_cls`` parameters are
            omitted from the call to underlying multi-environment's
            :meth:`get_agents`.

            If :class:`aiomas.rpc.Proxy` objects from all the agents are
            needed, call each slave environment manager's :meth:`get_agents`
            directly.
        """
        return await self.menv.get_agents(addr=True, agent_cls=None,
                                          as_coro=True)

    @aiomas.expose
    async def create_connections(self, connection_map):
        """Create connections for agents in the multi-environment.

        This is a managing function for
        :meth:`~creamas.mp.MultiEnvironment.create_connections`.
        """
        return await self.menv.create_connections(connection_map, as_coro=True)

    @aiomas.expose
    async def get_connections(self, data=True):
        """Return connections for all the agents in the slave environments.

        This is a managing function for
        :meth:`~creamas.mp.MultiEnvironment.get_connections`.
        """
        return await self.menv.get_connections(data=data, as_coro=True)

    @aiomas.expose
    def close(self, folder=None):
        """Implemented for consistency. This basic implementation does nothing.
        """
        pass

    @aiomas.expose
    async def set_as_host_manager(self, addr, timeout=5):
        """Set the this manager as a host manager for the manager in *addr*.

        This is a managing function for
        :py:meth:`~creamas.mp.MultiEnvironment.set_host_manager`.
        """
        return await self.menv.set_host_manager(addr, timeout=timeout)

    @aiomas.expose
    async def trigger_all(self, *args, **kwargs):
        """Trigger all agents in the managed multi-environment to act.

        This is a managing function for
        :py:meth:`~creamas.mp.MultiEnvironment.trigger_all`.
        """
        return await self.menv.trigger_all(*args, **kwargs)

    @aiomas.expose
    async def is_ready(self):
        """A managing function for
        :py:meth:`~creamas.mp.MultiEnvironment.is_ready`.
        """
        return await self.menv.is_ready()

    @aiomas.expose
    async def get_artifacts(self):
        """Get all the artifacts from the multi-environment.
        """
        return self.menv.artifacts

    @aiomas.expose
    async def get_slave_managers(self):
        """Get addresses of the slave environment managers in this
        multi-environment.
        """
        return self.menv.get_slave_managers()


class MultiEnvironment():
    """Environment for utilizing multiple processes (and cores) on a single
    machine. :class:`MultiEnvironment` is not a subclass of
    :class:`creamas.core.environment.Environment`.

    :py:class:`MultiEnvironment` has a master environment, typically
    containing only a single manager, and a set of slave environments each
    having their own manager and (once spawned) the actual agents.

    Order of usage is::

        import aiomas

        from creamas Environment
        from creamas.mp import EnvManager, MultiEnvironment
        from creamas.util import run

        # Create the multi-environment and the environment used to connect to
        # slave environments
        addr = ('localhost', 5555)
        env_cls = Environment
        env_kwargs = {'codec': aiomas.MsgPack}
        menv = MultiEnvironment(addr, env_cls, **env_kwargs)

        # Define slave environments and their arguments
        slave_addrs = [('localhost', 5556), ('localhost', 5557)]
        slave_env_cls = Environment
        slave_mgr_cls = EnvManager
        n_slaves = 2
        slave_kwargs = [{'codec': aiomas.MsgPack} for _ in range(n_slaves)]

        # Spawn the actual slave environments
        menv.spawn_slaves(slave_addrs, slave_env_cls,
                          slave_mgr_cls, slave_kwargs)

        # Wait that all the slaves are ready, if you need to do some other
        # preparation before environments' return True for is_ready, then
        # change check_ready=False
        run(menv.wait_slaves(10, check_ready=True))

        # Do any additional preparations here, like spawning the agents to
        # slave environments.

        # Trigger all agents to act
        run(menv.trigger_all())

        # Destroy the environment to free the resources
        menv.destroy(as_coro=False)
    """
    def __init__(self, addr, env_cls, mgr_cls=None, name=None,
                 logger=None, **env_kwargs):
        """
        :param addr:
            ``(HOST, PORT)`` address for the master environment.

        :param env_cls:
            Class for the master environment, used to make connections to the
            slave environments. Must be a subclass of
            :py:class:`~creamas.core.environment.Environment`.

        :param mgr_cls:
            Class for the multi-environment's manager.

        :param str name: Name of the environment. Will be shown in logs.

        :param logger:
            Optional. Logger for the master environment.
        """
        self._addr = addr
        self._env = env_cls.create(addr, **env_kwargs)

        if mgr_cls is not None:
            self._manager = mgr_cls(self._env)
            self._manager.menv = self
        else:
            self._manager = None

        self._age = 0
        self._artifacts = []
        self._candidates = []
        self._manager_addrs = []

        if type(name) is str:
            self._name = name
        else:
            self._name = "{}:{}".format(addr[0], addr[1])

        self._logger = logger
        self._pool = None
        self._r = None

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.name)

    @property
    def name(self):
        """The name of the environment.
        """
        return self._name

    @property
    def env(self):
        """The environment hosting the manager of this multi-environment.

        This environment is also used without the manager to connect to the
        slave environment managers and communicate with them.
        """
        return self._env

    def get_agents(self, addr=True, agent_cls=None, as_coro=False):
        """Get agents from the slave environments.

        :param bool addr:
            If ``True``, returns only addresses of the agents, otherwise
            returns a :class:`Proxy` object for each agent.

        :param agent_cls:
            If specified, returns only agents that are members of that
            particular class.

        :param bool as_coro:
            If ``True``, returns a coroutine, otherwise runs the method in
            an event loop.

        :returns:
            A coroutine or list of :class:`Proxy` objects or addresses as
            specified by the input parameters.

        Slave environment managers are excluded from the returned list by
        default. Essentially, this method calls each slave environment
        manager's :meth:`creamas.mp.EnvManager.get_agents` asynchronously.

        .. note::

            Calling each slave environment's manager might be costly in some
            situations. Therefore, it is advisable to store the returned agent
            list if the agent sets in the slave environments are not bound to
            change.
        """
        async def slave_task(mgr_addr, addr=True, agent_cls=None):
            r_manager = await self.env.connect(mgr_addr, timeout=TIMEOUT)
            return await r_manager.get_agents(addr=addr, agent_cls=agent_cls)

        tasks = create_tasks(slave_task, self.addrs, addr, agent_cls)
        return run_or_coro(tasks, as_coro)

    @property
    def addrs(self):
        """Addresses of the slave environment managers.
        """
        return self._manager_addrs

    @property
    def manager(self):
        """This multi-environment's master manager.
        """
        return self._manager

    @property
    def logger(self):
        """Logger for the environment.

        Logger should have at least :meth:`log` method which takes two
        arguments: a log level and a message.
        """
        return self._logger

    @property
    def artifacts(self):
        """Published artifacts for all agents.
        """
        return self._artifacts

    async def connect(self, *args, **kwargs):
        """A shortcut to :meth:`env.connect`.
        """
        return await self.env.connect(*args, **kwargs)

    def check_ready(self):
        """Check if this multi-environment itself is ready.

        Override in subclass if it needs any additional (asynchronous)
        initialization other than spawning its slave environments.

        :rtype: bool
        :returns: This basic implementation returns always True.
        """
        return True

    async def is_ready(self):
        """Check if the multi-environment has been fully initialized.

        This calls each slave environment managers' :py:meth:`is_ready` and
        checks if the multi-environment itself is ready by calling
        :py:meth:`~creamas.mp.MultiEnvironment.check_ready`.

        .. seealso::

            :py:meth:`creamas.core.environment.Environment.is_ready`
        """
        async def slave_task(addr, timeout):
            try:
                r_manager = await self.env.connect(addr, timeout=timeout)
                ready = await r_manager.is_ready()
                if not ready:
                    return False
            except:
                return False
            return True

        if not self.env.is_ready():
            return False
        if not self.check_ready():
            return False
        rets = await create_tasks(slave_task, self.addrs, 0.5)
        if not all(rets):
            return False
        return True

    async def spawn_slaves(self, slave_addrs, slave_env_cls, slave_mgr_cls,
                           slave_kwargs=None):
        """Spawn slave environments.

        :param slave_addrs:
            List of (HOST, PORT) addresses for the slave-environments.

        :param slave_env_cls: Class for the slave environments.

        :param slave_kwargs:
            If not None, must be a list of the same size as *addrs*. Each item
            in the list containing parameter values for one slave environment.

        :param slave_mgr_cls:
            Class of the slave environment managers.
        """
        pool, r = spawn_containers(slave_addrs, env_cls=slave_env_cls,
                                   env_params=slave_kwargs,
                                   mgr_cls=slave_mgr_cls)
        self._pool = pool
        self._r = r
        self._manager_addrs = ["{}{}".format(_get_base_url(a), 0) for
                               a in slave_addrs]

    async def wait_slaves(self, timeout, check_ready=False):
        """Wait until all slaves are online (their managers accept connections)
        or timeout expires.

        :param int timeout:
            Timeout (in seconds) after which the method will return even though
            all the slaves are not online yet.

        :param bool check_ready:
            If ``True`` also checks if all slave environment's are ready.
            A slave environment is assumed to be ready when its manager's
            :meth:`is_ready`-method returns ``True``.

        .. seealso::

            :meth:`creamas.core.environment.Environment.is_ready`,
            :meth:`creamas.mp.EnvManager.is_ready`,
            :meth:`creamas.mp.MultiEnvManager.is_ready`

        """
        status = 'ready' if check_ready else 'online'
        self._log(logging.DEBUG,
                  "Waiting for slaves to become {}...".format(status))
        t = time.monotonic()
        online = []
        while len(online) < len(self.addrs):
            for addr in self.addrs:
                if time.monotonic() - t > timeout:
                    self._log(logging.DEBUG, "Timeout while waiting for the "
                              "slaves to become {}.".format(status))
                    return False
                if addr not in online:
                    try:
                        r_manager = await self.env.connect(addr, timeout)
                        ready = True
                        if check_ready:
                            ready = await r_manager.is_ready()
                        if ready:
                            online.append(addr)
                            self._log(logging.DEBUG, "Slave {}/{} {}: {}"
                                      .format(len(online),
                                              len(self.addrs),
                                              status,
                                              addr))
                    except:
                        pass
            asyncio.sleep(0.5)
        self._log(logging.DEBUG, "All slaves {} in {} seconds!"
                  .format(status, time.monotonic() - t))
        return True

    def _get_log_folders(self, log_folder, addrs):
        if type(log_folder) is str:
            import os
            folders = [os.path.join(log_folder, '_{}'.format(i)) for i in
                       range(len(addrs))]
        else:
            folders = [None for _ in range(len(addrs))]
            return folders

    async def set_host_manager(self, addr, timeout=TIMEOUT):
        """Set this multi-environment's manager as the host manager for
        a manager agent in *addr*
        """
        r_manager = await self.env.connect(addr, timeout=timeout)
        return await r_manager.set_host_manager(self.manager.addr)

    async def set_host_managers(self, timeout=5):
        """Set the master environment's manager as host manager for the slave
        environment managers.

        :param int timeout: Timeout for connecting to the slave managers.

        This enables the slave environment managers to communicate back to the
        master environment. The master environment manager,
        :attr:`~creamas.mp.MultiEnvironment.manager`, must be an instance
        of :class:`~creamas.mp.MultiEnvManager` or its subclass if this method
        is called.
        """
        return await create_tasks(self.set_host_manager, self.addrs, timeout)

    async def trigger_act(self, addr):
        """Trigger agent in :attr:`addr` to act.

        This method is quite inefficient if used repeatedly for a large number
        of agents.

        .. seealso::

            :py:meth:`creamas.mp.MultiEnvironment.trigger_all`
        """
        r_agent = await self.env.connect(addr, timeout=TIMEOUT)
        return await r_agent.act()

    async def trigger_all(self, *args, **kwargs):
        """Trigger all agents in all the slave environments to :meth:`act`
        asynchronously.

        Given arguments and keyword arguments are passed down to each agent's
        :meth:`creamas.core.agent.CreativeAgent.act`.

        .. note::

            By design, the manager agents in each slave environment, i.e.
            :attr:`manager`, are excluded from acting.
        """
        async def slave_task(addr, *args, **kwargs):
            r_manager = await self.env.connect(addr, timeout=TIMEOUT)
            return await r_manager.trigger_all(*args, **kwargs)

        return await create_tasks(slave_task, self.addrs, *args, **kwargs)

    async def _get_smallest_env(self):
        """Get address of the slave environment manager with the smallest
        number of agents.
        """
        async def slave_task(mgr_addr):
            r_manager = await self.env.connect(mgr_addr, timeout=TIMEOUT)
            ret = await r_manager.get_agents(addr=True)
            return mgr_addr, len(ret)

        sizes = await create_tasks(slave_task, self.addrs, flatten=False)
        return sorted(sizes, key=lambda x: x[1])[0][0]

    async def spawn(self, agent_cls, *args, addr=None, **kwargs):
        """Spawn a new agent in a slave environment.

        :param str agent_cls:
            `qualname`` of the agent class.
            That is, the name should be in the form ``pkg.mod:cls``, e.g.
            ``creamas.core.agent:CreativeAgent``.
        :param str addr:
            Optional. Address for the slave enviroment's manager.
            If :attr:`addr` is None, spawns the agent in the slave environment
            with currently smallest number of agents.

        :returns: :class:`aiomas.rpc.Proxy` and address for the created agent.

        The ``*args`` and ``**kwargs`` are passed down to the agent's
        :meth:`__init__`.

        .. note::

            Use :meth:`~creamas.mp.MultiEnvironment.spawn_n` to spawn large
            number of agents with identical initialization parameters.
        """
        if addr is None:
            addr = await self._get_smallest_env()
        r_manager = await self.env.connect(addr)
        return await r_manager.spawn(agent_cls, *args, **kwargs)

    async def spawn_n(self, agent_cls, n, *args, addr=None, **kwargs):
        """Same as :meth:`~creamas.mp.MultiEnvironment.spawn`, but allows
        spawning multiple agents with the same initialization parameters
        simultaneously into **one** slave environment.

        :param str agent_cls:
            ``qualname`` of the agent class. That is, the name should be in the
            form of ``pkg.mod:cls``, e.g. ``creamas.core.agent:CreativeAgent``.
        :param int n: Number of agents to spawn
        :param str addr:
            Optional. Address for the slave enviroment's manager.
            If :attr:`addr` is None, spawns the agents in the slave environment
            with currently smallest number of agents.

        :returns:
            A list of (:class:`aiomas.rpc.Proxy`, address)-tuples for the
            spawned agents.

        The ``*args`` and ``**kwargs`` are passed down to each agent's
        :meth:`__init__`.
        """
        if addr is None:
            addr = await self._get_smallest_env()
        r_manager = await self.env.connect(addr)
        return await r_manager.spawn_n(agent_cls, n, *args, **kwargs)

    def create_connections(self, connection_map, as_coro=False):
        """Create agent connections from the given connection map.

        :param dict connection_map:
            A map of connections to be created. Dictionary where keys are
            agent addresses and values are lists of (addr, data)-tuples
            suitable for
            :meth:`~creamas.core.agent.CreativeAgent.add_connections`.

        :param bool as_coro:
            If ``True`` returns a coroutine, otherwise runs the asynchronous
            calls to the slave environment managers in the event loop.

        Only the connections for the agents that are in the slave environments
        are created.
        """
        async def slave_task(addr, connection_map):
            r_manager = await self.env.connect(addr)
            return await r_manager.create_connections(connection_map)

        tasks = create_tasks(slave_task, self.addrs, connection_map)
        return run_or_coro(tasks, as_coro)

    def get_connections(self, data=True, as_coro=False):
        """Return connections from all the agents in the slave environments.

        :param bool data:
            If ``True``, returns also the data stored for each connection.

        :param bool as_coro:
            If ``True`` returns a coroutine, otherwise runs the asynchronous
            calls to the slave environment managers in the event loop.

        .. seealso::

            :meth:`creamas.core.environment.Environment.get_connections`
        """
        async def slave_task(addr, data):
            r_manager = await self.env.connect(addr)
            return await r_manager.get_connections(data)

        tasks = create_tasks(slave_task, self.addrs, data)
        return run_or_coro(tasks, as_coro)

    def get_slave_managers(self):
        """Get addresses of all slave environment managers.
        """
        return self.addrs

    def add_artifact(self, artifact):
        """Add an artifact to the environment.

        :param object artifact: Artifact to be added.
        """
        artifact.env_time = self.age
        self.artifacts.append(artifact)
        self._log(logging.DEBUG, "ARTIFACTS appended: '{}', length={}"
                  .format(artifact, len(self.artifacts)))

    def add_artifacts(self, artifacts):
        """Add artifacts to :attr:`artifacts`.

        :param artifacts:
            list of :py:class:`~creamas.core.artifact.Artifact` objects
        """
        for artifact in artifacts:
            self.add_artifact(artifact)

    def get_artifacts(self, agent_name=None):
        """Get all artifacts or all artifacts published by a specific agent.

        :param str agent_name:
            Optional. Name of the agent which artifacts are returned.

        :returns: All artifacts or all artifacts published by the agent.
        :rtype: list
        """
        if agent_name is not None:
            return [a for a in self.artifacts if agent_name == a.creator]
        return self.artifacts

    def _log(self, level, msg):
        if self.logger is not None:
            self.logger.log(level, msg)

    def save_info(self, folder, *args, **kwargs):
        """Save information accumulated during the environment's lifetime.

        Called from :py:meth:`~creamas.mp.MultiEnvironment.destroy`. Override
        in subclass.

        :param str folder: root folder to save information
        """
        pass

    async def stop_slaves(self, timeout=1):
        """Stop all the slaves by sending a stop-message to their managers.

        :param int timeout:
            Timeout for connecting to each manager. If a connection can not
            be made before the timeout expires, the resulting error for that
            particular manager is logged, but the stopping of other managers
            is not halted.
        """
        for addr in self.addrs:
            try:
                r_manager = await self.env.connect(addr, timeout=timeout)
                await r_manager.stop()
            except:
                self._log(logging.WARNING, "Could not stop {}".format(addr))

    def destroy(self, folder=None, as_coro=False):
        """Destroy the multiprocessing environment and its slave environments.
        """
        async def _destroy(folder):
            ret = self.save_info(folder)
            await self.stop_slaves()
            # Terminate and join the process pool when we are destroyed.
            # Do not wait for unfinished processed with pool.close(),
            # the slaves should be anyway already stopped.
            if self._pool is not None:
                self._pool.terminate()
                self._pool.join()
            await self._env.shutdown(as_coro=True)
            return ret

        return run_or_coro(_destroy(folder), as_coro)


def spawn_container(addr, env_cls=Environment,
                    mgr_cls=EnvManager, set_seed=True, *args, **kwargs):
    """Spawn a new environment in a given address as a coroutine.

    Arguments and keyword arguments are passed down to the created environment
    at initialization time.

    If `setproctitle <https://pypi.python.org/pypi/setproctitle>`_ is
    installed, this function renames the title of the process to start with
    'creamas' so that the process is easily identifiable, e.g. with
    ``ps -x | grep creamas``.
    """
    # Try setting the process name to easily recognize the spawned
    # environments with 'ps -x' or 'top'
    try:
        import setproctitle as spt
        title = 'creamas: {}({})'.format(env_cls.__class__.__name__,
                                         _get_base_url(addr))
        spt.setproctitle(title)
    except:
        pass

    if set_seed:
        _set_random_seeds()

    # kwargs['codec'] = aiomas.MsgPack
    task = start(addr, env_cls, mgr_cls, *args, **kwargs)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(task)


def spawn_containers(addrs, env_cls=Environment,
                     env_params=None,
                     mgr_cls=EnvManager, *args, **kwargs):
    """Spawn environments in a multiprocessing :class:`multiprocessing.Pool`.

    Arguments and keyword arguments are passed down to the created environments
    at initialization time if *env_params* is None. If *env_params* is not
    None, then it is assumed to contain individual initialization parameters
    for each environment in *addrs*.

    :param addrs:
        List of (HOST, PORT) addresses for the environments.

    :param env_cls:
        Callable for the environments. Must be a subclass of
        :py:class:`~creamas.core.environment.Environment`.

    :param env_params: Initialization parameters for the environments.
    :type env_params: Iterable of same length as *addrs* or None.

    :param mgr_cls:
        Callable for the managers. Must be a subclass of
        :py:class:`~creamas.mp.EnvManager`.s

    :returns:
        The created process pool and the *ApplyAsync* results for the spawned
        environments.
    """
    pool = multiprocessing.Pool(len(addrs))
    kwargs['env_cls'] = env_cls
    kwargs['mgr_cls'] = mgr_cls
    r = []
    for i, addr in enumerate(addrs):
        if env_params is not None:
            k = env_params[i]
            k['env_cls'] = env_cls
            k['mgr_cls'] = mgr_cls
        # Copy kwargs so that we can apply different address to different
        # containers.
        else:
            k = kwargs.copy()
        k['addr'] = addr
        ret = pool.apply_async(spawn_container,
                               args=args,
                               kwds=k,
                               error_callback=logger.warning)
        r.append(ret)
    return pool, r


async def start(addr, env_cls, mgr_cls, *env_args, **env_kwargs):
    """`Coroutine
    <https://docs.python.org/3/library/asyncio-task.html#coroutine>`_ that
    starts an environment with :class:`mgr_cls` manager agent.

    The agent will connect to *addr* ``('host', port)`` and wait for commands
    to spawn new agents within its environment.

    The *env_args* and *env_kwargs* will be passed to :meth:`env_cls.create()`
    factory function.

    This coroutine finishes after manager's :meth:`stop` was called or when
    a :exc:`KeyboardInterrupt` is raised and calls :meth:`env_cls.destroy`
    before it finishes.

    :param addr:
        (HOST, PORT) for the new environment

    :param env_cls:
        Class of the environment, subclass of
        :class:`~creamas.core.environment.Environment`.

    :param mgr_cls:
        Class of the manager agent, subclass of
        :class:`~creamas.mp.EnvManager`.
    """
    env_kwargs.update(as_coro=True)
    log_folder = env_kwargs.get('log_folder', None)
    env = await env_cls.create(addr, *env_args, **env_kwargs)
    try:
        manager = mgr_cls(env)
        env.manager = manager
        await manager.stop_received
    except KeyboardInterrupt:
        logger.info('Execution interrupted by user')
    finally:
        await env.destroy(folder=log_folder, as_coro=True)


def _set_random_seeds():
    """Set new random seeds for the process.
    """
    try:
        import numpy as np
        np.random.seed()
    except:
        pass

    try:
        import scipy as sp
        sp.random.seed()
    except:
        pass

    import random
    random.seed()
