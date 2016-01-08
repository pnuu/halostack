#!/usr/bin/env python

from halostack.image import Image
import sys
import os

# input file
fname_in = sys.argv[1]

# form the output filename
head, tail = os.path.split(fname_in)
tail = tail.split('.')[:-1]
tail.append('png')
tail = 'br_' + '.'.join(tail)
out_fname = os.path.join(head, tail)

# the actual halostack bit is only four lines

# read image
img = Image(fname=fname_in, nprocs=4)
# change data type to 64-bit float
img.set_dtype('float64')
# combined gradient removal and B-R
img.enhance({'gradient': None, 'br': None})
# save the resulting image
img.save(out_fname)
