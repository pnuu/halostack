
The Plan
========

Command-line parsing
--------------------

- keep simple
- only most-used switches

Config file usage
-----------------

- everything that is available also as command line switches

  .. - follow: Sun or Moon

  - lens information
  - pixel dimensions
  - location


Image data I/O and conversions
------------------------------

- formats

  - everything ImageMagick supports, relevant ones being:

    - JPG
    - TIFF
    - PNG
    - RAW input (only linux?)

  - HDF5 using h5py (only linux?)

- convert read image to numpy array
- convert numpy array to ImageMagick format
- keep linear, if possible
- keep as integer data
- read date and time from EXIF

  - separate CSV file needed for TIFF?

Alignment prerequisites
-----------------------

- focus point selection
- selection of area for focus point during the stack

  - manual

..  - solar/lunar tracking based on date, time and location
..  - get reference locations from the first and last images

Image co-alignment
------------------

- lens projection handling
- find the focus point
- image resampling/shifting
- image rotation

  - manual
  - solar/lunar tracking based on date, time, location and lens projection

Image stacking
--------------

Image preprocessing
___________________

- remove gradients

  - use gradient model

    - fit the gradient plane: ax^2 + by^2 + cx + dy + e

  - use blurred version of the image

Calculate stacks
________________
- average
- median
- minimum
- maximum
- sigma-average

Image postprocessing
____________________
- remove gradients

  - select points for gradient removal

- B-R

  - select points to calculate optimal multiplier for R-channel
  - http://opticsaround.blogspot.fr/2013/03/le-traitement-bleu-moins-rouge-blue.html

- R, G, B = (R, G, B) - average(R, G, B)
- USM
- emboss
- gamma

Image/data output
-----------------

- scale data to cover full range of the format
- formats

  - 8/16-bit PNG
  - JPG preview
  - HDF5 (double, only linux?)
