import unittest

#from halostack import foo

class TestParser(unittest.TestCase):
    
    def setUp(self):
        pass

def suite():
    """The suite for test_parser
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestParser))
