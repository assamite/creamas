"""
.. py:module:: features
    :platform: Unix

Various feature implementations. Each feature value takes as
an input an artifact, and returns feature's value for that artifact.
"""
import cv2

from creamas.domains.image.image import channel_portion, intensity
from creamas.domains.image.image import fractal_dimension
from creamas.rules.feature import Feature

__all__ = ['ImageComplexityFeature', 'ImageRednessFeature',
           'ImageGreennessFeature', 'ImageBluenessFeature',
           'ImageIntensityFeature']


class ImageComplexityFeature(Feature):
    """Feature that estimates the fractal dimension of an image.
    The color values must be in range [0, 255] and type ``int``.
    """
    def __init__(self):
        super().__init__('image_complexity', ['image'], float)

    def extract(self, artifact):
        img = artifact.obj
        if len(img.shape) > 2:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(img, 100, 200)
        return float(fractal_dimension(edges))


class ImageRednessFeature(Feature):
    """Feature that measures the redness of an image.
    """

    def __init__(self):
        super().__init__('image_redness', ['image'], float)

    def extract(self, artifact):
        return channel_portion(artifact.obj, 0)


class ImageGreennessFeature(Feature):
    """Feature that measures the greenness of an image.
    """

    def __init__(self):
        super().__init__('image_greenness', ['image'], float)

    def extract(self, artifact):
        return channel_portion(artifact.obj, 1)


class ImageBluenessFeature(Feature):
    """Feature that measures the blueness of an image.
    """

    def __init__(self):
        super().__init__('image_blueness', ['image'], float)

    def extract(self, artifact):
        return channel_portion(artifact.obj, 2)


class ImageIntensityFeature(Feature):
    """Feature that measures the intensity of an image
    """

    def __init__(self):
        super().__init__('image_intensity', ['image'], float)

    def extract(self, artifact):
        return intensity(artifact.obj)
