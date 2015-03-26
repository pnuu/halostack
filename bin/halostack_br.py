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

# the actual halostack BR work is three lines

# read image
img = Image(fname=fname_in)
# gradient removal and B-R maneuver
img.enhance({'gradient': None, 'br': None})
# save the resulting image
img.save(out_fname)
