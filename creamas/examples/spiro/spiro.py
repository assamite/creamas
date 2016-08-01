'''
.. py:module:: spiro
    :platform: Unix

Simple Spirograph code, adapted from https://gist.github.com/alvesjnr/1948754
'''
import math
import numpy as np
from scipy import misc

PI = np.pi


def give_dots_yield(R, r, r_, resolution=2*PI/1000, spins=50):
    '''Generate Spirograph dots without numpy using yield.
    '''
    def x(theta):
        return (R-r) * math.cos(theta) + r_*math.cos((R-r) / r * theta)

    def y(theta):
        return (R-r) * math.sin(theta) - r_*math.sin((R-r) / r * theta)

    theta = 0.0
    while theta < 2*PI*spins:
        yield (x(theta), y(theta))
        theta += resolution


def give_dots(R, r, r_, resolution=2*PI/1000, spins=50):
    '''Generate Spirograph dots with numpy.
    '''
    thetas = np.arange(0, 2*PI*spins, resolution)
    Rr = R - r
    x = Rr * np.cos(thetas) + r_*np.cos(Rr / r * thetas)
    y = Rr * np.sin(thetas) - r_*np.sin(Rr / r * thetas)
    return x, y


def spiro_image(R, r, r_, resolution=2*PI/1000, spins=50, size=[32, 32]):
    '''Create image with given Spirograph parameters using numpy and scipy.
    '''
    x, y = give_dots(200, r, r_, spins=20)
    xy = np.array([x, y]).T
    xy = np.array(np.around(xy), dtype=np.int64)
    xy = xy[(xy[:, 0] >= -250) & (xy[:, 1] >= -250) &
            (xy[:, 0] < 250) & (xy[:, 1] < 250)]
    xy = xy + 250
    img = np.ones([500, 500], dtype=np.uint8)
    img[:] = 255
    img[xy[:, 0], xy[:, 1]] = 0
    img = misc.imresize(img, size)
    fimg = img / 255.0
    return fimg
