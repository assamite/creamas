'''
.. py:module:: test_features
    :platform: Unix

Unit tests for features.
'''
import unittest

from creamas.features import ModuloFeature
from creamas.core import Artifact


class DummyAgent():
    name = 'foo'


class FeaturesTestCase(unittest.TestCase):

    def test_ModuloFeature(self):
        mf = ModuloFeature(5)
        self.assertEqual(mf.n, 5)
        self.assertEqual(mf.name, 'mod(5)')

        ar = Artifact(DummyAgent(), 10)
        ar.domain = int
        ar2 = Artifact(DummyAgent(), 9)
        ar2.domain = int
        ar3 = Artifact(DummyAgent(), 15.0)
        ar3.domain = float
        self.assertEqual(mf(ar), True)
        self.assertEqual(mf(ar2), False)
        mf2 = ModuloFeature(5.0)
        self.assertEqual(mf2.n, 5.0)
        self.assertEqual(mf2.name, 'mod(5.0)')
        self.assertEqual(mf2(ar3), True)
        self.assertEqual(mf2(ar2), False)
        self.assertEqual(mf, mf2)
        mf3 = ModuloFeature(4.0)
        self.assertNotEqual(mf, mf3)
        self.assertEqual(False, mf == 1)

        with self.assertRaises(TypeError):
            ModuloFeature('n')
