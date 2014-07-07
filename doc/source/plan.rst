
The Plan
========

Command-line parsing
--------------------

``./halostack.py [options] <list of filenames>``

- -a, --average-stack --- *Output filename of the average stack*

  ``-a average_stack.png``

- -m, --min-stack --- *Output filename of the minimum stack*

  ``-m minimum_stack.png``

- -M, --max-stack --- *Output filename of the maximum stack*

  ``-M maximum_stack.png``

- -d, --median-stack --- *Output filename of the median stack*

  ``-d median_stack.png``

- -t, --correlation-threshold --- *Minimum required correlation [0.7]*

  ``-t 0.9``

- -s, --save-images --- *Save aligned images as PNG with the given filename postfix*

  ``-s aligned_images_``

  - this will save the images with filenames like *aligned_images_IMG_0001.png* etc.

- -n, --no-alignment --- *Stack without alignment*

  ``-n``

  - no arguments

- -e, --enhance-images --- *Enhancement functions applied to each input image*

  ``-e gradient:20``

- -E, --enhance-stacks --- *Enhancement functions applied to each stack*

  ``-E usm:25,2 gradient:20``

.. - -g, --view-gamma <num> --- *Adjust image gamma for alignment preview*
.. 
..  ``-g 1.5``

- -c, --config --- *Use config file <file>*

  ``-c config.ini``

- -C, --cli --- *Start CLI*

  ``-c``

  - no arguments
  - GUI not implemented, so this is default for now

- *<list of filenames>*

  ``*.jpg``
  ``*.*``
  ``IMG_0001.jpg, IMG_0002.jpg IMG_0003.jpg``

Config file usage
-----------------

- everything that is available also as command line switches

  - follow: Sun or Moon

    - will need pyephem, only linux?

  - lens information

    - projection
    - focal length

  - pixel dimensions
  - location


Image input and conversions
------------------------------

- formats

  - everything ImageMagick supports, relevant ones being:

    - JPG --- **check**
    - TIFF --- **check**
    - PNG --- **check**
    - RAW with IM+dcraw (only linux?)

- convert image to numpy array --- **check**
- convert numpy array to ImageMagick format --- **check**
- read date and time from EXIF

  - python-exif for linux, windows?
  - separate CSV file needed for TIFF and/or windows?

Alignment prerequisites
-----------------------

- focus reference selection

  - manual

    - matplotlib --- **check**
    - GUI (not by me)

- selection of area where focus point stays during the stack duration

  - manual

    - matplotlib --- **check**
    - GUI (not by me)

  - solar/lunar tracking based on date, time, location and idealized lens model

    - get reference locations from the first and last images

      - needs centroid calculations

Image co-alignment
------------------

- lens projection handling

  - convert all the images to RA/DEC coordinates if Sun or Moon used?

- calculate rotation

  - solar/lunar tracking based on date, time, location and lens projection

- rotate image
  
  - adjust search area?

- calculate shift

  - reference correlation --- **check**
  - phase correlation?
  - solar/lunar tracking based on date, time, location and lens projection

- shift image


Image stacking
--------------

Image preprocessing
___________________

- subtract bias?
- flat correction?

  - would reduce the effect of dust

- remove sky gradient

  - blurred (with large radius) version of the image --- **check**

    - pyimagemagick --- **check**

      - slow

    - convolution --- **check**

      - much faster
      - better results than with pyimagemagick

  - gradient model --- **check**

    - gradient plane: ax^2 + by^2 + cxy + dx + ey + f --- **check**

      - better fitting/evaluation algorithms needed

    - uniform reference point selection --- **check**
    - random reference point selectio --- **check**
    - area exclusion mask?

Calculate stacks
________________

- average --- **check**
- median --- **check**

  - needs lots of RAM

    - or memmap'd HDF5 (only linux?)

  - would be useful for making flat-field images
  - but not really needed?

- minimum --- **check**
- maximum --- **check**
- sigma-average

  - really necessary?
  - needs lots of RAM

    - or memmap'd HDF5 (only linux?)

Image postprocessing
____________________

- remove gradients --- **check**

  - should be done before stacking
  - select points or use blur --- **check**

- B-R --- **check**

  - automatic multiplier calculation --- **check**
  - http://opticsaround.blogspot.fr/2013/03/le-traitement-bleu-moins-rouge-blue.html

- R, G, B = (R, G, B) - average(R, G, B) --- **check**
- USM --- **check**
- emboss --- **check**
- gamma --- **check**

Image output
-----------------

- scale data to cover full range of the format --- **check**

  - mean
  - sigma-mean

- formats

  - 8/16-bit PNG
  - JPG preview
