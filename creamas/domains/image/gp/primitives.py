"""Basic primitives for the :class:`GPImageGenerator`.

"""
import math
import random

from noise import snoise2, pnoise1, pnoise2

MINVAL = 0.00001
HVAL = 10


def rand_eph():
    return random.random() * 2 - 1


def sign(x):
    """Sign function with value -1 when y < x and value 1 when y > x.
    """
    if x < 0:
        return -1.0
    if x > 0:
        return 1.0
    return 0.0


def _check_hval(x):
    if x > HVAL:
        return HVAL
    elif x < -HVAL:
        return -HVAL
    return x


def combine(num1, num2, num3):
    """Combines three values into a list, can be used as the first primitive in any tree to
    make RGB images.
    """
    return [float(num1), float(num2), float(num3)]


def safe_log10(x):
    """Safe base 10 logarithm.

    If ``x == 0``, uses :attr:`primitives.MINVAL`.
    """
    if x <= 0:
        x = MINVAL
    return math.log10(x)


def safe_log2(x):
    """Safe base 2 logarithm.

    If ``x == 0``, uses :attr:`primitives.MINVAL`.
    """
    if x <= 0:
        x = MINVAL
    return math.log2(x)


def safe_ln(x):
    """Safe natural logarithm.

    If ``x == 0``, uses :attr:`primitives.MINVAL`.
    """
    if x <= 0:
        x = MINVAL
    return math.log(x)


def safe_exp(x):
    """Safe exponential function.

    Values of x are clamped in [-100, 100].
    """
    if x < -100:
        x = -100
    elif x > 100:
        x = 100
    return math.exp(x)


def safe_div(a, b):
    """Safe divide.

    If ``b == 0``, uses :attr:`primitives.MINVAL`.
    """
    if b == 0:
        b = MINVAL
    return a / b


def safe_mod(a, b):
    """Safe modulo.

    If ``b == 0``, uses :attr:`primitives.MINVAL`.
    """
    if b == 0:
        b = MINVAL
    return a % b


def safe_cosh(x):
    x = _check_hval(x)
    return math.cosh(x)


def safe_sinh(x):
    x = _check_hval(x)
    return math.sinh(x)


def mdist(a, b):
    """Absolute distance between a and b.
    """
    return abs(a - b)


def safe_pow(a, b):
    """Safe power function.

    If ``a == 0 and b < 0`` returns 0.
    """
    if a == 0 and b < 0:
        return 0
    return pow(a, b)


def abs_sqrt(a):
    """Square root of absolute value of a.
    """
    return math.sqrt(abs(a))


def if_then_else(input, output1, output2):
    """If input return output1 else return output2.
    """
    return output1 if input else output2


def simplex2(x, y):
    """Simplex noise using noise-library.
    """
    return snoise2(x, y)


def perlin1(x):
    """1D Perlin noise using noise-library.
    """
    return pnoise1(x)


def perlin2(x, y):
    """2D Perlin noise using noise-library.
    """
    return pnoise2(x, y)


def plasma(x, y, t, scale):
    """ Plasma function.

    .. see:

        `Plasma effect <https://www.bidouille.org/prog/plasma>`_.

    :param float x:
        X of plasma
    :param float y:
        Y of plasma
    :param float t:
        Time step
    :param scale:
        Scale of plasma
    """
    if scale <= 0:
        scale = MINVAL
    v1 = math.sin(x * scale + t)
    v2 = math.sin(scale * (x * math.sin(t / 2) + y * math.cos(t / 3)) + t)
    cx = x + 1.0 * math.sin(t / 5)
    cy = y + 1.0 * math.cos(t / 3)
    v3 = math.sin(math.sqrt(scale ** 2 * (cx ** 2 + cy ** 2) + 1) + t)
    return v1 + v2 + v3


def parab(x):
    """Parabola function.

    x is clamped in [-100000, 100000].
    """
    if x > 100000:
        x = 100000
    if x < -100000:
        x = -100000
    return 4 * (x - 0.5) ** 2


def avg_sum(x, y):
    """Average of x and y.
    """
    return (x + y) / 2
