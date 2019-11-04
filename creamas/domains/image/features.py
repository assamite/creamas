"""
.. py:module:: features
    :platform: Unix

Various feature implementations for images requiring ``pip install creamas[extras]``.
"""

import numpy as np
import cv2

from creamas.rules.feature import Feature

__all__ = ['ImageComplexityFeature', 'ImageRednessFeature',
           'ImageGreennessFeature', 'ImageBluenessFeature',
           'ImageIntensityFeature', 'ImageBenfordsLawFeature',
           'ImageEntropyFeature', 'ImageSymmetryFeature']


def fractal_dimension(image):
    """Estimates the fractal dimension of an image with box counting.
    Counts pixels with value 0 as empty and everything else as non-empty.
    Input image has to be grayscale.

    See, e.g `fractal dimension on Wikipedia <https://en.wikipedia.org/wiki/Fractal_dimension>`_.

    :param numpy.ndarray image: Grayscale image as numpy array.
    :returns: estimation of the fractal dimension
    :rtype: float
    """
    pixels = np.asarray(np.nonzero(image > 0)).transpose()

    lx = image.shape[1]
    ly = image.shape[0]
    if len(pixels) < 2:
        return 0
    scales = np.logspace(1, 4, num=20, endpoint=False, base=2)
    Ns = []
    for scale in scales:
        H, edges = np.histogramdd(pixels, bins=(np.arange(0, lx, scale), np.arange(0, ly, scale)))
        H_sum = np.sum(H > 0)
        if H_sum == 0:
            H_sum = 1
        Ns.append(H_sum)

    coeffs = np.polyfit(np.log(scales), np.log(Ns), 1)
    hausdorff_dim = -coeffs[0]

    return hausdorff_dim


def channel_portion(image, channel):
    """Estimates the amount of color channel relative to other colors.

    :param image: numpy.ndarray
    :param channel: int
    :returns: portion of a channel in an image
    :rtype: float
    """
    # Separate color channels
    rgb = []
    for i in range(3):
        rgb.append(image[:, :, i].astype(int))
    ch = rgb.pop(channel)

    relative_values = ch - np.sum(rgb, axis=0) / 2
    relative_values = np.maximum(np.zeros(ch.shape), relative_values)

    return float(np.average(relative_values) / 255)


def intensity(image):
    """Calculates the average intensity of the pixels in an image.
    Accepts both RGB and grayscale images.

    :param image: numpy.ndarray
    :returns: image intensity
    :rtype: float
    """
    if len(image.shape) > 2:
        # Convert to grayscale
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) / 255
    elif issubclass(image.dtype.type, np.integer):
        image /= 255
    return float(np.sum(image) / np.prod(image.shape))


class ImageComplexityFeature(Feature):
    def __init__(self):
        """Feature that estimates the fractal dimension of an image. The color values must be in range [0, 255] and
        type ``int``. Returns a ``float``.
        """
        super().__init__('image_complexity', ['image'], float)

    def extract(self, artifact, canny_threshold1=100, canny_threshold2=200):
        """Extract fractal dimension estimate from the given image artifact.

        The method first extracts edges using :class:`cv2.Canny` and the resulting edge image is passed down to the
        fractal dimension estimator.
        """
        img = artifact.obj
        if len(img.shape) > 2:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(img, canny_threshold1, canny_threshold2)
        return float(fractal_dimension(edges))


class ImageBenfordsLawFeature(Feature):
    def __init__(self, ):
        """Feature that computes the Benford's Law for the image.

        .. seealso::
            `Benford's Law <https://en.wikipedia.org/wiki/Benford%27s_law>`_
        """
        super().__init__("image_Benfords_law", ['image'], float)
        # Histogram bin values for Benford
        self.b = [0.301, 0.176, 0.125, 0.097, 0.079, 0.067, 0.058, 0.051, 0.046]
        self.b_max = (1.0 - self.b[0]) + np.sum(self.b[1:])

    def extract(self, artifact):
        img = artifact.obj
        # Convert color image to black and white
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        hist = cv2.calcHist([img], [0], None, [9], [0, 256])
        # Sort, reverse and rescale to give the histogram a sum of 1.0
        h2 = np.sort(hist, 0)[::-1] * (1.0 / np.sum(hist))
        # Compute Benford's Law feature
        total = np.sum([np.abs(h2[i] - self.b[i]) for i in range(len(h2))])
        benford = float(1.0 - (total / self.b_max))
        return 0.0 if benford < 0 else benford


