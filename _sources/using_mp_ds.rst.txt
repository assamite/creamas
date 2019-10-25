Multiprocessing and Distributed Systems
=======================================

Creamas has builtin basic support for agent environments running on multiple
cores (see :doc:`mp`) and agent environments set up on distributed systems
(see :doc:`ds`), e.g. computing clusters. In this section, we explain the
basic architectural concepts required to understand how to build your own
multiprocessing and distributed environments. You should be familiar with
basic overview of the library before venturing forth (see :doc:`overview`).

Next, we first go over multiprocessing implementation of the basic environment,
:class:`~creamas.mp.MultiEnvironment`, and then the distributed system
implementation, :class:`~creamas.ds.DistributedEnvironment`.

Support for Multiple Cores
--------------------------

Multiprocessing support in Creamas is built around
:class:`~creamas.mp.MultiEnvironment`. This class spawns a set of
:class:`~creamas.core.environment.Environment` slaves in their own subprocesses
and acts as
a master for them. The master environment has also its own instance of
:class:`~creamas.core.environment.Environment` which is used to communicate
with the slaves, but because it does not contain any agents (other than
a possible manager agent, as we will see when dealing with distributed systems),
we will not distinguish it from the :class:`~creamas.mp.MultiEnvironment` for
the time being.

Slave Environments and Managers
...............................

Each of the slave environments in the :class:`~creamas.mp.MultiEnvironment`
is executed in its own subprocess (see Figure 1.).
As the slave environments are outside the master environment's
process, their functions cannot be directly called by the master and thus the
slaves require other functionality to accept orders from the master.
To this end, each slave environment is initialized
with a manager agent, :class:`~creamas.mp.EnvManager` or its subclass,
which acts as a bridge between external sources and the environment instance itself;
the external source being in most cases the master environment.

.. figure:: _static/multiprocessing_architecture.svg
	:width: 100%

	Figure 1. Basic architecture for :class:`~creamas.mp.MultiEnvironment`.
	The environment in the main process is used to connect to each slave
	environment's manager and sends commands to them. The managers then forward
	the commands to the slave environments which execute them.

