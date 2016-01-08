import unittest
import os
from halostack.align import Align
import numpy as np

class TestAlign(unittest.TestCase):
    
    def setUp(self):
        # reference image
        self.img = np.zeros((31, 31, 3))
        self.img[15, 15, :] = 1
        # reference area: center_y, center_x, dim/2-1
        ref_loc = (15, 15, 2)
        # area to search (whole image)
        srch_area = [0, 0, 31, 31]

        self.align = Align(self.img, nprocs=1)
        self.align.set_reference(ref_loc)
        self.align.set_search_area(srch_area)

    def test_simple_match(self):
        # image to be matched
        img = np.zeros((31, 31, 3))
        img[12, 12, :] = 1
        # correlation, y-location, x-location
        correct_result = [1.0, 12, 12]
        result = self.align._simple_match(img)
        self.assertItemsEqual(result, correct_result)


    def test_calc_shift(self):
        result = self.align._calc_shift(10, 10)
        correct_result = [5, 5]
        self.assertItemsEqual(result, correct_result)

    def test_calc_shift_ranges(self):
        result = self.align._calc_shift_ranges(2, -3)
        correct_result = [[2, 31], [0, 28],
                          [0, 29], [3, 31]]
        for i in range(4):
            self.assertItemsEqual(result[i], correct_result[i])

    def test_shift(self):
        img2 = self.align._shift(self.img, 2, -3)
        correct_result = np.zeros((31, 31, 3))
        correct_result[12, 17, :] = 1
        self.assertTrue(np.allclose(img2, correct_result))


def suite():
    """The suite for test_align
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestAlign))
