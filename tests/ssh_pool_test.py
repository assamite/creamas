'''
.. py:module:: test_ds
    :platform: Unix

Tests for creamas.ds-module.
'''
import asyncio
import unittest
import multiprocessing

import aiomas

from creamas.core.environment import Environment
from creamas.ds import DistributedEnvironment
from creamas.util import run
from creamas.serializers import proxy_serializer

from ssh_server import run_server


server_pool = multiprocessing.Pool(2)
server_ports = [8022, 8023]
#server_ports = [8022]
server_rets = []
for p in server_ports:
    r = server_pool.apply_async(run_server, kwds={'port': p})
    server_rets.append(r)

loop = asyncio.get_event_loop()
loop.run_forever()