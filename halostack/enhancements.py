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

"""Image processing methods and the registry that describes them.

Every enhancement is a plain function taking a float image array and returning
a new one, registered in :data:`ENHANCEMENTS` together with enough metadata --
a summary and a description of each parameter, with its default -- to build a
user interface without hard-coding anything about the individual methods.
:func:`enhance` is the entry point used by the rest of Halostack.

Image data is float32 nominally in ``[0, 1]``.  Methods are free to produce
values outside that range; the range is restored when the image is saved.
"""

import logging
from collections import namedtuple

import numpy as np
from scipy.ndimage import correlate1d, gaussian_filter

LOGGER = logging.getLogger(__name__)

#: One parameter of an enhancement, as shown to a user interface.
Parameter = namedtuple('Parameter', ['name', 'default', 'description'])

#: An image processing method and everything needed to present it.
Enhancement = namedtuple('Enhancement', ['name', 'func', 'summary', 'parameters'])

ENHANCEMENTS = {}


def register(name, summary, parameters):
    """Return a decorator registering a function as the *name* enhancement."""
    def decorator(func):
        ENHANCEMENTS[name] = Enhancement(name=name, func=func, summary=summary,
                                         parameters=tuple(parameters))
        return func
    return decorator


def luminance(img):
    """Return the mean of the colour channels.

    :param img: image data
    :type img: numpy.ndarray
    :rtype: 2-dimensional numpy.ndarray
    """
    if img.ndim == 3:
        return img.mean(axis=2)
    return img


def _blur_sigmas(img, sigma):
    """Return per-axis sigmas that blur within, but not across, channels."""
    if img.ndim == 3:
        return (sigma, sigma, 0)
    return (sigma, sigma)


def _default_radius(img):
    """Return the default blur radius: a twentieth of the smaller dimension."""
    return max(1.0, min(img.shape[0], img.shape[1]) / 20.0)


def _gaussian(img, sigma):
    """Gaussian blur that never degenerates to a zero-width kernel."""
    sigma = max(float(sigma), 1e-3)
    return gaussian_filter(img, _blur_sigmas(img, sigma), mode='nearest')


@register('blur', 'Gaussian blur.',
          [Parameter('radius', 'min(width, height) / 20', 'blur radius in pixels'),
           Parameter('sigma', 'radius / 3', 'standard deviation in pixels')])
def blur(img, radius=None, sigma=None):
    """Blur the image with a Gaussian kernel.

    :param img: image data
    :type img: numpy.ndarray
    :param radius: blur radius in pixels [min(width, height) / 20]
    :type radius: float or None
    :param sigma: standard deviation of the Gaussian [radius / 3]
    :type sigma: float or None
    :rtype: numpy.ndarray
    """
    if radius is None:
        radius = _default_radius(img)
    if sigma is None:
        sigma = radius / 3.0
    LOGGER.debug("Blur radius is %.1f pixels and sigma is %.3f.", radius, sigma)

    return _gaussian(img, sigma)


@register('usm', 'Unsharp mask: increase local contrast.',
          [Parameter('radius', None, 'radius of the effect in pixels'),
           Parameter('amount', None, 'strength of the effect'),
           Parameter('sigma', 'sqrt(radius)', 'standard deviation in pixels'),
           Parameter('threshold', '0', 'minimum difference to sharpen, '
                     'as a fraction of the full range')])
def unsharp_mask(img, radius, amount, sigma=None, threshold=0.0):
    """Sharpen the image by adding back its own high-pass content.

    :param img: image data
    :type img: numpy.ndarray
    :param radius: radius of the effect in pixels
    :type radius: float
    :param amount: strength of the effect
    :type amount: float
    :param sigma: standard deviation of the Gaussian [sqrt(radius)]
    :type sigma: float or None
    :param threshold: differences smaller than this are left alone [0]
    :type threshold: float
    :rtype: numpy.ndarray
    """
    if sigma is None:
        sigma = np.sqrt(radius)
    LOGGER.debug("Radius: %.1f, amount: %.1f, sigma: %.1f, threshold: %.3f.",
                 radius, amount, sigma, threshold)

    detail = img - _gaussian(img, sigma)
    if threshold:
        detail = np.where(np.abs(detail) < threshold, 0.0, detail)

    return img + amount * detail


@register('emboss', 'Relief shading from a virtual light source.',
          [Parameter('azimuth', '90', 'light source azimuth in degrees'),
           Parameter('elevation', '10', 'light source elevation in degrees')])
