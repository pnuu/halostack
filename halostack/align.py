#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014, 2015 Panu Lahtinen

# Author(s):

# Panu Lahtinen <pnuu+git@iki.fi>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Coaligning images on a reference feature.

The reference patch is located in each frame by normalized cross-correlation
evaluated with FFTs.  This replaces a pixel-by-pixel least-squares search that
had to be spread over a process pool to be bearable; the FFT form examines
every candidate position at once, so it is both faster and free of the
multiprocessing machinery.
"""

import logging

import numpy as np
from scipy.signal import fftconvolve

from halostack.enhancements import luminance
from halostack.image import Image

LOGGER = logging.getLogger(__name__)

#: Correlations below this are treated as no match at all.
_EPSILON = 1e-9


def _as_array(img):
    """Return the 2-D luminance of *img*, which may be an Image or an array."""
    if isinstance(img, Image):
        img = img.img

    return np.asarray(luminance(np.asarray(img)), dtype=np.float64)


def normalized_cross_correlation(image, template):
    """Correlate *template* against every position in *image*.

    :param image: image to search
    :type image: 2-dimensional numpy.ndarray
    :param template: pattern to look for; must not be larger than *image*
    :type template: 2-dimensional numpy.ndarray
    :rtype: numpy.ndarray of correlation coefficients, one per valid position

    Element ``[i, j]`` of the result is the Pearson correlation between the
    template and the window of *image* whose top-left corner is ``(i, j)``.
    """
    image = np.asarray(image, dtype=np.float64)
    template = np.asarray(template, dtype=np.float64)

    if image.ndim != 2 or template.ndim != 2:
        raise ValueError("Cross-correlation needs two-dimensional data.")
    if any(t > i for t, i in zip(template.shape, image.shape)):
        raise ValueError("The reference area (%s) does not fit inside the "
                         "search area (%s)." % (template.shape, image.shape))

    centred = template - template.mean()
    template_energy = float((centred ** 2).sum())
    if template_energy <= _EPSILON:
        # A featureless reference correlates with nothing.
        LOGGER.warning("The reference area is uniform; it cannot be matched.")
        return np.zeros([i - t + 1 for i, t in zip(image.shape, template.shape)])

    # Cross-correlation is convolution with the mirrored kernel.  Because the
    # template is mean-subtracted, this is already the covariance numerator.
    numerator = fftconvolve(image, centred[::-1, ::-1], mode='valid')

    # Windowed sums of the image and of its square give the local variance.
    window = np.ones_like(template)
    count = float(template.size)
    window_sum = fftconvolve(image, window, mode='valid')
    window_sum_squares = fftconvolve(image * image, window, mode='valid')
    variance = window_sum_squares - window_sum ** 2 / count
    # Cancellation in the line above can leave a tiny negative value.
    np.clip(variance, 0.0, None, out=variance)

    denominator = np.sqrt(variance * template_energy)
    correlation = np.zeros_like(numerator)
    usable = denominator > _EPSILON
    correlation[usable] = numerator[usable] / denominator[usable]

    return np.clip(correlation, -1.0, 1.0)


class Align(object):
    """Coalign images against a reference area of a reference image.

    :param img: reference image
    :type img: Image or numpy.ndarray
    :param cor_th: minimum acceptable correlation, squared, in [0, 1]
    :type cor_th: float
    :param mode: matching method; only ``'simple'`` exists
    :type mode: str
    :param nprocs: accepted and ignored, kept for backwards compatibility
    :type nprocs: int

    Call :meth:`set_reference` and :meth:`set_search_area` before
    :meth:`align`.
    """

    #: Matching methods, by name.
    MODES = ('simple',)

    def __init__(self, img, cor_th=0.7, mode='simple', nprocs=1):
        LOGGER.debug("Initialising aligner using %s mode.", mode)

        if mode not in self.MODES:
            LOGGER.warning("Alignment mode %s not recognized, using 'simple' "
                           "instead.", mode)
            mode = 'simple'
        self.mode = mode

        self.img = _as_array(img)
        self._img_shape = self.img.shape
        self.correlation_threshold = cor_th

        self.ref_loc = None
        self.ref = None
        # Default to searching the whole image, in the same (x, y, radius)
        # form that set_search_area expects.
        height, width = self._img_shape[:2]
        self.srch_area = (width // 2, height // 2, max(height, width))

        if nprocs not in (None, 1):
            LOGGER.debug("Alignment no longer uses multiple processes; "
                         "the FFT search examines all positions at once.")

    def set_reference(self, area):
        """Set the reference area to match against.

        The full reference image is released afterwards, so this can only be
        called once.

        :param area: (x, y, radius) of the reference feature
        :type area: 3-element sequence
        """
        if self.img is None:
            raise RuntimeError("The reference image has already been released; "
                               "set_reference() can only be called once.")
        LOGGER.debug("Setting reference location: (%d, %d), radius: %d.",
                     area[0], area[1], area[2])
        self.ref_loc = tuple(int(val) for val in area[:3])
        self.ref = self._cut_reference(self.img, self.ref_loc)
        if self.ref.size == 0:
            raise ValueError("The reference area lies outside the image.")
        # The full frame is no longer needed and is the largest thing here.
        self.img = None

    def set_search_area(self, area):
        """Set the area of each frame that is searched for the reference.

        :param area: (x, y, radius) of the search area
        :type area: 3-element sequence
        """
        LOGGER.debug("Setting search area to center: (%d, %d), radius: %d.",
                     area[0], area[1], area[2])
        self.srch_area = tuple(int(val) for val in area[:3])

    @staticmethod
    def _cut(img, area):
        """Return the square of *img* described by an (x, y, radius) area."""
        x_c, y_c, radius = area
        y_1 = max(0, y_c - radius)
        x_1 = max(0, x_c - radius)
        y_2 = min(img.shape[0], y_c + radius + 1)
        x_2 = min(img.shape[1], x_c + radius + 1)

        return img[y_1:y_2, x_1:x_2], (x_1, y_1)

    def _cut_reference(self, img, area):
        """Return only the data of :meth:`_cut`."""
        return self._cut(img, area)[0]

    def match(self, img):
        """Locate the reference area in *img*.

        :param img: image to search
        :type img: Image or numpy.ndarray
        :rtype: (correlation, x, y) with correlation in [0, 1]

        The correlation returned is the squared Pearson coefficient, matching
        the scale the ``-t`` command line option has always used.
        """
        if self.ref is None:
            raise RuntimeError("No reference area has been set.")

        data = _as_array(img)
        search, (offset_x, offset_y) = self._cut(data, self.srch_area)

        # The search window has to be at least as large as the reference.
        ref_height, ref_width = self.ref.shape
        if search.shape[0] < ref_height or search.shape[1] < ref_width:
            LOGGER.debug("Search area smaller than the reference; "
                         "searching the whole frame instead.")
            search, (offset_x, offset_y) = data, (0, 0)
            if search.shape[0] < ref_height or search.shape[1] < ref_width:
                raise ValueError("The reference area is larger than the image.")

        LOGGER.debug("Searching for the best match using an FFT correlation "
                     "over %s positions.",
                     (search.shape[0] - ref_height + 1,
                      search.shape[1] - ref_width + 1))
        correlation = normalized_cross_correlation(search, self.ref)

        peak = np.unravel_index(np.argmax(correlation), correlation.shape)
        best = float(correlation[peak])

        # Convert the window's top-left corner back to the centre of the match
        # in the coordinates of the full frame.
        x_loc = offset_x + peak[1] + ref_width // 2
        y_loc = offset_y + peak[0] + ref_height // 2

        return best ** 2, x_loc, y_loc

    def align(self, img):
        """Align *img* with the reference image.

        :param img: image to align
        :type img: Image
        :rtype: Image, or None if the image did not match well enough
        """
        LOGGER.info("Calculating image alignment.")

        correlation, x_loc, y_loc = self.match(img)
        if correlation < self.correlation_threshold:
            LOGGER.warning("Correlation (%.3f) lower than the given "
                           "threshold (%.3f).",
                           correlation, self.correlation_threshold)
            return None
        LOGGER.info("Match found, correlation: %.3f.", correlation)

        x_shift, y_shift = self._calc_shift(x_loc, y_loc)
        LOGGER.debug("Shifting image: x = %d, y = %d.", x_shift, y_shift)

        return self._shift(img, x_shift, y_shift)

    def _calc_shift(self, x_loc, y_loc):
        """Return how far the image has to move to line up with the reference."""
        LOGGER.debug("Calculating shift.")
        return self.ref_loc[0] - x_loc, self.ref_loc[1] - y_loc

    @staticmethod
    def _calc_shift_ranges(shape, x_shift, y_shift):
        """Return the output and input slices for a shift, as x/y ranges."""
        width = shape[1] - int(abs(x_shift))
        height = shape[0] - int(abs(y_shift))
        width = max(width, 0)
        height = max(height, 0)

        if x_shift < 0:
            out_x, in_x = (0, width), (-x_shift, -x_shift + width)
        else:
            out_x, in_x = (x_shift, x_shift + width), (0, width)
        if y_shift < 0:
            out_y, in_y = (0, height), (-y_shift, -y_shift + height)
        else:
            out_y, in_y = (y_shift, y_shift + height), (0, height)

        return out_x, out_y, in_x, in_y

    def _shift(self, img, x_shift, y_shift):
        """Return *img* moved by the given number of pixels, padded with zeros."""
        LOGGER.debug("Shifting image.")
        data = img.img if isinstance(img, Image) else np.asarray(img)

        out_x, out_y, in_x, in_y = self._calc_shift_ranges(data.shape,
                                                           x_shift, y_shift)
        shifted = np.zeros_like(data)
        shifted[out_y[0]:out_y[1], out_x[0]:out_x[1]] = \
            data[in_y[0]:in_y[1], in_x[0]:in_x[1]]

        if isinstance(img, Image):
            return Image(img=shifted)

        return shifted
