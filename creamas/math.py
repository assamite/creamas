'''
.. py:module:: math
    :platform: Unix

Various mathematical utility functions.
'''
from numpy import exp, sqrt, pi


def gaus_pdf(x, mean, std):
    '''Gaussian distribution's probability density function.

    See, e.g. `Wikipedia <https://en.wikipedia.org/wiki/Normal_distribution>`_.

    :param x: point in x-axis
    :type x: float or numpy.ndarray
    :param float mean: mean or expectation
    :param float str: standard deviation
    :returns: pdf(s) in point **x**
    :rtype: float or numpy.ndarray
    '''
    return exp(-((x - mean) / std)**2 / 2) / sqrt(2 * pi) / std


def logistic(x, x0, k, L):
    '''Logistic function.

    See, e.g `Wikipedia <https://en.wikipedia.org/wiki/Logistic_function>`_.

    :param x: point in x-axis
    :type x: float or numpy.ndarray
    :param float x0: sigmoid's midpoint
    :param float k: steepness of the curve
    :param float L: maximum value of the curve
    :returns: function's value(s) in point **x**
    :rtype: float or numpy.ndarray
    '''
    return L / (1 + exp(-k * (x - x0)))
