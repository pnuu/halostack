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

"""Asking the user where the alignment reference is.

The stacking pipeline needs two areas picked out of the first frame.  It gets
them through a :class:`PointSelector`, so that how the question is asked is not
baked into the processing code: the command line uses
:class:`MatplotlibSelector`, a graphical front end can implement the same two
methods against its own canvas, and tests and scripts can use
:class:`FixedPointSelector` to supply coordinates directly.
"""

import logging

import numpy as np

LOGGER = logging.getLogger(__name__)


def preview_data(img, gamma=None):
    """Return 8-bit display data for *img*.

    :param img: image to prepare
    :type img: halostack.image.Image or numpy.ndarray
    :param gamma: gamma correction to make faint detail visible
    :type gamma: float or None
    :rtype: numpy.ndarray of uint8
    """
    data = np.asarray(img, dtype=np.float64)

    data = data - data.min()
    maximum = data.max()
    if maximum > 0:
        data = data / maximum
    if gamma:
        data = data ** gamma

    return (255 * data).astype(np.uint8)


def points_to_area(points):
    """Convert two opposite corners into a centre and a radius.

    :param points: two (x, y) pairs
    :type points: sequence
    :rtype: (x, y, radius)
    """
    if len(points) < 2:
        raise ValueError("Two points are needed to define an area, got %d."
                         % len(points))
    (x_1, y_1), (x_2, y_2) = points[0], points[1]

    return (int(np.ceil((x_1 + x_2) / 2.0)),
            int(np.ceil((y_1 + y_2) / 2.0)),
            int(np.ceil(max(abs(x_1 - x_2), abs(y_1 - y_2)) / 2.0)))


class PointSelector(object):
    """Interface for asking the user to point at things in an image."""

    def select_points(self, img, count, title=''):
        """Return *count* (x, y) pairs chosen by the user.

        :param img: image to show
        :type img: halostack.image.Image or numpy.ndarray
        :param count: number of points to collect
        :type count: int
        :param title: instruction to show the user
        :type title: str
        :rtype: list of (x, y)
        """
        raise NotImplementedError

    def select_area(self, img, title=''):
        """Return an (x, y, radius) area from two clicked corners.

        :param img: image to show
        :type img: halostack.image.Image or numpy.ndarray
        :param title: instruction to show the user
        :type title: str
        :rtype: (x, y, radius)
        """
        return points_to_area(self.select_points(img, 2, title))


class MatplotlibSelector(PointSelector):
    """Collect points from clicks on a Matplotlib window.

    :param gamma: gamma correction applied to the preview only
    :type gamma: float or None
    """

    def __init__(self, gamma=None):
        self.gamma = gamma

    def select_points(self, img, count, title=''):
        """Show *img* and return *count* points clicked on it."""
        import warnings

        import matplotlib.pyplot as plt

        data = preview_data(img, self.gamma)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fig = plt.figure()
            plt.imshow(data, cmap='gray')
            if title:
                plt.title(title)
            fig.tight_layout()
            points = plt.ginput(count, show_clicks=True, timeout=0)
            plt.close(fig)

        if len(points) < count:
            raise ValueError("Expected %d points, got %d. The window was "
                             "probably closed early." % (count, len(points)))

        for x_c, y_c in points:
            LOGGER.debug("Got image coordinate (%d, %d).", int(x_c), int(y_c))

        return [(int(x_c), int(y_c)) for x_c, y_c in points]


class FixedPointSelector(PointSelector):
    """Return points decided in advance, without showing anything.

    Useful for scripted runs, for regression tests, and as the simplest
    possible example of the interface a graphical front end has to provide.

    :param points: the points to hand out, consumed in order
    :type points: sequence of (x, y)
    """

    def __init__(self, points):
        self.points = [tuple(point) for point in points]
        self._used = 0

    def select_points(self, img, count, title=''):
        """Return the next *count* points."""
        del img
        remaining = self.points[self._used:]
        if len(remaining) < count:
            raise ValueError("FixedPointSelector ran out of points: %d "
                             "requested, %d left." % (count, len(remaining)))
        self._used += count
        if title:
            LOGGER.debug("%s -> %s", title, remaining[:count])

        return remaining[:count]
