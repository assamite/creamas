'''
.. py:module:: mp
    :platform: Unix

This module contains multiprocessing implementation for
:class:`~creamas.core.environment.Environment`,
:class:`~creamas.mp.MultiEnvironment`.
It uses managers to obtain the same functionality as the single processor
environment. See :class:`~creamas.mp.EnvManager` and
:class:`~creamas.mp.MultiEnvManager` for details.

.. warning::
    This functionality is currently non-tested. However, it *seems* to work
    as intended and may be used in
    :class:`~creamas.core.simulation.Simulation`.
'''
import asyncio
import logging
import multiprocessing
import operator

from collections import Counter
from random import choice, shuffle

import aiomas
from aiomas.agent import _get_base_url

from creamas.logging import ObjectLogger
from creamas.core.environment import Environment


logger = logging.getLogger(__name__)
TIMEOUT = 5

# TODO: Refactor code! To use abstract classes.


class EnvManager(aiomas.subproc.Manager):
    """A single environment manager agent for a child environment running
    inside a multiprocessing environment.

    A Manager can spawn other agents into its environment, and can execute
    other tasks relevant to the environment.

    .. note::
        You should not have need to create managers directly, instead pass the
        desired manager class to an instance of
        :class:`~creamas.mp.MultiEnvironment` at its initialization time.
    """
    @property
    def env(self):
        return self.container

    @aiomas.expose
    def set_host_addr(self, addr):
        '''Set host (or master) manager for this manager.

        :param addr:
            Address for the host manager.
        '''
        self._host_addr = addr

    @aiomas.expose
    def host_addr(self):
        '''Get address of the host manager.
        '''
        return self._host_addr

    @aiomas.expose
    async def report(self, msg):
        '''Report message to the host manager.
        '''
        try:
            host_manager = await self.env.connect(self.host_addr,
                                                  timeout=TIMEOUT)
        except:
            raise ConnectionError("Could not reach host manager ({})."
                                  .format(self._host_addr))
        ret = await host_manager.handle(msg)
        return ret

    @aiomas.expose
    def handle(self, msg):
        '''Handle message, override in subclass if needed.'''
        pass

    @aiomas.expose
    def get_agents(self, address=True, agent_cls=None):
        '''Return addresses of agents belonging to certain class in this
        container. If *agent_cls* is None, returns addresses of all agents
        excluding the manager itself.
        '''
        agents = list(self.env.agents.dict.values())
        agents = [a for a in agents if a.addr.rsplit("/", 1)[1] != "0"]
        if agent_cls is not None:
            agents = [a for a in agents if type(a) is agent_cls]
        if address:
            agents = [a.addr for a in agents]
        return agents

    @aiomas.expose
    def set_log_folder(self, log_folder, addr=None):
        self.container.log_folder = log_folder

    @aiomas.expose
    def stop(self, folder=None):
        ret = self.env.save_info(folder)
        for a in self.get_agents(address=False):
            a.close(folder=folder)
        self.stop_received.set_result(True)
        return ret

    @aiomas.expose
    def act(self):
        '''For consistency. Override in subclass if needed.
        '''
        pass

    @aiomas.expose
    async def get_older(self, addr):
        '''Make agent in *addr* to get older, i.e. advance its internal clock.
        '''
        remote_agent = await self.env.connect(addr, timeout=TIMEOUT)
        ret = await remote_agent.get_older()
        return ret

    @aiomas.expose
    def candidates(self):
        return self.container.candidates

    @aiomas.expose
    def artifacts(self):
        return self.container.artifacts

    @aiomas.expose
    def validate_candidates(self, candidates):
        '''For consistency.
        '''
        return candidates

    @aiomas.expose
    def clear_candidates(self):
        self.container.clear_candidates()

    @aiomas.expose
    def vote(self, candidates):
        cands = candidates
        votes = [(c, 1.0) for c in cands]
        return votes

    @aiomas.expose
    async def add_candidate(self, artifact):
        host_manager = await self.env.connect(self._host_addr)
        host_manager.add_candidate(artifact)

    @aiomas.expose
    async def get_artifacts(self):
        host_manager = await self.env.connect(self._host_addr, timeout=TIMEOUT)
        artifacts = await host_manager.get_artifacts()
        return artifacts

    @aiomas.expose
    def close(self, folder=None):
        pass


