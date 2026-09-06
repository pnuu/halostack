"""Tests for the Image class."""

import numpy as np
import pytest

from halostack.image import Image


@pytest.fixture
def half():
    """An image whose pixels are all 0.5."""
    return Image(img=np.full((3, 3, 3), 0.5, dtype=np.float32))


def test_shape_follows_the_data(half):
    """Regression: shape used to be a stale attribute, often left as None."""
    assert half.shape == (3, 3, 3)
    half.enhance({'br': None})
    assert half.shape == (3, 3)


def test_arithmetic(half):
    """The forward operators return new Images with the expected values."""
    assert (half + 0.25)[0, 0, 0] == pytest.approx(0.75)
    assert (half - 0.25)[0, 0, 0] == pytest.approx(0.25)
    assert (half * 2)[0, 0, 0] == pytest.approx(1.0)
    assert (half / 2)[0, 0, 0] == pytest.approx(0.25)


def test_reflected_subtraction_has_the_right_sign(half):
    """Regression: __rsub__ used to return self - other."""
    assert (1.0 - half)[0, 0, 0] == pytest.approx(0.5)
    assert (0.25 - half)[0, 0, 0] == pytest.approx(-0.25)


def test_reflected_division(half):
    """Regression: reflected division was missing entirely."""
    assert (1.0 / half)[0, 0, 0] == pytest.approx(2.0)


def test_in_place_operators_keep_the_object(half):
    """Regression: `img -= x` used to rebind the name to None."""
    img = half
    img -= 0.25
    assert isinstance(img, Image)
    assert img[0, 0, 0] == pytest.approx(0.25)

    img += 0.5
    assert isinstance(img, Image)
    assert img[0, 0, 0] == pytest.approx(0.75)


def test_copy_is_independent(half):
    """A copy must not share its buffer with the original."""
    other = half.copy()
    other[0, 0, 0] = 0.9

    assert half[0, 0, 0] == pytest.approx(0.5)


def test_luminance_of_colour():
    """Luminance is the mean of the channels and drops the channel axis."""
    data = np.zeros((2, 2, 3), dtype=np.float32)
    data[:, :, 0], data[:, :, 1], data[:, :, 2] = 0.0, 0.5, 1.0

    lum = Image(img=data).luminance()
    assert lum.shape == (2, 2)
    assert lum[0, 0] == pytest.approx(0.5)


def test_save_normalises_to_the_full_range(tmp_path):
    """Saving stretches the data to the output range, as it always has."""
    data = np.linspace(0.2, 0.4, 12).reshape(2, 2, 3).astype(np.float32)
    fname = str(tmp_path / "out.png")
    Image(img=data).save(fname)

    read_back = Image(fname=fname)
    assert read_back.min() == pytest.approx(0.0, abs=1e-4)
    assert read_back.max() == pytest.approx(1.0, abs=1e-4)


def test_save_of_eight_bit_data_does_not_raise(tmp_path, frame):
    """Regression: saving unmodified 8-bit input raised OverflowError."""
    fname = str(tmp_path / "eight.png")
    Image(img=frame).save(fname, bits=16)

    assert Image(fname=fname).shape == frame.shape


def test_image_needs_data():
    """Constructing an empty Image is an error, not a later mystery."""
    with pytest.raises(ValueError):
        Image()


def test_unknown_enhancement_names_the_alternatives(half):
    """Regression: a typo used to raise a bare KeyError."""
    with pytest.raises(ValueError, match='gradient'):
        half.enhance({'gradiant': None})
