'''
.. py:module:: grid_agent
    :platform: Unix

A test implementation of a grid agent.
'''
import logging
import random

import aiomas
from creamas.grid import GridAgent


class ExampleGridAgent(GridAgent):

    @aiomas.expose
    async def rcv(self, msg):
        ret_msg = "{} got message: {}".format(self.addr, msg)
        self._log(logging.INFO, ret_msg)
        return ret_msg

    @aiomas.expose
    async def act(self, *args, **kwargs):
        card = random.choice(['N', 'S', 'E', 'W'])
        rcv = await self.send(card, "Message from {}".format(self.addr))
