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

import logging
import operator
from collections import Counter
from random import choice, shuffle

import aiomas

from creamas.logging import ObjectLogger


__all__ = ['Environment']


class Environment():
    '''Core environment class.'''

    def __init__(self, addr=('localhost', 5555), name=None, clock=None,
                 extra_ser=None, log_folder=None):
        self._container = aiomas.Container.create(addr, codec=aiomas.MsgPack,
                                                  clock=clock,
                                                  extra_serializers=extra_ser)
        self._age = 0
        self._artifacts = []
        self._candidates = []
        self._name = name if type(name) is str else 'env'

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
    def container(self):
        '''``aiomas.Container``, serves as a communication route between
        agents.
        '''
        return self._container

    @property
    def age(self):
        '''Age of the environment.'''
        return self._age

    @age.setter
    def age(self, _age):
        self._age = _age

    @property
    def agents(self):
        '''Agents in environment.'''
        return list(self._container.agents.dict.values())

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

    def clear_candidates(self):
        '''Remove current candidates from the environment.
        '''
        self._candidates = []

    def get_agent(self, name):
        '''Get agent by its name.'''
        agent = None
        for a in self.agents:
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
        for a in self.agents:
            others = self.agents[:]
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
        r_agent = choice(self.agents)
        while r_agent.addr == agent.addr:
            r_agent = choice(self.agents)
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

    def validate_candidates(self):
        '''Validate current candidates in the environment by pruning candidates
        that are not validated at least by one agent, i.e. they are vetoed.

        In larger societies this method might be costly, as it calls each
        agents' ``validate_candidates``-method.
        '''
        valid_candidates = set(self.candidates)
        for a in self.agents:
            vc = set(a.validate_candidates(self.candidates))
            valid_candidates = valid_candidates.intersection(vc)

        self._candidates = list(valid_candidates)
        self._log(logging.INFO, "{} valid candidates after agents used veto."
                  .format(len(self.candidates)))

    def _gather_votes(self):
        votes = []
        for a in self.agents:
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

    def destroy(self, folder=None):
        '''Destroy the environment.

        Does the following:

        1. calls :py:meth:`~creamas.core.Environment.save_info`
        2. for each agent: calls :py:meth:`close`
        3. calls shutdown for its **container**.
        '''
        ret = self.save_info(folder)
        for a in self.agents:
            a.close(folder=folder)
        self.container.shutdown()
        return ret
