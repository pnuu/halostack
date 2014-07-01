#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014

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

'''Module for removing gradients from images'''

import numpy as np
import itertools

class Gradient(object):
    '''Gradient removel class'''

    def __init__(self, img, method, args, order=2):
        self.img = img
        self.method = method
        self.gradient = np.empty(self.img.img.shape)
        self.args = args
        self.order = order
        self._x_pts = None
        self._y_pts = None

    def remove_gradient(self, method):
        '''Calculate the gradient from the image, subtract from the
        original, scale back to full bit depth and return the result.
        '''
        self._calculate_gradient(method)
        selfself.gradient

    def _calculate_gradient(self, method):
        '''Calculate gradient from the image using the given method.
        param method: name of the method for calculating the gradient
        '''

        methods = {'blur': self._blur,
#                   'user': self._get_user_points,
                   'random': self._random_points,
                   'grid': self._grid_points
#                   'mask': self._mask_points,
#                   'all': self._all_points
                   }

        func = methods[method]
        func()
        shape = self.img.img.shape

        if method is not 'blur':
            if len(shape) == 2:
                self._fit_surface()
            else:
                for i in range(shape[2]):
                    self._fit_surface(chan=i)

    def _blur(self):
        '''Blur the image to get the approximation of the background gradient.
        '''
        self.gradient = self.img.astype(self.img.img.dtype)
        self.gradient.adjust({'blur': 50})

    def _random_points(self):
        '''Automatically extract background points for gradient estimation.
        '''
        shape = self.img.img.shape
        self._y_pts = np.random.randint(shape[0], size=(self.args,))
        self._x_pts = np.random.randint(shape[1], size=(self.args,))

    def _get_user_points(self):
        '''Get background points from the user input (clicking with
        mouse in the image? mask?)
        '''
        pass

    def _grid_points(self):
        '''Get uniform sampling of image locations.
        '''
        shape = self.img.img.shape
        y_locs = np.arange(0, shape[0], self.args['grid'])
        x_locs = np.arange(0, shape[1], self.args['grid'])
        x_mat, y_mat = np.meshgrid(x_locs, y_locs, indexing='ij')

        self._y_pts = y_mat.ravel()
        self._x_pts = x_mat.ravel()

    def _mask_points(self):
        '''Get samples from the area defined by a mask.
        '''
        pass

    def _fit_surface(self, chan=None):
        '''Fit a surface to the given channel.
        '''
        shape = self.img.img.shape
        x_locs, y_locs = np.meshgrid(np.arange(shape[0]),
                                     np.arange(shape[1]))
        if chan:
            poly = polyfit2d(self._x_pts, self._y_pts,
                             self.img[self._y_pts, self._x_pts,
                                      chan].ravel(),
                             order=self.order)
            self.gradient[:, :, chan] = polyval2d(x_locs, y_locs, poly)
        else:
            poly = polyfit2d(self._x_pts, self._y_pts,
                             self.img[self._y_pts, self._x_pts].ravel(),
                             order=self.order)
            self.gradient[:, :] = polyval2d(x_locs, y_locs, poly)


def polyfit2d(x_loc, y_loc, z_val, order=2):
    '''Fit a 2-D polynomial to the given data.

    Implementation from: http://stackoverflow.com/a/7997925
    '''
    ncols = (order + 1)**2
    g_mat = np.zeros((x_loc.size, ncols))
    ij_loc = itertools.product(range(order+1), range(order+1))
    for k, (i, j) in enumerate(ij_loc):
        g_mat[:, k] = x_loc**i * y_loc**j
    poly, _, _, _ = np.linalg.lstsq(g_mat, z_val)
    return poly

def polyval2d(x_loc, y_loc, poly):
    '''Evaluate 2-D polynomial *poly* at the given locations

    Implementation from: http://stackoverflow.com/a/7997925
    '''
    order = int(np.sqrt(len(poly))) - 1
    ij_loc = itertools.product(range(order+1), range(order+1))
    surf = np.zeros_like(x_loc)
    for arr, (i, j) in zip(poly, ij_loc):
        surf += arr * x_loc**i * y_loc**j
    return surf
