'''
Initial simulation tests.
'''
from creamas import Simulation
from creamas.agents import NumberAgent



sim = Simulation.create(agent_cls=NumberAgent, log_folder='logs')
sim.steps(n=10)
sim.end()