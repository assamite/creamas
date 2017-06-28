"""
.. py:module:: mapper
    :platform: Unix

Mapper module hold base implementation for mappers. Mappers are functions that
map feature's possible values to the interval [-1, 1]. While features are
thought to belong to artifacts of certain types, mappers usually belong to
a single agent making it possible for each agent to have their own appreciation
standards for the feature.
"""
__all__ = ['Mapper']


class Mapper():
    """Base implementation of mapper, serves as identity function for ``int``
    and ``float`` types.

    Mappers, as rules and features, are callable after initialization.
    """

    def __init__(self):
        self._value_set = {int, float}

    @property
    def value_set(self):
        """Acceptable input types for the mapper."""
        return self._value_set

    def __call__(self, value):
        """Calling mapper object will first check that the given value is in
        accepted :attr:`value_set` and then calls :py:meth:`map`.

        :returns: Value mapped to the interval [-1, 1]
        :raises TypeError: if value's type is not in :attr:`value_set`
        """
        if type(value) not in self._value_set:
            raise TypeError('Value should be one of the accepted types ({}), '
                            'now got {}.'.format(self._value_set, type(value)))

        return self.map(value)

    def map(self, value):
        """Map given value to the interval [-1, 1].

        This base implementation maps each value to itself, capping to [-1, 1].

        :param value: Value to map
        :returns: Value mapped to the interval [-1, 1]
        :rtype float:
        """
        if value > 1.0:
            return 1.0
        if value < -1.0:
            return -1.0
        return float(value)
