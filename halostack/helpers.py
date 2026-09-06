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

"""Filename, configuration and command line helpers.

This module deliberately imports nothing that needs a display, so that it can
be used from a graphical front end, a script or a test without pulling in a
plotting library.  Interactive point selection lives in :mod:`halostack.ui`.
"""

import configparser
import glob
import logging
import os.path

LOGGER = logging.getLogger(__name__)

#: Characters that make a filename a shell-style pattern.
_WILDCARDS = '*?['


def get_filenames(fnames):
    """Expand wildcards in a list of filenames.

    Windows shells do not expand patterns before handing them to a program,
    so Halostack does it itself.

    :param fnames: filenames, possibly containing wildcards
    :type fnames: list of str
    :rtype: list of str
    """
    fnames_out = []

    for fname in fnames:
        if any(char in fname for char in _WILDCARDS):
            matches = sorted(glob.glob(fname))
            if not matches:
                LOGGER.warning("Pattern %s did not match any files.", fname)
            for match in matches:
                fnames_out.append(match)
                LOGGER.debug("Added %s to the image list", match)
        else:
            fnames_out.append(fname)
            LOGGER.debug("Added %s to the image list", fname)

    return fnames_out


def parse_enhancements(params):
    """Parse image processing methods and their arguments.

    :param params: method names, each optionally followed by ``:`` and a
                   comma separated argument list, e.g. ``['usm:20,8', 'br']``
    :type params: list of str
    :rtype: dict mapping method names to argument lists, in the given order
    """
    output = {}
    if params:
        LOGGER.debug("Parsing enhancements.")

    for param in params:
        name, _, argument_text = param.partition(':')
        if not argument_text:
            output[name] = None
            continue

        args = []
        for arg in argument_text.split(','):
            try:
                args.append(float(arg))
            except ValueError:
                args.append(arg)
        output[name] = args

    return output


def read_config(args):
    """Fill in *args* from a configuration file.

    Command line settings win: a value already present in *args* is never
    replaced, including the lists of image processing methods.

    :param args: command line arguments
    :type args: dict
    :rtype: dict, updated in place and returned
    """
    fname = args.get('config_file')
    if not fname:
        raise ValueError("No configuration file was given.")
    if not os.path.exists(fname):
        raise ValueError("No such configuration file: %s" % fname)

    config_item = args.get('config_item') or 'default'
    LOGGER.info("Reading configuration file %s, section %s.", fname, config_item)

    config = configparser.ConfigParser()
    config.read(fname)
    if not config.has_section(config_item):
        raise ValueError("Configuration file %s has no section %r. "
                         "Available sections: %s."
                         % (fname, config_item, ', '.join(config.sections())))

    for key, value in config.items(config_item):
        current = args.get(key)
        if 'enhance' in key:
            # A list of methods. Anything given on the command line replaces
            # the configured list rather than being added to it.
            if current:
                LOGGER.debug("Keeping command line value of %s.", key)
                continue
            args[key] = value.split()
        elif current is None:
            args[key] = _parse_value(value)
        else:
            LOGGER.debug("Keeping command line value of %s.", key)

    return args


def _parse_value(value):
    """Convert a configuration string to int, float, bool or str."""
    for convert in (int, float):
        try:
            return convert(value)
        except ValueError:
            pass
    lowered = value.lower()
    if lowered in ('true', 'yes', 'on'):
        return True
    if lowered in ('false', 'no', 'off'):
        return False

    return value


def intermediate_fname(prefix, fname):
    """Build the name of an intermediate image file.

    :param prefix: prefix for the base name of the file
    :type prefix: str
    :param fname: original filename, with or without a directory
    :type fname: str
    :rtype: str
    """
    dirname, basename = os.path.split(fname)
    barename = os.path.splitext(basename)[0]

    return os.path.join(dirname, ''.join([prefix, '_', barename, '.png']))


def get_image_coordinates(img, num):
    """Ask the user to click *num* points on *img*.

    Kept for backwards compatibility; new code should use
    :class:`halostack.ui.MatplotlibSelector` directly, or supply its own
    selector so that no plotting library is needed.

    :param img: image to show
    :type img: halostack.image.Image
    :param num: number of points to collect
    :type num: int
    :rtype: (list of x, list of y)
    """
    from halostack.ui import MatplotlibSelector

    points = MatplotlibSelector().select_points(img, num)

    return [int(point[0]) for point in points], [int(point[1]) for point in points]


def get_two_points(img):
    """Ask the user to click two opposite corners of an area.

    Kept for backwards compatibility; see :func:`get_image_coordinates`.

    :param img: image to show
    :type img: halostack.image.Image
    :rtype: (x, y, radius)
    """
    from halostack.ui import MatplotlibSelector, points_to_area

    return points_to_area(MatplotlibSelector().select_points(img, 2))
