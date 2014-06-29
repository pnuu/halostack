import unittest
import os
from halostack.align import Align
import numpy as np

class TestAlign(unittest.TestCase):
    
    def setUp(self):
        # reference image
        img = np.zeros((31, 31))
        img[15, 15] = 1
        # reference area: center_y, center_x, dim/2-1
        ref_loc = (15, 15, 2)
        # area to search (whole image)
        srch_area = [0, 0, 31, 31]

        self.align = Align(img, ref_loc=ref_loc, srch_area=srch_area)

    def test_simple_match(self):
        # image to be matched
        img = np.zeros((31, 31))
        img[12, 12] = 1
        # correlation, y-location, x-location
        correct_result = [1.0, 12, 12]
        result = self.align._simple_match(img)
        self.assertItemsEqual(result, correct_result)

def suite():
    """The suite for test_align
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestAlign))
