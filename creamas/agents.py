'''
.. py:module:: agents
    :platform: Unix

Agents module holds various agent implementations inheriting from
:py:class:`~creamas.core.agent.CreativeAgent`.
'''
import logging
from random import choice, randint

import aiomas

from creamas.core.agent import CreativeAgent
from creamas.core.artifact import Artifact
from creamas.logging import log_after
from creamas.features import ModuloFeature
from creamas.core.rule import Rule
from creamas.mappers import BooleanMapper


class NumberAgent(CreativeAgent):
    '''Number agent created for early testing purposes of basic functionality.

    Searchs "new" integers and evaluates them based on how many features in F
    (also integers) result in mod == 0.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rand = randint(2, 100)
        rule = Rule([ModuloFeature(rand)], [1.0])
        rule.mappers = [BooleanMapper()]
        self.add_rule(rule, 1.0)
        self._log(logging.DEBUG, 'Created with rule={}'.format(rule))

    def invent_number(self, low, high):
        '''Invent new number from given interval.'''
        self._log(logging.DEBUG, "Inventing number from ({}, {})"
                  .format(low, high))
        ars = []
        steps = 0
        while len(ars) < 10 and steps < 1000:
            steps += 1
            r = randint(low, high)
            ar = Artifact(self, r)
            ar.domain = int
            if ar not in self.A:
                ars.append(ar)

        if len(ars) == 0:
            self._log(logging.INFO,
                      "Could not invent new number!".format(self))
            return 1, 0.0

        best_eval, fr = self.evaluate(ars[0])
        ars[0].add_eval(self, best_eval, fr)
        best_number = ars[0].obj
        best_ar = ars[0]
        for ar in ars[1:]:
            e, fr = self.evaluate(ar)
            ar.add_eval(self, e, fr)
            if e > best_eval:
                best_eval = e
                best_number = ar.obj
                best_ar = ar

        self._log(logging.DEBUG, "Invented number {}, with e = {}."
                  .format(best_number, best_eval))
        if best_eval > 0.5:
            rule = Rule([ModuloFeature(best_number)], [1.0])
            rule.mappers = [BooleanMapper()]
            self.add_rule(rule, 1.0)
            self._log(logging.INFO,
                      "Appended {} to features.".format(best_number))

        return best_ar

    @log_after(attr='R')
    @log_after(attr='W')
    async def act(self, *args, **kwargs):
        m = 0
        for r in self.R:
            for f in r.F:
                if f.n > m:
                    m = f.n
        ar = self.invent_number(2, m + 100)
        if ar == 1:
            return
        self.add_artifact(ar)
        evaluations = []
        for a in self.connections:
            ev, fr = await self.ask_opinion(a, ar)
            ar.add_eval(a, ev, fr)
            evaluations.append(ev)

        evaluations.sort(reverse=True)
        be = sum(evaluations[:3]) / 3
        se = ar.evals[self.name]
        if be > 0.25 and se > 0.5:
            self.publish(ar)

    @aiomas.expose
    def add(self, value):
        return value + choice(self.F)

'''
    @aiomas.expose
    def extract(self, artifact):
        number = artifact.obj
        evaluation = 0.0
        framing = []
        if len(self.F) == 0:
            return evaluation, framing
        for n in self.F:
            if number % n == 0:
                framing.append(n)
                evaluation += 1

        return evaluation / len(self.F), framing
'''
