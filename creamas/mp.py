'''
.. py:module:: mp
    :platform: Unix

Multiprocessing functions to spawn multiple environments into subprocesses
to increase system performance.
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
from aiomas.codecs import MsgPack

logger = logging.getLogger(__name__)


class EnvManager(aiomas.subproc.Manager):
    """An agent that can start other agents within its environment.
    """
    @aiomas.expose
    def set_host_addr(self, addr):
        '''Set host (or master) manager for this manager.

        :param addr:
            Address for the host manager.
        '''
        self._host_addr = addr

    @aiomas.expose
    def host_addr(self):
        return self._host_addr

    @aiomas.expose
    async def report(self, msg):
        '''Report message to host manager.
        '''
        host_manager = await self.container.connect(self.host_addr)
        ret = await host_manager.handle(msg)
        return ret

    @aiomas.expose
    def handle(self, msg):
        '''Handle message, override in subclass if needed.'''
        pass

    @aiomas.expose
    def get_agents(self, agent_cls=None):
        '''Return addresses of agents belonging to certain class in this
        container. If *agent_cls* is None, returns addresses of all agents
        including the manager itself.
        '''
        agents = list(self.container.agents.dict.values())
        if agent_cls is not None:
            agents = [a for a in agents if type(a) is agent_cls]
        addrs = [a.addr for a in agents]
        return addrs

    @aiomas.expose
    def set_log_folder(self, log_folder, addr=None):
        self.container.log_folder = log_folder

    @aiomas.expose
    def stop(self, folder=None):
        ret = self.container.save_info(folder)
        self.stop_received.set_result(True)
        return ret

    @aiomas.expose
    def act(self):
        '''For consistency. Override in subclass if needed.
        '''
        pass

    @aiomas.expose
    def validate_candidates(self, candidates):
        return candidates

    @aiomas.expose
    def close(self, folder=None):
        pass

class MultiEnvManager(aiomas.Agent):
    '''An manager agent for the multi-environment.
    '''
    @aiomas.expose
    def handle(self, msg):
        '''Handle message. Override in subclass if needed.
        '''
        pass

    @aiomas.expose
    async def spawn(self, addr, agent_cls, *agent_args, **agent_kwargs):
        '''Spawn an agent to an environment in given address.
        '''
        #print("Spawning {} to {}".format(agent_cls, addr))
        remote_manager = await self.container.connect(addr, timeout=5)
        proxy, port = await remote_manager.spawn(agent_cls, *agent_args,
                                                 **agent_kwargs)
        return proxy, port

    @aiomas.expose
    async def get_agents(self, addr, agent_cls=None):
        #print("Getting agents from {}".format(addr))
        remote_manager = await self.container.connect(addr, timeout=5)
        agents = await remote_manager.get_agents(agent_cls)
        return agents

    @aiomas.expose
    async def kill(self, addr, folder=None):
        '''Send stop command to the manager agent in given address. This will
        shutdown the manager's environment.
        '''
        #print("Killing {}".format(addr))
        remote_manager = await self.container.connect(addr, timeout=5)
        ret = await remote_manager.stop(folder)
        return ret

    @aiomas.expose
    async def act(self, addr=None):
        '''Trigger agent in given *addr* to act.
        '''
        if addr is not None:
            remote_agent = await self.container.connect(addr)
            ret = await remote_agent.act()
            return ret
        else:
            pass

    @aiomas.expose
    def close(self, folder=None):
        pass

class MultiEnvironment():
    '''Environment for utilizing multiple processes.
    '''
    def __init__(self, addr, env_cls=Environment, mgr_cls=MultiEnvManager,
                 slave_addrs=[('localhost', 5555)], slave_env_cls=Environment,
                 slave_mgr_cls=EnvManager, name=None, clock=None,
                 extra_ser=None, log_folder=None):
        '''
        :param addr: (HOST, PORT) address from the manager environment.

        :param env_cls:
            Class for the environments. Must be a subclass of
            :py:class::`~creamas.core.environment.Environment`.

        :param addrs:
            List of (HOST, PORT) addresses for the slave-environments.

        :param str name: Name of the environment. Will be shown in logs.
        '''
        self._addrs = slave_addrs

        pool, r = spawn_containers(slave_addrs, env_cls=slave_env_cls,
                                   mgr_cls=slave_mgr_cls, codec=aiomas.MsgPack,
                                   clock=clock, extra_serializers=extra_ser)

        self._pool = pool
        self._r = r
        self._env = env_cls.create(addr, codec=aiomas.MsgPack, clock=clock,
                                   extra_serializers=extra_ser)
        self._manager = mgr_cls(self._env)
        self._manager_addrs = ["{}{}".format(_get_base_url(a), 0) for
                               a in self._addrs]

        self._age = 0
        self._artifacts = []
        self._candidates = []
        self._name = name if type(name) is str else 'multi-env'
        self._consistent = False
        self._agents = []

        if type(log_folder) is str:
            self.logger = ObjectLogger(self, log_folder, add_name=True,
                                       init=True)
        else:
            self.logger = None

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

    def get_agents(self, addresses=True, agent_cls=None):
        if self._consistent == False:
            ags = []
            for addr in self._manager_addrs:
                agents = aiomas.run(until=self._manager.get_agents(addr, agent_cls=agent_cls))
                ags.extend(agents)
            self._agents = ags
            self._consistent = True
            return ags
        else:
            return self._agents

    @property
    def addrs(self):
        return self._manager_addrs

    @property
    def manager(self):
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

    async def _register_host_manager(self):
        for addr in self._manager_addrs:
            remote_manager = await self._manager.connect(addr)
            r = remote_manager.set_host_addr(self._manager.addr)

    async def trigger_act(self, agent):
        ret = await self._manager.act(agent)
        return ret

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
        for i,addr in enumerate(self._manager_addrs[1:]):
            agents =  await self._manager.get_agents(addr)
            n = len(agents)
            if n < ns:
                ns = n
                saddr = self._manager_addrs[i+1]
        return saddr

    async def spawn(self, agent_cls, *args, addr=None, **kwargs):
        if addr is None:
            addr = await self._get_smallest_env()
        proxy, r_addr = await self._manager.spawn(addr, agent_cls, *args, **kwargs)
        self._consistent = False
        return proxy, r_addr

    def clear_candidates(self):
        '''Remove current candidates from the environment.
        '''
        self._candidates = []

    def get_agent(self, name):
        '''Get agent by its name.'''
        agent = None
        for a in self.get_agents():
            if a.name == name:
                agent = a
                break
        return agent

    def create_initial_connections(self, n=5):
        '''Create random initial connections for all agents.

        :param int n: the number of connections for each agent
        '''
        assert type(n) == int
        assert n > 0
        for a in self.get_agents:
            others = self.get_agents[:]
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
        r_agent = choice(self.get_agents())
        while r_agent.addr == agent.addr:
            r_agent = choice(self.get_agents)
        return r_agent

    def add_artifact(self, artifact):
        '''Add artifact with given framing to the environment.

        :param object artifact: Artifact to be added.
        '''
        artifact.env_time = self.age
        self.artifacts.append(artifact)
        self._log(logging.DEBUG, "ARTIFACTS appended: '{}', length={}"
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
        print(len(valid_candidates))
        tasks = []
        for a in self._manager_addrs:
            tasks.append(self._validate_candidates(a))
        ret = aiomas.run(until=asyncio.gather(*tasks))
        print(ret)
        for r in ret:
            result = yield from r
            print(result)
            vc = set(result)
            valid_candidates = valid_candidates.intersection(vc)
        print(valid_candidates)

        self._candidates = list(valid_candidates)
        self._log(logging.INFO, "{} valid candidates after get_agents used veto."
                  .format(len(self.candidates)))

    def _gather_votes(self):
        votes = []
        for a in self.get_agents():
            vote = a.vote(candidates=self.candidates)
            votes.append(vote)
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
                    ranking.append((c, len(ranking)+1))

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

        ranking.append((fpl[0], len(ranking)+1))
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

    def save_info(self, folder):
        '''Save information accumulated during the environments lifetime.

        Called from :py:meth:`~creamas.core.Environment.destroy`. Override in
        subclass.

        :param str folder: root folder to save information
        '''
        pass

    async def _destroy_childs(self, folder):
        '''Destroy child environments.
        '''
        rets = []
        for addr in self._manager_addrs:
            ret = await self._manager.kill(addr, folder)
            rets.append(ret)
        return rets

    def destroy(self, folder=None):
        '''Destroy the environment and the subprocesses.
        '''
        ret = [self.save_info(folder)]
        rets = aiomas.run(until=self._destroy_childs(folder))
        rets = ret + rets
        # Close and join the process pool nicely.
        self._pool.close()
        self._pool.terminate()
        self._pool.join()
        self._env.shutdown()
        return rets


def spawn_container(addr=('localhost', 5555), env_cls=Environment,
                    mgr_cls=EnvManager, *args, **kwargs):
    '''Spawn a new environment in a given address as a coroutine.

    Arguments and keyword arguments are passed down to the created environment
    at initialization time.
    '''
    #logging.basicConfig(level=getattr(logging, log_level.upper()))
    try:
        # Try importing setproctitle to change the name of the running process
        # to something we can identify with, e.g. 'ps' or 'top'.
        import setproctitle
        setproctitle.setproctitle('creamas:{}'.format(addr[1]))
    except:
        pass

    try:
        import numpy as np
        np.random.seed()
    except:
        pass

    import random
    random.seed()
    kwargs['codec'] = aiomas.MsgPack
    task = start(addr, env_cls, mgr_cls, *args, **kwargs)
    aiomas.run(until=task)


def spawn_containers(addrs=[('localhost', 5555)], env_cls=Environment,
                     mgr_cls=EnvManager, *args, **kwargs):
    '''Spawn environments in a multiprocessing :class:`multiprocessing.Pool`.

    Arguments and keyword arguments are passed down to the created environments
    at initialization time.

    :param addrs:
        List of (HOST, PORT) addresses for the environments.

    :param env_cls:
        Callable for the environments. Must be a subclass of
        :py:class:`~creamas.core.environment.Environment`.

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
    for addr in addrs:
        # Copy kwargs so that we can apply different address to different
        # containers.
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
    env = yield from env_cls.create(addr, *env_args, **env_kwargs)
    try:
        manager = mgr_cls(env)
        env.manager = manager
        yield from manager.stop_received
    except KeyboardInterrupt:
        logger.info('Execution interrupted by user')
    finally:
        yield from env.shutdown(as_coro=True)
