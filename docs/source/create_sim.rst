Using Simulation
================

Creamas contains easy to use iterative simulation to perform experiments on 
a single computer set up. Each agent wishing to use simulation has to implement
:meth:`~creamas.core.agent.CreativeAgent.act`:

.. automethod:: creamas.core.agent.CreativeAgent.act
	:noindex:

Simulation calls :meth:`act` for each agent in each simulation step. What agents 
do in their turn is up to you!

Simple Simulations
------------------

Good news! Creating a simple simulation is made easy with :py:class:`~creamas.core.simulation.Simulation.create`.
Observe.

.. code-block:: python

	from mymodule import MyAgent
	from creamas.core.simulation import Simulation

	env_kwargs={'addr': ('localhost', 5555)}
	agent_kwargs = {'foo': 'bar', 'Cthulhu': 'rises'}
	
	# Create initial simulation with default parameters using MyAgents-class
	# and passing agent_kwargs to each agent at initialization time.
	sim = Simulation.create(env_kwargs=env_kwargs,
	                        agent_cls=MyAgent,
	                        agent_kwargs=agent_kwargs,
	                        n_agents=20)
	
	# Advance simulation by a single step.
	sim.step()
	
	# Close the simulation and it's environment.
	sim.close()

:func:`create` offers few arguments to modify simulation initialization:

1. You can create simulation with multiple agent classes each with its own 
   keyword arguments and number of agents.

.. code-block:: python

    from mymodule import MyAgent, CthulhuAgent
    from.creamas.core.simulation import Simulation

    env_kwargs={'addr': ('localhost', 5555)}
    myagent_kwargs = {'foo': 'bar', 'Cthulhu': 'rises'}
    cthulhu_kwargs = {"R'lyeh": 'sunken'}
    agent_kwargs=[myagent_kwargs,cthulhu_kwargs]
    agent_cls = [MyAgent, CthulhuAgent]
    n_agents = [10, 1]

    sim = Simulation.create(env_kwargs=env_kwargs,
	                        agent_cls=agent_cls,
	                        n_agents=n_agents,
	                        agent_kwargs=agent_kwargs)

2. You can create a simulation with your own environment, which is automatically
   passed down to the agents at their initialization time.

.. code-block:: python

    from mymodule import StarSpawnAgent
    from myenv import InnsmouthEnvironment
    from creamas.core.simulation import Simulation

    env_kwargs = {'addr': ('localhost', 5555),
	              'weather': 'drizzle, slight wind',
	              'atmosphere': 'gloomy'}
	
    sim = Simulation.create(agent_cls=StarSpawnAgent
	                        env_cls=InnsmouthEnvironment,
	                        env_kwargs=env_kwargs)

Complex Simulation Setups
-------------------------

If you need more control on creating the environment and agents, you can 
create your environment directly and then create your agents. After you have
fully initialized the environment, you can then pass it to the 
:class:`~creamas.core.simulation.Simulation` at initialization time.

.. code-block:: python

    from mymodule import StarSpawnAgent
    from creamas.core.enviroment import Environment
    from creamas.core.simulation import Simulation

    env = Environment.create(('localhost', 5555))

    for i in range(10):
        # Do some complex computation.
        StarSpawnAgent(env, cause_havoc=True, non_euclidian_angle=mystery)

    sim = Simulation(env=env)

Advancing Simulation
--------------------

Simulation holds a few different ways to advance it.

.. code-block:: python

    # Advance simulation by a single step (executing all agents once) executing agents in a sequence.
    sim.step()

    # Advance simulation by 10 steps.
    sim.steps(10)

    # Advance simulation by running agents asynchronously once.
    sim.async_step()

    # Advance simulation by running agents asynchronously 10 steps.
    # All agents are awaited to finish a step before the next step is initialized.
    sim.async_steps(10)

Logging Simulation
------------------

TODO: Log the logging of logger.

