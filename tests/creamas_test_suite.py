'''
All tests in one go.
'''
import unittest

from test_agent import TestAgent
from test_environment import TestEnvironment
from test_simulation import TestSimulation

suite = unittest.TestSuite()
suite.addTest(TestAgent('test_agent'))
suite.addTest(TestEnvironment('test_environment'))
suite.addTest(TestSimulation('test_create'))
tr = unittest.TestResult()
suite.run(tr)