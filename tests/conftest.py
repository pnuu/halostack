"""Shared fixtures.

The old test suite shipped five zero-byte JPEGs, so nothing could ever open an
image.  These fixtures generate real files instead, which lets the tests cover
reading, alignment, stacking and writing end to end.
"""

import numpy as np
import pytest

from halostack import io


def synthetic_frame(shape=(60, 80), offset=(0, 0), seed=0, blob=0.9):
    """Return a frame with a bright blob at a known, shiftable position.

    :param shape: (height, width) of the frame
    :param offset: (dx, dy) displacement of the blob from the centre
    :param seed: seed for the background noise
    :param blob: brightness of the blob
    :rtype: numpy.ndarray of float32, shape (height, width, 3)
    """
    rng = np.random.default_rng(seed)
    data = rng.random((shape[0], shape[1], 3)).astype(np.float32) * 0.05

    centre_y = shape[0] // 2 + offset[1]
    centre_x = shape[1] // 2 + offset[0]
    y_grid, x_grid = np.ogrid[:shape[0], :shape[1]]
    disc = ((y_grid - centre_y) ** 2 + (x_grid - centre_x) ** 2) <= 16
    data[disc] = blob

    return data


@pytest.fixture
def make_frame():
    """The frame builder itself, for tests that need several frames.

    Exposed as a fixture rather than imported across test modules, so that
    the suite does not depend on the repository being on sys.path -- which
    differs between `pytest` and `python -m pytest`.
    """
    return synthetic_frame


@pytest.fixture
def frame():
    """A single synthetic frame."""
    return synthetic_frame()


@pytest.fixture
def frame_files(tmp_path):
    """Three PNG files whose blob moves by a known amount between them.

    :rtype: (list of filenames, list of (dx, dy) offsets)
    """
    offsets = [(0, 0), (3, 2), (-4, 3)]
    fnames = []
    for number, offset in enumerate(offsets):
        fname = tmp_path / ("frame%d.png" % number)
        io.write(str(fname), synthetic_frame(offset=offset, seed=number))
        fnames.append(str(fname))

    return fnames, offsets
