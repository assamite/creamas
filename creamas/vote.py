'''
.. py:module:: vote
    :platform: Unix

Implementations for voting and other social choice behaviors.

Holds basic implementations for:

    * :class:`~creamas.vote.VoteAgent`: An agent implementing functions needed
      for voting
    * :class:`~creamas.vote.VoteEnvironment`: An environment holding basic
      voting functionality.
    * :class:`~creamas.vote.VoteManager`: A manager agent for instances of
      :class:`~creamas.vote.VoteEnvironment` when they are slave environments
      in multi- or distributed environments.
    * :class:`~creamas.vote.VoteOrganizer`: A class which can initiate voting
      and compute its results.

It should be noted that only the "true" slave environments, i.e. environments
derived from :class:`Environment` need to have voting behavior implemented
(and appropriate voting managers). :class:`~creamas.vote.VoteOrganizer`
communicates with the "true" slave environments directly without the need of
the middle layer environments (multi-environments) or managers in the case of
distributed systems.
'''
import logging
import operator
from collections import Counter
from random import shuffle

import aiomas

from creamas import CreativeAgent, Environment, EnvManager
from creamas.util import create_tasks, run

TIMEOUT = 5


class VoteAgent(CreativeAgent):
    '''An agent with voting behavior.

    Implements three functions needed for voting:

    * :meth:`~creamas.vote.VoteAgent.validate`: Validates a set of candidates
      returning only the validated candidates.
    * :meth:`~creamas.vote.VoteAgent.vote`: Votes from a set of candidates,
      i.e. orders them by preference. Returns the ordered list and preferences.
      Basic implementation orders the candidates using the agent's
      :meth:`evaluate` function.
    * :meth:`~creamas.vote.VoteAgent.add_candidate`: Add candidate artifact to
      the agent's environment's list of current candidates.
    '''

    @aiomas.expose
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

    def add_candidate(self, artifact):
        '''Add artifact to the environment's current list of candidates.
        '''
        self.env.add_candidate(artifact)


