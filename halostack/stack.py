#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014, 2015, Panu Lahtinen

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

'''Module for image stacks'''

import numpy as np
import logging
from halostack.image import Image

LOGGER = logging.getLogger(__name__)

class Stack(object):
    '''Class for image stacks.

    :param mode: type of the stack
    :type mode: str
    :param num: maximum number of images to be added
    :type num: int

    Available stack types are::

    'min' - minimum stack
    'max' - maximum stack
    'mean' - average stack
    'median' - median stack
    '''

    def __init__(self, mode, num, nprocs=1):
        LOGGER.debug("Initializing %s stack for %d images.",
                     mode, num)
        self.stack = None
        self.mode = mode
        self.nprocs = nprocs
        self._mode_functions = {'min': {'update': self._update_min,
                                        'calc': None},
                                'max': {'update': self._update_max,
                                        'calc': None},
                                'mean': {'update': self._update_mean,
                                         'calc': None},
                                # 'sigma': {'update': self._update_deep,
                                #          'calc': self._calculate_sigma},
                                'median': {'update': self._update_deep,
                                           'calc': self._calculate_median}}
        self._update_func = self._mode_functions[mode]['update']
        self._calculate_func = self._mode_functions[mode]['calc']
        self.num = num
        self._num = 0

    def add_image(self, img):
        '''Add a frame to the stack.

        :param img: image to be added to stack
        :type img: halostack.image.Image
        '''

        if not isinstance(img, Image):
            LOGGER.debug("Converting %s to Image object.", img)
            img = Image(img=img, nprocs=self.nprocs)

        LOGGER.debug("Adding image to %s stack.", self.mode)

        self._update_stack(img)

    def calculate(self):
        '''Calculate the result image and return Image object.

        :rtype: halostack.image.Image
        '''
        if self._calculate_func is None:
            return self.stack

        LOGGER.info("Calculating %s stack", self.mode)

        return self._calculate_func()

    def _update_stack(self, img):
        '''Update the stack
        '''
        self._update_func(img)
        self._num += 1

    def _update_mean(self, img):
        '''Update average stack
        '''

        if self.stack is None:
            self.stack = img
        else:
            self.stack += img

    def _update_min(self, img):
        '''Update minimum stack. Minimum values are selected using
        luminance.
        '''
        if self.stack is None:
            self.stack = img
        else:
            lum_stack = self.stack.luminance()
            lum_img = img.luminance()
            idxs_y, idxs_x = np.where(lum_stack > lum_img)
            if np.any(idxs_x):
                for i in range(img.img.shape[-1]):
                    self.stack.img[idxs_y, idxs_x, i] = img[idxs_y, idxs_x, i]


    def _update_max(self, img):
        '''Update maximum stack. Maximum values are selected using
        luminance.
        '''

        if self.stack is None:
            self.stack = img
        else:
            lum_stack = self.stack.luminance()
            lum_img = img.luminance()
            idxs_y, idxs_x = np.where(lum_stack < lum_img)
            if np.any(idxs_x):
                for i in range(img.img.shape[-1]):
                    self.stack[idxs_y, idxs_x, i] = img[idxs_y, idxs_x, i]


    def _update_deep(self, img):
        '''Update deep (median or sigma-reject average) stack.
        '''
        if self.stack is None:
            self.stack = {}
            shape = img.img.shape[:2]
            self.stack['R'] = np.empty((shape[0], shape[1], self.num),
                                       dtype=img.img.dtype)
            self.stack['G'] = np.empty((shape[0], shape[1], self.num),
                                       dtype=img.img.dtype)
            self.stack['B'] = np.empty((shape[0], shape[1], self.num),
                                       dtype=img.img.dtype)

        self.stack['R'][:, :, self._num] = img[:, :, 0]
        self.stack['G'][:, :, self._num] = img[:, :, 1]
        self.stack['B'][:, :, self._num] = img[:, :, 2]


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
        img[:, :, 1] = ch_g.astype(self.stack['G'].dtype)
        img[:, :, 2] = ch_b.astype(self.stack['B'].dtype)

        return Image(img=img, nprocs=self.nprocs)

    def _calculate_sigma(self):
        '''Calculate the sigma-reject average of the stack and return
        the result as Image(dtype=uint16).
        '''
        LOGGER.error("Sigma stack not implemented.")