class ImageEntropyFeature(Feature):
    MIN = 0.0
    # Max entropy for 256 bins, i.e. the histogram has even distribution
    MAX = 5.5451774444795623

    def __init__(self, normalize=False):
        """Compute entropy of an image and normalize it to interval [0, 1].

        Entropy computation uses 256 bins and a grey scale image.

        :param bool normalize:
            Should the returned entropy value be normalized.
        """
        super().__init__('image_entropy', ['image'], float)
        self._normalize = normalize

    def extract(self, artifact):
        img = artifact.obj
        # Convert color image to black and white
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        img = img.astype(np.uint8)
        hg = cv2.calcHist([img], [0], None, [256], [0, 256])
        # Compute probabilities for each bin in histogram
        hg = hg / (img.shape[0] * img.shape[1])
        # Compute entropy based on bin probabilities
        e = -np.sum([hg[i] * np.log(hg[i]) for i in range(len(hg)) if hg[i] > 0.0])
        e = float(e)
        if self._normalize:
            return e / ImageEntropyFeature.MAX
        else:
            return e


class ImageSymmetryFeature(Feature):
    HORIZONTAL = 1
    VERTICAL = 2
    DIAGONAL = 4
    ALL_AXES = 7

    def __init__(self, axis, use_entropy=True):
        """Compute symmetry of the image in given ax or combination of axis.

        Feature also allows adding the computed symmetry with "liveliness" of the
        image using ``use_entropy=True``. If entropy is not used, simple images
        (e.g. plain color images) will give high symmetry values.

        :param axis:
            :attr:`ImageSymmetryFeature.HORIZONTAL`,
            :attr:`ImageSymmetryFeature.VERTICAL`,
            :attr:`ImageSymmetryFeature.DIAGONAL`,
            :attr:`ImageSymmetryFeature.ALL_AXES`

            These can be combined, e.g. ``axis=ImageSymmetryFeature.HORIZONTAL+
            ImageSymmetryFeature.VERTICAL``.

        :param bool use_entropy:
            If ``True`` multiples the computed symmetry value with image's entropy
            ("liveliness").
        """
        super().__init__('image_symmetry', ['image'], float)
        self.axis = axis
        self.threshold = 13
        b = "{:0>3b}".format(self.axis)
        self.horizontal = int(b[2])
        self.vertical = int(b[1])
        self.diagonal = int(b[0])
        self.liveliness = use_entropy

    def _hsymm(self, left, right):
        fright = np.fliplr(right)
        delta = np.abs(left - fright)
        t = delta <= self.threshold
        sim = np.sum(t) / (left.shape[0] * left.shape[1])
        return sim

    def _vsymm(self, up, down):
        fdown = np.flipud(down)
        delta = np.abs(up - fdown)
        t = delta <= self.threshold
        sim = np.sum(t) / (up.shape[0] * up.shape[1])
        return sim

    def _dsymm(self, ul, ur, dl, dr):
        fdr = np.fliplr(np.flipud(dr))
        fur = np.fliplr(np.flipud(ur))
        d1 = np.abs(ul - fdr)
        d2 = np.abs(dl - fur)
        t1 = d1 <= self.threshold
        t2 = d2 <= self.threshold
        s1 = np.sum(t1) / (ul.shape[0] * ul.shape[1])
        s2 = np.sum(t2) / (ul.shape[0] * ul.shape[1])
        return (s1 + s2) / 2

    def extract(self, artifact):
        """Return symmetry of the image.
        """
        img = artifact.obj
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        img = img * 1.0
        cx = int(img.shape[0] / 2)
        cy = int(img.shape[1] / 2)
        n = 0
        symms = 0.0
        liv = 1.0
        if self.horizontal:
            symms += self._hsymm(img[:, :cy], img[:, cx:])
            n += 1
        if self.vertical:
            symms += self._vsymm(img[:cx, :], img[cx:, :])
            n += 1
        if self.diagonal:
            symms += self._dsymm(img[:cx, :cy], img[:cx, cy:],
                                 img[cx:, :cy], img[cx:, cy:])
            n += 1
        if self.liveliness:
            ie = ImageEntropyFeature(normalize=True)
            liv = ie(artifact)

        return float(liv * (symms / n))


class ImageRednessFeature(Feature):
    def __init__(self):
        """Feature that measures the redness of an RGB image. Returns a ``float`` in range [0, 1].
        """
        super().__init__('image_redness', ['image'], float)

    def extract(self, artifact):
        """Get redness of the image.
        """
        return channel_portion(artifact.obj, 0)


class ImageGreennessFeature(Feature):
    def __init__(self):
        """Feature that measures the greenness of an RGB image. Returns a ``float`` in range [0, 1].
        """
        super().__init__('image_greenness', ['image'], float)

    def extract(self, artifact):
        """Get greenness of the image.
        """
        return channel_portion(artifact.obj, 1)


class ImageBluenessFeature(Feature):
    def __init__(self):
        """Feature that measures the blueness of an  RGB image. Returns a ``float`` in range [0, 1].
        """
        super().__init__('image_blueness', ['image'], float)

    def extract(self, artifact):
        """Get blueness of the image.
        """
        return channel_portion(artifact.obj, 2)


class ImageIntensityFeature(Feature):
    def __init__(self):
        """Feature that measures the intensity of an image. Returns a ``float`` in range [0, 1].
        """
        super().__init__('image_intensity', ['image'], float)

    def extract(self, artifact):
        """Get average intensity of the image.
        """
        return intensity(artifact.obj)
