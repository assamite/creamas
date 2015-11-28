'''
.. py:module:: features
    :platform: Unix

Various implemented features
'''
from creamas.core.feature import Feature


class ModuloFeature(Feature):
    '''Feature that returns true if artifact's object's remainder is zero when
    divided by *n*.

    Accepts ints and floats as artifact domains.
    '''

    def __init__(self, n):
        if type(n) not in {int, float}:
            raise TypeError("Divisor must be either int or float, got '{}'."
                            .format(type(n)))
        name = "mod({})".format(n)
        domains = {int, float}
        rtype = bool
        super().__init__(name, domains, rtype)
        self.__n = n

    def __eq__(self, other):
        if isinstance(other, ModuloFeature):
            return self.__n == other.n
        return NotImplemented

    def __ne__(self, other):
        ret = self.__eq__(other)
        if ret is NotImplemented:
            return ret
        return not ret

    @property
    def n(self):
        '''Feature's divisor.'''
        return self.__n

    def extract(self, artifact):
        if artifact.obj % self.__n == 0:
            return True
        return False
