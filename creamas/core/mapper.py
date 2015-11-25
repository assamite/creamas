'''
.. py:module:: mapper
    :platform: Unix

Mapper module hold base implementation for mappers. Mappers are functions, that
map each feature's possible values to the interval [-1, 1]. While features are
though to belong to artifacts of certain types, mappers usually belong to
single agent making it possible for each agent to have their own appreciation
standards for the feautre.
'''
__all__ = ['Mapper']


class Mapper():
    '''Base implementation of mapper, serves as identity function.

    Mappers, as rules and features, are callable after initialization.
    '''

    def __init__(self):
        self._value_set = {int, float}

    def __call__(self, value):
        '''Calling mapper object will first check that the given value is in
        accepted value types and the calls :py:meth:`map`.

        :raises TypeError: if value's type is not in value_set.
        '''
        if type(value) not in self._value_set:
            raise TypeError('Value should be one of the accepted types ({}), '
                            'now got {}.'.format(self._value_set, type(value)))

        return self.map(value)

    def map(self, value):
        '''Map given value to the interval [-1, 1].

        This base implementation maps each value to itself, capping to [-1, 1].

        :param value: value to map
        :returns: value mapped to the interval [-1, 1]
        :rtype float:
        '''
        if value > 1.0:
            return 1.0
        if value < -1.0:
            return -1.0
        return float(value)
