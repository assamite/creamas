'''
.. py:module:: math
    :platform: Unix

Various mathematical utility functions.
'''
from numpy import exp, sqrt, pi
import numpy as np


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


def fractal_dimension(image):
    '''Estimates the fractal dimension of an image with box counting.
    Counts pixels with value 0 as empty and everything else as non-empty.
    Input image has to be grayscale.

    See, e.g `Wikipedia <https://en.wikipedia.org/wiki/Fractal_dimension>`_.

    :param image: numpy.ndarray
    :return:
    '''
    pixels = []
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            if image[i, j] > 0:
                pixels.append((i, j))
    lx = image.shape[1]
    ly = image.shape[0]
    pixels = np.array(pixels)
    if len(pixels) < 2:
        return 0
    scales = np.logspace(1, 4, num=20, endpoint=False, base=2)
    Ns = []
    for scale in scales:
        H, edges = np.histogramdd(pixels,
                                  bins=(np.arange(0, lx, scale),
                                        np.arange(0, ly, scale)))
        H_sum = np.sum(H > 0)
        if H_sum == 0:
            H_sum = 1
        Ns.append(H_sum)

    coeffs = np.polyfit(np.log(scales), np.log(Ns), 1)
    hausdorff_dim = -coeffs[0]

    return hausdorff_dim
