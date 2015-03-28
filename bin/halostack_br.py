#!/usr/bin/env python

from halostack.image import Image
import sys
import os
from collections import OrderedDict as od

# input file
fname_in = sys.argv[1]

# form the output filename
head, tail = os.path.split(fname_in)
tail = tail.split('.')[:-1]
tail.append('png')
tail = 'br_' + '.'.join(tail)
out_fname = os.path.join(head, tail)

# the actual halostack bit is only three lines

# read image
img = Image(fname=fname_in)
# combined gradient removal and B-R
img.enhance({'gradient': None, 'br': None})
# save the resulting image
img.save(out_fname)
