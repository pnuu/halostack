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
        rgb_arr = np.ones((3, 3, 3))
        rgb_arr[:, :, 1] += 1
        rgb_arr[:, :, 2] += 2
        self.img_rgb = Image(img=rgb_arr)
        self.img_rand8 = Image(img=np.random.randint(2**8-1, size=(3, 3, 3)))
        self.img_rand16 = Image(img=np.random.randint(2**16-1, size=(3, 3, 3)))
        self.img_rand_big1 = Image(img=np.random.randint(30 * (2**16 - 1),
                                                         size=(3, 3, 3)))
        self.img_rand_big2 = Image(img=np.random.randint(30 * (2**16 - 1),
                                                         size=(3, 3, 3)))
        self.img_rand_neg = Image(img=np.random.randint(-100, 100,
                                                         size=(3, 3, 3)))

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

    def test_luminance(self):
        # B&W image
        result = self.img2.luminance()
        self.assertItemsEqual(self.img2.img, result.img)
        # RGB image
        result = self.img_rgb.luminance()
        self.assertItemsEqual(self.img3.img, result.img)

    def test_channel_differences(self):
        # B-R
        img = 1*self.img_rgb
        img._blue_red_subtract({'multiplier': 1})
        self.assertItemsEqual(self.img3.img, img.img)
        img = 1*self.img_rgb
        img._red_green_subtract({'multiplier': 2})
        self.assertItemsEqual(self.img1.img, img.img)
        img = 1*self.img_rgb
        img._red_green_subtract({'multiplier': None})
        self.assertItemsEqual(-1.5*self.img2.img, img.img)

    def test_rgb_subtract(self):
        img = 1*self.img_rgb
        img._rgb_subtract()
        correct_result = np.zeros((3, 3, 3))
        correct_result[:, :, 0] = -1
        correct_result[:, :, 2] = 1
        self.assertItemsEqual(correct_result, img.img)

    def test_scale_values(self):
        self.img_rand8._scale({'bits': 8})
        self.assertTrue(self.img_rand8.img.dtype == 'uint8')
        self.assertTrue(self.img_rand8.min() == 0)
        self.assertTrue(self.img_rand8.max() == 255)

        self.img_rand16._scale({'bits': 16})
        self.assertTrue(self.img_rand16.img.dtype == 'uint16')
        self.assertTrue(self.img_rand16.min() == 0)
        self.assertTrue(self.img_rand16.max() == 2**16-1)

        self.img_rand_big1._scale({'bits': 8})
        self.assertTrue(self.img_rand_big1.img.dtype == 'uint8')
        self.assertTrue(self.img_rand_big1.min() == 0)
        self.assertTrue(self.img_rand_big1.max() == 255)

        self.img_rand_big2._scale({'bits': 16})
        self.assertTrue(self.img_rand_big2.img.dtype == 'uint16')
        self.assertTrue(self.img_rand_big2.min() == 0)
        self.assertTrue(self.img_rand_big2.max() == 2**16-1)

        self.img_rand_neg._scale({'bits': 8})
        self.assertTrue(self.img_rand_neg.min() >= 0)

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
