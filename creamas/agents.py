'''
.. py:module:: creamas.agents
    :platform: Unix

Agents module holds various agent implementations inheriting from
:py:class:`~creamas.core.agent.CreativeAgent`.
'''
import logging
from random import choice, randint

import aiomas

from creamas.core.agent import CreativeAgent
from creamas.util import log_after


class NumberAgent(CreativeAgent):
    '''Number agent created for early testing purposes of basic functionality.

    Searchs "new" integers and evaluates them based on how many features in F
    (also integers) result in mod == 0.
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rand = randint(2, 100)
        self.add_feature(rand, 0.0)
        self._log(logging.DEBUG, 'Created with feat={}'.format(self.F))

    def invent_number(self, low, high):
        '''Invent new number from given interval.'''
        self._log(logging.DEBUG, "Inventing number from ({}, {})"
                  .format(low, high))
        numbers = []
        steps = 0
        while len(numbers) < 10 and steps < 1000:
            steps += 1
            r = randint(low, high)
            if r not in self.A:
                numbers.append(r)

        if len(numbers) == 0:
            self._log(logging.INFO,
                      "Could not invent new number!".format(self))
            return 1

        best_eval = self.evaluate(numbers[0])
        best_number = numbers[0]
        for n in numbers[1:]:
            e = self.evaluate(n)
            if e > best_eval:
                best_eval = e
                best_number = n

        print("{} invented number {}, with e = {}."
              .format(self, best_number, best_eval))
        if best_eval > 0.5:
            self.add_feature(best_number, 0.0)
            self._log(logging.INFO,
                      "Appended {} to features.".format(best_number))

        return best_number, best_eval

    @log_after(attr='F')
    @log_after(attr='W')
    async def act(self, *args, **kwargs):
        m = max(self.F)
        n, e = self.invent_number(2, m + 100)
        self.add_artifact({'artifact': n, 'eval': e})
        evaluations = []
        for a in self.connections:
            ev = await self.ask_opinion(a, n)
            evaluations.append(ev)

        evaluations.sort(reverse=True)
        be = sum(evaluations[:3]) / 3
        if be > 0.25 and e > 0.5:
            self.publish(n, (e, be))

    @aiomas.expose
    def add(self, value):
        return value + choice(self.F)

    @aiomas.expose
    def evaluate(self, number):
        evaluation = 0.0
        for n in self.F:
            if number % n == 0:
                evaluation += 1

        return evaluation / len(self.F)
