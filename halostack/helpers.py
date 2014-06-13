
import logging
from glob import glob

LOGGER = logging.getLogger(__name__)

def get_filenames(fnames):
    '''Get filenames to a list. Expand wildcards etc.
    '''

    fnames_out = []

    # Ensure that all files are used also on Windows, as the command
    # prompt does not automatically parse wildcards to a list of images
    for fname in fnames:
        if '*' in fname:
            all_fnames = glob(fname)
            for fname2 in all_fnames:
                fnames_out.append(fname2)
                LOGGER.info("Added %s to the image list" % fname2)
        else:
            fnames_out.append(fname)
            LOGGER.info("Added %s to the image list" % fname)

    return fnames_out