class MultiEnvManager(aiomas.subproc.Manager):
    """A multi-environment manager agent for a whole multiprocessing
    environment.

    A Manager can spawn other agents into its child environments, and can
    execute other tasks relevant to the whole environment.

    .. note::
        You should not have need to create managers directly, instead pass the
        desired manager class to an instance of
        :class:`~creamas.mp.MultiEnvironment` at its initialization time.
    """
    @property
    def env(self):
        return self.container

    @aiomas.expose
    def handle(self, msg):
        '''Handle message. Override in subclass if needed.
        '''
        pass

    @aiomas.expose
    async def spawn(self, addr, agent_cls, *agent_args, **agent_kwargs):
        '''Spawn an agent to an environment in given address.
        '''
        remote_manager = await self.env.connect(addr, timeout=TIMEOUT)
        proxy, port = await remote_manager.spawn(agent_cls, *agent_args,
                                                 **agent_kwargs)
        return proxy, port

    @aiomas.expose
    async def get_agents(self, addr, address=True, agent_cls=None,
                         filter_managers=True):
        '''Get agents in the slave manager's environment.

        :param addr: Address of the slave environment's manager
        :param address: Return only the addresses of the agents, not proxies.
        '''
        remote_manager = await self.env.connect(addr, timeout=TIMEOUT)
        agents = await remote_manager.get_agents(address=address,
                                                 agent_cls=agent_cls)
        if filter_managers:
            if address:
                agents = [a for a in agents if a.rsplit("/", 1)[1] != "0"]
            else:
                agents = [a for a in agents if a.addr.rsplit("/", 1)[1] != "0"]
        return agents

    @aiomas.expose
    async def kill(self, addr, folder=None):
        '''Send stop command to the manager agent in a given address. This will
        shutdown the manager's environment.
        '''
        remote_manager = await self.env.connect(addr, timeout=TIMEOUT)
        ret = await remote_manager.stop(folder)
        return ret

    @aiomas.expose
    async def act(self, addr=None):
        '''Trigger agent in given *addr* to act.
        '''
        if addr is not None:
            remote_agent = await self.env.connect(addr, timeout=TIMEOUT)
            ret = await remote_agent.act()
            return ret
        else:
            pass

    @aiomas.expose
    def close(self, folder=None):
        pass

    @aiomas.expose
    async def set_host_manager(self, addr):
        '''Set this manager as host manager to the manager in *addr*.
        '''
        remote_manager = await self.env.connect(addr, timeout=TIMEOUT)
        ret = remote_manager.set_host_addr(self.addr)
        return ret

    async def get_older(self, addr):
        '''Make agent in *addr* to get older, i.e. advance its internal clock.
        '''
        remote_agent = await self.env.connect(addr, timeout=TIMEOUT)
        ret = await remote_agent.get_older()
        return ret

    async def get_candidates(self, addr):
        '''Get candidates from the environment manager in *addr* manages.
        '''
        remote_manager = await self.env.connect(addr)
        candidates = await remote_manager.candidates()
        return candidates

    @aiomas.expose
    def add_candidate(self, artifact):
        '''Add candidate artifact into the candidates.
        '''
        self.menv.add_candidate(artifact)

    @aiomas.expose
    async def get_votes(self, addr, candidates):
        remote_agent = await self.env.connect(addr, timeout=TIMEOUT)
        votes = await remote_agent.vote(candidates)
        return votes

    @aiomas.expose
    async def clear_candidates(self, addr):
        remote_manager = await self.env.connect(addr, timeout=TIMEOUT)
        ret = await remote_manager.clear_candidates()
        return ret

    @aiomas.expose
    async def get_artifacts(self):
        return self.env.artifacts

    @aiomas.expose
    async def destroy(self):
        return self.env.destroy()


