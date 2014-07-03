import unittest
import os
from halostack.helpers import get_filenames, parse_enhancements

class TestHelpers(unittest.TestCase):
    
    def setUp(self):
        self.fnames = ['tests/data/1.jpg', 'tests/data/2.jpg']
        self.fnames2 = [os.path.join('tests', 'data', '*.jpg')]
        self.fnames3 = ['tests/data/1.jpg', 'tests/data/a*.jpg']
        self.enh1 = ['br', 'gradient']
        self.enh2 = ['usm:25,5', 'gradient']

    def test_get_filenames(self):
        result = get_filenames(self.fnames)
        result.sort()
        self.assertItemsEqual(result, self.fnames)

        result = get_filenames(self.fnames2)
        result.sort()
        correct_result = [os.path.join('tests', 'data', img) for \
                          img in ['1.jpg', '2.jpg', '3.jpg',
                                  'a1.jpg', 'a2.jpg']]
        correct_result.sort()
        self.assertItemsEqual(result, correct_result)

        result = get_filenames(self.fnames3)
        result.sort()
        correct_result = [os.path.join('tests', 'data', img) for \
                          img in ['1.jpg', 'a1.jpg', 'a2.jpg']]
        correct_result.sort()
        self.assertItemsEqual(result, correct_result)

    def test_parse_enhancements(self):
        result = parse_enhancements(self.enh1)
        self.assertDictEqual(result, {'br': None, 'gradient': None})
        result = parse_enhancements(self.enh2)
        self.assertDictEqual(result, {'usm': [25., 5.], 'gradient': None})

    def assertItemsEqual(self, a, b):
        for i in range(len(a)):
            if isinstance(a[i], dict):
                self.assertDictEqual(a[i], b[i])
            else:
                self.assertEqual(a[i], b[i])
        self.assertEqual(len(a), len(b))

    def assertDictEqual(self, a, b):
        for key in a:
            self.assertTrue(key in b)
            self.assertEqual(a[key], b[key])

        self.assertEqual(len(a), len(b))


def suite():
    """The suite for test_helpers
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestHelpers))
