'''
.. py:module:: test_vote
    :platform: Unix

Basic tests for vote-module. Multiprocessing and distributed system
voting tests are on their own modules.
'''
import asyncio
import unittest
from random import choice, random

import aiomas

from creamas.vote import VoteAgent, VoteEnvironment, VoteOrganizer
from creamas.vote import vote_mean, vote_IRV, vote_best, vote_least_worst, vote_random
from creamas.core.artifact import Artifact
from creamas.core.environment import Environment
from creamas.serializers import artifact_serializer


class VoteTestAgent(VoteAgent):
    def __init__(self, *args, n=1, **kwargs):
        super().__init__(*args, **kwargs)
        self.n = n

    @aiomas.expose
    async def act(self, *args, **kwargs):
        return args, kwargs

    @aiomas.expose
    def evaluate(self, number_artifact):
        '''Evaluate number with absolute difference to agent's number.
        '''
        return 3 - abs(self.n - number_artifact.obj), None

    @aiomas.expose
    def validate(self, candidates):
        valid = []
        for cand in candidates:
            e, _ = self.evaluate(cand)
            if e > 0:
                valid.append(cand)
        return valid


class TestVote(unittest.TestCase):

    def setUp(self):
        addr = ('localhost', 5555)
        codec = aiomas.MsgPack
        eser=[artifact_serializer]
        self.env = VoteEnvironment.create(addr,
                                          codec=codec,
                                          extra_serializers=[eser])
        self.vo = VoteOrganizer(self.env)
        self.loop = asyncio.get_event_loop()

    def tearDown(self):
        self.env.close()

    def test_vote_env(self):
        '''Test VoteEnvironment (and VoteAgent).
        '''
        self.assertEqual(len(self.env.candidates), 0)
        # Cannot set candidates directly
        with self.assertRaises(AttributeError):
            self.env.candidates = 'Iä iä!'

        a0 = VoteTestAgent(self.env, n=0)
        a1 = VoteTestAgent(self.env, n=1)
        a2 = VoteTestAgent(self.env, n=2)
        c0 = Artifact(a0, 0)
        c1 = Artifact(a1, 1)
        c2 = Artifact(a2, 2)
        c3 = Artifact(a1, 3)
        c4 = Artifact(a2, 4)

        # Adding and clearing candidates works
        a1.add_candidate(c1)
        self.assertEqual(len(self.env.candidates), 1)
        a2.add_candidate(c2)
        self.assertEqual(len(self.env.candidates), 2)
        self.env.clear_candidates()
        self.assertEqual(len(self.env.candidates), 0)

        # Gather votes works: one vote from each agent in environment, each
        # vote having evaluation for each of the candidates
        a0.add_candidate(c0)
        a1.add_candidate(c1)
        a2.add_candidate(c2)
        a1.add_candidate(c3)
        votes = self.env.gather_votes(self.env.candidates)
        self.assertEqual(len(votes), len(self.env.get_agents()))
        for v in votes:
            self.assertEqual(len(v), len(self.env.candidates))
            for cand in self.env.candidates:
                self.assertIn(cand, [e[0] for e in v])

        a2.add_candidate(c4)
        # Validate candidates works. Should return only three candidates as
        # c3 gets rejected by a0, and c4 by a0 and a1
        valid = self.env.validate_candidates(self.env.candidates)
        self.assertEqual(len(valid), 3)
        self.assertNotIn(c3, valid)
        self.assertNotIn(c4, valid)

    def test_vote_vo(self):
        '''Test VoteOrganizer
        '''
        a0 = VoteTestAgent(self.env, n=0)
        a1 = VoteTestAgent(self.env, n=1)
        a2 = VoteTestAgent(self.env, n=2)
        c0 = Artifact(a0, 0)
        c1 = Artifact(a1, 1)
        c2 = Artifact(a2, 2)
        c3 = Artifact(a1, 3)
        c4 = Artifact(a2, 4)

        # Adding and clearing candidates works
        a1.add_candidate(c1)
        self.vo.gather_candidates()
        self.assertEqual(len(self.vo.candidates), 1)
        a2.add_candidate(c2)
        self.vo.gather_candidates()
        self.assertEqual(len(self.vo.candidates), 2)
        self.vo.clear_candidates(clear_env=False)
        self.assertEqual(len(self.vo.candidates), 0)
        self.assertEqual(len(self.env.candidates), 2)
        self.vo.clear_candidates(clear_env=True)
        self.assertEqual(len(self.vo.candidates), 0)
        self.assertEqual(len(self.env.candidates), 0)

        # Gather votes works: one vote from each agent in environment, each
        # vote having evaluation for each of the candidates
        a0.add_candidate(c0)
        a1.add_candidate(c1)
        a2.add_candidate(c2)
        a1.add_candidate(c3)
        self.vo.gather_candidates()
        self.vo.gather_votes()
        self.assertEqual(len(self.vo.votes), len(self.env.get_agents()))
        for v in self.vo.votes:
            self.assertEqual(len(v), len(self.env.candidates))
            for cand in self.env.candidates:
                self.assertIn(cand, [e[0] for e in v])

        a2.add_candidate(c4)
        # Validate candidates works. Should leave only three candidates as
        # c3 gets rejected by a0, and c4 by a0 and a1
        self.vo.validate_candidates()
        self.assertEqual(len(self.vo.candidates), 3)
        self.assertNotIn(c3, self.vo.candidates)
        self.assertNotIn(c4, self.vo.candidates)

        # Gathering votes for zero candidates sets votes to empty list
        self.vo.clear_candidates(clear_env=True)
        self.vo.gather_votes()
        self.assertEqual(len(self.vo.votes), 0)

    def test_vote_methods(self):
        '''Test different predefined voting methods.
        '''
        a0 = VoteTestAgent(self.env, n=0)
        a1 = VoteTestAgent(self.env, n=1)
        a2 = VoteTestAgent(self.env, n=2)
        c0 = Artifact(a0, 0)
        c1 = Artifact(a1, 1)
        c2 = Artifact(a2, 2)
        c3 = Artifact(a1, 3)
        c4 = Artifact(a2, 4)

        a0.add_candidate(c2)
        a1.add_candidate(c3)
        a2.add_candidate(c4)
        a0.add_candidate(c1)
        a0.add_candidate(c0)
        self.vo.gather_candidates()
        self.vo.gather_votes()
        winners = self.vo.compute_results(vote_random, winners=3)
        self.assertEqual(len(winners), 3)
        winners = self.vo.compute_results(vote_random, winners=5)
        self.assertEqual(len(winners), 5)
        winners = self.vo.compute_results(vote_random, winners=1)
        self.assertEqual(len(winners), 1)
        self.vo.clear_candidates(clear_env=True)

        a0.add_candidate(c2)
        a1.add_candidate(c3)
        a2.add_candidate(c4)
        self.vo.gather_candidates()
        self.vo.gather_votes()
        winners = self.vo.compute_results(vote_best, winners=1)
        winner = winners[0][0]
        res = winners[0][1]
        self.assertEqual(c2, winner)
        self.assertEqual(3, res)
        self.vo.clear_candidates(clear_env=True)

        a0.add_candidate(c0)
        a1.add_candidate(c1)
        a2.add_candidate(c2)
        self.vo.gather_candidates()
        self.vo.gather_votes()
        winners = self.vo.compute_results(vote_least_worst, winners=1)
        winner = winners[0][0]
        res = winners[0][1]
        self.assertEqual(c1, winner)
        self.assertEqual(2, res)
        self.vo.clear_candidates(clear_env=True)

        a0.add_candidate(c0)
        a1.add_candidate(c1)
        a2.add_candidate(c2)
        self.vo.gather_candidates()
        self.vo.gather_votes()
        winners = self.vo.compute_results(vote_mean, winners=1)
        winner = winners[0][0]
        mean = winners[0][1]
        self.assertEqual(c1, winner)
        self.assertEqual(7/3, mean)
        self.vo.clear_candidates(clear_env=True)

        a0.add_candidate(c0)
        a1.add_candidate(c1)
        a2.add_candidate(c2)
        self.vo.gather_candidates()
        self.vo.gather_votes()
        winners = self.vo.compute_results(vote_IRV, winners=1)
        self.assertEqual(len(winners), 1)
        winners = self.vo.compute_results(vote_IRV, winners=2)
        self.assertEqual(len(winners), 2)
        self.vo.clear_candidates(clear_env=True)
