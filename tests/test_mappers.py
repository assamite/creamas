'''
.. py:module:: test_mappers
    :platform: Unix

Unit tests for mappers.
'''
import unittest

from creamas.core.mapper import Mapper
from creamas.mappers import *


class MapperTestCase(unittest.TestCase):

    def test_Mapper(self):
        m = Mapper()
        self.assertSetEqual(m._value_set, {int, float})

        with self.assertRaises(TypeError):
            m('a')

        self.assertEqual(m(0.0), 0.0)
        self.assertEqual(m(-1.0), -1.0)
        self.assertEqual(m(1.0), 1.0)
        self.assertEqual(m(10.0), 1.0)
        self.assertEqual(m(-10.0), -1.0)

class MappersTestCase(unittest.TestCase):

    def test_BooleanMapper(self):
        bm = BooleanMapper(mode='10')
        self.assertEqual(bm(True), 1.0)
        self.assertEqual(bm(False), 0.0)
        bm = BooleanMapper(mode='01')
        self.assertEqual(bm(True), 0.0)
        self.assertEqual(bm(False), 1.0)
        bm = BooleanMapper(mode='1-1')
        self.assertEqual(bm(True), 1.0)
        self.assertEqual(bm(False), -1.0)
        bm = BooleanMapper(mode='-11')
        self.assertEqual(bm(True), -1.0)
        self.assertEqual(bm(False), 1.0)

        self.assertEqual(bm.mode, '-11')
        with self.assertRaises(ValueError):
            bm.mode = 'aa'

    def test_LinearMapper(self):
        lm = LinearMapper(-1, 3, mode='10')
        self.assertEqual(lm(-1), 1.0)
        self.assertEqual(lm(1), 0.5)
        self.assertEqual(lm(3), 0.0)
        self.assertEqual(lm(-10), 1.0)
        self.assertEqual(lm(10), 0.0)
        lm = LinearMapper(-1, 3, mode='01')
        self.assertEqual(lm(-1), 0.0)
        self.assertEqual(lm(1), 0.5)
        self.assertEqual(lm(3), 1.0)
        self.assertEqual(lm(-10), 0.0)
        self.assertEqual(lm(10), 1.0)
        lm = LinearMapper(-1, 3, mode='1-1')
        self.assertEqual(lm(-1), 1.0)
        self.assertEqual(lm(1), 0.0)
        self.assertEqual(lm(3), -1.0)
        self.assertEqual(lm(-10), 1.0)
        self.assertEqual(lm(10), -1.0)
        lm = LinearMapper(-1, 3, mode='-11')
        self.assertEqual(lm(-1), -1.0)
        self.assertEqual(lm(1), 0.0)
        self.assertEqual(lm(3), 1.0)
        self.assertEqual(lm(-10), -1.0)
        self.assertEqual(lm(10), 1.0)

        self.assertEqual(lm.mode, '-11')
        with self.assertRaises(ValueError):
            lm.mode = 'aa'

    def test_DoubleLinearMapper(self):
        dlm = DoubleLinearMapper(-1, 3, 11, mode='10')
        self.assertEqual(dlm(-1), 1.0)
        self.assertEqual(dlm(3), 0.0)
        self.assertEqual(dlm(7), 0.5)
        self.assertEqual(dlm(11), 1.0)
        self.assertEqual(dlm(-10), 1.0)
        self.assertEqual(dlm(20), 1.0)
        dlm = DoubleLinearMapper(-1, 3, 11, mode='01')
        self.assertEqual(dlm(-1), 0.0)
        self.assertEqual(dlm(3), 1.0)
        self.assertEqual(dlm(7), 0.5)
        self.assertEqual(dlm(11), 0.0)
        self.assertEqual(dlm(-10), 0.0)
        self.assertEqual(dlm(20), 0.0)
        dlm = DoubleLinearMapper(-1, 3, 11, mode='1-1')
        self.assertEqual(dlm(-1), 1.0)
        self.assertEqual(dlm(3), -1.0)
        self.assertEqual(dlm(7), 0.0)
        self.assertEqual(dlm(11), 1.0)
        self.assertEqual(dlm(-10), 1.0)
        self.assertEqual(dlm(20), 1.0)
        dlm = DoubleLinearMapper(-1, 3, 11, mode='-11')
        self.assertEqual(dlm(-1), -1.0)
        self.assertEqual(dlm(3), 1.0)
        self.assertEqual(dlm(7), 0.0)
        self.assertEqual(dlm(11), -1.0)
        self.assertEqual(dlm(-10), -1.0)
        self.assertEqual(dlm(20), -1.0)

        self.assertEqual(dlm.mode, '-11')
        with self.assertRaises(ValueError):
            dlm.mode = 'aa'

    def test_GaussianMapper(self):
        gm = GaussianMapper(0.0, 1.0, mode='10')
        self.assertAlmostEqual(gm(0.0), 0.0)
        self.assertAlmostEqual(gm(-1.0), 0.39346934028736658)
        self.assertAlmostEqual(gm(1.0), 0.39346934028736658)
        gm = GaussianMapper(0.0, 1.0, mode='01')
        self.assertAlmostEqual(gm(0.0), 1.0)
        self.assertAlmostEqual(gm(-1.0), 0.60653065971263342)
        self.assertAlmostEqual(gm(1.0), 0.60653065971263342)
        gm = GaussianMapper(0.0, 1.0, mode='1-1')
        self.assertAlmostEqual(gm(0.0), -1.0)
        self.assertAlmostEqual(gm(-1.0), -0.21306131942526685)
        self.assertAlmostEqual(gm(1.0), -0.21306131942526685)
        gm = GaussianMapper(0.0, 1.0, mode='-11')
        self.assertAlmostEqual(gm(0.0), 1.0)
        self.assertAlmostEqual(gm(-1.0), 0.21306131942526685)
        self.assertAlmostEqual(gm(1.0), 0.21306131942526685)

        self.assertEqual(gm.mode, '-11')
        with self.assertRaises(ValueError):
            gm.mode = 'aa'