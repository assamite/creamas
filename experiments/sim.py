'''
Initial simulation tests.
'''
from creamas import Simulation
from creamas.agents import NumberAgent



sim = Simulation.create(agent_cls=NumberAgent)
sim.env.create_initial_connections()
for a in sim.env.agents:
    print("{}:{}".format(a.name, len(a.connections)))
    print(a.connections)