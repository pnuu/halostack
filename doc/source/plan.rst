
The Plan
========

Command-line parsing
--------------------

- keep simple
- only most-used switches

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

    - matplotlib

- selection of area where focus point stays during the stack duration

  - manual

    - matplotlib

  - solar/lunar tracking based on date, time, location and idealized lens model

    - get reference locations from the first and last images

Image co-alignment
------------------

- lens projection handling

  - convert all the images to RA/DEC coordinates if Sun or Moon used?

- calculate rotation

  - solar/lunar tracking based on date, time, location and lens projection

- rotate image
  
  - adjust search area?

- calculate shift

  - reference correlation
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

  - blurred (with large radius) version of the image

    - simple, easy to implement
    - halos affect slightly the resulting background value

  - gradient model

    - gradient plane: ax^2 + by^2 + cxy + dx + ey + f
    - uniform reference point selection?

      - area exclusion mask?
      - discard a point if too large difference compared to neighbours?

	- median filtering for reference points?
	- would reduce the effect of halos

    - user supplied reference points?

      - from first image, use same locations for each image
      - select points individually for each image

Calculate stacks
________________

- average --- **check**
- median --- **check**

  - needs lots of RAM, or memmap'd HDF5 (only linux?)
  - would be useful for making flat-field images
  - but not really needed?

- minimum --- **check**
- maximum --- **check**
- sigma-average

  - really necessary?
  - needs lots of RAM, or memmap'd HDF5 (only linux?)

Image postprocessing
____________________

- remove gradients?

  - should be done before stacking
  - select points or use blur

- B-R --- **check**

  - user supplied multiplier (default: 1.0) --- **check**
  - select points to calculate optimal multiplier for R-channel
  - http://opticsaround.blogspot.fr/2013/03/le-traitement-bleu-moins-rouge-blue.html

- R, G, B = (R, G, B) - average(R, G, B) --- **check**
- USM --- **check**
- emboss --- **check**
- gamma --- **check**

Image output
-----------------

- scale data to cover full range of the format

  - mean
  - sigma-mean

- formats

  - 8/16-bit PNG
  - JPG preview
