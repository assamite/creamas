'''
.. :py:module:: test_simulation
    :platform: Unix

Tests for simulation module.
'''
import unittest

from creamas.core.agent import CreativeAgent
from creamas.agents import NumberAgent
from creamas.core.environment import Environment
from creamas.core.simulation import Simulation


class TestSimulation(unittest.TestCase):

    def test_create(self):
        '''Test Simulation.create.'''
        sim = Simulation.create(env_cls=Environment, env_kwargs={},
                                agent_cls=CreativeAgent, n_agents=10,
                                agent_kwargs={}, conns=3, log_folder=None)

        env = sim.env
        self.assertEqual(sim.name, 'sim')
        self.assertEqual(env.__class__, Environment,
                         'env class is not expected')
        agents = sim.env.agents
        a = agents[0]
        self.assertEqual(a.__class__, CreativeAgent,
                         'Agent class is not expected')
        self.assertEqual(len(agents), 10,
                         'Simulation did not create correct amount of agents')

        for a in agents:
            self.assertEqual(len(a.connections), 3,
                             'Simulation did not correct initial connections')

        sim.end()
        self.assertIsNone(sim.env.container._tcp_server)

        a_classes = [CreativeAgent, NumberAgent]
        a_nums = [10, 5]
        sim = Simulation.create(agent_cls=a_classes, n_agents=a_nums,
                                agent_kwargs=[{}, {}])

        # Both agents get created right amount
        n_ca = 0
        n_na = 0
        for a in sim.env.agents:
            if a.__class__ == CreativeAgent:
                n_ca += 1
            if a.__class__ == NumberAgent:
                n_na += 1
        self.assertEqual(n_ca, 10)
        self.assertEqual(n_na, 5)
        sim.end()

        sim = Simulation.create(agent_cls=NumberAgent, conns=3)
        self.assertEqual(sim.age, 0)
        self.assertEqual(len(sim._agents_to_act), 0)
        sim.step()
        self.assertEqual(len(sim._agents_to_act), 0)
        self.assertEqual(sim.age, 1)
        sim.next()
        self.assertEqual(sim.age, 2)
        self.assertEqual(len(sim._agents_to_act), 9)
        sim.finish_step()
        self.assertEqual(len(sim._agents_to_act), 0)
        sim.steps(10)
        self.assertEqual(sim.age, 12)
        self.assertEqual(len(sim._agents_to_act), 0)
        sim.end()

if __name__ == '__main__':
    unittest.main()
