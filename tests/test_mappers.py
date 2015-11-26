'''
.. py:module:: test_mappers
    :platform: Unix

Unit tests for mappers.
'''
import unittest

from creamas.core.mapper import Mapper
from creamas.mappers import BooleanMapper, LinearMapper, LogisticMapper
from creamas.mappers import DoubleLinearMapper, GaussianMapper


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
        bm.mode = '1-1'
        self.assertEqual(bm.mode, '1-1')
        self.assertEqual(bm(True), 1.0)
        self.assertEqual(bm(False), -1.0)
        bm = BooleanMapper(mode='-11')
        self.assertEqual(bm(True), -1.0)
        self.assertEqual(bm(False), 1.0)

        self.assertEqual(bm.mode, '-11')
        with self.assertRaises(ValueError):
            bm.mode = 'aa'

        with self.assertRaises(ValueError):
            bm = BooleanMapper(mode='asfafsaf')

    def test_LinearMapper(self):
        lm = LinearMapper(-1, 3, mode='10')
        self.assertEqual(lm(-1), 1.0)
        self.assertEqual(lm(1), 0.5)
        self.assertEqual(lm(3), 0.0)
        self.assertEqual(lm(-10), 1.0)
        self.assertEqual(lm(10), 0.0)
        lm.mode = '01'
        self.assertEqual(lm.mode, '01')
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

        with self.assertRaises(ValueError):
            lm = LinearMapper(-1, 1, mode='asfafsaf')

        with self.assertRaises(ValueError):
            lm = LinearMapper(1, -1)

    def test_DoubleLinearMapper(self):
        dlm = DoubleLinearMapper(-1, 3, 11, mode='10')
        self.assertEqual(dlm(-1), 1.0)
        self.assertEqual(dlm(3), 0.0)
        self.assertEqual(dlm(7), 0.5)
        self.assertEqual(dlm(11), 1.0)
        self.assertEqual(dlm(-10), 1.0)
        self.assertEqual(dlm(20), 1.0)
        dlm.mode = '01'
        self.assertEqual(dlm.mode, '01')
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

        with self.assertRaises(ValueError):
            dlm = DoubleLinearMapper(-1, 1, 3, mode='asfafsaf')

        with self.assertRaises(ValueError):
            dlm = DoubleLinearMapper(1, -1, 3)

        with self.assertRaises(ValueError):
            dlm = DoubleLinearMapper(1, 3, 2)

    def test_GaussianMapper(self):
        gm = GaussianMapper(0.0, 1.0, mode='10')
        self.assertAlmostEqual(gm(0.0), 0.0)
        self.assertAlmostEqual(gm(-1.0), 0.39346934028736658)
        self.assertAlmostEqual(gm(1.0), 0.39346934028736658)
        gm.mode = '01'
        self.assertEqual(gm.mode, '01')
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

        with self.assertRaises(ValueError):
            GaussianMapper(0.0, 1, mode='asfafsaf')

    def test_LogisticMapper(self):
        lm = LogisticMapper(0.0, 1.0, mode='01')
        self.assertAlmostEqual(lm(0.0), 0.5)
        self.assertAlmostEqual(lm(0.5), 0.62245933120185459)
        self.assertAlmostEqual(lm(-0.3), 0.42555748318834102)
        lm.mode = '10'
        self.assertEqual(lm.mode, '10')
        self.assertAlmostEqual(lm(0.0), 0.5)
        self.assertAlmostEqual(lm(-0.5), 0.62245933120185459)
        self.assertAlmostEqual(lm(0.3), 0.42555748318834102)
        lm.mode = '-11'
        self.assertAlmostEqual(lm(0.0), 0.0)
        self.assertAlmostEqual(lm(0.5), 0.24491866240370919)
        self.assertAlmostEqual(lm(-1.0), -0.46211715726000979)
        lm.mode = '1-1'
        self.assertAlmostEqual(lm(0.0), 0.0)
        self.assertAlmostEqual(lm(-0.5), 0.24491866240370919)
        self.assertAlmostEqual(lm(1.0), -0.46211715726000979)
        # Change midpoint
        lm = LogisticMapper(1.0, 1.0, mode='01')
        self.assertAlmostEqual(lm(1.0), 0.5)
        self.assertAlmostEqual(lm(1.5), 0.62245933120185459)
        self.assertAlmostEqual(lm(0.7), 0.42555748318834102)
        # Change steepness
        lm = LogisticMapper(1.0, 2.0, mode='01')
        self.assertAlmostEqual(lm(1.0), 0.5)
        self.assertGreater(lm(1.5), 0.62245933120185459)
        self.assertLess(lm(0.7), 0.42555748318834102)

        with self.assertRaises(ValueError):
            LogisticMapper(0.0, 1.0, mode='asfafsaf')
