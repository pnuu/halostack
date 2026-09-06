#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014, 2015, Panu Lahtinen

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

"""Combining a series of images into a single stack.

``min``, ``max`` and ``mean`` keep a running result and so need memory for one
image regardless of how many are stacked.  ``median`` and ``sigma`` have to see
every frame before they can produce an answer and therefore hold them all.

A stack never keeps a reference to an image it was given: several stacks are
routinely fed the same frames, and sharing a buffer between them would let one
stack overwrite another's result.
"""

import logging

import numpy as np

from halostack.image import IMAGE_DTYPE, Image

LOGGER = logging.getLogger(__name__)

#: Accumulator dtype for the running mean.  Wider than the frames themselves so
#: that adding hundreds of exposures does not lose the low-order bits.
STACK_DTYPE = np.float64

#: Default kappa for sigma stacking.
DEFAULT_KAPPA = 2.0


class Stack(object):
    """A stack of images.

    :param mode: one of ``'min'``, ``'max'``, ``'mean'``, ``'median'`` or
                 ``'sigma'``
    :type mode: str
    :param num: expected number of images; only used to report progress
    :type num: int or None
    :param nprocs: accepted and ignored, kept for backwards compatibility
    :type nprocs: int
    :param kwargs: extra options; ``sigma`` takes ``kappa`` and ``max_iters``
    :type kwargs: dict or None
    """

    #: The stacking methods that exist, in the order the CLI presents them.
    MODES = ('min', 'max', 'mean', 'median', 'sigma')

    def __init__(self, mode, num=None, nprocs=1, kwargs=None):
        if mode not in self.MODES:
            raise ValueError("Unknown stack type %r. Available types: %s."
                             % (mode, ', '.join(self.MODES)))
        LOGGER.debug("Initializing %s stack for %s images.", mode, num)

        self.mode = mode
        self.num = num
        self.nprocs = nprocs
        self._kwargs = kwargs or {}

        self._num = 0
        # Running result for min/max, accumulator for mean, list for the deep
        # modes.  Only one of these is ever in use.
        self.stack = None
        self._frames = [] if mode in ('median', 'sigma') else None
        self._shape = None

        self._update_func = getattr(self, '_update_' + mode)

    def __len__(self):
        return self._num

    @property
    def count(self):
        """Number of images added so far."""
        return self._num

    def add_image(self, img):
        """Add a frame to the stack.

        :param img: image to add
        :type img: Image or numpy.ndarray
        """
        if not isinstance(img, Image):
            LOGGER.debug("Converting %s to Image object.", img)
            img = Image(img=img)

        data = img.img
        if self._shape is None:
            self._shape = data.shape
        elif data.shape != self._shape:
            raise ValueError("Image shape %s does not match the rest of the "
                             "stack, %s." % (data.shape, self._shape))

        LOGGER.debug("Adding image to %s stack.", self.mode)
        self._update_func(data)
        self._num += 1

    def calculate(self):
        """Combine the frames and return the result.

        :rtype: Image
        """
        if self._num == 0:
            raise ValueError("No images were added to the %s stack." % self.mode)

        LOGGER.info("Calculating %s stack of %d images.", self.mode, self._num)
        calculate = getattr(self, '_calculate_' + self.mode)

        return Image(img=calculate())

    # -- running stacks --------------------------------------------------

    def _update_min(self, data):
        """Keep the darkest value seen at each pixel, judged by luminance."""
        if self.stack is None:
            self.stack = data.copy()
            return
        self._keep_where(data, np.less)

    def _update_max(self, data):
        """Keep the brightest value seen at each pixel, judged by luminance."""
        if self.stack is None:
            self.stack = data.copy()
            return
        self._keep_where(data, np.greater)

    def _keep_where(self, data, comparison):
        """Copy pixels of *data* into the stack where its luminance wins."""
        if data.ndim == 3:
            better = comparison(data.mean(axis=2), self.stack.mean(axis=2))
            better = better[:, :, np.newaxis]
        else:
            better = comparison(data, self.stack)

        np.copyto(self.stack, data, where=better)

    def _update_mean(self, data):
        """Accumulate the sum; the division happens in :meth:`calculate`."""
        if self.stack is None:
            self.stack = data.astype(STACK_DTYPE)
            return
        self.stack += data

    def _calculate_min(self):
        return self.stack

    _calculate_max = _calculate_min

    def _calculate_mean(self):
        """Return the arithmetic mean of the frames."""
        return self.stack / self._num

    # -- deep stacks -----------------------------------------------------

    def _update_median(self, data):
        """Remember the frame; the median needs all of them."""
        self._frames.append(data.copy())

    _update_sigma = _update_median

    def _stacked_frames(self):
        """Return the frames as one array, and forget the individual ones."""
        data = np.stack(self._frames, axis=0)
        # The frames are the largest thing in the process; release them as soon
        # as the combined array exists.
        del self._frames[:]

        return data

    def _calculate_median(self):
        """Return the per-pixel median of the frames."""
        return np.median(self._stacked_frames(), axis=0).astype(IMAGE_DTYPE)

    def _calculate_sigma(self):
        """Return the per-pixel mean of the frames, rejecting outliers.

        Values further than *kappa* standard deviations from the mean are
        masked and the mean recomputed, up to *max_iters* times or until
        nothing more is rejected.
        """
        kappa = float(self._kwargs.get('kappa') or DEFAULT_KAPPA)
        max_iters = self._kwargs.get('max_iters')
        if not max_iters:
            max_iters = max(1, self._num // 8)
        max_iters = int(max_iters)

        LOGGER.info("Calculating kappa-sigma average, kappa=%.2f, "
                    "max_iters=%d.", kappa, max_iters)

        data = self._stacked_frames()
        out = np.empty(data.shape[1:], dtype=IMAGE_DTYPE)

        # One channel at a time: the boolean mask is the same size as the whole
        # stack, and there is no reason to hold a copy of it for every channel
        # at once.
        if data.ndim == 4:
            for chan in range(data.shape[3]):
                out[:, :, chan] = _sigma_clip(data[:, :, :, chan], kappa,
                                              max_iters)
        else:
            out[:] = _sigma_clip(data, kappa, max_iters)

        return out


def _sigma_clip(data, kappa, max_iters):
    """Return the kappa-sigma clipped mean along the first axis.

    :param data: frames stacked along axis 0
    :type data: numpy.ndarray
    :param kappa: rejection threshold in standard deviations
    :type kappa: float
    :param max_iters: maximum number of rejection passes
    :type max_iters: int
    :rtype: numpy.ndarray with the first axis removed
    """
    data = data.astype(STACK_DTYPE, copy=False)
    keep = np.ones(data.shape, dtype=bool)
    count = np.full(data.shape[1:], data.shape[0], dtype=STACK_DTYPE)
    mean = data.mean(axis=0)

    for _ in range(max_iters):
        deviation = data - mean
        variance = np.sum(np.where(keep, deviation * deviation, 0.0), axis=0)
        std = np.sqrt(variance / count)

        still_keep = keep & (np.abs(deviation) <= kappa * std)
        # A pixel whose samples all fall outside the threshold would be left
        # with nothing to average; keep what it had instead.
        empty = ~still_keep.any(axis=0)
        if empty.any():
            still_keep[:, empty] = keep[:, empty]

        if np.array_equal(still_keep, keep):
            break

        keep = still_keep
        count = keep.sum(axis=0).astype(STACK_DTYPE)
        mean = np.sum(np.where(keep, data, 0.0), axis=0) / count

    return mean
