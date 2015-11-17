Using Simulation
==========================

*creamas* contains easy to use iterative simulation for test and research
purposes. Each agent wishing to use simulation has to implement couple of 
methods:

.. automethod:: creamas.core.agent.CreativeAgent.act

Simulation calls **act** for each agent in each simulation step.


Simple Simulations
-----------------------------

Creating simple iterative simulation is made easy with 
:py:class:`~creamas.core.simulation.Simulation.create`. Observe.

.. code-block:: python

	from mymodule import MyAgent
	from creamas.core.simulation import Simulation
	
	# Create initial simulation with default parameters using MyAgents
	sim = Simulation.create(agent_cls = MyAgent)
	
	# Advance simulation by single step
	sim.step()

**create** offers few arguments to modify simulation initialization:




Advancing Simulation
--------------------

Simulation holds few different ways to advance it.

.. code-block:: python
	
	# Advance simulation by single step
	sim.step()
	
	# Advance simulation by executing single agent.
	sim.next()
	
	# Advance simulation to the end of the current step.
	sim.finish_step()
	
	# Advance simulation by 10 steps
	sim.steps(10)
	

