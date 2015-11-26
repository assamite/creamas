'''
.. py:module:: mappers
    :platform: Unix

Various mapper implementations. Mappers are functions that map possible feature
value's to the interval [-1, 1]. In Creamas, they are used by individual
agent's to represent agent's preferences over features values.
'''
from scipy.stats import norm

from creamas.core import Mapper

__all__ = ['BooleanMapper', 'LinearMapper', 'DoubleLinearMapper',
           'GaussianMapper']


class BooleanMapper(Mapper):
    '''Boolean mapper that has four different modes.

    Depending on the mode, True and False are mapped either to 1, 0, or -1.

        ======= ======= =======
        mode    True    False
        ======= ======= =======
         '10'    1.0     0.0
         '01'    0.0     1.0
         '1-1'   1.0    -1.0
         '-11'  -1.0     1.0
        ======= ======= =======
    '''
    modes = ['10', '01', '1-1', '-11']

    def __init__(self, mode='10'):
        self._value_set = {bool}
        self._mode = mode
        self._mode_maps = {'10': self._map10, '01': self._map01,
                           '1-1': self._map1_1, '-11': self._map_11}

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self._mode)

    @property
    def mode(self):
        '''Mode of the mapper.'''
        return self._mode

    @mode.setter
    def mode(self, value):
        if value not in self.modes:
            raise ValueError('Value ({}) not found from modes.'.format(value))
        self._mode = value

    def map(self, value):
        return self._mode_maps[self._mode](value)

    def _map10(self, value):
        return 1.0 if value else 0.0

    def _map01(self, value):
        return 0.0 if value else 1.0

    def _map1_1(self, value):
        return 1.0 if value else -1.0

    def _map_11(self, value):
        return -1.0 if value else 1.0


class LinearMapper(Mapper):
    '''Mapper that maps values in given interval linearly.

    Can be used for features that return either 'int' or 'float' values.

    Based on its mode, maps *lo* and *hi* to different end points and values
    between them to a straight line. Depending on the mode, *lo* and *hi* have
    following end points:

        ======= ===== =====
        mode    lo    hi
        ======= ===== =====
         '10'    1.0   0.0
         '01'    0.0   1.0
         '1-1'   1.0  -1.0
         '-11'  -1.0   1.0
        ======= ===== =====

    '''
    _value_set = {int, float}
    modes = ['10', '01', '1-1', '-11']

    def __init__(self, lo, hi, mode='01'):
        if lo > hi:
            raise ValueError('lo ({}) must be smaller than hi ({}).'
                             .format(lo, hi))
        self._lo = lo
        self._hi = hi
        self._mode_maps = {'10': self._map10, '01': self._map01,
                           '1-1': self._map1_1, '-11': self._map_11}
        self.mode = mode

    def __str__(self):
        return "{}({}-{},{})".format(self.__class__.__name__, self._lo,
                                     self._hi, self._mode)

    @property
    def mode(self):
        '''Mode of the mapper.'''
        return self._mode

    @mode.setter
    def mode(self, value):
        if value not in self.modes:
            raise ValueError('Value ({}) not found from modes.'.format(value))
        self._mode = value

    @property
    def value_set(self):
        '''Accepted value types, i.e. this mapper can be used for the features
        that return these types of values.'''
        return self._value_set

    def map(self, value):
        return self._mode_maps[self._mode](self._lo, self._hi, value)

    def _map10(self, lo, hi, value):
        if value < lo:
            return 1.0
        if value > hi:
            return 0.0
        diff = hi - lo
        val_diff = value - lo
        return 1.0 - (float(val_diff) / diff)

    def _map01(self, lo, hi, value):
        if value < lo:
            return 0.0
        if value > hi:
            return 1.0
        diff = hi - lo
        val_diff = value - lo
        return 0.0 + (float(val_diff) / diff)

    def _map1_1(self, lo, hi, value):
        if value < lo:
            return 1.0
        if value > hi:
            return -1.0
        diff = hi - lo
        val_diff = value - lo
        return 1.0 - (2*(float(val_diff) / diff))

    def _map_11(self, lo, hi, value):
        if value < lo:
            return -1.0
        if value > hi:
            return 1.0
        diff = hi - lo
        val_diff = value - lo
        return -1.0 + (2*(float(val_diff) / diff))


