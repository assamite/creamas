'''
.. py:module:: test_ds
    :platform: Unix

Tests for creamas.ds-module.
'''
import asyncio
import unittest
import multiprocessing
import subprocess

import aiomas

from creamas.core.environment import Environment
from creamas.ds import DistributedEnvironment
from creamas.util import run
from creamas.serializers import proxy_serializer

from ssh_server import run_server

loop = asyncio.get_event_loop()
#server_pool = multiprocessing.Pool(2)
server_ports = [8022, 8023]
#server_ports = [8022]
server_rets = []
for p in server_ports:
    fut = asyncio.Future()
    r = loop.run_in_executor(None, run_server, p)
    #r = server_pool.apply_async(run_server, kwds={'port': p})
    server_rets.append(r)


spawn_cmds = ['python spawn_test_node.py --port 5560',
              'python spawn_test_node.py --port 5570']
#spawn_cmds =  ['python spawn_test_node.py --port 5560']
#spawn_cmds = ['source ~/git/mas/env/bin/activate &&  python ~/git/mas/tests/spawn_test_node.py --port 5560']

addr = ('localhost', 5555)
nodes = [('localhost', p) for p in server_ports]

denv = DistributedEnvironment(addr,
                              Environment,
                              nodes,
                              codec=aiomas.MsgPack,
                              extra_serializers=[proxy_serializer])
ports = {('localhost', 8022): 5560, ('localhost', 8023): 5570}
run(denv.spawn_slaves(spawn_cmds,
                      ports=ports,
                      known_hosts=None,
                      username='test',
                      password='test'))
ret = run(denv.wait_slaves(5, check_ready=True))
print(ret)
for _ in range(8):
    ret = run(denv.spawn_n('denv_agent:DenvTestAgent', 10))
    print(ret)
ret = denv.get_agents()
print(len(ret))
run(denv.destroy(as_coro=True))