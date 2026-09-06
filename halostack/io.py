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

"""Image reading and writing.

Every backend used here ships as a binary wheel for Windows, macOS and Linux,
so Halostack has no system-level dependencies.  Formats are dispatched to the
backend that handles them without losing data:

``.png``
    :mod:`imagecodecs` (libpng).  Pillow cannot *write* 16-bit RGB PNG at all
    and silently truncates one to 8 bits when reading, which would quietly
    throw away half the dynamic range of a stack.
``.tif``, ``.tiff``
    :mod:`tifffile`, which handles 8-, 16- and 32-bit data natively.
raw formats
    :mod:`rawpy`, an optional extra (``pip install halostack[raw]``).
everything else
    :mod:`imageio` with its Pillow backend, for 8-bit formats such as JPEG.

Images are handed to the rest of Halostack as ``float32`` arrays scaled to
``[0, 1]``, so no code outside this module has to care about the bit depth or
the file format the data came from.
"""

import logging
import os

import numpy as np

LOGGER = logging.getLogger(__name__)

#: Extensions handled by :mod:`rawpy` rather than by an ordinary image reader.
RAW_EXTENSIONS = frozenset((
    '.3fr', '.arw', '.cr2', '.cr3', '.crw', '.dcr', '.dng', '.erf', '.iiq',
    '.kdc', '.mef', '.mos', '.mrw', '.nef', '.nrw', '.orf', '.pef', '.raf',
    '.raw', '.rw2', '.rwl', '.sr2', '.srf', '.srw', '.x3f'))

PNG_EXTENSIONS = frozenset(('.png',))
TIFF_EXTENSIONS = frozenset(('.tif', '.tiff'))

#: Formats that cannot store more than 8 bits per channel.
EIGHT_BIT_ONLY = frozenset(('.jpg', '.jpeg', '.jpe', '.gif', '.bmp'))


class ImageFormatError(IOError):
    """Raised when an image cannot be read or written as requested."""


def _extension(fname):
    """Return the lower-case extension of *fname*, including the dot."""
    return os.path.splitext(str(fname))[1].lower()


def to_float(img):
    """Scale integer image data to ``float32`` in ``[0, 1]``.

    Floating point input is passed through unchanged apart from the dtype, on
    the assumption that it is already in a sensible range.

    :param img: image data
    :type img: numpy.ndarray
    :rtype: numpy.ndarray of float32
    """
    if np.issubdtype(img.dtype, np.floating):
        return np.asarray(img, dtype=np.float32)
    if np.issubdtype(img.dtype, np.integer):
        info = np.iinfo(img.dtype)
        if info.min < 0:
            raise ImageFormatError("Signed integer image data is not supported.")
        return img.astype(np.float32) / np.float32(info.max)
    if img.dtype == np.bool_:
        return img.astype(np.float32)
    raise ImageFormatError("Unsupported image dtype: %s" % img.dtype)


def to_integer(img, bits=16):
    """Convert ``[0, 1]`` float data to unsigned integers of *bits* bits.

    Values outside ``[0, 1]`` are clipped rather than allowed to wrap around.

    :param img: image data in the range [0, 1]
    :type img: numpy.ndarray
    :param bits: output bit depth, 8 or 16
    :type bits: int
    :rtype: numpy.ndarray of uint8 or uint16
    """
    if bits not in (8, 16):
        raise ValueError("Only 8- and 16-bit output is supported, not %r." % bits)
    dtype = np.uint8 if bits == 8 else np.uint16
    scale = float(2 ** bits - 1)
    # Round rather than truncate, and compute in float64 so that the top of
    # the range does not fall a quantum short.
    scaled = np.clip(np.asarray(img, dtype=np.float64), 0.0, 1.0) * scale
    return np.rint(scaled).astype(dtype)


