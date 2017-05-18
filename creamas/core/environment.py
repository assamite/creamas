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
import operator
from collections import Counter
from random import choice, shuffle

from aiomas import Container

from creamas.logging import ObjectLogger


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
        self._name = 'env@{}'.format(base_url)

        # Try setting the process name to easily recognize the spawned
        # environments with 'ps -x' or 'top'
        try:
            import setproctitle as spt
            spt.setproctitle('Creamas: {}({})'.format(type(self), base_url))
        except:
            pass

    @property
    def name(self):
        '''Name of the environment.'''
        return self._name

    @property
    def age(self):
        '''Age of the environment.'''
        return self._age

    @age.setter
    def age(self, _age):
        self._age = _age

    @property
    def artifacts(self):
        '''Published artifacts for all agents.'''
        return self._artifacts

    @property
    def candidates(self):
        '''Current artifact candidates, subject to e.g. agents voting to
        determine which candidate(s) are added to **artifacts**.
        '''
        return self._candidates

    @property
    def logger(self):
        '''Logger for the environment.
        '''
        return self._logger

    @property
    def log_folder(self):
        '''Logging folder for the environment. If set, will create
        py:class::`creamas.logging.ObjectLogger` for that folder.
        '''
        return self._log_folder

    @log_folder.setter
    def log_folder(self, _log_folder):
        assert(type(_log_folder) is str)
        self._log_folder = _log_folder
        self._logger = ObjectLogger(self, _log_folder, add_name=True,
                                    init=True)

    def get_agents(self, address=True, agent_cls=None, exclude_manager=False):
        '''Get agents in the environment.

        :param bool address: If true, returns only addresses of the agents.
        :param agent_cls:
            Optional, if specified returns only agents belonging to that
            particular class.

        :param bool exclude_manager:
            If True, excludes the environment's manager, i.e. the agent in the
            address ``tcp://environment-host:port/0``, from the returned
            list.

        :returns: A list of agents in the environment.
        :rtype: list
        '''
        agents = list(self.agents.dict.values())
        if exclude_manager:
            agents = [a for a in agents if a.addr.rsplit('/', 1)[1] != '0']
        if agent_cls is not None:
            agents = [a for a in agents if type(a) is agent_cls]
        if address:
            agents = [agent.addr for agent in agents]
        return agents

    async def trigger_act(self, addr=None, agent=None):
        '''Trigger agent to act.

        If *agent* is None, then looks the agent by the address.

        :raises ValueError: if both *agent* and *addr* are None.
        '''
        if agent is None and addr is None:
            raise ValueError("Either addr or agent has to be defined.")
        if agent is None:
            for a in self.get_agents(address=False):
                if addr == a.addr:
                    agent = a
        self._log(logging.DEBUG, "Triggering agent in {}".format(agent.addr))
        await agent.get_older()
        ret = await agent.act()
        return ret

    async def trigger_all(self, exclude_manager=False):
        '''Trigger all agents in the environment to act asynchronously.

        :param bool exclude_manager:
            If True, excludes the first agent (i.e. the manager agent) in the
            environment from acting.
        '''
        tasks = []
        for a in self.get_agents(address=False):
            if exclude_manager and a.addr.rsplit("/", 1)[1] == '0':
                continue
            else:
                task = asyncio.ensure_future(self.trigger_act(agent=a))
                tasks.append(task)
        rets = await asyncio.gather(*tasks)
        return rets

    def clear_candidates(self):
        '''Remove current candidates from the environment.
        '''
        self._candidates = []

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
        for a in self.get_agents(address=False):
            others = self.get_agents(address=False)[:]
            others.remove(a)
            shuffle(others)
            for r_agent in others[:n]:
                a.add_connection(r_agent)

    def get_random_agent(self, agent):
        '''Return random agent that is not the same as agent given as
        parameter.

        :param agent: Agent that is not wanted to return
        :type agent: :py:class:`~creamas.core.agent.CreativeAgent`
        :returns: random, non-connected, agent from the environment
        :rtype: :py:class:`~creamas.core.agent.CreativeAgent`
        '''
        r_agent = choice(self.get_agents(address=False))
        while r_agent.addr == agent.addr:
            r_agent = choice(self.get_agents(address=False))
        return r_agent

    def add_artifact(self, artifact):
        '''Add artifact with given framing to the environment.

        :param object artifact: Artifact to be added.
        '''
        artifact.env_time = self.age
        self.artifacts.append(artifact)
        self._log(logging.DEBUG, "ARTIFACTS appended: '{}', length={}"
                  .format(artifact, len(self.artifacts)))

    async def get_artifacts(self, agent=None):
        '''Get artifacts published to the environment.

        :param agent:
            If not ``None``, then returns only artifacts created by the agent.

        :returns: All artifacts published (by the agent).
        :rtype: list

        If environment has a :attr:`manager` agent, e.g. it is a slave
        environment in a :class:`~creamas.mp.MultiEnvironment`, then the
        manager's :meth:`~creamas.mp.EnvManager.get_artifacts` is called.
        '''
        if hasattr(self, 'manager'):
            artifacts = await self.manager.get_artifacts()
        else:
            artifacts = self.artifacts
        if agent is not None:
            artifacts = [a for a in artifacts if agent.name == a.creator]
        return artifacts

    def add_candidate(self, artifact):
        '''Add candidate artifact to current candidates.
        '''
        self.candidates.append(artifact)
        self._log(logging.DEBUG, "CANDIDATES appended:'{}'"
                  .format(artifact))

    def validate_candidates(self):
        '''Validate current candidates in the environment by pruning candidates
        that are not validated at least by one agent, i.e. they are vetoed.

        In larger societies this method might be costly, as it calls each
        agents' :meth:`validate`.
        '''
        valid_candidates = set(self.candidates)
        for a in self.get_agents(address=False):
            vc = set(a.validate(self.candidates))
            valid_candidates = valid_candidates.intersection(vc)

        self._candidates = list(valid_candidates)
        self._log(logging.DEBUG,
                  "{} valid candidates after agents used veto."
                  .format(len(self.candidates)))

    def _gather_votes(self):
        votes = []
        for a in self.get_agents(address=False):
            vote = a.vote(candidates=self.candidates)
            votes.append(vote)
        return votes

    def perform_voting(self, method='IRV', accepted=1):
        '''Perform voting to decide the ordering of the current candidates.

        Voting calls each agent's :func:`vote`-method, which might be costly in
        larger societies.

        :param str method:
            Used voting method. One of the following:
            IRV = instant run-off voting,
            mean = best mean vote (requires cardinal ordering for votes),
            best = best singular vote (requires cardinal ordering, returns only
            one candidate),
            least_worst = least worst singular vote,
            random = selects random candidates

        :param int accepted:
            the number of returned candidates

        :returns:
            list of :py:class:`~creamas.core.artifact.Artifact` objects,
            accepted artifacts. Some voting methods, e.g. mean, also return the
            associated scores for each accepted artifact.

        :rype: list
        '''
        if len(self.candidates) == 0:
            self._log(logging.WARNING, "Could not perform voting because "
                      "there are no candidates!")
            return []
        self._log(logging.DEBUG, "Voting from {} candidates with method: {}"
                  .format(len(self.candidates), method))

        votes = self._gather_votes()

        if method == 'IRV':
            ordering = self._vote_IRV(votes)
            best = ordering[:min(accepted, len(ordering))]
        if method == 'best':
            best = [votes[0][0]]
            for v in votes[1:]:
                if v[0][1] > best[0][1]:
                    best = [v[0]]
        if method == 'least_worst':
            best = [votes[0][-1]]
            for v in votes[1:]:
                if v[-1][1] > best[0][1]:
                    best = [v[-1]]
        if method == 'random':
            rcands = list(self.candidates)
            shuffle(rcands)
            rcands = rcands[:min(accepted, len(rcands))]
            best = [(i, 0.0) for i in rcands]
        if method == 'mean':
            best = self._vote_mean(votes, accepted)

        return best

    def add_artifacts(self, artifacts):
        '''Add artifacts to **artifacts**.

        :param artifacts:
            list of :py:class:`~creamas.core.artifact.Artifact` objects
        '''
        for artifact in artifacts:
            self.add_artifact(artifact)

    def _remove_zeros(self, votes, fpl, cl, ranking):
        '''Remove zeros in IRV voting.'''
        for v in votes:
            for r in v:
                if r not in fpl:
                    v.remove(r)
        for c in cl:
            if c not in fpl:
                if c not in ranking:
                    ranking.append((c, 0))

    def _remove_last(self, votes, fpl, cl, ranking):
        '''Remove last candidate in IRV voting.
        '''
        for v in votes:
            for r in v:
                if r == fpl[-1]:
                    v.remove(r)
        for c in cl:
            if c == fpl[-1]:
                if c not in ranking:
                    ranking.append((c, len(ranking) + 1))

    def _vote_IRV(self, votes):
        '''Perform IRV voting based on votes.
        '''
        votes = [[e[0] for e in v] for v in votes]
        f = lambda x: Counter(e[0] for e in x).most_common()
        cl = list(self.candidates)
        ranking = []
        fp = f(votes)
        fpl = [e[0] for e in fp]

        while len(fpl) > 1:
            self._remove_zeros(votes, fpl, cl, ranking)
            self._remove_last(votes, fpl, cl, ranking)
            cl = fpl[:-1]
            fp = f(votes)
            fpl = [e[0] for e in fp]

        ranking.append((fpl[0], len(ranking) + 1))
        ranking = list(reversed(ranking))
        return ranking

    def _vote_mean(self, votes, accepted):
        '''Perform mean voting based on votes.
        '''
        sums = {str(candidate): [] for candidate in self.candidates}
        for vote in votes:
            for v in vote:
                sums[str(v[0])].append(v[1])
        for s in sums:
            sums[s] = sum(sums[s]) / len(sums[s])
        ordering = list(sums.items())
        ordering.sort(key=operator.itemgetter(1), reverse=True)
        best = ordering[:min(accepted, len(ordering))]
        d = []
        for e in best:
            for c in self.candidates:
                if str(c) == e[0]:
                    d.append((c, e[1]))
        return d

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
            for a in self.get_agents(address=False):
                a.close(folder=folder)
            await self.shutdown(as_coro=True)
            return ret

        if as_coro:
            return _destroy(folder)
        else:
            loop = asyncio.get_event_loop()
            ret = loop.run_until_complete(_destroy(folder))
            return ret
