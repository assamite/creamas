'''
.. py:module:: spiro
    :platform: Unix

Simple Spirograph code from https://gist.github.com/alvesjnr/1948754
'''

import math
import numpy as np

PI = np.pi


def give_dots_yield(R, r, r_, resolution=2*PI/1000, spins=50):

    def x(theta):
        return (R - r) * math.cos( theta ) + r_* math.cos( (R - r) / r * theta )

    def y(theta):
        return (R - r) * math.sin( theta ) - r_* math.sin( (R - r) / r * theta )

    theta = 0.0
    while theta < 2*PI*spins:
        yield (x(theta), y(theta))
        theta += resolution


def give_dots(R, r, r_, resolution=2*PI/1000, spins=50):
    thetas = np.arange(0, 2*PI*spins, resolution)
    Rr = R-r
    x = Rr * np.cos(thetas) + r_* np.cos(Rr / r * thetas)
    y = Rr * np.sin(thetas) - r_* np.sin(Rr / r * thetas)
    return x,y


if __name__=='__main__':
    import time
    
    t = time.clock()
    for i in range(100):
        dots = list(give_dots_yield(190,70,160, spins=50))
    t2 = time.clock()
    dt1 = t2-t
    print("Time with yield: {}".format(dt1))
    t = time.clock()
    for i in range(100):
        x,y = give_dots(190,70,160, spins=50)
    t2 = time.clock()
    dt2 = t2-t
    print("Time with numpy: {}".format(dt2))
    print(dt1/dt2)
    #from pylab import plot, show, savefig
    #plot(x,y, color = 'black')
    #show()