'''
.. py:module:: vote
    :platform: Unix

Implementations for agents able to vote from a set of candidate artifacts,
:class:`~creamas.vote.VoteAgent` and a vote organizing class that can initiate
and compute the results of votes in an environment,
:class:`~creamas.vote.VoteOrganizer`.
'''
import logging
import operator
from collections import Counter
from random import shuffle

import aiomas

from creamas import CreativeAgent


class VoteAgent(CreativeAgent):
    '''An agent with voting behavior.

    Implements two functions needed for voting:
    :meth:`~creamas.vote.VoteAgent.validate` and
    :meth:`~creamas.vote.VoteAgent.vote`.
    '''

    def validate(self, candidates):
        '''Validate a list of candidate artifacts.

        Candidate validation should prune unwanted artifacts from the overall
        candidate set. Agent can use its own reasoning to validate the
        given candidates. The method should return a subset of the given
        candidates list containing the validated artifacts (i.e. the
        artifacts that are not pruned).

        .. note::
            This basic implementation returns the given candidate list as is.
            Override this function in the subclass for the appropriate
            validation procedure.

        :param candidates: A list of candidate artifacts
        :returns: The validated artifacts, a subset of given candidates
        '''
        return candidates

    @aiomas.expose
    def vote(self, candidates):
        '''Rank artifact candidates.

        The voting is needed for the agents living in societies using
        social decision making. The function should return a sorted list
        of (candidate, evaluation)-tuples. Depending on the social choice
        function used, the evaluation might be omitted from the actual decision
        making, or only a number of (the highest ranking) candidates may be
        used.

        This basic implementation ranks candidates based on
        :meth:`~creamas.core.agent.CreativeAgent.evaluate`.

        :param candidates:
            list of :py:class:`~creamas.core.artifact.Artifact` objects to be
            ranked

        :returns:
            Ordered list of (candidate, evaluation)-tuples
        '''
        ranks = [(c, self.evaluate(c)[0]) for c in candidates]
        ranks.sort(key=operator.itemgetter(1), reverse=True)
        return ranks


class VoteOrganizer():
    '''A class which organizes voting behavior in an environment.
    '''
    def __init__(self, environment, logger=None):
        self._env = environment
        self._env.vote_organizer = self
        self._candidates = []

        self.logger = logger

    @property
    def env(self):
        '''The environment associated with this voting organizer. The
        environment is used to get all the voting agents and perform the
        voting for the candidates.
        '''
        return self._env

    @property
    def candidates(self):
        '''Current artifact candidates, subject to agents voting to
        determine which candidate(s) are added to the environment's
        **artifacts**.
        '''
        return self._candidates

    def add_candidate(self, artifact):
        '''Add candidate artifact to the current candidates.
        '''
        self.candidates.append(artifact)
        self._log(logging.DEBUG, "CANDIDATES appended:'{}'"
                  .format(artifact))

    def clear_candidates(self):
        '''Clear the current candidates.
        '''
        self._candidates = []

    def validate_candidates(self):
        '''Validate current candidates in the environment by pruning candidates
        that are not validated at least by one agent, i.e. they are vetoed.

        In larger societies this method might be costly, as it calls each
        agents' :meth:`validate`.
        '''
        valid_candidates = set(self.candidates)
        for a in self.env.get_agents(address=False):
            vc = set(a.validate(self.candidates))
            valid_candidates = valid_candidates.intersection(vc)

        self._candidates = list(valid_candidates)
        self._log(logging.DEBUG,
                  "{} valid candidates after agents used veto."
                  .format(len(self.candidates)))

    def _gather_votes(self):
        votes = []
        for a in self.env.get_agents(address=False):
            vote = a.vote(candidates=self.candidates)
            votes.append(vote)
        return votes

    def perform_voting(self, method='IRV', accepted=1):
        '''Perform voting to decide the ordering of the current candidates.

        Voting calls each agent's :func:`vote`-method, which might be costly in
        larger societies.

        :param str method:
            Used voting method. One of the following:

            * IRV: instant run-off voting
            * mean: best mean vote (requires cardinal ordering for votes),
            * best: best singular vote (requires cardinal ordering, returns
              only one candidate)
            * least_worst: least worst singular vote,
            * random:  selects random candidates

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
