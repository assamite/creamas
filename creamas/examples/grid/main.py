'''
.. py:module:: main
    :platform: Unix

Main module to run massive scale agent simulations using Ukko-cluster. Uses
basic grid implementations from :mod:`creamas.grid`.

.. warning::

    Do not expect this to work on your machine. Instead, this example is
    provided as a case example how distributed environments can be built using
    :class:`creamas.mp.MultiEnvironment` and
    :class:`creamas.ds.DistributedEnvironment`.

'''
import argparse
import asyncio
import logging
import os
import socket
import time
import traceback

import asyncssh

from creamas.ds import DistributedEnvironment
import ukko
import utils

# Base timeout for node connections in seconds.
TIMEOUT = 30

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
#CMD_PREFIX = 'cd {} && '.format(DIR_PATH)
CMD_PREFIX = ''

HOST = socket.gethostname()
if HOST.startswith('ukko'):
    HOST = "{}.hpc.cs.helsinki.fi".format(HOST)

SPAWN_CMD = "python {cmd} -p {port} -s {n_slaves} -o {origin} -gs {grid_size}"

logger = logging.getLogger(__name__)

LOG_LEVEL = logging.INFO
MGR_FILE = 'mgr_addrs.txt'


class DistributedGridEnvironment(DistributedEnvironment):
    '''Distributed grid environment.

    For basic usage, refer to :py:class:`DistributedEnvironment`.
    '''
    def __init__(self, host, port, nodes, ngs, n_slaves, gs, agent_cls, 
                 folder, logger=None):
        '''
        :param host:
            Host of the grand managing environment (this node).

        :param port:
            Port for the managing environments on each node, e.g. 5555. This
            port is not currently checked for availability before the node
            environments are spawned.

        :param nodes:
            List of nodes (servers) which are used to host the
            multi-environments. Each node should allow ssh-connection without
            login credentials.

        :param tuple ngs:
            2D-shape of the node grid, i.e. how multi-environments are stacked
            w.r.t. each other. For example (4,4) would stack 16 nodes into four
            by four grid (each multi-environment can then contain multiple
            environments by themselves).

        :param int n_slaves:
            Number of slave environments for each multi-environment.
            Multi-environments are expected to stack their slaves horizontally
            to the grid.

        :param gs:
            2D-shape of the agent grid for all the slave environments on all
            the nodes. For example, (10,10) would mean that each slave
            environment contain 100 agents.

        :param agent_cls:
            Class of agents which is used to populate the environments.

        :param str folder:
            Relative path to the logging folder, where the logs are saved.
        '''
        super().__init__(host, port, nodes, logger)
        self._n_slaves = n_slaves
        self._gs = gs
        self._agent_cls = agent_cls
        self._log_folder = folder
        self._ngs = ngs
        self.grid = self._make_node_grid(ngs, self.manager_addrs)
        self.cmds = self._build_cmds(port, n_slaves, gs, agent_cls, folder)
        self.spawn_nodes(self.cmds, known_hosts=None)

    def _make_node_grid(self, ngs, manager_addrs):
        assert ngs[0]*ngs[1] == len(manager_addrs)
        grid = [[None for _ in range(ngs[1])] for _ in range(ngs[0])]
        for i in range(len(grid)):
            for j in range(len(grid[0])):
                k = i*len(grid[0]) + j
                grid[i][j] = manager_addrs[k]
        return grid

    def save_manager_addrs(self, filename):
        with open(filename, 'w') as f:
            for addr in self.manager_addrs:
                f.write("{}\n".format(addr))

    def _build_cmds(self, port, n_slaves, gs, agent_cls, folder):
        orig = (0,0)
        cmds = []
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                k = i*len(self.grid[0]) + j
                co = [orig[0] + (gs[0] * i * n_slaves), orig[1] + (gs[1] * j)]
                cmd = _build_spawn_cmd(CMD_PREFIX, 'grid_node.py', port,
                                       n_slaves, gs, co, agent_cls, folder)
                cmds.append(cmd)
        return cmds

    async def prepare_nodes(self):
        '''Prepare nodes (and slave environments and agents) so that they are
        ready for the simulation.
        '''
        return await self.set_neighbors()

    async def _set_neighbors(self, mgr_addr):
        r_manager = await self.env.connect(mgr_addr, timeout=TIMEOUT)
        await r_manager.set_neighbors()

    async def _set_node_neighbors(self, mgr_addr, N, E, S, W):
        r_manager = await self.env.connect(mgr_addr, timeout=TIMEOUT)
        if N is not None:
            await r_manager.set_grid_neighbor('N', N)
        if E is not None:
            await r_manager.set_grid_neighbor('E', E)
        if S is not None:
            await r_manager.set_grid_neighbor('S', S)
        if W is not None:
            await r_manager.set_grid_neighbor('W', W)

    async def set_neighbors(self):
        '''Set neighbors for multi-environments, their slave environments,
        and agents.
        '''
        t = time.time()
        self.logger.debug("Settings grid neighbors for the multi-environments.")
        tasks = []
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                addr = self.grid[i][j]
                N, E, S, W = None, None, None, None
                if i != 0:
                    W = self.grid[i-1][j]
                if i != len(self.grid) - 1:
                    E = self.grid[i+1][j]
                if j != 0:
                    N = self.grid[i][j-1]
                if j != len(self.grid[0]) - 1:
                    S = self.grid[i][j+1]
                task = asyncio.ensure_future(self._set_node_neighbors(addr, N, E, S, W))
                tasks.append(task)
        await asyncio.gather(*tasks)

        self.logger.debug("Setting grid neighbors for the slave environments "
                          "and their agents.")
        tasks = []
        for addr in self.manager_addrs:
            task = asyncio.ensure_future(self._set_neighbors(addr))
            tasks.append(task)
        await asyncio.gather(*tasks)
        self.logger.debug("All grid neighbors set in {} seconds."
                          .format(time.time() - t))
        x = self._ngs[0] * self._gs[0] * self._n_slaves
        y = self._ngs[1] * self._gs[1]
        self.logger.info("Initialized a distributed grid with overall size "
                         "({}, {}). Total of {} agents.".format(x, y, x*y))


