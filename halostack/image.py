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

'''Module for image I/O and conversions'''

from halostack.gradients import Gradient
from PythonMagick import Image as PMImage
from PythonMagick import Blob
import numpy as np

class Image(object):
    '''Image class'''

    def __init__(self):
        self.img = None
        self.fname = None

    def __add__(self, img):
        if isinstance(img, Image):
            return Image(self.img + img.img)
        else:
            # Assume a numpy array or scalar
            return Image(self.img + img)

    def __sub__(self, img):
        if isinstance(img, Image):
            return Image(self.img - img.img)
        else:
            # Assume a numpy array or scalar
            return Image(self.img - img)

    def __mult__(self, img):
        if isinstance(img, Image):
            return Image(self.img * img.img)
        else:
            # Assume a numpy array or scalar
            return Image(self.img * img)

    def __div__(self, img):
        if isinstance(img, Image):
            return Image(self.img / img.img)
        else:
            # Assume a numpy array or scalar
            return Image(self.img / img)

    def __abs__(self):
        return Image(np.abs(self.img))

    def read(self):
        '''Read the image.
        '''
        pass

    def save(self):
        '''Save the image data.
        '''
        pass

    def _to_numpy(self):
        '''Convert the image data to numpy array.
        '''
        self.img.magick('RGB')
        blob = Blob()
        self.img.write(blob)
        data = blob.data
        if self.img.depth() == 8:
            img = np.fromstring(data, dtype='uint8')
        else:
            img = np.fromstring(data, dtype='uint16')

        height, width, chans = img.rows(), img.columns(), 3
        if img.monochrome():
            chans = 1

        self.img = img.reshape(height, width, chans)

    def _to_imagemagick(self):
        '''Convert the numpy array to Imagemagick format.
        '''
        if not isinstance(self.img, PMImage):
            img = PMImage()
            if self.img.dtype == 'uint16':
                img.depth(16)
            else:
                img.depth(8)
            img.magick('RGB')
            shape = img.shape
            img.size(str(shape[1])+'x'+str(shape[0]))
            blob = Blob()
            blob.data = self.img.tosting()
            img.read(blob)
            img.magick('PNG')

            self.img = img

    def luminance(self):
        '''Return luminance (channel average).
        '''
        if self.img.shape == 3:
            return np.mean(self.img, 2)
        else:
            return self.img

    def process(self, funcs):
        '''Process the image with the given function(s) and arguments.
        '''
        functions = {'usm': self._usm,
                     'emboss': self._emboss,
                     'gamma': self._gamma,
                     'br': self._blue_red_subtract,
                     'rg': self._red_green_subtract,
                     'rgb_sub': self._rgb_subtract,
                     'gradient': self._gradient
                     }
        for key in funcs:
            func = getattr(key, functions)
            self.img = func(*funcs[key])

    def _usm(self, radius, sigma, amount, threshold):
        '''Return unsharp mask sharpened image.
        '''
        img = self._to_imagemagick()
        img.unsharpmask(radius, sigma, amount, threshold)

    def _emboss(self):
        '''Return emboss filtered image.
        '''
        pass

    def _gamma(self):
        '''Return gamma corrected image.
        '''
        pass

    def _channel_difference(self, chan1, chan2, multiplier=1):
        '''Return channel difference: chan1 * multiplier - chan2.
        '''
        return multiplier * self.img[:, :, chan1] - self.img[:, :, chan2]


    def _blue_red_subtract(self, multiplier):
        '''Subtract red channel from the blue channel after scaling
        the blue channel using the supplied multiplier.
        '''
        return self._channel_difference(2, 0, multiplier=multiplier)

    def _red_green_subtract(self, multiplier):
        '''Subtract green channel from the red channel after scaling
        the red channel using the supplied multiplier.
        '''
        return self._channel_difference(0, 1, multiplier=multiplier)

    def _rgb_subtract(self):
        '''Subtract the mean(r,g,b) from all the channels.
        '''
        return self.img - self.luminance()

    def _gradient(self):
        '''Return image with the background gradient subtracted.
        '''
        grad = Gradient()
        grad.remove_gradient()
        img = self.img

        return img
