"""Tests for the stacking modes."""

import numpy as np
import pytest

from halostack.image import Image
from halostack.stack import Stack, _sigma_clip


def constant(value, shape=(2, 2, 3)):
    """An Image whose pixels all hold *value*."""
    return Image(img=np.full(shape, value, dtype=np.float32))


@pytest.mark.parametrize('mode', Stack.MODES)
def test_every_mode_returns_an_image(mode):
    """Each mode must produce an Image of the frames' shape."""
    stack = Stack(mode, 3)
    for value in (0.2, 0.4, 0.6):
        stack.add_image(constant(value))

    result = stack.calculate()
    assert isinstance(result, Image)
    assert result.shape == (2, 2, 3)


def test_minimum_and_maximum():
    """min keeps the darkest pixel and max the brightest."""
    minimum, maximum = Stack('min', 3), Stack('max', 3)
    for value in (0.2, 0.9, 0.5):
        minimum.add_image(constant(value))
        maximum.add_image(constant(value))

    assert minimum.calculate()[0, 0, 0] == pytest.approx(0.2)
    assert maximum.calculate()[0, 0, 0] == pytest.approx(0.9)


def test_mean_is_a_mean_not_a_sum():
    """Regression: the average stack used to return the sum of the frames."""
    stack = Stack('mean', 3)
    for value in (0.2, 0.4, 0.6):
        stack.add_image(constant(value))

    assert stack.calculate()[0, 0, 0] == pytest.approx(0.4)


def test_stacks_do_not_share_a_buffer():
    """Regression: several stacks held and overwrote the same first frame."""
    stacks = [Stack(mode, 2) for mode in ('min', 'max', 'mean')]
    first, second = constant(0.1), constant(0.8)
    for stack in stacks:
        stack.add_image(first)
        stack.add_image(second)

    assert stacks[0].calculate()[0, 0, 0] == pytest.approx(0.1)
    assert stacks[1].calculate()[0, 0, 0] == pytest.approx(0.8)
    assert stacks[2].calculate()[0, 0, 0] == pytest.approx(0.45)


def test_input_images_are_not_modified():
    """Adding an image to a stack must leave the caller's image alone."""
    first = constant(0.1)
    stack = Stack('min', 2)
    stack.add_image(first)
    stack.add_image(constant(0.8))

    assert first[0, 0, 0] == pytest.approx(0.1)


def test_deep_stacks_ignore_frames_that_never_arrived():
    """Regression: unfilled slots held uninitialised memory."""
    for mode, expected in (('median', 0.4), ('sigma', 0.4)):
        stack = Stack(mode, 9)          # promised nine, given three
        for value in (0.4, 0.4, 0.4):
            stack.add_image(constant(value))
        assert stack.calculate()[0, 0, 0] == pytest.approx(expected)


def test_median_picks_the_middle_value():
    """The median of an odd number of frames is the middle one."""
    stack = Stack('median', 3)
    for value in (0.1, 0.7, 0.2):
        stack.add_image(constant(value))

    assert stack.calculate()[0, 0, 0] == pytest.approx(0.2)


def test_sigma_rejects_an_outlier():
    """A frame far from the others must not pull the average."""
    stack = Stack('sigma', 9, kwargs={'kappa': 2.0, 'max_iters': 3})
    for value in [0.1] * 8 + [0.9]:
        stack.add_image(constant(value))

    assert stack.calculate()[0, 0, 0] == pytest.approx(0.1)


def test_sigma_keeps_black_pixels():
    """Regression: zero-valued pixels were treated as missing data."""
    stack = Stack('sigma', 3, kwargs={'kappa': 2.0, 'max_iters': 2})
    for _ in range(3):
        stack.add_image(constant(0.0))

    assert stack.calculate()[0, 0, 0] == pytest.approx(0.0)


def test_sigma_without_outliers_is_the_plain_mean():
    """With nothing to reject, sigma and mean must agree."""
    values = [0.30, 0.32, 0.34, 0.36]
    sigma = Stack('sigma', len(values), kwargs={'kappa': 3.0})
    mean = Stack('mean', len(values))
    for value in values:
        sigma.add_image(constant(value))
        mean.add_image(constant(value))

    assert sigma.calculate()[0, 0, 0] == pytest.approx(
        mean.calculate()[0, 0, 0], abs=1e-6)


def test_sigma_clip_never_empties_a_pixel():
    """Even pathological data must leave a finite result."""
    assert np.isfinite(_sigma_clip(np.zeros((5, 2, 2)), 0.1, 5)).all()


def test_mismatched_shapes_are_rejected():
    """Stacking frames of different sizes is a mistake worth naming."""
    stack = Stack('mean', 2)
    stack.add_image(constant(0.5, shape=(4, 4, 3)))

    with pytest.raises(ValueError, match='shape'):
        stack.add_image(constant(0.5, shape=(5, 5, 3)))


def test_unknown_mode_is_rejected():
    """An unknown mode names the ones that exist."""
    with pytest.raises(ValueError, match='median'):
        Stack('nosuchmode', 1)


def test_empty_stack_is_reported():
    """Calculating an empty stack explains itself instead of crashing."""
    with pytest.raises(ValueError, match='No images'):
        Stack('mean', 1).calculate()