def _drop_alpha(img):
    """Discard an alpha channel and promote greyscale data to three channels."""
    if img.ndim == 2:
        return np.repeat(img[:, :, np.newaxis], 3, axis=2)
    if img.ndim != 3:
        raise ImageFormatError("Expected a 2- or 3-dimensional image, got %d "
                               "dimensions." % img.ndim)
    if img.shape[2] == 1:
        return np.repeat(img, 3, axis=2)
    if img.shape[2] in (2, 4):
        LOGGER.debug("Discarding alpha channel.")
        return np.ascontiguousarray(img[:, :, :img.shape[2] - 1])
    if img.shape[2] == 3:
        return img
    raise ImageFormatError("Unsupported channel count: %d" % img.shape[2])


def _read_raw(fname):
    """Read a camera raw file as linear 16-bit RGB."""
    try:
        import rawpy
    except ImportError:
        raise ImageFormatError(
            "Reading %s requires the optional 'rawpy' dependency; install it "
            "with 'pip install halostack[raw]'." % fname)
    LOGGER.debug("Reading %s with rawpy.", fname)
    with rawpy.imread(str(fname)) as raw:
        # Linear output with no automatic brightness: halo photometry wants the
        # sensor's own response, not a display-ready rendering.
        return raw.postprocess(output_bps=16, gamma=(1, 1), no_auto_bright=True,
                               use_camera_wb=True)


def _read_png(fname):
    """Read a PNG of any bit depth."""
    import imagecodecs
    with open(fname, 'rb') as fid:
        return imagecodecs.png_decode(fid.read())


def _read_tiff(fname):
    """Read a TIFF of any bit depth."""
    import tifffile
    return tifffile.imread(str(fname))


def read(fname):
    """Read an image file and return it as float32 RGB in ``[0, 1]``.

    :param fname: name of the file to read
    :type fname: str
    :rtype: numpy.ndarray of shape (height, width, 3)
    """
    fname = str(fname)
    if not os.path.exists(fname):
        raise ImageFormatError("No such file: %s" % fname)
    ext = _extension(fname)

    LOGGER.info("Reading image %s.", fname)
    try:
        if ext in RAW_EXTENSIONS:
            data = _read_raw(fname)
        elif ext in PNG_EXTENSIONS:
            data = _read_png(fname)
        elif ext in TIFF_EXTENSIONS:
            data = _read_tiff(fname)
        else:
            import imageio.v3 as iio
            data = iio.imread(fname)
    except ImageFormatError:
        raise
    except Exception as err:
        raise ImageFormatError("Could not read %s: %s" % (fname, err))

    data = _drop_alpha(np.asarray(data))
    LOGGER.debug("Read %s: %s, %s.", fname, data.shape, data.dtype)

    return to_float(data)


def _write_png(fname, data):
    """Write a PNG at the bit depth of *data*."""
    import imagecodecs
    with open(fname, 'wb') as fid:
        fid.write(imagecodecs.png_encode(data))


def _write_tiff(fname, data):
    """Write a TIFF at the bit depth of *data*."""
    import tifffile
    tifffile.imwrite(str(fname), data)


def write(fname, img, bits=16):
    """Write ``[0, 1]`` float image data to *fname*.

    :param fname: name of the file to write
    :type fname: str
    :param img: image data in the range [0, 1]
    :type img: numpy.ndarray
    :param bits: output bit depth; silently reduced to 8 for formats that
                 cannot hold more
    :type bits: int
    """
    fname = str(fname)
    ext = _extension(fname)

    if bits == 16 and ext in EIGHT_BIT_ONLY:
        LOGGER.debug("%s cannot store 16 bits per channel, writing 8-bit.", ext)
        bits = 8

    data = to_integer(img, bits=bits)

    LOGGER.info("Saving %s.", fname)
    try:
        if ext in PNG_EXTENSIONS:
            _write_png(fname, data)
        elif ext in TIFF_EXTENSIONS:
            _write_tiff(fname, data)
        else:
            import imageio.v3 as iio
            iio.imwrite(fname, data)
    except Exception as err:
        raise ImageFormatError("Could not write %s: %s" % (fname, err))
