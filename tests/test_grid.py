"""
.. py:module:: test_grid
    :platform: Unix

Basic tests for creamas.grid-module.
"""
import asyncio
import unittest

import aiomas

from creamas.grid import GridAgent, GridEnvironment
from creamas.util import run


class ExampleGridAgent(GridAgent):
    @aiomas.expose
    async def act(self, *args, **kwargs):
        return args, kwargs


class GridTestCase(unittest.TestCase):

    def setUp(self):
        self.env = GridEnvironment.create(('localhost', 5555))
        self.loop = asyncio.get_event_loop()

    def tearDown(self):
        self.env.destroy()

    def test_grid_env(self):
        self.assertEqual(self.env.gs, (0, 0))
        self.assertEqual(self.env.origin, (0, 0))
        self.assertEqual(len(self.env.grid), 0)

        self.env.gs = (4, 5)
        self.assertEqual(self.env.gs, (4, 5))
        self.assertEqual(len(self.env.grid), 4)
        self.assertEqual(len(self.env.grid[0]), 5)
        for r in self.env.grid:
            for c in r:
                self.assertIsNone(c)

        # Grid isn't full or ready until it actually is. The agents are spawned
        # from left to right, from up to down into the grid
        for i in range(20):
            self.assertFalse(self.env.is_full())
            self.assertFalse(self.env.is_ready())
            a = ExampleGridAgent(self.env)
            self.assertEqual(a.xy, (int(i/5), i % 5))

        self.assertTrue(self.env.is_full())
        self.assertTrue(self.env.is_ready())

        # Cannot insert agents into a full grid.
        with self.assertRaises(ValueError):
            ExampleGridAgent(self.env)

        # Agents have right neighbors after setting them.
        run(self.env.set_agent_neighbors())
        for x in range(len(self.env.grid)):
            for y in range(len(self.env.grid[0])):
                a = self.env.grid[x][y]
                self.assertEqual(a.xy, (x, y))
                nb = a.neighbors
                if y == 0:
                    self.assertEqual(nb['N'], None)
                else:
                    self.assertEqual(nb['N'], self.env.grid[x][y - 1].addr)
                if y == 4:
                    self.assertEqual(nb['S'], None)
                else:
                    self.assertEqual(nb['S'], self.env.grid[x][y + 1].addr)
                if x == 0:
                    self.assertEqual(nb['W'], None)
                else:
                    self.assertEqual(nb['W'], self.env.grid[x - 1][y].addr)
                if x == 3:
                    self.assertEqual(nb['E'], None)
                else:
                    self.assertEqual(nb['E'], self.env.grid[x + 1][y].addr)