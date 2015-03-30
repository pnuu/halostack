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

'''Module for image I/O and conversions'''

from PythonMagick import Image as PMImage
from PythonMagick import Blob
import numpy as np
import itertools
import logging

LOGGER = logging.getLogger(__name__)

class Image(object):
    '''Image class'''

    def __init__(self, img=None, fname=None, enhancements=None):
        self.img = img
        self.fname = fname

        if fname is not None:
            self._read()
        if enhancements:
            self.enhance(enhancements)
        self.shape = None
        self._to_numpy()

    def __add__(self, img):
        if isinstance(img, Image):
            img.to_numpy()
            return Image(img=self.img+img.img)
        else:
            # Assume a numpy array or scalar
            return Image(img=self.img+img)

    def __radd__(self, img):
        return self.__add__(img)

    def __sub__(self, img):
        if isinstance(img, Image):
            img.to_numpy()
            return Image(img=self.img-img.img)
        else:
            # Assume a numpy array or scalar
            return Image(img=self.img-img)

    def __rsub__(self, img):
        return self.__sub__(img)

    def __isub__(self, img):
        self.img = self.__sub__(img)

    def __mul__(self, img):
        if isinstance(img, Image):
            img.to_numpy()
            return Image(img=self.img*img.img)
        else:
            # Assume a numpy array or scalar
            return Image(img=self.img*img)

    def __rmul__(self, img):
        return self.__mul__(img)

    def __div__(self, img):
        if isinstance(img, Image):
            img.to_numpy()
            return Image(img=self.img/img.img)
        else:
            # Assume a numpy array or scalar
            return Image(img=self.img/img)

    def __abs__(self):
        self._to_numpy()
        return Image(img=np.abs(self.img))

    def __lt__(self, img):
        if isinstance(img, Image):
            img.to_numpy()
            img = img.img
        return self.img < img

    def __le__(self, img):
        if isinstance(img, Image):
            img.to_numpy()
            img = img.img
        return self.img <= img

    def __gt__(self, img):
        if isinstance(img, Image):
            img.to_numpy()
            img = img.img
        return self.img > img

    def __ge__(self, img):
        if isinstance(img, Image):
            img.to_numpy()
            img = img.img
        return self.img >= img

    def __eq__(self, img):
        if isinstance(img, Image):
            img.to_numpy()
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

    def to_numpy(self):
        '''Convert from PMImage to numpy.
        '''
        self._to_numpy()

    def _to_numpy(self):
        '''Convert from PMImage to numpy.
        '''
        self.img = to_numpy(self.img)
        self.shape = self.img.shape

    def _to_imagemagick(self):
        '''Convert from numpy to PMImage.
        '''
        self.img = to_imagemagick(self.img)

    def save(self, fname, bits=16, scale=True, enhancements=None):
        '''Save the image data.
        '''
        if enhancements:
            self.enhance(enhancements)
        if scale:
            self._scale(bits)
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

    def enhance(self, enhancements):
        '''Enhance the image with the given function(s) and argument(s).
        '''
        functions = {'usm': self._usm,
                     'emboss': self._emboss,
                     'blur': self._blur3,
                     'gamma': self._gamma,
                     'br': self._blue_red_subtract,
                     'rg': self._red_green_subtract,
                     'rgb_sub': self._rgb_subtract,
                     'gradient': self._remove_gradient,
                     'stretch': self._stretch}

        for key in enhancements:
            LOGGER.info("Apply %s.", key)
            func = functions[key]
            func(enhancements[key])

    def _channel_difference(self, chan1, chan2, multiplier=None):
        '''Calculate channel difference: chan1 * multiplier - chan2.
        '''
        self._to_numpy()
        chan1 = self.img[:, :, chan1].copy()
        chan2 = self.img[:, :, chan2].copy()
        if multiplier is None:
            idxs = np.logical_and(chan1 > 0, chan2 > 0)
            multiplier = np.mean(chan1[idxs]/chan2[idxs])
        self.img = multiplier * chan1 - chan2

    def _blue_red_subtract(self, args):
        '''Subtract red channel from the blue channel after scaling
        the blue channel using the supplied multiplier.
        '''
        LOGGER.debug("Calculating channel difference, blue-red.")
        self._channel_difference(2, 0, multiplier=args)

    def _red_green_subtract(self, args):
        '''Subtract green channel from the red channel after scaling
        the red channel using the supplied multiplier.
        '''
        LOGGER.debug("Calculating channel difference, red-green.")
        self._channel_difference(0, 1, multiplier=args)

    def _rgb_subtract(self, args):
        '''Subtract the mean(r,g,b) from all the channels.
        '''
        LOGGER.debug("Subtracting luminance from all color channels.")
        del args
        self._to_numpy()
        self.img = self.img.astype(np.float)
        luminance = self.luminance().img
        for i in range(3):
            self.img[:, :, i] -= luminance
        self.img -= self.img.min()

    def _stretch(self, args):
        '''Apply a linear stretch to the image.
        '''
        self._to_numpy()
        # args = [bits, low_cut, high_cut]
        if len(args) == 1:
            args.append(0.05)
        if len(args) == 2:
            args.append(0.05)
        LOGGER.debug("Applying linear stretch.")
        LOGGER.debug("%d bits, low cut: %.2f %%, high cut: %.2f %%",
                     args[0], args[1], args[2])
        # Use luminance
        lumin = np.mean(self.img, 2)
        lumin -= np.min(lumin)
        lumin = (2**args[0]-1)*lumin/np.max(lumin)

        hist, _ = np.histogram(lumin.flatten(), 2**args[0]-1,
                               normed=True)
        cdf = hist.cumsum() # cumulative distribution function
        cdf = (2**args[0]-1) * cdf / cdf[-1] # normalize

        start = 0
        csum = 0
        while csum < (2**args[0]-1)*args[1]:
            csum += cdf[start]
            start += 1
        end = 2**args[0]-1
        csum = 0
        while csum < (2**args[0]-1)*args[2]:
            csum += (cdf[-1]-cdf[end])
            end -= 1

        self.img -= start
        self.img = (2**args[0]-1)*self.img/(end-start)

    def _remove_gradient(self, args):
        '''Calculate the gradient from the image, subtract from the
        original, scale back to full bit depth and return the result.
        '''
        self._to_numpy()
        LOGGER.debug("Removing gradient.")
        self.img = self.img.astype(np.float)
        args = {'method': {'blur': args}}
        gradient = self._calculate_gradient(args)
        self.img -= gradient.img

        if self.img.min() < 0:
            self.img -= self.img.min()

    def _calculate_gradient(self, args):
        '''Calculate gradient from the image using the given method.
        param method: name of the method for calculating the gradient
        '''
        methods = {'blur': self._gradient_blur,
                   'random': self._gradient_random_points,
                   'grid': self._gradient_grid_points}
        # 'user': self._gradient_get_user_points,
        # 'mask': self._gradient_mask_points,
        # 'all': self._gradient_all_points

        LOGGER.debug("Calculating gradient.")
        try:
            func = methods[args['method'].keys()[0]]
        except TypeError:
            LOGGER.error("Method \"%s\" not available, using method \"blur\"",
                         args['method'].keys()[0])
            args = {}
            args['method'] = {'blur': None}
            func = methods['blur']
        result = func(args['method'])
        shape = self.img.shape

        if args['method'].keys()[0] is 'blur':
            return result

        x_pts, y_pts = result
        if len(shape) == 2:
            return Image(img=self._gradient_fit_surface(x_pts, y_pts,
                                                        order=args['order']))
        else:
            gradient = np.empty(shape)
            for i in range(shape[2]):
                gradient[:, :, i] = \
                    self._gradient_fit_surface(x_pts, y_pts,
                                               order=args['order'],
                                               chan=i)
            return Image(img=gradient)

    def _gradient_blur(self, args):
        '''Blur the image to get the approximation of the background
        gradient.
        '''
        gradient = Image(img=self.img.copy())
        gradient.enhance(args)

        return gradient

    def _gradient_random_points(self, args):
        '''Automatically extract background points for gradient estimation.
        '''
        shape = self.img.shape
        y_pts = np.random.randint(shape[0], size=(args['points'],))
        x_pts = np.random.randint(shape[1], size=(args['points'],))

        return (x_pts, y_pts)

    def _gradient_grid_points(self, args):
        '''Get uniform sampling of image locations.
        '''
        shape = self.img.shape
        y_locs = np.arange(0, shape[0], args['points'])
        x_locs = np.arange(0, shape[1], args['points'])
        x_mat, y_mat = np.meshgrid(x_locs, y_locs, indexing='ij')

        return (x_mat.ravel(), y_mat.ravel())

    def _gradient_fit_surface(self, x_pts, y_pts, order=2, chan=None):
        '''Fit a surface to the given channel.
        '''
        shape = self.img.shape
        x_locs, y_locs = np.meshgrid(np.arange(shape[0]),
                                     np.arange(shape[1]))
        if chan is not None:
            poly = polyfit2d(x_pts, y_pts, self.img[y_pts, x_pts, chan].ravel(),
                             order=order)
            return polyval2d(x_locs, y_locs, poly)
        else:
            poly = polyfit2d(x_pts, y_pts, self.img[y_pts, x_pts].ravel(),
                             order=order)
            return polyval2d(x_locs, y_locs, poly).T

    def _scale(self, *args):
        '''Scale image to cover the whole bit-range.
        '''
        self._to_numpy()
        img = 1.0*self.img - np.min(self.img)
        img_max = np.max(img)
        if img_max != 0:
            img = (2**args[0] - 1) * img / img_max
        if args[0] <= 8:
            LOGGER.info("Fitting the image to 8-bits.")
            self.img = img.astype('uint8')
        else:
            LOGGER.info("Fitting the image to 16-bits.")
            self.img = img.astype('uint16')

    def _rotate(self, *args):
        '''Rotate image.
        '''
        # use scipy.ndimage.interpolation.rotate()
        del args
        LOGGER.error("Image rotation not implemented.")

    def _usm(self, args):
        '''Unsharp mask sharpen the image.
        '''
        LOGGER.debug("Apply unsharp mask.")
        self._to_imagemagick()
        if len(args) == 2:
            args.append(np.sqrt(args[0]))
        if len(args) == 3:
            args.append(0)
        self.img.unsharpmask(*args)

    def _emboss(self, args):
        '''Emboss filter the image. Actually uses shade() from
        ImageMagick.
        '''
        LOGGER.debug("Apply emboss.")
        if args is None:
            args = []
        if len(args) == 0:
            args.append(90)
        if len(args) == 1:
            args.append(45)
        self._to_imagemagick()
        self.img.shade(*args)

    def _blur(self, args):
        '''Blur the image.
        '''
        self._to_imagemagick()
        # args['radius'], args['weight'])
        self.img.blur(*args)

    def _blur2(self, args):
        '''Blur the image using 1D convolution for each column and
        row. Data borders are padded with mean of the data before
        convolution to reduce the edge effects.
        '''
        shape = self.img.shape
        if args is None:
            radius = int(np.min(shape[:2])/20.)
        else:
            radius = args[0] # args['radius']

        kernel = np.ones(2*radius)/(2*radius)
        for i in range(shape[-1]):
            # rows
            for j in range(shape[0]):
                vect = np.mean(self.img[j, :, i]) + \
                    np.zeros(2*radius+shape[1]-1)
                vect[radius:radius+shape[1]] = self.img[j, :, i]
                vect_conv = np.convolve(vect, kernel, mode='full')
                self.img[j, :, i] = vect_conv[2*radius:2*radius+shape[1]]
            # columns
            for j in range(shape[1]):
                vect = np.mean(self.img[:, j, i]) +\
                    np.zeros(2*radius+shape[0]-1)
                vect[radius:radius+shape[0]] = self.img[:, j, i]
                vect_conv = np.convolve(vect, kernel, mode='full')
                self.img[:, j, i] = vect_conv[2*radius:2*radius+shape[0]]

        self.img -= np.min(self.img)

    def _blur3(self, args):
        '''Blur the image using 1D convolution for each column and
        row. Data borders are padded with mean of the border area
        before convolution to reduce the edge effects.
        '''
        shape = self.img.shape
        if args is None:
            radius = int(np.min(shape[:2])/20.)
        else:
            radius = args[0] # args['radius']

        kernel = np.ones(2*radius)/(2*radius)
        for i in range(shape[-1]):
            # rows
            for j in range(shape[0]):
                vect = np.zeros(2*radius+shape[1]-1)
                vect[:radius] = np.mean(self.img[j, :radius, i])
                vect[radius:radius+shape[1]] = self.img[j, :, i]
                vect[-radius:] = np.mean(self.img[j, -radius:, i])
                vect_conv = np.convolve(vect, kernel, mode='full')
                self.img[j, :, i] = vect_conv[2*radius:2*radius+shape[1]]
            # columns
            for j in range(shape[1]):
                vect = np.zeros(2*radius+shape[0]-1)
                vect[:radius] = np.mean(self.img[:radius, j, i])
                vect[radius:radius+shape[0]] = self.img[:, j, i]
                vect[-radius:] = np.mean(self.img[-radius:, j, i])
                vect_conv = np.convolve(vect, kernel, mode='full')
                self.img[:, j, i] = vect_conv[2*radius:2*radius+shape[0]]

        self.img -= np.min(self.img)

    def _gamma(self, args):
        '''Apply gamma correction to the image.
        '''
        self._to_imagemagick()
        self.img.gamma(args[0])

