import unittest
import os
from halostack.image import Image
from halostack.stack import Stack
import numpy as np

class TestStack(unittest.TestCase):
    
    def setUp(self):
        self.median = Stack('median', 3)

        self.img1 = Image(img=np.zeros((3, 3, 3), dtype=np.float))
        self.img2 = Image(img=np.zeros((3, 3, 3), dtype=np.float)+1)
        self.img3 = Image(img=np.zeros((3, 3, 3), dtype=np.float)+2)

    def test_min_stack(self):
        stack = Stack('min', 2)
        self.assertEqual(stack.mode, 'min')
        self.assertEqual(stack.num, 2)
        self.assertEqual(stack._num, 0)

        stack._update_stack(self.img1)
        correct_result = np.zeros((3, 3, 3), dtype=np.uint8)
        self.assertItemsEqual(stack.stack.img, correct_result)

        stack._update_stack(self.img2)
        self.assertItemsEqual(stack.calculate().img, correct_result)

    def test_max_stack(self):
        stack = Stack('max', 2)
        self.assertEqual(stack.mode, 'max')
        self.assertEqual(stack.num, 2)
        self.assertEqual(stack._num, 0)

        stack._update_stack(self.img1)
        correct_result = np.zeros((3, 3, 3), dtype=np.uint8)
        self.assertItemsEqual(stack.calculate().img, correct_result)

        stack._update_stack(self.img2)
        correct_result = np.zeros((3, 3, 3), dtype=np.uint8)+1
        self.assertItemsEqual(stack.stack.img, correct_result)

    def test_mean_stack(self):
        stack = Stack('mean', 3)
        self.assertEqual(stack.mode, 'mean')
        self.assertEqual(stack.num, 3)
        self.assertEqual(stack._num, 0)
        stack._update_stack(self.img1)
        self.assertEqual(stack._num, 1)
        stack._update_stack(self.img2)
        self.assertEqual(stack._num, 2)
        stack._update_stack(self.img3)
        self.assertEqual(stack._num, 3)
        self.assertItemsEqual(stack.stack.img, 3*np.ones((3, 3, 3),
                                                         dtype=np.float))
        stack.stack.img[1, 1, 1] = 13
        stack.stack.img[2, 2, 1] = 23
        stack.stack._scale(16)
        result = stack.stack.img
        self.assertTrue(result.min() == 0)
        self.assertTrue(result[1, 1, 1] == 32767)
        self.assertTrue(result.max() == 65535)

    def test_median_stack(self):
        stack = Stack('median', 3)
        self.assertEqual(stack.mode, 'median')
        self.assertEqual(stack.num, 3)
        self.assertEqual(stack._num, 0)
        stack._update_stack(self.img1)
        self.assertEqual(stack._num, 1)
        stack._update_stack(self.img2)
        self.assertEqual(stack._num, 2)
        stack._update_stack(self.img3)
        self.assertEqual(stack._num, 3)
        self.assertItemsEqual(stack.calculate().img, np.ones((3, 3, 3),
                                                             dtype=np.uint8))
        result = stack.calculate().img
        self.assertItemsEqual(result, np.ones((3, 3, 3), dtype=np.uint16))

    def assertItemsEqual(self, a, b):
        if isinstance(a, np.ndarray):
            self.assertTrue(np.all(a == b))
            self.assertTrue(a.shape == b.shape)
        else:
            for i in range(len(a)):
                self.assertEqual(a[i], b[i])
            self.assertEqual(len(a), len(b))

def suite():
    """The suite for test_stack
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestStack))
