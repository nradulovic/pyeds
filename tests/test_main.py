'''
Created on Jul 7, 2017

@author: nenad
'''
import unittest
import pyeds


class GenericTestCase(unittest.TestCase):
    def test_get_version(self):
        self.assertIsInstance(
            pyeds.__version__, 
            str,
            'Version string is not available')


if __name__ == '__main__':
    unittest.main()

