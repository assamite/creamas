Overview
========

Creamas is developed as a tool for people to easily build and do research
on multi-agent systems in the field of `computational creativity
<https://en.wikipedia.org/wiki/Computational_creativity>`_. Creamas is built
on top of `aiomas <http://aiomas.readthedocs.org/en/latest/>`_, which provides
a communication route between agents and the basic agent implementation.

Agents And Environments
-----------------------

Agents in Creamas focus on building artifacts and evaluating them. Each agent
belongs to an environment, which also serves as a
communication route between agents. Environment can also hold other information
shared by all agents, or, e.g. keep a track of agents places in a 3D
environment. Agents are created by giving the environment as an initialization
parameter.

.. code-block:: python

	from creamas.core import CreativeAgent,Environment
	# Create environment to http://localhost:5555/
	env = Environment(('localhost', 5555))
	# Create agent with address http://localhost:5555/0
	a1 = CreativeAgent(env)
	# Create agent with address http://localhost:5555/1
	a2 = CreativeAgent(env)

Agents create artifacts in some domain(s) and evaluate them. They can also ask
other agent's opinions about their own artifacts or other artifacts they have
seen. This way, the agents can accumulate knowledge about other agents
preferences, and start to prefer asking opinions from certain agents while 
avoiding others.

.. code-block:: python

	# This is a toy example. Code won't work off the shelf as the agent's don't
	# have any evaluation methods, which we will see in the next section.
	from creamas.core import Artifact
	# Create some artifact.
	ar = Artifact()
	# first evaluate it yourself
	ev = a1.evaluate(ar)
	# ask other agent's opinion (evaluation) of it
	ret = a1.ask_opinion(a2, ar)
	# get a1's current attitude towards a2
	att = a1.get_attitude(a2)
	# get difference between evaluations
	diff = abs(ev - ret)
	# if evaluations are very similar, become friendlier with the agent
	if diff < 0.2:
		a1.set_attitude(a2, att + 0.1)
	# if evaluations are very different, dislike the agent
	if diff > 0.8
		a1.set_attitude(a2, att - 0.1)

Features, Mappers And Rules
---------------------------

Agents evaluate artifacts by extracting features from them. As features can
have all kinds of outputs, they are paired with mappers. Mapper serves as a
function from feature's outputs to the interval :math:`[-1, 1] \in \mathbb{R}`.
Where features are though to be artifact domain depended, and shareable between
agents, mappers represent individual agent's preferences over possible feature
values.

Rules combine a set of features, and their corresponding mappers, to a
functional unit. Rules also have weight for each feature, which may inhibit its
effect on the overall rule's evaluation. In its most basic form rule has one
feature and its mapper, but agents are encouraged to merge existing rules
together, or add new features to them in order to make them more expressive.

Simulation
----------

* Quick intro to simulation
