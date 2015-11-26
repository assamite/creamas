'''
.. py:module:: features
    :platform: Unix

Various implemented features
'''
from creamas.core.feature import Feature


class ModuloFeature(Feature):
    '''Feature that returns true if artifact's object's remainder is zero when
    divided by *n*.

    Accepts ints and floats as artifact domains
    '''

    def __init__(self, n):
        name = "mod-{}".format(n)
        domains = {int, float}
        value_type = float
        super().__init__(name, domains, value_type)
        self.n = n

    def __eq__(self, other):
        if isinstance(other, ModuloFeature):
            return self.n == other.n
        return NotImplemented

    def __ne__(self, other):
        ret = self.__eq__(other)
        if ret is NotImplemented:
            return ret
        return not ret

    def extract(self, artifact):
        if artifact.obj % self.n == 0:
            return True
        return False
