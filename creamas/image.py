'''
.. py:module:: image
    :platform: Unix

Various image information functions.
'''
import numpy as np
import cv2


def fractal_dimension(image):
    '''Estimates the fractal dimension of an image with box counting.
    Counts pixels with value 0 as empty and everything else as non-empty.
    Input image has to be grayscale.

    See, e.g `Wikipedia <https://en.wikipedia.org/wiki/Fractal_dimension>`_.

    :param image: numpy.ndarray
    :returns: estimation of fractal dimension
    :rtype: float
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


def channel_portion(image, channel):
    '''Estimates the amount of a color relative to other colors.

    :param image: numpy.ndarray
    :param channel: int
    :returns: portion of a channel in an image
    :rtype: float
    '''

    # Separate color channels
    rgb = []
    for i in range(3):
        rgb.append(image[:, :, i].astype(int))
    ch = rgb.pop(channel)

    relative_values = ch - np.sum(rgb, axis=0) / 2
    relative_values = np.maximum(np.zeros(ch.shape), relative_values)

    return np.average(relative_values) / 255


def intensity(image):
    '''Calculates the average intensity of the pixels in an image.
    Accepts both RGB and grayscale images.

    :param image: numpy.ndarray
    :returns: image intensity
    :rtype: float
    '''
    if len(image.shape) > 2:
        # Convert to grayscale
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) / 255
    elif issubclass(image.dtype.type, np.integer):
        image /= 255
    return np.sum(image) / np.prod(image.shape)
