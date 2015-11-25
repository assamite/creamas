'''
.. py:module:: features
    :platform: Unix

Various implemented features
'''
from creamas.core.feature import Feature


class ModuloFeature(Feature):

    def __init__(self, n):
        name = "mod-{}".format(n)
        domains = {'int', 'float'}
        super().__init__(name, domains)
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
            return 1.0
        return 0.0
