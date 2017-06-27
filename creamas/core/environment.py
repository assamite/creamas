'''
.. py:module:: environment

This module holds ``Enviroment``-class, an universe where the agents live.
Environment holds methods for inter-agent communication and some utilities that
are usually needed when implementing creative multi-agent systems.

All implementations should subclass ``Environment`` in order to provide basic
functionality for the system to operate.

Environments are used by defining their address at the instantation time, and
adding agents to their container.
'''
import asyncio

import logging
from random import choice, shuffle

from aiomas import Container

from creamas.logging import ObjectLogger
from creamas.util import run_or_coro


__all__ = ['Environment']


class Environment(Container):
    '''Base environment class inherited from :py:class:`aiomas.Container`.
    '''
    def __init__(self, base_url, clock, connect_kwargs):
        super().__init__(base_url, clock, connect_kwargs)
        self._age = 0
        self._logger = None
        self._log_folder = None
        self._artifacts = []
        self._candidates = []
        self._name = base_url

        # Try setting the process name to easily recognize the spawned
        # environments with 'ps -x' or 'top'
        try:
            import setproctitle as spt
            spt.setproctitle('Creamas: {}'.format(str(self)))
        except:
            pass

    @property
    def name(self):
        '''Name of the environment.'''
        return self._name

    @property
    def artifacts(self):
        '''Published artifacts for all agents.'''
        return self._artifacts

    @property
    def age(self):
        '''Age of the environment.
        '''
        return self._age

    @age.setter
    def age(self, a):
        self._age = a

    @property
    def logger(self):
        '''Logger for the environment.
        '''
        return self._logger

    @property
    def log_folder(self):
        '''Logging folder for the environment. If set, will create
        py:class:`creamas.logging.ObjectLogger` for that folder.
        '''
        return self._log_folder

    @log_folder.setter
    def log_folder(self, _log_folder):
        assert(type(_log_folder) is str)
        self._log_folder = _log_folder
        self._logger = ObjectLogger(self, _log_folder, add_name=True,
                                    init=True)

    def get_agents(self, addr=True, agent_cls=None, include_manager=False):
        '''Get agents in the environment.

        :param bool addr: If ``True``, returns only addresses of the agents.
        :param agent_cls:
            Optional, if specified returns only agents belonging to that
            particular class.

        :param bool include_manager:
            If `True``` includes the environment's manager, i.e. the agent in
            the address ``tcp://environment-host:port/0``, to the returned
            list if the environment has attribute :attr:`manager`. If
            environment does not have :attr:`manager`, then the parameter does
            nothing.

        :returns: A list of agents in the environment.
        :rtype: list

        .. note::
            By design, manager agents are excluded from the returned lists of
            agents by default.
        '''
        agents = list(self.agents.dict.values())
        if hasattr(self, 'manager') and self.manager is not None:
            if not include_manager:
                agents = [a for a in agents if a.addr.rsplit('/', 1)[1] != '0']
        if agent_cls is not None:
            agents = [a for a in agents if type(a) is agent_cls]
        if addr:
            agents = [agent.addr for agent in agents]
        return agents

    async def trigger_act(self, *args, addr=None, agent=None, **kwargs):
        '''Trigger agent to act.

        If *agent* is None, then looks the agent by the address.

        :raises ValueError: if both *agent* and *addr* are None.
        '''
        if agent is None and addr is None:
            raise TypeError("Either addr or agent has to be defined.")
        if agent is None:
            for a in self.get_agents(addr=False):
                if addr == a.addr:
                    agent = a
        self._log(logging.DEBUG, "Triggering agent in {}".format(agent.addr))
        ret = await agent.act(*args, **kwargs)
        return ret

    async def trigger_all(self, *args, **kwargs):
        '''Trigger all agents in the environment to act asynchronously.

        :returns: A list of agents' :meth:`act` return values.

        Given arguments and keyword arguments are passed down to each agent's
        :meth:`creamas.core.agent.CreativeAgent.act`.

        .. note::

            By design, the environment's manager agent, i.e. if the environment
            has :attr:`manager`, is excluded from acting.
        '''
        tasks = []
        for a in self.get_agents(addr=False, include_manager=False):
            task = asyncio.ensure_future(self.trigger_act
                                         (*args, agent=a, **kwargs))
            tasks.append(task)
        rets = await asyncio.gather(*tasks)
        return rets

    def is_ready(self):
        '''Check if the environment is fully initialized.

        The function is mainly used by the multiprocessing environment managers
        and distributed environments to ensure that the environment has been
        correctly initialized before any other preparations are done for the
        environments or the simulation is started.

        Override the function in the subclasses which need more time consuming
        initialization routines. The function should return True when the
        environment is ready be used in a simulation, or when any
        cross-environment initialization routines can be run. That is, the
        environment is inherently in a coherent state, and can execute orders
        from managers or simulations.

        :rtype: bool
        :returns: This basic implementation returns always True.
        '''
        return True

    def create_random_connections(self, n=5):
        '''Create random connections for all agents in the environment.

        :param int n: the number of connections for each agent

        Existing agent connections that would be created by chance are not
        doubled in the agent's :attr:`connections`, but count towards
        connections created.
        '''
        if type(n) != int:
            raise TypeError("Argument 'n' must be of type int.")
        if n <= 0:
            raise ValueError("Argument 'n' must be greater than zero.")
        for a in self.get_agents(addr=False):
            others = self.get_agents(addr=False)[:]
            others.remove(a)
            shuffle(others)
            for r_agent in others[:n]:
                a.add_connection(r_agent)

    def create_connections(self, connection_map):
        '''Create agent connections from a given connection map.

        :param dict connection_map:
            A map of connections to be created. Dictionary where keys are
            agent addresses and values are lists of (addr, attitude)-tuples
            suitable for
            :meth:`~creamas.core.agent.CreativeAgent.add_connections`.

        Only connections for agents in this environment are made.
        '''
        agents = self.get_agents(addr=False)
        rets = []
        for a in agents:
            if a.addr in connection_map:
                r = a.add_connections(connection_map[a.addr])
                rets.append(r)
        return rets

    def get_connections(self, data=True):
        """Return connections from all the agents in the environment.

        :param bool data:
            If ``True`` return also the dictionary associated with each
            connection

        :returns:
            A list of ``(addr, connections)``-tuples, where ``connections`` is
            a list of addresses agent in ``addr`` is connected to. If
            ``data`` parameter is ``True``, then the ``connections``
            list contains tuples of ``(nb_addr, data)``-pairs , where ``data``
            is a dictionary.

        :rtype: dict

        .. note::

            By design, potential manager agent is excluded from the returned
            list.
        """
        connections = []
        for a in self.get_agents(addr=False):
            c = (a.addr, a.get_connections(data=data))
            connections.append(c)
        return connections

    def clear_connections(self):
        """Clear all connections from the agents in the environment.
        """
        for a in self.get_agents(addr=False):
            a.clear_connections()

    def get_random_agent(self, agent):
        '''Return random agent that is not the same as agent given as
        parameter.

        :param agent: Agent that is not wanted to return
        :type agent: :py:class:`~creamas.core.agent.CreativeAgent`
        :returns: random, non-connected, agent from the environment
        :rtype: :py:class:`~creamas.core.agent.CreativeAgent`
        '''
        r_agent = choice(self.get_agents(addr=False))
        while r_agent.addr == agent.addr:
            r_agent = choice(self.get_agents(addr=False))
        return r_agent

    def add_artifact(self, artifact):
        '''Add artifact with given framing to the environment.

        :param object artifact: Artifact to be added.
        '''
        artifact.env_time = self.age
        self.artifacts.append(artifact)
        self._log(logging.DEBUG, "ARTIFACTS appended: '{}', length={}"
                  .format(artifact, len(self.artifacts)))

    def add_artifacts(self, artifacts):
        '''Add artifacts to :attr:`artifacts`.

        :param artifacts:
            list of :py:class:`~creamas.core.artifact.Artifact` objects
        '''
        for artifact in artifacts:
            self.add_artifact(artifact)

    async def get_artifacts(self, agent=None):
        '''Return artifacts published to the environment.

        :param agent:
            If not ``None``, then returns only artifacts created by the agent.

        :returns: All artifacts published (by the agent).
        :rtype: list

        If environment has a :attr:`manager` agent, e.g. it is a slave
        environment in a :class:`~creamas.mp.MultiEnvironment`, then the
        manager's :meth:`~creamas.mp.EnvManager.get_artifacts` is called.
        '''
        # TODO: Figure better way for this
        if hasattr(self, 'manager') and self.manager is not None:
            artifacts = await self.manager.get_artifacts()
        else:
            artifacts = self.artifacts
        if agent is not None:
            artifacts = [a for a in artifacts if agent.name == a.creator]
        return artifacts

    def _log(self, level, msg):
        if self.logger is not None:
            self.logger.log(level, msg)

    def save_info(self, folder, *args, **kwargs):
        '''Save information accumulated during the environments lifetime.

        Called from :py:meth:`~creamas.core.Environment.destroy`. Override in
        subclass.

        :param str folder: root folder to save information
        '''
        pass

    def destroy(self, folder=None, as_coro=False):
        '''Destroy the environment.

        Does the following:

        1. calls :py:meth:`~creamas.core.Environment.save_info`
        2. for each agent: calls :py:meth:`close`
        3. Shuts down its RPC-service.
        '''
        async def _destroy(folder):
            ret = self.save_info(folder)
            for a in self.get_agents(addr=False):
                a.close(folder=folder)
            await self.shutdown(as_coro=True)
            return ret

        return run_or_coro(_destroy(folder), as_coro)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.name)
