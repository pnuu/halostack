"""Tests for coalignment."""

import numpy as np
import pytest

from halostack.align import Align, normalized_cross_correlation
from halostack.image import Image
from tests.conftest import synthetic_frame


@pytest.fixture
def aligner():
    """An aligner referenced on the blob in the middle of a 60x80 frame."""
    align = Align(Image(img=synthetic_frame()), cor_th=0.7)
    align.set_reference((40, 30, 8))
    align.set_search_area((40, 30, 20))

    return align


def test_default_threshold_is_usable():
    """Regression: the default was 70.0, which rejected every image."""
    assert 0.0 <= Align(np.zeros((10, 10))).correlation_threshold <= 1.0


def test_correlation_peaks_at_the_true_position():
    """A template cut from an image correlates perfectly with its origin."""
    image = synthetic_frame()[:, :, 0]
    template = image[20:30, 30:40]

    correlation = normalized_cross_correlation(image, template)
    assert correlation.max() == pytest.approx(1.0)
    assert np.unravel_index(np.argmax(correlation), correlation.shape) == (20, 30)


def test_correlation_rejects_an_oversized_template():
    """A reference bigger than the search area is a clear error."""
    with pytest.raises(ValueError, match='does not fit'):
        normalized_cross_correlation(np.zeros((4, 4)), np.zeros((8, 8)))


def test_uniform_reference_does_not_divide_by_zero():
    """A featureless reference correlates with nothing, but must not crash."""
    correlation = normalized_cross_correlation(np.random.rand(10, 10),
                                               np.ones((3, 3)))

    assert np.isfinite(correlation).all()


@pytest.mark.parametrize('offset', [(0, 0), (3, 2), (-4, 3), (7, -6), (-9, 8)])
def test_match_finds_the_shifted_reference(aligner, offset):
    """The matched centre must move exactly with the blob."""
    moved = Image(img=synthetic_frame(offset=offset, seed=1))

    correlation, x_loc, y_loc = aligner.match(moved)
    assert correlation > 0.7
    assert (x_loc, y_loc) == (40 + offset[0], 30 + offset[1])


def test_align_undoes_the_shift(aligner):
    """An aligned frame must line up with the reference frame."""
    original = synthetic_frame()
    aligned = aligner.align(Image(img=synthetic_frame(offset=(5, -3))))

    # Ignore the border, which the shift fills with zeros.
    assert aligned is not None
    inner = (slice(10, -10), slice(10, -10))
    assert np.abs(aligned.img[inner] - original[inner]).max() < 0.2


def test_align_rejects_a_frame_that_does_not_match(aligner):
    """Below the threshold, align() returns None so the frame is skipped."""
    noise = Image(img=np.random.default_rng(7).random((60, 80, 3)).astype(np.float32))

    assert aligner.align(noise) is None


def test_shift_moves_data_and_pads_with_zeros(aligner):
    """The shift itself is a plain translation."""
    data = np.zeros((10, 10, 3), dtype=np.float32)
    data[5, 5] = 1.0

    shifted = aligner._shift(Image(img=data), 2, -3)
    assert shifted[2, 7, 0] == pytest.approx(1.0)
    assert shifted[5, 5, 0] == pytest.approx(0.0)


def test_unknown_mode_falls_back_to_simple():
    """Regression: an unknown mode raised KeyError instead of falling back."""
    assert Align(np.zeros((8, 8)), mode='nosuchmode').mode == 'simple'


def test_search_area_defaults_to_the_whole_image():
    """Regression: the default was a 4-element list in a different layout.

    It has to be an (x, y, radius) triple like every other area, centred on
    the image and large enough to cover it.
    """
    align = Align(np.zeros((40, 60)))
    x_c, y_c, radius = align.srch_area

    assert (x_c, y_c) == (30, 20)
    assert radius >= 30


def test_reference_can_only_be_set_once(aligner):
    """set_reference() releases the reference frame; say so if used again."""
    with pytest.raises(RuntimeError):
        aligner.set_reference((40, 30, 8))
