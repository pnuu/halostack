.. .. sectnum::
..   :depth: 4
..   :start: 2
..   :suffix: .

.. _string-format: https://docs.python.org/2/library/string.html#format-string-syntax

Usage
-----

Command-line interface ``halostack_cli.py`` to Halostack libraries is
available in the ``bin/`` directory.  There is also a very simple
example how to generate B-R processed image, ``halostack_br.py``.


Basic usage
___________

As a first step, we'll show how the alignment reference is selected
from the first image in the stack.  To start, issue the following command::

  $ halostack_cli.py -a average_stack.png *.jpg

You'll get a new window showing the first image:

.. image:: images/align_reference.jpg

It is usually helpful first to expand the window to full screen.

From the image, we need to click the two corner points of the area
having the Sun.  These points are marked with plus-signs, and the
image will be closed after the second point has been selected.  Try to
select the points so that the area is as tightly around the Sun as
possible, but still so that there's some black from the blocker
included in the area.

Simililarly, we need to select the area where this reference area will
be searched from in the following images:

.. image:: images/align_search_area.jpg

This area needs to be larger than the reference area.  In northern
hemishphere, the Sun (and Moon) moves towards right, so with a image
series photographed using a tripod we don't need to add much extra
area on the left side of the reference.  There's a tradeoff in the
area size: The smaller the area is, the faster the alignment will be.
But if the area is too small, the reference might not be inside the
area, and that image will not be used in the stack.  Or even worse,
there's a similar area with good enough correlation and that feature
is selected, ruining the whole stack.


Command-line options
____________________

``python bin/halostack_cli.py [options] <list of filenames>``

- ``-a, --average-stack``

  - ``-a average_stack.png``
  - output filename of the average stack

- ``-m, --min-stack``

  - ``-m minimum_stack.png``
  - output filename of the minimum stack

- ``-M, --max-stack``

  - ``-M maximum_stack.png``
  - output filename of the maximum stack

- ``-d, --median-stack``

  - ``-d median_stack.png``
  - output filename of the median stack

- ``-t, --correlation-threshold``

  - ``-t 0.9``
  - minimum required correlation
  - default: 0.7

- ``-s, --save-images``

  - ``-s aligned_images_``
  - save aligned images as PNG with the given filename prefix
  - this will save the images with filenames like ``aligned_images_IMG_0001.png`` etc.

- ``-n, --no-alignment``

  - ``-n``
  - stack without alignment
  - no arguments

- ``-e, --enhance-images``

  - ``-e gradient:20``
  - enhancement functions applied to each input image before alignment and stacking
  - can be called several times
  - processing is done in the given order

- ``-E, --enhance-stacks``

  - ``-E usm:25,2``
  - enhancement functions applied to each stack
  - can be called several times
  - processing is done in the given order

- ``-g, --view-gamma``

  - ``-g 1.5``
  - adjust image gamma for alignment preview
  - default: 1.0

- ``-C, --config``

  - ``-C config.ini``
  - use config file <file>

- ``-c, --config_item``

  - ``-c default``
  - select the config item to use

- ``-l, --loglevel``

  - ``-l debug``
  - ``-l info``
  - ``-l warning``
  - ``-l error``
  - set the level of messages

- ``<list of filenames>``

  - ``*.jpg``
  - ``images/*.*``
  - ``IMG_0001.jpg IMG_0002.jpg IMG_0003.jpg``


Configuration file
__________________

Everything that can be set with the command-line options can also be
setup in a configuration file.  Command-line options will override
settings obtained from the configuration file.

Below is an example configuration::

    # average stack from raw/tiff images with view gamma set
    [avg_from_raw]
    average_stack = average.png
    view_gamma = 1.5

    # average stack from raw/tiff images with view gamma set and USM applied to the stack
    [avg_from_raw]
    average_stack = average.png
    view_gamma = 1.5
    enhance_stacks = usm:25,2

    # B-R processing without stacking and less output
    [br]
    no_alignment = 
    enhance_stacks = gradient br
    loglevel = warning

These pre-set configurations can be used like this::

    $ halostack_cli.py -C <configuration file> -c <config item>

For example, using the B-R configuration defined above::

    $ halostack_cli.py -C config.ini -c br


Image processing options
________________________

This *tries* to be a complete list of image pre- and post-processing
options available in Halostack.  These enhancements can be applied
using ``-e`` and ``-E`` command-line switches, or corresponding
configuration file options ``enhance_images`` and ``enhance_stacks``.

Unsharp mask
++++++++++++

Unsharp mask, or USM in short, is a way to enhance halos.

Blue - Red
++++++++++

br

Red - Green
+++++++++++

rg

Gradient removal
++++++++++++++++

gradient

Emboss
++++++

emboss

Luminance subtraction
+++++++++++++++++++++

rgb_sub

Linear stretching
+++++++++++++++++

stretch