class DoubleLinearMapper(LinearMapper):
    '''Mapper that concatenates two linear mappers.

    Can be used for features that return either 'int' or 'float' values.

    First line is created from *lo* to *mid* and second line from *mid* to
    *hi*. Depending on the mode, *lo*, *mid* and *hi* are mapped to following
    end points.

        ======= ===== ====== ======
        mode    lo    mid    hi
        ======= ===== ====== ======
         '10'    1.0   0.0    1.0
         '01'    0.0   1.0    0.0
         '1-1'   1.0  -1.0    1.0
         '-11'  -1.0   1.0   -1.0
        ======= ===== ====== ======
    '''

    # Reverse modes (modes for second line) for the modes described in the
    # LinearMapper.
    reverse_modes = ['01', '10', '-11', '1-1']

    def __init__(self, lo, mid, hi, mode='01'):
        if lo > mid:
            raise ValueError('lo ({}) must be smaller than mid ({}).'
                             .format(lo, mid))
        if mid > hi:
            raise ValueError('mid ({}) must be smaller than hi ({}).'
                             .format(mid, hi))
        self._lo = lo
        self._mid = mid
        self._hi = hi
        self._mode_maps = {'10': self._map10, '01': self._map01,
                           '1-1': self._map1_1, '-11': self._map_11}
        self.mode = mode
        self._rmode = self._get_reverse_mode(mode)

    def __str__(self):
        return "{}({}-{}-{},{})".format(self.__class__.__name__, self._lo,
                                        self._mid, self._hi, self._mode)

    def _get_reverse_mode(self, mode):
        return self.reverse_modes[self.modes.index(mode)]

    @property
    def mode(self):
        '''Mode of the mapper.'''
        return self._mode

    @mode.setter
    def mode(self, value):
        if value not in self.modes:
            raise ValueError('Value ({}) not found from modes.'.format(value))
        self._mode = value
        self._rmode = self._get_reverse_mode(self._mode)

    def map(self, value):
        if value <= self._mid:
            return self._mode_maps[self._mode](self._lo, self._mid, value)
        return self._mode_maps[self._rmode](self._mid, self._hi, value)


class GaussianMapper(Mapper):
    '''Gaussian distribution mapper.

    The mapped value is relative to given Gaussian distribution's
    maximum point (*pmax*, evaluated at point *loc*) and the probability
    density function's value at given evaluation point (*pval*).

    The actual value calculation changes with the mode of the mapper:

        ======= =======================
        mode    mapped value
        ======= =======================
         '10'    :math:`1.0 - (pval / pmax)`
         '01'    :math:`pval / pmax`
         '1-1'   :math:`1.0 - 2(pval / pmax)`
         '-11'   :math:`-1.0 + 2(pval / pmax)`
        ======= =======================

    '''

    _value_set = {int, float}
    modes = ['10', '01', '1-1', '-11']

    def __init__(self, loc, scale, mode='01'):
        if mode not in self.modes:
            TypeError('Mode ({}) is not an accepted mode type.'.format(mode))
        self._loc = loc
        self._scale = scale
        self._mode = mode
        self._mode_maps = {'10': self._map10, '01': self._map01,
                           '1-1': self._map1_1, '-11': self._map_11}

    def __str__(self):
        return "{}({}-{},{})".format(self.__class__.__name__, self._loc,
                                     self._scale, self._mode)

    @property
    def mode(self):
        '''Mode of the mapper.'''
        return self._mode

    @mode.setter
    def mode(self, value):
        if value not in self.modes:
            raise ValueError('Value ({}) not found from modes.'.format(value))
        self._mode = value

    def map(self, value):
        return self._mode_maps[self._mode](self._loc, self._scale, value)

    def _map10(self, loc, scale, value):
        lmax = norm.pdf(loc, loc, scale)
        pdf = norm.pdf(value, loc, scale)
        return 1.0 - (pdf / lmax)

    def _map01(self, loc, scale, value):
        lmax = norm.pdf(loc, loc, scale)
        pdf = norm.pdf(value, loc, scale)
        return pdf / lmax

    def _map1_1(self, loc, scale, value):
        lmax = norm.pdf(loc, loc, scale)
        pdf = norm.pdf(value, loc, scale)
        return 1.0 - 2*(pdf / lmax)

    def _map_11(self, loc, scale, value):
        lmax = norm.pdf(loc, loc, scale)
        pdf = norm.pdf(value, loc, scale)
        return -1.0 + 2*(pdf / lmax)
