'''
.. :py:module:: test_logging

Tests for logging module.
'''
import unittest

from testfixtures import TempDirectory

from creamas.core import Environment
from creamas.logging import log_after, log_before, ObjectLogger


class DummyAgent():
    def __init__(self, log_folder, add_name, init):
        self.age = 0
        self.name = 'dummy'
        self.foo = 'bar'
        self.baz = 'foo'
        self.logger = ObjectLogger(self, log_folder, add_name, init)

    @log_after('foo')
    async def test_after(self):
        self.foo = 'baz'
        return self.foo

    @log_before('baz')
    async def test_before(self):
        self.baz = 'bar'
        return self.baz


class LoggingTestCase(unittest.TestCase):

    def setUp(self):
        self.env = Environment(('localhost', 5555))
        self.d = TempDirectory()
        self.td = self.d.path

    def tearDown(self):
        TempDirectory.cleanup_all()
        self.env.destroy()

    def test_logging(self):
        dum = DummyAgent(self.td, False, True)
        '''
        dum.test_after()
        with open(dum.logger.get_file('foo')) as f:
            msg = f.read()
        self.assertEqual(msg, '0\tb\ta\tz\n')
        '''
        dum.test_before()
        with open(dum.logger.get_file('baz')) as f:
            msg = f.read()
        self.assertEqual(msg, '0\tf\to\to\n')
