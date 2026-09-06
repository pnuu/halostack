#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Entry point for the ``halostack_br`` example command.

See :mod:`bin.halostack_br` for the script version of the same thing.
"""

import os
import sys

from halostack.image import Image


def main(argv=None):
    """Write a gradient-removed blue-red version of one image.

    :param argv: arguments, defaulting to ``sys.argv``
    :type argv: list of str or None
    :rtype: process exit status
    """
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("Usage: halostack_br <image file>")
        return 1

    fname_in = argv[0]
    head, tail = os.path.split(fname_in)
    out_fname = os.path.join(head, 'br_' + os.path.splitext(tail)[0] + '.png')

    img = Image(fname=fname_in)
    img.enhance({'gradient': None, 'br': None})
    img.save(out_fname)
    print("Wrote %s" % out_fname)

    return 0


if __name__ == "__main__":
    sys.exit(main())
