import unittest
import os
from halostack.image import Image
import numpy as np

class TestImage(unittest.TestCase):
    
    def setUp(self):
        self.img1 = Image(img=np.zeros((3, 3)))
        self.img2 = Image(img=np.ones((3, 3)))
        self.img3 = Image(img=2*np.ones((3, 3)))
        self.img4 = Image(img=3*np.ones((3, 3)))
#        self.img_rgb = Image(img=np.array([[[0])

    def test_add(self):
        result = self.img1 + self.img2
        correct_result = np.ones((3, 3))
        self.assertItemsEqual(result.img, correct_result)

    def test_radd(self):
        result = 2 + self.img1
        correct_result = 2 * np.ones((3, 3))
        self.assertItemsEqual(result.img, correct_result)
        
    def test_sub(self):
        result = self.img3 - self.img2
        correct_result = np.ones((3, 3))
        self.assertItemsEqual(result.img, correct_result)

    def test_mul(self):
        result = self.img3 * self.img4
        correct_result = 6 * np.ones((3, 3))
        self.assertItemsEqual(result.img, correct_result)

    def test_rmul(self):
        result = 2 * self.img3
        correct_result = 4 * np.ones((3, 3))
        self.assertItemsEqual(result.img, correct_result)

    def test_div(self):
        result = self.img3 / 2
        correct_result = np.ones((3, 3))
        self.assertItemsEqual(result.img, correct_result)

        result = self.img4 / self.img3
        correct_result = 1.5 * np.ones((3, 3))
        self.assertItemsEqual(result.img, correct_result)

    def test_abs(self):
        result = abs(-1 * self.img2)
        correct_result = np.ones((3, 3))
        self.assertItemsEqual(result.img, correct_result)

    def test_lt(self):
        result = self.img1 < self.img2
        correct_result = np.ones((3, 3)) < 2
        self.assertItemsEqual(result, correct_result)

    def test_le(self):
        result = self.img1 <= self.img2
        correct_result = np.ones((3, 3)) < 2
        self.assertItemsEqual(result, correct_result)

    def test_gt(self):
        result = self.img1 > self.img2
        correct_result = np.ones((3, 3)) > 2
        self.assertItemsEqual(result, correct_result)

    def test_ge(self):
        result = self.img1 >= self.img2
        correct_result = np.ones((3, 3)) >= 2
        self.assertItemsEqual(result, correct_result)

    def test_eq(self):
        result = self.img1 == self.img1
        correct_result = np.ones((3, 3)) == 1
        self.assertItemsEqual(result, correct_result)

    def test_getitem(self):
        result = self.img1[0, 0]
        correct_result = 0
        self.assertEqual(result, correct_result)

    def test_setitem(self):
        self.img1[0, 0] = 1
        result = self.img1[0, 0]
        correct_result = 1
        self.assertEqual(result, correct_result)

    def test_min(self):
        result = self.img1.min()
        correct_result = 0
        self.assertEqual(result, correct_result)

    def test_max(self):
        self.img1[0, 0] = 1
        result = self.img1.max()
        correct_result = 1
        self.assertEqual(result, correct_result)

#    def test_luminance(self):
#        result = self.img2.luminance()
#        print result
#        self.assertEqual(self.img2.img, result.img)

    def assertItemsEqual(self, a, b):
        if isinstance(a, np.ndarray):
            self.assertTrue(np.all(a == b))
            self.assertTrue(a.shape == b.shape)
        else:
            for i in range(len(a)):
                self.assertEqual(a[i], b[i])
            self.assertEqual(len(a), len(b))

def suite():
    """The suite for test_image
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestImage))
