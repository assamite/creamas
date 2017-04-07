'''
.. py:module:: grid_node
    :platform: Unix

A script to spawn a new multiprocessing grid environment on an Ukko-node.
'''
import argparse
import asyncio
import logging
import socket
import os
import sys

from creamas.grid import GridMultiEnvironment, GridEnvironment, GridEnvManager, GridMultiEnvManager
import utils

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
os.chdir(DIR_PATH)

# Host of this particular node.
HOST = socket.gethostname()
SHORT_HOST = HOST
if HOST.startswith('ukko'):
    SHORT_HOST = HOST
    HOST = "{}.hpc.cs.helsinki.fi".format(HOST)

LOG_LEVEL = logging.INFO
logger = logging.getLogger(__name__)

def create_grid_menv(addr, slave_addrs, grid_size, origin, log_folder=None,
                     extra_ser=None):
    '''
    :param addr: Address of the multi-environment
    :param slave_addrs: Addresses for the slave environments.
    :param tuple grid_size: Grid size for each slave environment, e.g. (4, 4)
    :param origin:
        Origin of the multi-environment (slave envs are stacked horizontally).

    :param log_folder:
        Root logging folder for the multi-environment. Passed to slave
        environments.

    :param extra_ser:
        Extra serializers for the environments (used to communicate arbitrary
        Python objects between the agents).

    :returns: Instance of :py:class:`GridMultiEnvironment`
    '''
    name = "menv_{}_{}".format(origin[0], origin[1])
    menv = GridMultiEnvironment(addr, env_cls=GridEnvironment,
                                mgr_cls=GridMultiEnvManager,
                                slave_env_cls=GridEnvironment,
                                slave_mgr_cls=GridEnvManager,
                                slave_addrs=slave_addrs,
                                log_folder=log_folder,
                                log_level=logging.INFO,
                                grid_size=grid_size,
                                origin=origin,
                                extra_ser=extra_ser,
                                name=name)
    menv.log_folder = log_folder
    return menv


def populate_menv(menv, agent_cls_name, log_folder):
    '''Populate given multiprocessing grid environment with agents.

    :param menv: Instance of :py:class:`GridMultiEnvironment`
    :param str agent_cls_name: Name of the agent class, e.g. 'grip_mp:GridAgent'
    :param str log_folder: Root logging folder for the agents.
    '''
    gs = menv.gs
    n_agents = gs[0] * gs[1]
    n_slaves = len(menv.addrs)
    loop = asyncio.get_event_loop()
    logger.info("Populating {} with {} agents".format(HOST, n_agents*n_slaves))
    loop.run_until_complete(menv.populate(agent_cls_name, n_agents,
                                          log_folder=log_folder))
    logger.info("Populating complete.")


async def run_node(menv, log_folder):
    try:
        await menv.manager.stop_received
    except KeyboardInterrupt:
        logger.info('Execution interrupted by user.')
    finally:
        ret = await menv.destroy(log_folder, as_coro=True)
        return ret


def get_slave_addrs(mgr_addr, N):
    '''Get ports for the slave environments.

    Currently the ports are not checked for availability.
    '''
    return  [(HOST, p) for p in range(mgr_addr+1, mgr_addr+1+N)]


def _origin(s):
    try:
        x, y = map(int, s.split(","))
        return (x,y)
    except:
        raise TypeError("Origin must be x,y")


def _gs(s):
    try:
        x, y = map(int, s.split(","))
        return (x,y)
    except:
        raise TypeError("Grid size must be x,y")


if __name__ == "__main__":
    desc = '''Starts a grid multi-environment on a node and populates it if
    agent class is given. Multi-environment runs until its manager receives
    'stop'-command.

    Slave environment ports are the successive ports from the given manager
    environment's port, i.e. if the manager environment's port is 5555
    (default), then the slave environment ports are 5556, 5557, etc.. The ports
    are not checked for availability before hand.
    '''
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-p', '--port', type=int, metavar='PORT', dest='port',
                        help="Port number for the multi-environment's manager "
                        "environment.", default=5555)
    parser.add_argument('-s', '--slaves', type=int, default=4,
                        dest='n_slaves',
                        help="Number of the slave environments.")
    parser.add_argument('-o', '--origin', type=_origin, dest='origin',
                        help='Origin coordinate of the multi-environment.',
                        default=(0,0))
    parser.add_argument('-gs', '--grid_size', type=_gs, dest='gs',
                        default=(4,4),
                        help='Grid size for each of the slave environments.')
    parser.add_argument('--agent_cls', type=str, dest='agent_cls',
                        help='If present, this agent class is used to populate '
                        'the multi-environment, e.g. grid:GridAgent.')
    parser.add_argument('--folder', type=str, dest='folder',
                        help="Logging folder for the multi-enviroment.")
    args = parser.parse_args()

    addr = (HOST, args.port)
    addrs = get_slave_addrs(args.port, args.n_slaves)
    origin = args.origin
    gs = args.gs
    log_folder = args.folder
    utils.configure_logger(logger, 'node_{}.log'.format(SHORT_HOST),
                           log_folder, LOG_LEVEL)
    agent_cls = args.agent_cls
    logger.info("Spawning grid node with addr={} slaves={} origin={} gs={}"
                " log={} agent_cls={}"
                .format(addr, args.n_slaves, origin, gs, log_folder, agent_cls))
    menv = create_grid_menv(addr, addrs, gs, origin, log_folder)
    if agent_cls is not None:
        populate_menv(menv, agent_cls, log_folder)
    loop = asyncio.get_event_loop()

    # Run this node until its manager's stop-service is called.
    ret = loop.run_until_complete(run_node(menv, log_folder))
