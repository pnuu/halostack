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

"""Image data and the operations that can be applied to it.

An :class:`Image` wraps a single float32 NumPy array.  Unlike the ImageMagick
backed version this class replaced, there is only ever one representation of
the data, so no method has to convert between formats and no operation can
lose precision by round-tripping through an 8- or 16-bit integer buffer.
"""

import logging

import numpy as np

from halostack import io
from halostack.enhancements import ENHANCEMENTS, enhance, luminance

LOGGER = logging.getLogger(__name__)

#: Working dtype.  float32 holds a 16-bit sample exactly while halving the
#: memory needed by the deep stacks compared with float64.
IMAGE_DTYPE = np.float32


class Image(object):
    """Image data.

    :param img: image data, or another Image to copy the data from
    :type img: numpy.ndarray, Image or None
    :param fname: name of an image file to read
    :type fname: str or None
    :param enhancements: image processing to apply immediately
    :type enhancements: dict or None

    Exactly one of *img* and *fname* is normally given.  Data is held as
    float32 scaled to ``[0, 1]``; processing may take it outside that range,
    and :meth:`save` restores it.
    """

    def __init__(self, img=None, fname=None, enhancements=None):
        self.fname = fname

        if img is None and fname is None:
            raise ValueError("An Image needs either data or a filename.")
        if fname is not None:
            img = io.read(fname)
        if isinstance(img, Image):
            img = img.img

        self.img = np.asarray(img, dtype=IMAGE_DTYPE)

        if enhancements:
            LOGGER.info("Preprocessing image.")
            self.enhance(enhancements)

    # -- data description ------------------------------------------------

    @property
    def shape(self):
        """Shape of the image data.  Always current, being read from the array."""
        return self.img.shape

    @property
    def dtype(self):
        """dtype of the image data."""
        return self.img.dtype

    def __repr__(self):
        return "<Image %s %s>" % (self.img.shape, self.img.dtype)

    def copy(self):
        """Return an independent copy of this image.

        :rtype: Image
        """
        return Image(img=self.img.copy())

    def set_dtype(self, dtype):
        """Convert the image data to *dtype*.

        :param dtype: dtype to convert to
        :type dtype: numpy dtype
        """
        LOGGER.debug('Changing dtype from %s to %s.', self.img.dtype, str(dtype))
        self.img = self.img.astype(dtype)

    # -- arithmetic ------------------------------------------------------
    #
    # Stack keeps running results as Images, so these have to behave like
    # numbers.  Reflected and in-place forms included: getting __rsub__ or
    # __isub__ subtly wrong is silent corruption, not an error.

    @staticmethod
    def _operand(other):
        """Return the array underlying *other*, which may be an Image."""
        if isinstance(other, Image):
            return other.img
        return other

    def __add__(self, other):
        return Image(img=self.img + self._operand(other))

    def __radd__(self, other):
        return Image(img=self._operand(other) + self.img)

    def __iadd__(self, other):
        self.img = self.img + self._operand(other)
        return self

    def __sub__(self, other):
        return Image(img=self.img - self._operand(other))

    def __rsub__(self, other):
        return Image(img=self._operand(other) - self.img)

    def __isub__(self, other):
        self.img = self.img - self._operand(other)
        return self

    def __mul__(self, other):
        return Image(img=self.img * self._operand(other))

    def __rmul__(self, other):
        return Image(img=self._operand(other) * self.img)

    def __imul__(self, other):
        self.img = self.img * self._operand(other)
        return self

    def __truediv__(self, other):
        return Image(img=self.img / self._operand(other))

    def __rtruediv__(self, other):
        return Image(img=self._operand(other) / self.img)

    def __itruediv__(self, other):
        self.img = self.img / self._operand(other)
        return self

    # Python 2 spelling, kept so that older client code keeps working.
    __div__ = __truediv__
    __rdiv__ = __rtruediv__

    def __abs__(self):
        return Image(img=np.abs(self.img))

    def __neg__(self):
        return Image(img=-self.img)

    def __lt__(self, other):
        return self.img < self._operand(other)

    def __le__(self, other):
        return self.img <= self._operand(other)

    def __gt__(self, other):
        return self.img > self._operand(other)

    def __ge__(self, other):
        return self.img >= self._operand(other)

    def __eq__(self, other):
        return self.img == self._operand(other)

    def __ne__(self, other):
        return self.img != self._operand(other)

    __hash__ = None  # __eq__ is elementwise, so Images are not hashable.

    def __getitem__(self, idx):
        return self.img[idx]

    def __setitem__(self, idx, val):
        self.img[idx] = self._operand(val)

    def __array__(self, dtype=None, copy=None):
        """Let NumPy treat an Image as the array it wraps."""
        if dtype is None:
            return self.img
        return self.img.astype(dtype)

    # -- statistics ------------------------------------------------------

    def min(self):
        """Return the minimum value in the image.

        :rtype: float
        """
        return self.img.min()

    def max(self):
        """Return the maximum value in the image.

        :rtype: float
        """
        return self.img.max()

    def luminance(self):
        """Return the channel average as a new Image.

        :rtype: Image
        """
        return Image(img=luminance(self.img))

    # -- processing ------------------------------------------------------

    def enhance(self, enhancements):
        """Apply image processing methods to the image, in order.

        :param enhancements: names of methods mapped to their arguments
        :type enhancements: dict

        The available methods, their arguments and their defaults are
        described by :data:`halostack.enhancements.ENHANCEMENTS`; see
        :mod:`halostack.enhancements` for the individual implementations.
        """
        self.img = np.asarray(enhance(self.img, enhancements), dtype=IMAGE_DTYPE)

    def normalized(self):
        """Return the image data scaled so that it spans ``[0, 1]``.

        A stack is an arbitrary sum of exposures, so its absolute scale means
        nothing; stretching to the full output range is what makes the result
        viewable.

        :rtype: numpy.ndarray
        """
        img = self.img.astype(np.float64)
        img = img - img.min()
        maximum = img.max()
        if maximum > 0:
            img = img / maximum

        return img

    def save(self, fname, bits=16, enhancements=None):
        """Write the image to *fname*.

        :param fname: output filename; the format follows the extension
        :type fname: str
        :param bits: output bit depth, 8 or 16
        :type bits: int
        :param enhancements: image processing applied before saving
        :type enhancements: dict or None
        """
        if enhancements:
            LOGGER.info("Postprocessing output image.")
            self.enhance(enhancements)

        io.write(fname, self.normalized(), bits=bits)


def available_enhancements():
    """Return the registered image processing methods.

    Useful for building a user interface: each entry carries a summary and a
    description of every parameter.

    :rtype: dict of str to halostack.enhancements.Enhancement
    """
    return dict(ENHANCEMENTS)
