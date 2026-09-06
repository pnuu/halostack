"""Tests for reading and writing image files."""

import numpy as np
import pytest

from halostack import io


@pytest.mark.parametrize('extension', ['png', 'tif'])
def test_roundtrip_is_lossless_at_16_bits(tmp_path, frame, extension):
    """A 16-bit format must survive a write/read cycle to within a quantum."""
    fname = str(tmp_path / ("test." + extension))
    io.write(fname, frame, bits=16)

    assert np.abs(io.read(fname) - frame).max() < 1.0 / 65535


def test_png_is_written_with_16_bits(tmp_path, frame):
    """Regression: Pillow silently writes 8-bit RGB, losing half the range."""
    imagecodecs = pytest.importorskip('imagecodecs')
    fname = str(tmp_path / "deep.png")
    io.write(fname, frame, bits=16)

    with open(fname, 'rb') as fid:
        assert imagecodecs.png_decode(fid.read()).dtype == np.uint16


def test_png_is_read_with_16_bits(tmp_path, frame):
    """Regression: Pillow silently truncates a 16-bit RGB PNG when reading."""
    fname = str(tmp_path / "deep.png")
    io.write(fname, frame, bits=16)
    # More than 256 distinct values can only survive if 16 bits were kept.
    assert len(np.unique(io.read(fname))) > 256


def test_eight_bit_output(tmp_path, frame):
    """Asking for 8 bits gives 8 bits, not corrupted 16-bit data."""
    fname = str(tmp_path / "shallow.png")
    io.write(fname, frame, bits=8)
    read_back = io.read(fname)

    assert np.abs(read_back - frame).max() < 1.0 / 255
    assert len(np.unique(read_back)) <= 256


def test_jpeg_falls_back_to_eight_bits(tmp_path, frame):
    """JPEG cannot hold 16 bits; asking for them must not raise."""
    fname = str(tmp_path / "test.jpg")
    io.write(fname, frame, bits=16)

    assert io.read(fname).shape == frame.shape


def test_greyscale_is_promoted_to_three_channels(tmp_path):
    """Channel differences need three channels, so reading always gives three."""
    fname = str(tmp_path / "grey.png")
    io.write(fname, np.linspace(0, 1, 64).reshape(8, 8).astype(np.float32))

    assert io.read(fname).shape == (8, 8, 3)


def test_alpha_is_discarded(tmp_path):
    """An alpha channel is dropped rather than treated as image data."""
    rgba = (np.random.rand(6, 6, 4) * 65535).astype(np.uint16)
    fname = str(tmp_path / "alpha.png")
    __import__('imagecodecs')
    with open(fname, 'wb') as fid:
        fid.write(__import__('imagecodecs').png_encode(rgba))

    assert io.read(fname).shape == (6, 6, 3)


def test_to_integer_clips_instead_of_wrapping():
    """Regression: out-of-range values used to wrap around to black."""
    data = np.array([-0.5, 0.0, 0.5, 1.0, 1.5])

    assert io.to_integer(data, bits=8).tolist() == [0, 0, 128, 255, 255]


def test_to_integer_reaches_the_top_of_the_range():
    """1.0 must map to the largest value the bit depth can hold."""
    assert io.to_integer(np.array([1.0]), bits=16)[0] == 65535
    assert io.to_integer(np.array([1.0]), bits=8)[0] == 255


def test_to_float_scales_by_the_dtype_range():
    """Integer input is scaled by its own maximum, not by a hard-coded one."""
    assert io.to_float(np.array([255], dtype=np.uint8))[0] == pytest.approx(1.0)
    assert io.to_float(np.array([65535], dtype=np.uint16))[0] == pytest.approx(1.0)


def test_missing_file_is_reported_clearly(tmp_path):
    """A missing file gives a useful error, not a backend traceback."""
    with pytest.raises(io.ImageFormatError):
        io.read(str(tmp_path / "nope.png"))
