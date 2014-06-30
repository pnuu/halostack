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

    def __init__(self, img=None, fname=None, adjustments=None):
        self.img = img
        self.fname = fname

        if fname is not None:
            self._read()
        if adjustments:
            self._adjust(adjustments)

    def __add__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            return Image(img=self.img+img.img)
        else:
            # Assume a numpy array or scalar
            return Image(img=self.img+img)

    def __radd__(self, img):
        return self.__add__(img)

    def __sub__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            return Image(img=self.img-img.img)
        else:
            # Assume a numpy array or scalar
            return Image(img=self.img-img)

    def __rsub__(self, img):
        return self.__add__(img)

    def __isub__(self, img):
        self.img = self.__sub__(img)

    def __mul__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            return Image(img=self.img*img.img)
        else:
            # Assume a numpy array or scalar
            return Image(img=self.img*img)

    def __rmul__(self, img):
        return self.__mul__(img)

    def __div__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            return Image(img=self.img/img.img)
        else:
            # Assume a numpy array or scalar
            return Image(img=self.img/img)

    def __abs__(self):
        self._to_numpy()
        return Image(img=np.abs(self.img))

    def __lt__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            img = img.img
        return self.img < img

    def __le__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            img = img.img
        return self.img <= img

    def __gt__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            img = img.img
        return self.img > img

    def __ge__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            img = img.img
        return self.img >= img

    def __eq__(self, img):
        self._to_numpy()
        if isinstance(img, Image):
            img = img.img
        return self.img == img

    def __getitem__(self, idx):
        self._to_numpy()
        return self.img[idx]

    def __setitem__(self, idx, val):
        self._to_numpy()
        self.img[idx] = val

    def _read(self):
        '''Read the image.
        '''
        self.img = PMImage(self.fname)

    def _to_numpy(self):
        '''Convert from PMImage to numpy.
        '''
        self.img = to_numpy(self.img)

    def _to_imagemagick(self):
        '''Convert from numpy to PMImage.
        '''
        self.img = to_numpy(self.img)

    def save(self, fname, bits=16, scale=True, adjustments=None):
        '''Save the image data.
        '''
        if scale:
            self._scale(bits)
        if adjustments:
            self._adjust(adjustments)
        self._to_imagemagick()
        self.img.write(fname)

    def min(self):
        '''Return the minimum value in the image.
        '''
        self._to_numpy()
        return np.min(self.img)

    def max(self):
        '''Return the maximum value in the image.
        '''
        self._to_numpy()
        return np.max(self.img)

    def astype(self, dtype):
        '''Return the image with the given dtype.
        '''
        return Image(img=self.img.astype(dtype))

    def luminance(self):
        '''Return luminance (channel average).
        '''
        if len(self.img.shape) == 3:
            return Image(img=np.mean(self.img, 2))
        else:
            return Image(img=self.img)

    def _adjust(self, adjustments):
        '''Adjust the image with the given function(s) and arguments.
        '''
        self._to_imagemagick()
        functions = {'usm': self._usm,
                     'emboss': self._emboss,
                     'gamma': self._gamma,
                     'br': self._blue_red_subtract,
                     'rg': self._red_green_subtract,
                     'rgb_sub': self._rgb_subtract,
                     'gradient': self._gradient
                     }
        for key in adjustments:
            func = functions[key]
            self.img = func(*adjustments[key])

    def _channel_difference(self, chan1, chan2, multiplier=1.0):
        '''Calculate channel difference: chan1 * multiplier - chan2.
        '''
        self._to_numpy()
        self.img = multiplier * self.img[:, :, chan1] - self.img[:, :, chan2]

    def _blue_red_subtract(self, multiplier):
        '''Subtract red channel from the blue channel after scaling
        the blue channel using the supplied multiplier.
        '''
        self._channel_difference(2, 0, multiplier=multiplier)

    def _red_green_subtract(self, multiplier):
        '''Subtract green channel from the red channel after scaling
        the red channel using the supplied multiplier.
        '''
        self._channel_difference(0, 1, multiplier=multiplier)

    def _rgb_subtract(self):
        '''Subtract the mean(r,g,b) from all the channels.
        '''
        self._to_numpy()
        self.img -= self.luminance().img

    def _gradient(self):
        '''Remove the background gradient.
        '''
        self._to_numpy()
#        grad = Gradient(self.img, method, *args)
#        grad.remove_gradient()
        self.img = self.img

    def _scale(self, bits):
        '''Scale image to cover the whole bit-range.
        '''
        self._to_numpy()
        img = 1.0*self.img - np.min(self.img)
        img_max = np.max(img)
        if img_max != 0:
            img = (2**bits - 1) * img / img_max
        if bits <= 8:
            self.img = img.astype('uint8')
        else:
            self.img = img.astype('uint16')

    def _usm(self, radius, sigma, amount, threshold):
        '''Unsharp mask sharpen the image.
        '''
        self._to_imagemagick()
        self.img.unsharpmask(radius, sigma, amount, threshold)

    def _emboss(self):
        '''Emboss filter the image. Actually uses shade() from
        ImageMagick.
        '''
        self._to_imagemagick()
        self.img.emboss(90, 45)

    def _gamma(self, gamma):
        '''Apply gamma correction to the image.
        '''
        self._to_imagemagick()
        self.img.gamma(gamma)

def to_numpy(img):
    '''Convert the image data to numpy array.
    '''

    if not isinstance(img, np.ndarray):
        img.magick('RGB')
        blob = Blob()
        img.write(blob)
        data = blob.data
        out_img = np.fromstring(data, dtype='uint'+str(img.depth()))

        height, width, chans = img.rows(), img.columns(), 3
        if img.monochrome():
            chans = 1

        return out_img.reshape(height, width, chans)

    return img

def to_imagemagick(img):
    '''Convert the numpy array to Imagemagick format.
    '''
    if not isinstance(img, PMImage):
        out_img = PMImage()
        if img.dtype == 'uint8':
            out_img.depth(8)
        else:
            out_img.depth(16)
        out_img.magick('RGB')
        shape = out_img.shape
        out_img.size(str(shape[1])+'x'+str(shape[0]))
        blob = Blob()
        blob.data = img.tosting()
        out_img.read(blob)
        out_img.magick('PNG')

        return out_img
    return img
