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

# from halostack.image import Image
import numpy as np

class Gradient(object):
    '''Gradient removel class'''

    def __init__(self, img, method, *args):
        self.img = img
        self.method = method
        self.gradient = None
        self.args = args
        self._x_pts = None
        self._y_pts = None

    def remove_gradient(self, method):
        '''Subtract the precalculated(?) gradient from the image.
        '''
        self._calculate_gradient(method)
        self.img -= self.gradient

    def _calculate_gradient(self, method):
        '''Calculate gradient from the image using the given method.
        param method: name of the method for calculating the gradient
        return gradient: array holding the calculated gradient
        '''

        methods = {'blur': self._blur,
                   'user': self._get_user_points,
                   'random': self._random_points,
                   'grid': self._grid_points,
                   'mask': self._mask_points,
                   'all': None
                   }

        func = methods[method]
        func()

    def _blur(self):
        '''Blur the image to get the approximation of the background gradient.
        '''
        pass

    def _random_points(self):
        '''Automatically extract background points for gradient estimation.
        '''
        luminance = self.img.luminance()
        shape = luminance.img.shape
        self._y_pts = np.random.randint(shape[0], size=(self.args,))
        self._x_pts = np.random.randint(shape[1], size=(self.args,))

    def _get_user_points(self):
        '''Get background points from the user input (clicking with
        mouse in the image? mask?)
        '''

    def _fit_surface(self):
        '''Fit a surface to the given (x,y,z) data.
        '''
        # Used surface is of form: z(x,y) = ax2 + by2 + cx + dy + f
        pass
