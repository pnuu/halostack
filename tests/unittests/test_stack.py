import unittest
import os
from halostack.image import Image
from halostack.stack import Stack
import numpy as np

class TestStack(unittest.TestCase):
    
    def setUp(self):
        self.mean = Stack('mean', 3)
        self.median = Stack('median', 3)

        self.img1 = Image(img=np.zeros((3, 3, 3), dtype=np.uint8))
        self.img2 = Image(img=np.zeros((3, 3, 3), dtype=np.uint8)+1)
        self.img3 = Image(img=np.zeros((3, 3, 3), dtype=np.uint8)+2)

    def test_update_stack_min(self):
        stack = Stack('min', 2)
        self.assertEqual(stack.mode, 'min')
        self.assertEqual(stack.num, 2)
        self.assertEqual(stack._num, 0)

        stack._update_stack(self.img1)
        correct_result = np.zeros((3, 3, 3), dtype=np.uint8)
        self.assertItemsEqual(stack.stack.img, correct_result)

        stack._update_stack(self.img2)
        self.assertItemsEqual(stack.stack.img, correct_result)

    def test_update_stack_max(self):
        stack = Stack('max', 2)
        self.assertEqual(stack.mode, 'max')
        self.assertEqual(stack.num, 2)
        self.assertEqual(stack._num, 0)

        stack._update_stack(self.img1)
        correct_result = np.zeros((3, 3, 3), dtype=np.uint8)
        self.assertItemsEqual(stack.stack.img, correct_result)

        stack._update_stack(self.img2)
        correct_result = np.zeros((3, 3, 3), dtype=np.uint8)+1
        self.assertItemsEqual(stack.stack.img, correct_result)

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