def _gs(s):
    try:
        x, y = map(int, s.split(","))
        return (x,y)
    except:
        raise TypeError("Grid size must be x,y")


def _build_spawn_cmd(prefix, script_name, port, n_slaves, gs, origin,
                     agent_cls, folder=None):
    script_path = os.path.join(DIR_PATH, script_name)
    str_origin = "{},{}".format(origin[0], origin[1])
    str_gs = "{},{}".format(gs[0], gs[1])
    spawn_cmd = SPAWN_CMD.format(cmd=script_path, port=port, n_slaves=n_slaves,
                                 origin=str_origin, grid_size=str_gs)

    if agent_cls is not None:
        spawn_cmd += " --agent_cls {}".format(agent_cls)
    if folder is not None:
        spawn_cmd += " --folder {}".format(folder)

    return prefix + spawn_cmd


if __name__ == "__main__":
    desc = '''Run the node simulation in Ukko-cluster.

    Assumes that your configuration allows you to make SSH-connections without
    login credentials to the Ukko-cluster.
    '''
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--venv', type=str,
                        help="Path to the Python virtual environment's "
                        "'activate'-script.")
    parser.add_argument('-ngs', '--node_grid_size', type=_gs, dest='ngs',
                        default=(2,2), help="The grid size of Ukko-nodes used "
                        "for the simulation, e.g. '4,4' which translates to "
                        "a simulation using 16 Ukko-nodes. Defaults to 2,2.")
    parser.add_argument('--n_slaves', type=int, dest='n_slaves', default=4,
                        help="Number of slave environments per node. "
                        "Defaults to 4.")
    parser.add_argument('-p', '--port', type=int, dest='port', default=5555,
                        help="Port for the managing environments on each "
                        "Ukko-node, including this environment. "
                        "Defaults to 5555.")
    parser.add_argument('-gs', '--grid_size', type=_gs, dest='gs',
                        default=(4,4),
                        help='Grid size for each of the slave environments. '
                        'Defaults to (4,4)')
    parser.add_argument('--steps', type=int, dest='steps', default=10,
                        help='Number of simulation steps. Defaults to 10.')
    parser.add_argument('--folder', type=str, dest='folder',
                        help="Logging folder relative to this script.")
    parser.add_argument('--agent_cls', type=str, dest='agent_cls',
                        help="If present, this agent class is used to "
                        "populate all the multi-environments in different "
                        "Ukko-nodes. The used form is 'module:class', "
                        "e.g. 'grid_agent:ExampleGridAgent'.")
    args = parser.parse_args()

    if args.venv is not None:
        CMD_PREFIX += "source {} && ".format(args.venv)
    port = args.port
    ngs = args.ngs
    n_nodes = ngs[0] * ngs[1]
    n_slaves = args.n_slaves
    gs = args.gs
    agent_cls = args.agent_cls
    steps = args.steps

    folder = None
    if args.folder is not None:
        folder = os.path.join(DIR_PATH, args.folder)
    utils.configure_logger(logger, 'main.log', folder, LOG_LEVEL)
    logger.info("Starting a new distributed environment: port={} ngs={} "
                "slaves={} gs={} log={} agent_cls={} steps={}"
                .format(port, ngs, n_slaves, gs, folder, agent_cls, steps))

    loop=None
    if HOST.startswith('ukko'):
        loop = asyncio.get_event_loop()
    nodes = ukko.get_nodes(n_nodes, exclude=[HOST], loop=loop)
    logger.info("Using Ukko-nodes: {}".format(" ".join(nodes)))

    dgs = DistributedGridEnvironment(HOST, port, nodes, ngs, n_slaves, gs,
                                     agent_cls, folder, logger=logger)
    dgs.save_manager_addrs(MGR_FILE)
    loop = asyncio.get_event_loop()
    timeout = 30
    nodes_ready = loop.run_until_complete(dgs.wait_nodes(timeout))
    if nodes_ready:
        logger.info("Preparing nodes for the simulation.")
        loop.run_until_complete(dgs.prepare_nodes())
        logger.info("Nodes prepared.")

        for i in range(0, steps):
            t = time.time()
            logger.info("***** Step {}/{} *****".format(i+1, steps))
            loop.run_until_complete(dgs.trigger_all())
            logger.info("Iteration completed in {} seconds"
                        .format(time.time() - t))
        logger.info("Simulation iterations finished. Destroying the main "
                    "environment and closing all nodes.")
    else:
        # If all nodes are not ready, then we stop the ones that are because
        # the simulation cannot continue without all the nodes.
        logger.info("Nodes did not become ready before timeout. Can not run "
                    "the simulation.")

    dgs.destroy()
    logger.info("Exiting the simulation.")
