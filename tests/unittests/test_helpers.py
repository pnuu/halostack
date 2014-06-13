import unittest
import os
from halostack.helpers import get_filenames

class TestParser(unittest.TestCase):
    
    def setUp(self):
        self.fnames = ['tests/data/1.jpg', 'tests/data/2.jpg']
        self.fnames2 = [os.path.join('tests', 'data', '*.jpg')]
        self.fnames3 = ['tests/data/1.jpg', 'tests/data/a*.jpg']

    def test_get_filenames(self):
        result = get_filenames(self.fnames)
        result.sort()
        self.assertItemsEqual(result, self.fnames)
        self.assertEqual(len(result), len(self.fnames))

        result = get_filenames(self.fnames2)
        result.sort()
        correct_result = [os.path.join('tests', 'data', img) for \
                          img in ['1.jpg', '2.jpg', '3.jpg',
                                  'a1.jpg', 'a2.jpg']]
        correct_result.sort()
        self.assertItemsEqual(result, correct_result)
        self.assertEqual(len(result), len(correct_result))

        result = get_filenames(self.fnames3)
        result.sort()
        correct_result = [os.path.join('tests', 'data', img) for \
                          img in ['1.jpg', 'a1.jpg', 'a2.jpg']]
        correct_result.sort()
        self.assertItemsEqual(result, correct_result)
        self.assertEqual(len(result), len(correct_result))


def suite():
    """The suite for test_parser
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestParser))
