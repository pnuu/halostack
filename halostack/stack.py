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

'''Module for stacking images'''

import numpy as np
from halostack.image import Image
from halostack import image

class Stack(object):
    '''Class for image stacks'''

    def __init__(self, mode, num):
        self.stack = None
        self.mode = mode
        self._mode_functions = {'min': {'update': self._update_min,
                                        'calc': None},
                                'max': {'update': self._update_max,
                                        'calc': None},
                                'mean': {'update': self._update_mean,
                                         'calc': self._calculate_mean},
                                #'sigma': {'update': self._update_deep,
                                #          'calc': self._calculate_sigma},
                                'median': {'update': self._update_deep,
                                           'calc': self._calculate_median}}
        self._update_func = self._mode_functions[mode]['update']
        self._calculate_func = self._mode_functions[mode]['calc']
        self.num = num
        self._num = 0

    def add_image(self, img):
        '''Add a frame to the stack.
        '''
        if not isinstance(img, Image):
            img = Image(img=img)

        self._update_stack(image.to_numpy(img))
        self._num += 1

    def calculate(self):
        '''Calculate the result image and return Image object.
        '''
        if self._calculate_func is None:
            return self.stack
        return self._calculate_func()

    def _update_stack(self, img):
        '''Update the stack
        '''
        self._update_func(img)

    def _update_mean(self, img):
        '''Update average stack
        '''
        if self.stack is None:
            self.stack = img.astype(np.float)
        else:
            self.stack += img

    def _update_min(self, img):
        '''Update minimum stack.
        '''
        if self.stack is None:
            self.stack = img
        else:
            idxs = np.where(self.stack > img)
            if np.any(idxs):
                self.stack.img[idxs] = img[idxs]

    def _update_max(self, img):
        '''Update maximum stack.
        '''

        if self.stack is None:
            self.stack = img
        else:
            idxs = np.where(self.stack < img)
            if np.any(idxs):
                self.stack[idxs] = img[idxs]

    def _update_deep(self, img):
        '''Update deep (median or sigma-reject average) stack.
        '''
        if self.stack is None:
            self.stack = {}
            shape = img.shape[:2]
            self.stack['R'] = np.empty((shape[0], shape[1], self.num),
                                       dtype=img.dtype)
            self.stack['G'] = np.empty((shape[0], shape[1], self.num),
                                       dtype=img.dtype)
            self.stack['B'] = np.empty((shape[0], shape[1], self.num),
                                       dtype=img.dtype)

        self.stack['R'][:, :, self._num] = img[:, :, 0]
        self.stack['G'][:, :, self._num] = img[:, :, 1]
        self.stack['B'][:, :, self._num] = img[:, :, 2]

    def _calculate_mean(self):
        '''Calculate the average of the stack and return as
        Image(dtype=uint16).
        '''
        self.stack /= self.num
        return Image(img=self.stack.astype(np.uint16))

    def _calculate_median(self):
        '''Calculate the median of the stack and return the resulting
        image with the original dtype.
        '''
        ch_r = np.median(self.stack['R'], 2)
        ch_g = np.median(self.stack['G'], 2)
        ch_b = np.median(self.stack['B'], 2)
        shape = ch_r.shape[:2]
        img = np.empty((shape[0], shape[1], 3), dtype=self.stack['R'].dtype)
        img[:, :, 0] = ch_r.astype(self.stack['R'].dtype)
        img[:, :, 1] = ch_r.astype(self.stack['G'].dtype)
        img[:, :, 2] = ch_r.astype(self.stack['B'].dtype)

        return Image(img=img)

    def _calculate_sigma(self):
        '''Calculate the sigma-reject average of the stack and return
        the result as Image(dtype=uint16).
        '''
        pass
