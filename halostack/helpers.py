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

'''Misc helper functions'''

import logging
from glob import glob
import matplotlib.pyplot as plt
import numpy as np
import ConfigParser
from collections import OrderedDict as od
import warnings

LOGGER = logging.getLogger(__name__)

def get_filenames(fnames):
    '''Get filenames to a list. Expand wildcards etc.

    :param fnames: list of filenames or wildcard strings
    :type fnames: list of strings
    :rtype: list of strings
    '''

    fnames_out = []

    # Ensure that all files are used also on Windows, as the command
    # prompt does not automatically parse wildcards to a list of images
    for fname in fnames:
        if '*' in fname:
            all_fnames = glob(fname)
            for fname2 in all_fnames:
                fnames_out.append(fname2)
                LOGGER.debug("Added %s to the image list", fname2)
        else:
            fnames_out.append(fname)
            LOGGER.debug("Added %s to the image list", fname)

    return fnames_out

def parse_enhancements(params):
    '''Parse image enhancements and their parameters, if any.

    :param params: list of enhancement names and parameters
    :type params: list of strings
    :rtype: ordered dictionary

    example of *params*: ['usm:20,8', 'br']
    '''

    output = od()
    if len(params) > 0:
        LOGGER.debug("Parsing enhancements.")
    for param in params:
        param = param.split(":")
        if len(param) > 1:
            name, args = param
            args = args.split(',')
            arg_list = []
            for arg in args:
                try:
                    arg = float(arg)
                except ValueError:
                    pass
                arg_list.append(arg)
                
            output[name] = arg_list
        else:
            output[param[0]] = None

    return output

def get_two_points(img_in):
    '''Get two image pixel coordinates from users' clicks on the
    image, and return them as 3-tuple:
    (mean(xs), mean(ys), max(abs_diff(xs), abs_diff(ys))/2.

    :param img_in: input image
    :type img_in: Numpy array
    :rtype: 3-tuple
    '''

    x_cs, y_cs = get_image_coordinates(img_in, 2)

    return (int(np.ceil(np.mean(x_cs))),
            int(np.ceil(np.mean(y_cs))),
            int(np.ceil(np.max([np.abs(x_cs[0]-x_cs[1]),
                                np.abs(y_cs[0]-y_cs[1])])/2.)))

def get_image_coordinates(img_in, num):
    '''Get *num* image coordinates from users' clicks on the image.

    :param img_in: input image
    :type img_in: Numpy array
    :param num: number of coordinates to collect
    :type num: int
    '''

    img = img_in.img.copy()
    if img.dtype != 'uint8':
        img -= np.min(img)
        img = 255*img/np.max(img)
        img = img.astype(np.uint8)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fig = plt.figure()
        plt.imshow(img, cmap='gray')
        fig.tight_layout()
        points = plt.ginput(num, show_clicks=True, timeout=0)
        plt.close()

    x_cs, y_cs = [], []
    for pnt in points:
        x_c, y_c = pnt
        x_cs.append(int(x_c))
        y_cs.append(int(y_c))
        LOGGER.debug("Got image coordinate (%d, %d).", x_cs[-1], y_cs[-1])

    return x_cs, y_cs

def read_config(args):
    '''Read and parse configuration from a file given in *args* and
    update the argument dictionary.

    :param args: command-line arguments
    :type args: dictionary
    :rtype: dictionary with updated arguments
    '''

    fname = args['config_file']
    LOGGER.info("Reading configuration file %s.", fname)
    config_item = args.get('config_item', 'default')

    config = ConfigParser.ConfigParser()
    config.read(fname)

    cfg = dict(config.items(config_item))

    for key in cfg.keys():
        if key not in args or isinstance(args[key], list) or args[key] is None:
            if 'enhance' in key:
                vals = cfg[key].split()
                for val in vals:
                    args[key].append(val)
            else:
                try:
                    args[key] = int(cfg[key])
                except ValueError:
                    try:
                        args[key] = float(cfg[key])
                    except ValueError:
                        if cfg[key].lower() == 'true':
                            args[key] = True
                        elif cfg[key].lower() == 'false':
                            args[key] = False
                        else:
                            args[key] = cfg[key]

    return args
