'''
.. py:module:: features
    :platform: Unix

Various feature implementations. Each feature value takes as
an input an artifact, and returns feature's value for that artifact.
'''
import cv2

from creamas.rules.feature import Feature
from creamas.math import fractal_dimension

__all__ = ['ImageComplexityFeature']


class ImageComplexityFeature(Feature):
    '''Feature that estimates the fractal dimension of an image.
    The color values must be in range [0, 255] and type ``int``.
    '''
    def __init__(self):
        super().__init__('image_complexity', ['image'], float)

    def extract(self, artifact):
        grayscale = cv2.cvtColor(artifact.obj, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(grayscale, 100, 200)
        return float(fractal_dimension(edges))
