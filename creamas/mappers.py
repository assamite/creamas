'''
.. py:module:: mappers
    :platform: Unix

Various mapper implementations. Mappers are functions that map possible feature
value's to the interval [-1, 1]. In Creamas, they are used by individual
agent's to represent certain preferences over features values.
'''
from creamas.core import Mapper

__all__ = ['BooleanMapper', 'LinearMapper', 'DoubleLinearMapper']


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
        self._mode_maps = {'10': self.__map10, '01': self.__map10,
                           '1-1': self.__map1_1, '-11': self.__map_11}

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

    def __map10(self, value):
        return 1.0 if value else 0.0

    def __map01(self, value):
        return 0.0 if value else 1.0

    def __map1_1(self, value):
        return 1.0 if value else -1.0

    def __map_11(self, value):
        return -1.0 if value else 1.0


class LinearMapper(Mapper):
    '''Mapper that maps values in given interval linearly.

    Accepts ints and floats.

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
