'''
.. py:module:: spawn_test_node
    :platform: Unix

A script to spawn a new multiprocessing environment on a test node.
'''
import argparse
import asyncio
import logging
import socket
import os
import sys

import aiomas

from creamas import Environment
from creamas.mp import MultiEnvironment, EnvManager, MultiEnvManager
from creamas.ds import run_node
from creamas.util import run

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
os.chdir(DIR_PATH)

HOST = 'localhost'

LOG_LEVEL = logging.DEBUG
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(LOG_LEVEL)

def create_menv(addr, slave_addrs, env_kwargs):
    '''
    :param addr: Address of the multi-environment
    :param slave_addrs: Addresses for the slave environments.
    :param env_kwargs:
        Extra keyword arguments for environments.

    :returns: Instance of :py:class:`GridMultiEnvironment`
    '''
    menv = MultiEnvironment(addr, env_cls=Environment,
                                mgr_cls=MultiEnvManager,
                                logger=None,
                                **env_kwargs)
    slave_kwargs = [env_kwargs.copy()
                    for _ in range(len(slave_addrs))]
    run(menv.spawn_slaves(slave_addrs=slave_addrs,
                          slave_env_cls=Environment,
                          slave_mgr_cls=EnvManager,
                          slave_kwargs=slave_kwargs))
    return menv


def populate_menv(menv, agent_cls_name, n_agents):
    '''Populate given multiprocessing environment with agents.

    :param menv: Instance of :py:class:`MultiEnvironment`
    :param str agent_cls_name: Name of the agent class, e.g. 'test_ds:DenvTestAgent'
    '''
    n_slaves = len(menv.addrs)
    logger.info("Populating {} with {} agents".format(HOST, n_agents*n_slaves))
    for _ in range(n_slaves):
        run(menv.spawn_n(agent_cls_name, n_agents))
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
    desc = '''Simple script to start a multi-environment on a node.'''
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-p', '--port', type=int, metavar='PORT', dest='port',
                        help="Port number for the multi-environment's manager "
                        "environment.", default=5555)
    parser.add_argument('-s', '--slaves', type=int, default=4,
                        dest='n_slaves',
                        help="Number of the slave environments.")
    args = parser.parse_args()

    addr = (HOST, args.port)
    addrs = get_slave_addrs(args.port, args.n_slaves)
    log_folder = None
    logger.info("Spawning node with addr={} slaves={}"
                .format(addr, args.n_slaves))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    from creamas.serializers import proxy_serializer
    env_kwargs = {'codec': aiomas.MsgPack,
                  'extra_serializers': [proxy_serializer]}
    menv = create_menv(addr, addrs, env_kwargs)
    run(menv.wait_slaves(30, check_ready=True), loop=loop)
    run(menv.set_host_managers(), loop=loop)

    # Run this node until its manager's stop-service is called.
    ret = run(run_node(menv, log_folder), loop=loop)
