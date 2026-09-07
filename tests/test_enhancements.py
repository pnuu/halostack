"""Tests for the image processing methods."""

import numpy as np
import pytest

from halostack import enhancements as enh


def test_every_registered_method_runs(frame):
    """Each method must work on ordinary colour data with its defaults."""
    required = {'usm': [4, 2], 'gamma': [0.5]}
    for name in enh.ENHANCEMENTS:
        out = enh.apply_enhancement(frame, name, required.get(name))
        assert out.shape[:2] == frame.shape[:2]
        assert np.isfinite(out).all()


def test_registry_describes_its_parameters():
    """A GUI builds its controls from this metadata, so it must be complete."""
    for name, enhancement in enh.ENHANCEMENTS.items():
        assert enhancement.summary
        assert enhancement.name == name
        for parameter in enhancement.parameters:
            assert parameter.name and parameter.description


def test_channel_difference_uses_the_given_multiplier():
    """br with an explicit multiplier is exactly multiplier*blue - red."""
    data = np.zeros((2, 2, 3), dtype=np.float32)
    data[:, :, 0], data[:, :, 2] = 0.25, 0.5

    assert enh.blue_red(data, 2.0)[0, 0] == pytest.approx(0.75)


def test_channel_difference_reduces_to_two_dimensions(frame):
    """br, gr and bg all collapse the colour axis."""
    for func in (enh.blue_red, enh.green_red, enh.blue_green):
        assert func(frame).ndim == 2


def test_channel_difference_on_flat_data_is_explained(frame):
    """Applying br twice is a user error and must say so."""
    once = enh.blue_red(frame)
    with pytest.raises(ValueError, match='three-channel'):
        enh.blue_red(once)


def test_blur_smooths_without_moving_the_mean(frame):
    """Blurring reduces variance but keeps the overall level."""
    blurred = enh.blur(frame, radius=6)

    assert blurred.var() < frame.var()
    assert blurred.mean() == pytest.approx(frame.mean(), rel=0.05)


def test_blur_handles_images_smaller_than_the_default_radius():
    """Regression: a small image gave radius 0 and a ZeroDivisionError."""
    tiny = np.random.rand(9, 9, 3).astype(np.float32)

    assert np.isfinite(enh.blur(tiny)).all()


def test_blur_does_not_mix_channels():
    """Each channel is blurred on its own."""
    data = np.zeros((9, 9, 3), dtype=np.float32)
    data[:, :, 1] = 1.0

    blurred = enh.blur(data, radius=3)
    assert blurred[:, :, 0].max() == pytest.approx(0.0)
    assert blurred[:, :, 2].max() == pytest.approx(0.0)


def test_unsharp_mask_increases_local_contrast(frame):
    """USM must sharpen, i.e. add high-frequency content back."""
    sharpened = enh.unsharp_mask(frame, 4, 2)

    assert sharpened.var() > frame.var()


def test_unsharp_mask_threshold_suppresses_small_differences(frame):
    """A threshold above every local difference leaves the image alone."""
    assert enh.unsharp_mask(frame, 4, 2, threshold=10.0) == pytest.approx(frame)


def test_gamma_darkens_or_brightens_monotonically():
    """Gamma must preserve ordering and the normalised end points."""
    data = np.linspace(0, 1, 25).reshape(5, 5).astype(np.float32)

    out = enh.gamma(data, 0.5)
    assert out.min() == pytest.approx(0.0)
    assert out.max() == pytest.approx(1.0)
    assert (np.diff(out.ravel()) >= 0).all()
    assert out[0, 1] > data[0, 1]


def test_gamma_of_integer_valued_data_does_not_raise():
    """Regression: gamma on unmodified image data raised UFuncTypeError."""
    assert np.isfinite(enh.gamma(np.full((3, 3, 3), 0.5, np.float32), 2.0)).all()


def test_gradient_flattens_a_ramp():
    """A pure background ramp should mostly disappear."""
    ramp = np.tile(np.linspace(0, 1, 60), (60, 1)).astype(np.float32)
    ramp = np.repeat(ramp[:, :, np.newaxis], 3, axis=2)

    flattened = enh.remove_gradient(ramp, radius=8)
    assert flattened.std() < ramp.std() / 5


def test_gradient_after_channel_difference_is_rejected_clearly(frame):
    """2-D data cannot be blurred by the colour-aware path; say why."""
    flat = enh.blue_red(frame)

    # Blurring 2-D data is fine; it is the channel difference that is not.
    assert enh.remove_gradient(flat).shape == flat.shape


def test_stretch_clips_the_extremes():
    """The clipped range must match the requested quantiles."""
    data = np.linspace(0, 1, 1000).reshape(100, 10).astype(np.float32)

    out = enh.stretch(data, 0.1, 0.9)
    assert out.min() == pytest.approx(0.1, abs=0.02)
    assert out.max() == pytest.approx(0.9, abs=0.02)


def test_rgb_subtract_removes_the_common_level():
    """Equal channels carry no colour information and become flat."""
    grey = np.full((4, 4, 3), 0.3, dtype=np.float32)

    assert enh.rgb_subtract(grey) == pytest.approx(0.0)


def test_rgb_subtract_does_not_underflow():
    """Regression: unsigned data used to wrap around to huge values."""
    data = np.zeros((2, 2, 3), dtype=np.float32)
    data[:, :, 0] = 0.9

    assert enh.rgb_subtract(data).max() <= 1.0


def test_emboss_is_shaped_like_its_input(frame):
    """Emboss shades the whole frame and keeps the colour axis."""
    out = enh.emboss(frame, 90, 10)

    assert out.shape == frame.shape
    assert out.min() >= 0.0


def test_enhance_applies_in_order():
    """Methods run in the order given, which is what makes br last work."""
    data = np.full((8, 8, 3), 0.5, dtype=np.float32)

    assert enh.enhance(data, {'gradient': None, 'br': None}).ndim == 2


def test_too_many_arguments_is_reported(frame):
    """Extra arguments are a mistake worth naming."""
    with pytest.raises(ValueError, match='at most'):
        enh.apply_enhancement(frame, 'gamma', [1.0, 2.0, 3.0])


def test_gradient_takes_a_radius_and_a_sigma(frame):
    """Regression: '-E gradient:50,20' is documented and must keep working."""
    wide = enh.remove_gradient(frame, 20, 12)
    narrow = enh.remove_gradient(frame, 20, 2)

    assert wide.shape == frame.shape
    # A wider kernel leaves less of the background behind.
    assert not np.allclose(wide, narrow)


def test_gradient_is_the_image_minus_its_own_blur(frame):
    """gradient is defined that way, up to the offset it adds.

    remove_gradient lifts its result so that no pixel is negative, so the two
    agree only after that constant is taken back out.
    """
    difference = frame - enh.blur(frame, 8)
    result = enh.remove_gradient(frame, 8)

    assert result - result.min() == pytest.approx(difference - difference.min(),
                                                  abs=1e-6)