def emboss(img, azimuth=90.0, elevation=10.0):
    """Shade the image as a relief lit from the given direction.

    This reproduces ImageMagick's ``shade`` operator: a surface normal is
    estimated from the local intensity gradient and shaded against a light
    source, which is what the old ImageMagick-backed implementation did.

    :param img: image data
    :type img: numpy.ndarray
    :param azimuth: light source azimuth in degrees [90]
    :type azimuth: float
    :param elevation: light source elevation in degrees [10]
    :type elevation: float
    :rtype: numpy.ndarray
    """
    LOGGER.debug("Azimuth: %.1f, elevation: %.1f.", azimuth, elevation)

    azimuth = np.deg2rad(azimuth)
    elevation = np.deg2rad(elevation)
    light = np.array([np.cos(azimuth) * np.cos(elevation),
                      np.sin(azimuth) * np.cos(elevation),
                      np.sin(elevation)])

    intensity = luminance(img).astype(np.float64)
    # Separable 3x3 sums: the difference of the neighbouring columns and rows
    # gives the surface normal, exactly as ImageMagick's ShadeImage does.
    smoothed_rows = correlate1d(intensity, [1.0, 1.0, 1.0], axis=0, mode='nearest')
    smoothed_cols = correlate1d(intensity, [1.0, 1.0, 1.0], axis=1, mode='nearest')
    normal_x = correlate1d(smoothed_rows, [1.0, 0.0, -1.0], axis=1, mode='nearest')
    normal_y = correlate1d(smoothed_cols, [-1.0, 0.0, 1.0], axis=0, mode='nearest')
    normal_z = 2.0 / 3.0

    length = np.sqrt(normal_x ** 2 + normal_y ** 2 + normal_z ** 2)
    shade = (light[0] * normal_x + light[1] * normal_y + light[2] * normal_z) / length
    shade = np.clip(shade, 0.0, None)

    if img.ndim == 3:
        shade = shade[:, :, np.newaxis]

    return np.broadcast_to(shade, img.shape).astype(img.dtype).copy()


@register('gamma', 'Gamma correction.',
          [Parameter('gamma', None, 'gamma value')])
def gamma(img, gamma):
    """Apply gamma correction, after normalising the image to its maximum.

    :param img: image data
    :type img: numpy.ndarray
    :param gamma: gamma value
    :type gamma: float
    :rtype: numpy.ndarray
    """
    LOGGER.debug("Apply gamma correction, gamma: %.2f.", gamma)

    img_max = img.max()
    if img_max == 0:
        return img
    normalised = np.clip(img / img_max, 0.0, None)

    return normalised ** gamma


def _channel_difference(img, chan1, chan2, multiplier=None):
    """Return ``multiplier * chan1 - chan2``.

    When no multiplier is given it is estimated from the pixels where the two
    channels are in a plausible background ratio, which is what makes ``br``
    work without the user having to tune anything.
    """
    if img.ndim != 3 or img.shape[2] < 3:
        raise ValueError("Channel differences need a three-channel image; "
                         "this one has shape %s. Channel differences produce "
                         "a single-channel image, so they can only be applied "
                         "once, and last." % (img.shape,))
    first = img[:, :, chan1]
    second = img[:, :, chan2]

    if multiplier is None:
        idxs = (1.5 * first < second) & (2.5 * first > second) & (first > 0)
        if not idxs.any():
            multiplier = 2.0
        else:
            multiplier = float(np.mean(second[idxs] / first[idxs]))
    LOGGER.debug("Multiplier: %.3f", multiplier)

    return multiplier * first - second


@register('br', 'Blue minus red: isolates colourful halos from the background.',
          [Parameter('multiplier', 'estimated from the image',
                     'multiplier for the blue channel')])
def blue_red(img, multiplier=None):
    """Subtract the red channel from a scaled blue channel.

    :param img: image data
    :type img: numpy.ndarray
    :param multiplier: multiplier for the blue channel [estimated]
    :type multiplier: float or None
    :rtype: 2-dimensional numpy.ndarray
    """
    LOGGER.debug("Calculating channel difference, Blue - Red.")
    return _channel_difference(img, 2, 0, multiplier)


@register('gr', 'Green minus red.',
          [Parameter('multiplier', 'estimated from the image',
                     'multiplier for the green channel')])
def green_red(img, multiplier=None):
    """Subtract the red channel from a scaled green channel.

    :param img: image data
    :type img: numpy.ndarray
    :param multiplier: multiplier for the green channel [estimated]
    :type multiplier: float or None
    :rtype: 2-dimensional numpy.ndarray
    """
    LOGGER.debug("Calculating channel difference, Green - Red.")
    return _channel_difference(img, 1, 0, multiplier)


@register('bg', 'Blue minus green.',
          [Parameter('multiplier', 'estimated from the image',
                     'multiplier for the blue channel')])
def blue_green(img, multiplier=None):
    """Subtract the green channel from a scaled blue channel.

    :param img: image data
    :type img: numpy.ndarray
    :param multiplier: multiplier for the blue channel [estimated]
    :type multiplier: float or None
    :rtype: 2-dimensional numpy.ndarray
    """
    LOGGER.debug("Calculating channel difference, Blue - Green.")
    return _channel_difference(img, 2, 1, multiplier)