def to_numpy(img):
    '''Convert ImageMagick data to numpy array.
    '''
    if not isinstance(img, np.ndarray):
        LOGGER.debug("Converting from ImageMagick to Numpy.")
        img.magick('RGB')
        blob = Blob()
        img.write(blob)
        out_img = np.fromstring(blob.data, dtype='uint'+str(img.depth()))

        height, width, chans = img.rows(), img.columns(), 3
        if img.monochrome():
            chans = 1

        return out_img.reshape(height, width, chans)

    return img

def to_imagemagick(img):
    '''Convert numpy array to Imagemagick format.
    '''

    if not isinstance(img, PMImage):
        LOGGER.debug("Converting from Numpy to ImageMagick.")
        out_img = PMImage()
        if img.dtype == np.uint8:
            out_img.depth(8)
        else:
            out_img.depth(16)

        shape = img.shape
        # Save also B&W images as RGB
        if len(shape) == 2:
            tmp = np.empty((shape[0], shape[1], 3), dtype=img.dtype)
            tmp[:, :, 0] = img
            tmp[:, :, 1] = img
            tmp[:, :, 2] = img
            img = tmp
        out_img.magick('RGB')
        out_img.size(str(shape[1])+'x'+str(shape[0]))
        blob = Blob()
        blob.data = img.tostring()

        out_img.read(blob)
        out_img.magick('PNG')

        return out_img
    return img

def polyfit2d(x_loc, y_loc, z_val, order=2):
    '''Fit a 2-D polynomial to the given data.

    Implementation from: http://stackoverflow.com/a/7997925
    '''
    LOGGER.debug("2D polynomial fit")
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
    LOGGER.debug("Evaluate 2D polynomial.")
    order = int(np.sqrt(len(poly))) - 1
    ij_loc = itertools.product(range(order+1), range(order+1))
    surf = np.zeros_like(x_loc)
    for arr, (i, j) in zip(poly, ij_loc):
        surf += arr * x_loc**i * y_loc**j
    return surf
