#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Produce a gradient-removed blue-red image from a single photograph.

An example of using the Halostack library directly; the actual processing is
the four lines at the end.
"""

import os
import sys

try:
    from halostack.image import Image
except ImportError:                     # running from a source checkout
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from halostack.image import Image


def main(argv=None):
    """Process the file named on the command line."""
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("Usage: halostack_br.py <image file>")
        return 1

    fname_in = argv[0]
    head, tail = os.path.split(fname_in)
    out_fname = os.path.join(head, 'br_' + os.path.splitext(tail)[0] + '.png')

    # read image
    img = Image(fname=fname_in)
    # combined gradient removal and B-R
    img.enhance({'gradient': None, 'br': None})
    # save the resulting image
    img.save(out_fname)
    print("Wrote %s" % out_fname)

    return 0


if __name__ == "__main__":
    sys.exit(main())
