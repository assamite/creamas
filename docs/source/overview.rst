Overview
========

Creamas is developed as a tool for people to effortlessly build, and do research
on, multi-agent systems in the field of `computational creativity
<https://en.wikipedia.org/wiki/Computational_creativity>`_. Creamas is built
on top of `aiomas <http://aiomas.readthedocs.org/en/latest/>`_, which provides
a communication route (RPC) between agents and the basic agent and container
(dubbed as :class:`~creamas.Environment` in Creamas) implementations. If you
want to know more about how the low level communication works, see aiomas
documentation.

Agents And Environments
-----------------------

Agents (:class:`~creamas.CreativeAgent`) in Creamas focus on building artifacts
and evaluating them. Each agent belongs to :class:`~creamas.Environment`, which
also serves as a communication route between the agents.
Environment can also hold other information shared by
all agents, or, e.g. provide means for the agents to communicate with nearby
agents in a 2D-grid. Agents are created by giving the environment as an
initialization parameter.

.. code-block:: python

	from creamas.core import CreativeAgent, Environment
	# Create environment to tcp://localhost:5555/
	env = Environment.create(('localhost', 5555))
	# Create agent with address tcp://localhost:5555/0
	a1 = CreativeAgent(env)
	# Create agent with address tcp://localhost:5555/1
	a2 = CreativeAgent(env)

The fundamental design principle guiding the development of Creamas is that
agents create artifacts (:class:`~creamas.Artifact`) in some domain(s) and
evaluate them. A lot of the current functionality is geared towards this goal.

.. note::

	Creamas does not take a stand on the design of the multi-agent systems or
	individual agents and is quite agnostic of the agent implementations.
	Therefore, Creamas can be used to develop arbitrary
	agent societies, but you might want to take a look at `aiomas
	<http://aiomas.readthedocs.org/en/latest/>`_ if you do not need any of
	the additional functionality provided by Creamas.

Communication Between the Agents
--------------------------------

Communication between the agents in one of the key interests in multi-agent systems.
In Creamas, agents can expose their own functions as services to other agents by using
:func:`expose` decorator from *aiomas* library. An agent wishing to communicate
with another agent connects to the remote agent and calls the exposed function
remotely. To this end they have to know the other agent's (tcp) address.

.. note::

	Agents derived from :class:`~creamas.core.agent.CreativeAgent` are
	supposed to store addresses of known other agents in their
	:attr:`~creamas.core.agent.CreativeAgent.connections`.

Consider a following hypothetical :meth:`service`-method an agent **A** has::

	@aiomas.expose
	def service(self, param):
		# do something with param
		# ...
		return value

Another agent, agent **B**, knowing that the agent **A**'s address is ``addr``
can then use **A**'s ``service`` method by connecting to agent **A** through
its environment. ::

	async def client(self, my_param):
		remote_agent_A = await self.env.connect(addr)
		value = await remote_agent_A.service(my_param)
		# do something with the value

Importantly, the agents do not have to reside in the same environment or even in
the same machine, i.e. you can connect to any agent or environment as long as
you know the address of the specific agent in the environment. However, the
remote agent and its environment have to be implemented using classes derived
from *aiomas* library, like Creamas agent classes and environments do.

.. note::

	Connecting to an agent and calling an exposed function are done
	asynchronously using ``await`` keyword before the function call. Any method
	using ``await`` has to have ``async`` keyword at the start of its function
	definition.

Creating and Analyzing Agent Connections
........................................

Studying varying social network structures in creative agent systems is one of
the main purposes Creamas exists. To generate agent connections and to analyze
them, Creamas has some built-in support for integration with
`NetworkX <http://networkx.readthedocs.io/en/stable/>`_ graph library.
These functionalities are found from :mod:`creamas.nx` module. The main
functions are :func:`~creamas.nx.connections_from_graph` and
:func:`~creamas.nx.graph_from_connections`. They allow priming agent-to-agent
connections with varying properties and analyzing them easily using NetworkX
graph structures.

Evaluating Artifacts
....................

Exchanging artifacts, and information about them, is an eminent functionality for
agents in Creamas. An agent can ask other agent's opinions about its own
artifacts or other artifacts it has seen. This allows the agent to accumulate
knowledge about the artifact preferences of other agents, which may alter the agent's
own behavior.

Method :func:`~creamas.core.agent.CreativeAgent.ask_opinion` offers
a shortcut to ask an opinion about an artifact from a remote agent.

.. code-block:: python

	# This is a toy example. Code won't work off the shelf as the agents don't
	# have any evaluation methods, which we will see in the next section.
	from creamas.core import Artifact
	# Create some artifact.
	ar = Artifact()
	# first evaluate it yourself
	ev = a1.evaluate(ar)
	# ask other agent's opinion (evaluation) of it
	remote_addr = a1.connections[0]
	ret = a1.ask_opinion(remote_addr, ar)
	# get a1's current attitude towards a2
	att = a1.get_attitude(remote_addr)
	# get difference between evaluations
	diff = abs(ev - ret)
	# if evaluations are very similar, become friendlier with the agent
	if diff < 0.2:
		a1.set_attitude(a2.addr, att + 0.1)
	# if evaluations are very different, dislike the agent
	if diff > 0.8
		a1.set_attitude(a2.addr, att - 0.1)

..
	Features, Mappers And Rules
	---------------------------

	.. warning::
		Functionality in this section is not yet fully developed and tested.

	Agents can evaluate artifacts by extracting features from them. As features can
	have all kinds of outputs, they are paired with mappers. A mapper serves as a
	function from feature's outputs to the interval :math:`[-1, 1] \in \mathbb{R}`.
	Features are artifact domain depended, and shareable between agents.
	Mappers represent individual agent's preferences over possible feature
	values.

	Rules combine a set of features, and their corresponding mappers, to a
	functional unit. Rules also have weight for each feature, which may inhibit its
	effect on the overall rule's evaluation. In its most basic form rule has one
	feature and its mapper, but agents are encouraged to merge existing rules
	together, or add new features to them in order to make them more expressive.

Iterative Simulation
--------------------

Creamas provides an easy to use :class:`~creamas.core.simulation.Simulation`
which can be used to run iterative simulations using agents' :meth:`act`.
Simulations can be created directly or they can be given an environment at
initialization time. See :doc:`create_sim` for details.

Voting and Other Social Choice Functions
----------------------------------------

Creamas offers some basic social choice/social decision making behavior for
agents in the form of voting. Agents can publish their own artifacts as
**candidates**. These candidates can then be collected and voted upon. Optionally,
agents can validate each others candidates, i.e. exercise *veto* power on them,
before voting takes place. See :doc:`vote` for details.

Support for Multiple Cores and Distributed Systems
---------------------------------------------------

Creamas has inherent support for using multiple cores on a single machine and
distributing your environments on multiple nodes, e.g., on a computing cluster.
However, these functionalities are not yet fully tested, but have been used in
several systems and platforms effectively. Multiprocessing functionality is in
``mp``-module (see :doc:`mp`), and distributing the environments on several
nodes is in ``ds``-module (see :doc:`ds`).

If you want to learn more about multiprocessing and distributed system support
in Creamas, read an overview of them: :doc:`using_mp_ds`.