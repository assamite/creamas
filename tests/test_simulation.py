'''
.. :py:module:: test_simulation
    :platform: Unix

Tests for simulation module.
'''
import unittest

from creamas.core.agent import CreativeAgent
from creamas.core.environment import Environment
from creamas.core.simulation import Simulation


class TestSimulation(unittest.TestCase):

    def test_create(self):
        '''Test Simulation.create.'''
        sim = Simulation.create(env_cls=Environment, env_kwargs={},
                                agent_cls=CreativeAgent, n_agents=10,
                                agent_kwargs={}, conns=3, log_folder=None)

        env = sim.env
        self.assertEqual(env.__class__, Environment,
                         'env class is not expected {}, got {}'
                         .format(Environment, env.__class__))
        agents = sim.env.agents
        a = agents[0]
        self.assertEqual(a.__class__, CreativeAgent,
                         'agent class is not expected {}, got {}'
                         .format(CreativeAgent, a.__class__))
        self.assertEqual(len(agents), 10,
                         'Simulation did not create correct amount of agents '
                         '({}), got {}'.format(10, len(agents)))

        for a in agents:
            self.assertEqual(len(a.connections), 3,
                             'Simulation did not create initial connections '
                             '({}), got {}'.format(3, len(a.connections)))


if __name__ == '__main__':
    unittest.main()
