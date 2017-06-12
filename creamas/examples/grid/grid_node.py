'''
.. py:module:: spawn_test_node
    :platform: Unix

A script to spawn a new multiprocessing grid environment on an Ukko-node.
'''
import argparse
import asyncio
import logging
import socket
import os
import sys

import aiomas

from creamas import Environment
from creamas.grid import GridMultiEnvironment, GridEnvironment, GridEnvManager, GridMultiEnvManager
from creamas.ds import run_node
from creamas.util import run
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

def create_grid_menv(addr, slave_addrs, grid_size, origin, logger=logger,
                     extra_ser=None):
    '''
    :param addr: Address of the multi-environment
    :param slave_addrs: Addresses for the slave environments.
    :param tuple grid_size: Grid size for each slave environment, e.g. (4, 4)
    :param origin:
        Origin of the multi-environment (slave envs are stacked horizontally).

    :param logger:
        Root logger for the multi-environment.

    :param extra_ser:
        Extra serializers for the environments (used to communicate arbitrary
        Python objects between the agents).

    :returns: Instance of :py:class:`GridMultiEnvironment`
    '''
    env_kwargs = {'codec': aiomas.MsgPack, 'extra_serializers': extra_ser}
    menv = GridMultiEnvironment(addr,
                                env_cls=Environment,
                                mgr_cls=GridMultiEnvManager,
                                logger=logger,
                                grid_size=grid_size,
                                origin=origin,
                                **env_kwargs)
    slave_kwargs = [{'codec': aiomas.MsgPack, 'extra_serializers': extra_ser}
                    for _ in range(len(slave_addrs))]
    run(menv.spawn_slaves(slave_addrs=slave_addrs,
                          slave_env_cls=GridEnvironment,
                          slave_mgr_cls=GridEnvManager,
                          slave_kwargs=slave_kwargs))
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
    logger.info("Populating {} with {} agents".format(HOST, n_agents*n_slaves))
    run(menv.populate(agent_cls_name, n_agents, log_folder=log_folder))
    logger.info("Populating complete.")


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
                        help="If present, this agent class is used to populate "
                        "the multi-environment, e.g. 'grid_agent:ExampleGridAgent'")
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
    menv = create_grid_menv(addr, addrs, gs, origin, logger=None)
    run(menv.wait_slaves(5, check_ready=False))
    run(menv.set_slave_params())
    if agent_cls is not None:
        populate_menv(menv, agent_cls, log_folder)
    run(menv.wait_slaves(10, check_ready=True))
    run(menv.set_host_managers())

    # Run this node until its manager's stop-service is called.
    ret = run(run_node(menv, log_folder))