@register('rgb_sub', 'Subtract the luminance from every colour channel.', [])
def rgb_subtract(img):
    """Subtract the mean of the channels from each channel.

    :param img: image data
    :type img: numpy.ndarray
    :rtype: numpy.ndarray
    """
    LOGGER.debug("Subtracting luminance from colour channels.")
    if img.ndim != 3:
        return img - img.min()

    out = img - luminance(img)[:, :, np.newaxis]

    return out - out.min()


@register('rgb_mix', 'Blend the luminance-subtracted image back into the original.',
          [Parameter('ratio', '0.7', 'mixing ratio')])
def rgb_mix(img, ratio=0.7):
    """Blend *img* with its luminance-subtracted version.

    :param img: image data
    :type img: numpy.ndarray
    :param ratio: mixing ratio [0.7]
    :type ratio: float
    :rtype: numpy.ndarray
    """
    LOGGER.debug("Mixing factor: %.2f", ratio)

    return (1.0 - ratio) * img + ratio * rgb_subtract(img)


@register('gradient', 'Remove the background gradient.',
          [Parameter('radius', 'min(width, height) / 20',
                     'radius of the gradient estimate in pixels'),
           Parameter('sigma', 'radius / 3',
                     'standard deviation of the gradient estimate in pixels')])
def remove_gradient(img, radius=None, sigma=None):
    """Subtract a blurred copy of the image to flatten the background.

    :param img: image data
    :type img: numpy.ndarray
    :param radius: blur radius used to estimate the gradient
    :type radius: float or None
    :param sigma: standard deviation of the Gaussian [radius / 3]
    :type sigma: float or None
    :rtype: numpy.ndarray
    """
    LOGGER.debug("Calculating gradient.")

    out = img - blur(img, radius, sigma)
    minimum = out.min()
    if minimum < 0:
        out = out - minimum

    return out


@register('stretch', 'Linear histogram stretch.',
          [Parameter('low', '0.01', 'low cut, as a fraction of the histogram'),
           Parameter('high', '1 - low', 'high cut, as a fraction of the histogram')])
def stretch(img, low=0.01, high=None):
    """Clip the extremes of the histogram.

    The clipped image is rescaled to the full output range when it is saved,
    which is what makes this a stretch rather than only a clip.

    :param img: image data
    :type img: numpy.ndarray
    :param low: low cut as a fraction of the histogram [0.01]
    :type low: float
    :param high: high cut as a fraction of the histogram [1 - low]
    :type high: float or None
    :rtype: numpy.ndarray
    """
    if high is None:
        high = 1.0 - low
    LOGGER.debug("low cut: %.1f %%, high cut: %.1f %%", 100 * low, 100 * high)

    lumin = luminance(img)
    low_value, high_value = (float(val) for val in np.quantile(lumin, [low, high]))
    if high_value <= low_value:
        return img
    LOGGER.debug("Truncation values: %.4f and %.4f", low_value, high_value)

    return np.clip(img, low_value, high_value)


def _as_arguments(args):
    """Normalise a parsed enhancement argument into a list."""
    if args is None:
        return []
    if isinstance(args, (list, tuple)):
        return list(args)
    return [args]


def apply_enhancement(img, name, args=None):
    """Apply a single enhancement to *img*.

    :param img: image data
    :type img: numpy.ndarray
    :param name: name of the enhancement, a key of :data:`ENHANCEMENTS`
    :type name: str
    :param args: positional arguments for the enhancement
    :type args: list, scalar or None
    :rtype: numpy.ndarray
    """
    try:
        enhancement = ENHANCEMENTS[name]
    except KeyError:
        raise ValueError("Unknown image processing method %r. Available "
                         "methods: %s." % (name, ', '.join(sorted(ENHANCEMENTS))))

    args = _as_arguments(args)
    if len(args) > len(enhancement.parameters):
        raise ValueError("%r takes at most %d argument(s), got %d: %r."
                         % (name, len(enhancement.parameters), len(args), args))

    LOGGER.info("Apply \"%s\".", name)
    try:
        return enhancement.func(img, *args)
    except TypeError as err:
        required = [par.name for par in enhancement.parameters
                    if par.default is None]
        raise ValueError("%r requires the argument(s) %s (%s)."
                         % (name, ', '.join(required), err))


def enhance(img, enhancements):
    """Apply several enhancements in order.

    :param img: image data
    :type img: numpy.ndarray
    :param enhancements: names mapped to their arguments, applied in iteration
                         order
    :type enhancements: dict
    :rtype: numpy.ndarray
    """
    for name in enhancements:
        img = apply_enhancement(img, name, enhancements[name])

    return img