class VoteEnvironment(Environment):
    '''An environment implementing functionality needed for voting.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._candidates = []

    @property
    def candidates(self):
        '''Current artifact candidates, subject to e.g. agents voting to
        determine which candidate(s) are added to :attr:`~artifacts`.
        See :doc:`vote` for details of voting behavior.
        '''
        return self._candidates

    def clear_candidates(self):
        '''Remove current candidates from the environment.
        '''
        self._candidates = []

    def add_candidate(self, artifact):
        '''Add candidate artifact to the current candidates.
        '''
        self.candidates.append(artifact)
        self._log(logging.DEBUG, "CANDIDATES appended:'{}'"
                  .format(artifact))

    def validate_candidates(self, candidates):
        '''Validate the candidates with the agents in the environment.

        In larger societies this method might be costly, as it calls each
        agents' :meth:`validate`.

        :returns:
            A list of candidates that are validated by all agents in the
            environment.
        '''
        valid_candidates = set(candidates)
        for a in self.get_agents(addr=False):
            vc = set(a.validate(candidates))
            valid_candidates = valid_candidates.intersection(vc)

        return list(valid_candidates)

    def gather_votes(self, candidates):
        '''Gather votes for the given candidates from the agents in the
        environment.

        Votes should be anonymous, i.e. they cannot be tracked to any
        individual agent afterwards.

        :returns:
            A list of votes. Each vote is a list of ``(artifact, preference)``
            -tuples sorted by the preference.
        '''
        votes = []
        for a in self.get_agents(addr=False):
            vote = a.vote(candidates)
            votes.append(vote)
        return votes


class VoteManager(EnvManager):
    '''Manager agent for voting environments.
    '''
    @aiomas.expose
    async def get_candidates(self):
        '''Get current candidates from the managed environment.
        '''
        return self.env.candidates

    @aiomas.expose
    async def validate_candidates(self, candidates):
        '''Validate the candidates with the agents in the managed environment.

        This is a managing function for
        :meth:`~creamas.vote.VoteEnvironment.validate_candidates`.
        '''
        return self.env.validate_candidates(candidates)

    @aiomas.expose
    def clear_candidates(self):
        '''Clear candidates in the managed environment.

        This is a managing function for
        :py:meth:`~creamas.environment.Environment.clear_candidates`.
        '''
        self.env.clear_candidates()

    @aiomas.expose
    def get_votes(self, candidates):
        self.env._candidates = candidates
        votes = self.env._gather_votes()
        return votes

    @aiomas.expose
    async def gather_votes(self, candidates):
        '''Gather votes for the given candidates from the agents in the
        managed environment.

        This is a managing function for
        :py:meth:`~creamas.environment.Environment.gather_votes`.
        '''
        return self.env.gather_votes(candidates)


class VoteOrganizer():
    '''A class which organizes voting behavior in an environment.

    The organizer can :meth:`~creamas.vote.VoteOrganizer.gather_candidates`
    from the environment, and then
    :meth:`~creamas.vote.VoteOrganizer.gather_votes` for the candidates.
    Optionally the organizer may
    :meth:`~creamas.vote.VoteOrganizer.validate_candidates` before gathering
    the votes. After the votes have been collected the organizer may
    :meth:`~creamas.vote.VoteOrganizer.compute_results` of the votes with a
    given voting method.

    The organizer also has :meth:`~creamas.vote.VoteOrganizer.gather_and_vote`
    to do all of the above in one go.
    '''
    def __init__(self, environment, logger=None):
        self._env = environment
        self._candidates = []
        self._votes = []
        self.logger = logger

        self._single_env = self._determine_single_env(environment)

    @property
    def env(self):
        '''The environment associated with this voting organizer.
        '''
        return self._env

    @property
    def candidates(self):
        '''Current list of candidates gathered from the environment.
        '''
        return self._candidates

    @property
    def votes(self):
        '''Current list of votes gathered from the environment.
        '''
        return self._votes

    def _determine_single_env(self, env):
        if issubclass(env.__class__, VoteEnvironment):
            return True
        return False

    def get_managers(self):
        '''Get managers for the slave environments.
        '''
        if self._single_env:
            return None
        if not hasattr(self, '_managers'):
            self._managers = self.env.get_slave_managers()
        return self._managers

    def gather_votes(self):
        '''Gather votes from all the underlying slave environments for the
        current list of candidates.

        The votes are stored in :attr:`votes`, overriding any previous votes.
        '''
        async def slave_task(addr, candidates):
            r_manager = await self.env.connect(addr)
            return await r_manager.gather_votes(candidates)

        if len(self.candidates) == 0:
            self._log(logging.DEBUG, "Could not gather votes because there "
                      "are no candidates!")
            self._votes = []
            return
        self._log(logging.DEBUG, "Gathering votes for {} candidates."
                  .format(len(self.candidates)))

        if self._single_env:
            self._votes = self.env.gather_votes(self.candidates)
        else:
            mgrs = self.get_managers()
            tasks = create_tasks(slave_task, mgrs, self.candidates)
            self._votes = run(tasks)

    def gather_candidates(self):
        '''Gather candidates from the slave environments.

        The candidates are stored in :attr:`candidates`, overriding any
        previous candidates.
        '''
        async def slave_task(addr):
            r_manager = await self.env.connect(addr)
            return await r_manager.get_candidates()

        if self._single_env:
            self._candidates = self.env.candidates
        else:
            mgrs = self.get_managers()
            tasks = create_tasks(slave_task, mgrs)
            self._candidates = run(tasks)

    def clear_candidates(self, clear_env=True):
        '''Clear the current candidates.

        :param bool clear_env:
            If ``True``, clears also environment's (or its underlying slave
            environments') candidates.
        '''
        async def slave_task(addr):
            r_manager = await self.env.connect(addr)
            return await r_manager.clear_candidates()

        self._candidates = []
        if clear_env:
            if self._single_env:
                self.env.clear_candidates()
            else:
                mgrs = self.get_managers()
                run(create_tasks(slave_task, mgrs))

    def validate_candidates(self):
        '''Validate current candidates.

        This method validates the current candidate list in all the agents
        in the environment (or underlying slave environments) and replaces
        the current :attr:`candidates` with the list of validated candidates.

        The artifact candidates must be hashable and have a :meth:`__eq__`
        implemented for validation to work on multi-environments and
        distributed environments.
        '''
        async def slave_task(addr, candidates):
            r_manager = await self.env.connect(addr)
            return await r_manager.validate_candidates(candidates)

        self._log(logging.DEBUG, "Validating {} candidates"
                  .format(len(self.candidates)))

        candidates = self.candidates
        if self._single_env:
            self._candidates = self.env.validate_candidates(candidates)
        else:
            mgrs = self.get_managers()
            tasks = create_tasks(slave_task, mgrs, candidates, flatten=False)
            rets = run(tasks)
            valid_candidates = set(self.candidates)
            for r in rets:
                valid_candidates = valid_candidates.intersection(set(r))
            self._candidates = list(valid_candidates)

        self._log(logging.DEBUG, "{} candidates after validation"
                  .format(len(self.candidates)))

    def gather_and_vote(self, voting_method, validate=False, winners=1,
                        **kwargs):
        '''Convenience function to gathering candidates and votes and
        performing voting using them.

        Additional ``**kwargs`` are passed down to voting method.

        :param voting_method:
            The voting method to use, see
            :meth:`~creamas.vote.VoteOrganizer.compute_results` for details.
        :param bool validate: Validate gathered candidates before voting.
        :param int winners: The number of vote winners

        :returns: Winner(s) of the vote.
        '''
        self.gather_candidates()
        if validate:
            self.validate_candidates()
        self.gather_votes()
        r = self.compute_results(voting_method, self.votes, winners=winners,
                                 **kwargs)
        return r

    def compute_results(self, voting_method, votes=None, winners=1, **kwargs):
        '''Compute voting results to decide the winner(s) from the
        :attr:`votes`.

        The votes should have been made for the current
        :attr:`~creamas.vote.VoteOrganizer.candidates`.

        :param voting_method:
            A function which computes the results from the votes. Should
            accept at least three parameters: candidates, votes and number of
            vote winners. The function should return at least a list of vote
            winners. See, e.g. :func:`~creamas.vote.vote_mean` or
            :func:`~creamas.vote.vote_best`. Additional ``**kwargs`` are passed
            down to the voting method.

        :param list votes:
            A list of votes by which the voting is performed. Each vote should
            have the same set of artifacts in them. If ``None`` the results
            are computed for the current list of
            :attr:`~creamas.vote.VoteOrganizer.votes`.

        :param int winners:
            The number of vote winners

        :returns:
            list of :py:class:`~creamas.core.artifact.Artifact` objects,
            the winning artifacts. Some voting methods may also return a score
            associated with each winning artifact.

        :rtype: list
        '''
        if votes is None:
            votes = self.votes

        if len(votes) == 0:
            self._log(logging.DEBUG, "Could not compute results as there are "
                      "no votes!")
            return []

        self._log(logging.DEBUG, "Computing results from {} votes."
                  .format(len(votes)))
        return voting_method(self.candidates, votes, winners, **kwargs)

    def _log(self, level, msg):
        if self.logger is not None:
            self.logger.log(level, msg)


def vote_random(candidates, votes, n_winners):
    '''Selected random winners from the votes.

    :param candidates: All candidates in the vote
    :param votes: Votes from the agents
    :param int n_winners: The number of vote winners
    '''
    rcands = list(candidates)
    shuffle(rcands)
    rcands = rcands[:min(n_winners, len(rcands))]
    best = [(i, 0.0) for i in rcands]
    return best


def vote_least_worst(candidates, votes, n_winners):
    '''Select "least worst" artifact as the winner of the vote.

    Least worst artifact is the artifact with the best worst evaluation, i.e.
    its worst evaluation is the best among all of the artifacts.

    Ties are resolved randomly.

    :param candidates: All candidates in the vote
    :param votes: Votes from the agents
    :param int n_winners: The number of vote winners
    '''
    worsts = {str(c): 100000000.0 for c in candidates}
    for v in votes:
        for e in v:
            if worsts[str(e[0])] > e[1]:
                worsts[str(e[0])] = e[1]
    s = sorted(worsts.items(), key=lambda x: x[1], reverse=True)
    best = s[:min(n_winners, len(candidates))]
    d = []
    for e in best:
        for c in candidates:
            if str(c) == e[0]:
                d.append((c, e[1]))
    return d

def vote_best(candidates, votes, n_winners):
    '''Select the artifact with the single best evaluation as the winner of
    the vote.

    Ties are resolved randomly.

    :param candidates: All candidates in the vote
    :param votes: Votes from the agents
    :param int n_winners: The number of vote winners
    '''
    best = [votes[0][0]]
    for v in votes[1:]:
        if v[0][1] > best[0][1]:
            best = [v[0]]
    return best

def vote_IRV(candidates, votes, n_winners):
    '''Perform IRV voting based on votes.

    Ties are resolved randomly.

    :param candidates: All candidates in the vote
    :param votes: Votes from the agents
    :param int n_winners: The number of vote winners
    '''
    def _remove_zeros(votes, fpl, cl, ranking):
        '''Remove zeros in IRV voting.'''
        for v in votes:
            for r in v:
                if r not in fpl:
                    v.remove(r)
        for c in cl:
            if c not in fpl:
                if c not in ranking:
                    ranking.append((c, 0))

    def _remove_last(votes, fpl, cl, ranking):
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

    # TODO: Check what is wrong in here.
    votes = [[e[0] for e in v] for v in votes]
    f = lambda x: Counter(e[0] for e in x).most_common()
    cl = list(candidates)
    ranking = []
    fp = f(votes)
    fpl = [e[0] for e in fp]

    while len(fpl) > 1:
        _remove_zeros(votes, fpl, cl, ranking)
        _remove_last(votes, fpl, cl, ranking)
        cl = fpl[:-1]
        fp = f(votes)
        fpl = [e[0] for e in fp]

    ranking.append((fpl[0], len(ranking) + 1))
    ranking = list(reversed(ranking))
    return ranking[:min(n_winners, len(ranking))]

def vote_mean(candidates, votes, n_winners):
    '''Perform mean voting based on votes.

    Mean voting computes the mean preference for each of the artifact
    candidates from the votes and sorts the candidates in the mean preference
    order.

    Ties are resolved randomly.

    :param candidates: All candidates in the vote
    :param votes: Votes from the agents
    :param int n_winners: The number of vote winners
    '''
    sums = {str(candidate): [] for candidate in candidates}
    for vote in votes:
        for v in vote:
            sums[str(v[0])].append(v[1])
    for s in sums:
        sums[s] = sum(sums[s]) / len(sums[s])
    ordering = list(sums.items())
    ordering.sort(key=operator.itemgetter(1), reverse=True)
    best = ordering[:min(n_winners, len(ordering))]
    d = []
    for e in best:
        for c in candidates:
            if str(c) == e[0]:
                d.append((c, e[1]))
    return d