.. note::

	If an environment is a slave environment in some
	:class:`~creamas.mp.MultiEnvironment`, then its first agent (the agent in path
	``tcp://environment-address:port/0``) is always expected to be an instance of
	:class:`~creamas.mp.EnvManager`, or a subclass of it.

Managing Functions
..................

The basic manager implementation contains several exposed
*managing functions* for the environment's functions, i.e. functions that call
the underlying environment's
functions with the same name. These managing functions allow the master to
execute tasks on each of the slave environments, e.g., to collect the addresses
of all the agents in all the environments or trigger :meth:`act` of each of
these agents.

Communication Between Master and Slaves
.......................................

The communication between the master and the slave environment happens through
**tcp** connection. In principle, the functionality works as follows: 

	1. Master environment connects to the slave's manager.
	2. Master environment calls slave manager's exposed method.
	3. The slave's manager calls the method with the same name in its environment with the given arguments.
	4. The slave environment executes the method and returns possible return value.
	5. The slave manager passes the return value back to the master environment.
	6. Master environment closes the connection.

.. warning::

	Managers do not check who gives the execution orders by default. When
	deploying in open environments, e.g. environments exposed to internet, it
	is important that you do not expose any unwanted functionality through them
	without adding some safe guards to the exposed functions.

	Creamas is mainly developed to be a research tool to be used in closed
	environments, and therefore is not particularly designed to offer protection
	for any kinds of attacks. However, `aiomas <https://aiomas.readthedocs.io/en/latest/guides/tls.html>`_
	has some built-in encryption support for, e.g., TSL. As Creamas'
	:class:`~creamas.core.environment.Environment` is just a subclass of aiomas'
	:class:`Container`, the TSL support from aiomas can be utilised in Creamas.

Developing for Multiple Cores
.............................

To utilize multiprocessing support in your own implementations, you can give
following initialization parameters to :class:`~creamas.mp.MultiEnvironment`:

	* **Address**: Address for the manager/master environment.

	* **Environment class**: Class for the manager/master environment
	  which is used to connect to each of the slave managers.

	* **Manager class**: Class for the master environment's manager. This
	  should not be needed if you are not using :class:`~creamas.mp.MultiEnvironment`
	  as a part of :class:`~creamas.ds.DistributedEnvironment`

After the master environment has been created, the slave environments can be
spawned using :meth:`~creamas.mp.MultiEnvironment.spawn_slaves`. It accepts
at least the following arguments.

	* **Slave addresses**: Addresses for the slave environments, the size of
	  this list will define how many subprocesses are spawned.

	* **Slave environment class**: Class for each slave environment inside the
	  multiprocessing environment.

	* **Slave environment parameters**: Initialization parameters for each slave
	  environment.

	* **Slave manager class**: This is the manager agent class that is used for
	  each slave environment.

You can, of course, also subclass :class:`~creamas.mp.MultiEnvironment` itself
(see :class:`~creamas.grid.GridMultiEnvironment` for an example).

Support for Distributed Systems
-------------------------------

Support for distributed systems in Creamas is built around
:class:`~creamas.ds.DistributedEnvironment`. Distributed environment is
designed to be used with multiple (quite homogeneous) nodes which operate in
a closed system where each node can make **tcp** connections to ports in
other nodes. Further on, it requires that it is located in a machine that is
able to make SSH connections to the nodes.

The basic architecture of :class:`~creamas.ds.DistributedEnvironment` can
be seen in the Figure 2. In short, :class:`~creamas.ds.DistributedEnvironment` acts
as a master for the whole environment, i.e. it does not hold "actual" simulation
agents, but serves only as a manager for the simulation. Other nodes
in the environment then each contain an instance of
:class:`~creamas.mp.MultiEnvironment` with its own manager, which accepts orders
from :class:`~creamas.ds.DistributedEnvironment`. The slave environments inside
each :class:`~creamas.mp.MultiEnvironment` then hold the actual agents for the
simulation (and the manager for the slave environment).

.. figure:: _static/distributed_architecture.svg
	:width: 100%

	Figure 2. Basic architecture for :class:`~creamas.ds.DistributedEnvironment`.
	It manages a set of nodes each containing a :class:`~creamas.mp.MultiEnvironment`.
	The main difference from the single node implementation is, that the main
	process environment on each node also holds a manager which accepts commands
	for that node.

Next, we look at how to set up and use :class:`~creamas.ds.DistributedEnvironment`.
In the following, node and :class:`~creamas.mp.MultiEnvironment` are used
interchangeably.

Using a Distributed Environment
...............................

Initialization of a distributed environment is done roughly in the following
steps:

	1. Initialize :class:`~creamas.ds.DistributedEnvironment` with a list of node locations
	2. Create node spawning terminal commands for each node, i.e. commands which start :class:`~creamas.mp.MultiEnvironment` on each node.
	3. Spawn nodes using :meth:`~creamas.ds.DistributedEnvironment.spawn_nodes`
	4. Wait until all nodes are **ready** (see, e.g. :meth:`~creamas.mp.MultiEnvironment.is_ready`) using :meth:`~creamas.ds.DistributedEnvironment.wait_nodes`. A node is ready when it has finished its own initialization and is ready to execute orders.
    5. Make any additional preparation for the nodes using :meth:`~creamas.ds.DistributedEnvironment.prepare_nodes`.

After this sequence, the :class:`~creamas.ds.DistributedEnvironment` should be
ready to be used. The main usage for iterative simulations is to call
:meth:`~creamas.ds.DistributedEnvironment.trigger_all`, which triggers all
agents in all the nodes (in all the slave environments) to act.

Spawning Nodes
..............

When :meth:`~creamas.ds.DistributedEnvironment.spawn_nodes` is called,
:class:`~creamas.ds.DistributedEnvironment` spawns a new process for each node
in the list of node locations given at initialization time. For each process
it does the following:

	1. it opens a SSH connection to one of the nodes, and
	2. executes a command line script on the node.

The command line script executed is assumed to spawn an instance of
:class:`~creamas.mp.MultiEnvironment` with a manager attached to it. This
manager is then used to communicate any commands from
:class:`~creamas.ds.DistributedEnvironment` to the slave environments on that
node. The command line script can also do other preparation for the node, e.g.
populate its slave environments with agents.

The command line script executed is assumed to wait until the
:class:`~creamas.mp.MultiEnvironment` is stopped, i.e. it does not exit
after the initialization (as in the naive case this would delete the
environment). To achieve this, you can for example add a following kind of
function to your node spawning script and call it last in the script::

    async def run_node(menv, log_folder):
        try:
	        await menv.manager.stop_received
	    except KeyboardInterrupt:
	        logger.info('Execution interrupted by user.')
	    finally:
	        ret = await menv.close(log_folder, as_coro=True)
	        return ret

When :func:`run_node` is called, the script will block its execution until the
manager of :class:`~creamas.mp.MultiEnvironment` receives a stop sign. The stop
sign is sent to each node's manager when :meth:`~creamas.ds.DistributedEnvironment.stop_nodes`
is called.

See ``creamas/examples/grid/`` for an example implementation of a distributed
agent environment.