class MultiEnvironment():
    '''Environment for utilizing multiple processes.
    '''
    def __init__(self, addr, env_cls=None, mgr_cls=None,
                 slave_addrs=[], slave_env_cls=None,
                 slave_params=None,
                 slave_mgr_cls=None, name=None, clock=None,
                 extra_ser=None, log_folder=None, log_level=logging.INFO):
        '''
        :param addr: (HOST, PORT) address from the manager environment.

        :param env_cls:
            Class for the environments. Must be a subclass of
            :py:class::`~creamas.core.environment.Environment`.

        :param addrs:
            List of (HOST, PORT) addresses for the slave-environments.

        :param str name: Name of the environment. Will be shown in logs.
        '''
        pool, r = spawn_containers(slave_addrs, env_cls=slave_env_cls,
                                   env_params=slave_params,
                                   mgr_cls=slave_mgr_cls, codec=aiomas.MsgPack,
                                   clock=clock, extra_serializers=extra_ser)
        self._pool = pool
        self._r = r
        self._manager_addrs = ["{}{}".format(_get_base_url(a), 0) for
                               a in slave_addrs]

        self._age = 0
        self._artifacts = []
        self._candidates = []
        self._name = name if type(name) is str else 'multi-env'
        self._consistent = False
        self._agents = []

        if type(log_folder) is str:
            self.logger = ObjectLogger(self, log_folder, add_name=True,
                                       init=True, log_level=log_level)
        else:
            self.logger = None

        self._env = env_cls.create(addr, codec=aiomas.MsgPack, clock=clock,
                                   extra_serializers=extra_ser)
        self._manager = mgr_cls(self._env)
        self._manager.menv = self
        r = aiomas.run(until=self._set_host_managers())

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

    def get_agents(self, address=True, filter_managers=True):
        '''Get agents associated with the environment and its child
        environments.

        Essentially calls :py:meth:`get_agents` for each of the child
        environment managers.

        :param bool address:
            If *True*, returns only addresses of the agents, otherwise returns
            a :class:`Proxy` object for each agent.

        :param bool filter_managers:
            If *True* filters manager agents from the returned list.

        :returns:
            List of :py:class:`Proxy` objects or addresses as specified by the
            input parameters.
        '''
        if self._consistent is False:
            ags = []
            tasks = []
            for addr in self._manager_addrs:
                tasks.append(asyncio.ensure_future
                             (self.manager.get_agents
                              (addr, address=True,
                               filter_managers=filter_managers)))
            aa = aiomas.run(until=asyncio.gather(*tasks))
            for a in aa:
                ags.extend(a)
            self._agents = ags
            self._consistent = True
            return ags
        else:
            return self._agents

    @property
    def addrs(self):
        '''Addresses of the slave environment managers.
        '''
        return self._manager_addrs

    @property
    def manager(self):
        '''This multi-environment's manager.
        '''
        return self._manager

    @property
    def artifacts(self):
        '''Published artifacts for all get_agents.'''
        return self._artifacts

    @property
    def candidates(self):
        '''Current artifact candidates, subject to e.g. agents voting to
        determine which candidate(s) are added to **artifacts**.
        '''
        return self._candidates

    def _get_log_folders(self, log_folder, addrs):
        if type(log_folder) is str:
            import os
            folders = [os.path.join(log_folder, '_{}'.format(i)) for i in
                       range(len(addrs))]
        else:
            folders = [None for _ in range(len(addrs))]
            return folders

    async def _set_host_managers(self):
        for addr in self.addrs:
            await self._manager.set_host_manager(addr)

    async def trigger_act(self, addr):
        '''Trigger agent in addr to act.
        '''
        if addr.rsplit("/", 1)[1] == '0':
            self._log(logging.DEBUG, "Skipping manager in {} from acting."
                      .format(addr))
            return
        self._log(logging.DEBUG, "Triggering agent in {} to act".format(addr))
        await self._manager.get_older(addr)
        ret = await self._manager.act(addr)
        return ret

    async def trigger_all(self):
        '''Trigger all agents in all the child environments to act.'''
        rets = []
        tasks = []
        for addr in self.get_agents():
            task = asyncio.ensure_future(self.trigger_act(addr))
            tasks.append(task)
        rr = aiomas.run(until=asyncio.gather(*tasks))
        for r in rr:
            rets.append(r)
        return rets

    def random_addr(self):
        '''Get random env.
        '''
        return choice(self._manager_addrs)

    async def _get_smallest_env(self):
        '''Get address for the environment with smallest amount of agents.
        '''
        agents = await self._manager.get_agents(self._manager_addrs[0])
        ns = len(agents)
        saddr = self._manager_addrs[0]
        for i, addr in enumerate(self._manager_addrs[1:]):
            agents = await self._manager.get_agents(addr)
            n = len(agents)
            if n < ns:
                ns = n
                saddr = self._manager_addrs[i + 1]
        return saddr

    async def spawn(self, agent_cls, *args, addr=None, **kwargs):
        '''Spawn a new agent.

        If *addr* is None, spawns the agent in the slave environment with
        currently smallest number of agents.

        :param agent_cls: Subclass of :py:class:`~CreativeAgent`
        :param addr: Address for the slave enviroment's manager, if specified.
        :returns: Proxy and address for the created agent.
        '''
        if addr is None:
            addr = await self._get_smallest_env()
        proxy, r_addr = await self._manager.spawn(addr, agent_cls, *args,
                                                  **kwargs)
        self._consistent = False
        return proxy, r_addr

    def clear_candidates(self):
        '''Remove current candidates from the environment.
        '''
        self._candidates = []
        tasks = []
        for addr in self._manager_addrs:
            tasks.append(asyncio.ensure_future(self._clear_candidates(addr)))
        aiomas.run(until=asyncio.gather(*tasks))

    async def _clear_candidates(self, manager_addr):
        ret = await self.manager.clear_candidates(manager_addr)
        return ret

    async def create_connection(self, addr, conn):
        remote_agent = await self._env.connect(addr, timeout=TIMEOUT)
        remote_agent.add_connection(conn)

    def create_initial_connections(self, n=5):
        '''Create random initial connections for all agents.

        :param int n: the number of connections for each agent
        '''
        assert type(n) == int
        assert n > 0
        for addr in self.get_agents():
            others = self.get_agents()[:]
            others.remove(addr)
            shuffle(others)
            for r_agent in others[:n]:
                aiomas.run(until=self.create_connection(addr, r_agent))

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
            r_agent = choice(self.get_agents)
        return r_agent

    def add_artifact(self, artifact):
        '''Add artifact with given framing to the environment.

        :param object artifact: Artifact to be added.
        '''
        artifact.env_time = self.age
        self.artifacts.append(artifact)
        self._log(logging.INFO, "ARTIFACTS appended: '{}', length={}"
                  .format(artifact, len(self.artifacts)))

    def get_artifacts(self, agent):
        '''Get artifacts published by certain agent.

        :returns: All artifacts published by the agent.
        :rtype: list
        '''
        ret = [a for a in self.artifacts if agent.name == a.creator]
        return ret

    def add_candidate(self, artifact):
        '''Add candidate artifact to current candidates.
        '''
        self.candidates.append(artifact)
        self._log(logging.DEBUG, "CANDIDATES appended:'{}'"
                  .format(artifact))

    async def _validate_candidates(self, addr):
        remote_manager = await self._manager.container.connect(addr)
        vc = remote_manager.validate_candidates(self.candidates)
        return vc

    def validate_candidates(self):
        '''Validate current candidates in the environment by pruning candidates
        that are not validated at least by one agent, i.e. they are vetoed.

        In larger societies this method might be costly, as it calls each
        get_agents' ``validate_candidates``-method.
        '''
        valid_candidates = set(self.candidates)
        tasks = []
        for a in self._manager_addrs:
            tasks.append(self._validate_candidates(a))
        ret = aiomas.run(until=asyncio.gather(*tasks))
        for r in ret:
            result = yield from r
            vc = set(result)
            valid_candidates = valid_candidates.intersection(vc)

        self._candidates = list(valid_candidates)
        self._log(logging.INFO,
                  "{} valid candidates after get_agents used veto."
                  .format(len(self.candidates)))

    async def get_vote(self, addr, candidates):
        votes = await self._manager.get_votes(addr, candidates)
        return votes

    def _gather_votes(self):
        tasks = []
        for addr in self.get_agents(address=True):
            if addr.rsplit("/", 1)[1] == 0:
                # Skip managers.
                pass
            else:
                t = asyncio.ensure_future(self.get_vote(addr, self.candidates))
                tasks.append(t)

        votes = aiomas.run(until=asyncio.gather(*tasks))
        return votes

    def perform_voting(self, method='IRV', accepted=1):
        '''Perform voting to decide the ordering of the current candidates.

        Voting calls each agent's ``vote``-method, which might be costly in
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
            list of :py:class`~creamas.core.artifact.Artifact`s, accepted
            artifacts

        :rype: list
        '''
        if len(self.candidates) == 0:
            self._log(logging.WARNING, "Could not perform voting because "
                      "there are no candidates!")
            return []
        self._log(logging.INFO, "Voting from {} candidates with method: {}"
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

    async def _destroy_childs(self, folder):
        '''Shutdown the child environments.
        '''
        rets = []
        for addr in self.addrs:
            ret = await self._manager.kill(addr, folder)
            rets.append(ret)
        return rets

    def destroy(self, folder=None, as_coro=False):
        '''Destroy the multiprocessing environment and its slave environments.
        '''
        async def _destroy(folder):
            ret = [self.save_info(folder)]
            rets = await self._destroy_childs(folder)
            rets = ret + rets
            # Close and join the process pool nicely.
            self._pool.close()
            self._pool.terminate()
            self._pool.join()
            await self._env.shutdown(as_coro=True)
            return rets

        if as_coro:
            return _destroy(folder)
        else:
            ret = aiomas.run(until=_destroy(folder))
            return ret


def spawn_container(addr=('localhost', 5555), env_cls=Environment,
                    mgr_cls=EnvManager, set_seed=True, *args, **kwargs):
    '''Spawn a new environment in a given address as a coroutine.

    Arguments and keyword arguments are passed down to the created environment
    at initialization time.

    If 'setproctitle' is installed, this function renames the title of the
    process to start with Creamas so that the process is easily identifiable,
    e.g. with 'ps -x | grep Creamas'.
    '''
    # Try setting the process name to easily recognize the spawned
    # environments with 'ps -x' or 'top'
    try:
        import setproctitle as spt
        spt.setproctitle('Creamas: {}({})'.format(env_cls,
                                                  _get_base_url(addr)))
    except:
        pass

    if set_seed:
        _set_random_seeds()

    kwargs['codec'] = aiomas.MsgPack
    task = start(addr, env_cls, mgr_cls, *args, **kwargs)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(task)


def spawn_containers(addrs=[('localhost', 5555)], env_cls=Environment,
                     env_params=None,
                     mgr_cls=EnvManager, *args, **kwargs):
    '''Spawn environments in a multiprocessing :class:`multiprocessing.Pool`.

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
    '''
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
        ret = pool.apply_async(spawn_container, args=args, kwds=k)
        r.append(ret)
    return pool, r


@asyncio.coroutine
def start(addr, env_cls=Environment, mgr_cls=EnvManager,
          *env_args, **env_kwargs):
    """`Coroutine
    <https://docs.python.org/3/library/asyncio-task.html#coroutine>`_ that
    starts an environment with *mgr_cls* manager agent.

    The agent will connect to *addr* ``('host', port)`` and wait for commands
    to spawn new agents within its environment.

    The *env_args* and *env_kwargs* will be passed to
    :meth:`~creamas.core.environment.Environment.create()` factory function.

    This coroutine finishes after :meth:`EnvManager.stop()` was called or when
    a :exc:`KeyboardInterrupt` is raised.

    :param addr:
        (HOST, PORT) for the new environment

    :param env_cls:
        Class of the environment, subclass of *Environment*.

    :param mgr_cls:
        Class of the manager agent, subclass of *EnvManager*.
    """
    env_kwargs.update(as_coro=True)
    log_folder = env_kwargs.get('log_folder', None)
    env = yield from env_cls.create(addr, *env_args, **env_kwargs)
    try:
        manager = mgr_cls(env)
        env.manager = manager
        yield from manager.stop_received
    except KeyboardInterrupt:
        logger.info('Execution interrupted by user')
    finally:
        yield from env.destroy(folder=log_folder, as_coro=True)


def _set_random_seeds():
    '''Set new random seeds for the process.
    '''
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
