'''
Initial simulation tests.
'''
from random import randint

from creamas import Simulation
from creamas.agents import NumberAgent
from creamas.features import ModuloFeature
from creamas.core.artifact import Artifact


sim = Simulation.create(agent_cls=NumberAgent, log_folder='logs')
sim.env.create_initial_connections()
sim.steps(30)
print(sim.env.artifacts)
sim.end()