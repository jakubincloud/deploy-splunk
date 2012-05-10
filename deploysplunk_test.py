from StringIO import StringIO
import unittest
from deploysplunk import DeploySplunk

__author__ = 'jakub.zygmunt'

class DeploySplunkTest(unittest.TestCase):
    def setUp(self):
        """
        set up data used in the tests
        """
        self.out = StringIO()

    def testRedirectOutput(self):
        expectedString = 'This is a logging test'
        ds = DeploySplunk(out=self.out)
        ds.testOutput(expectedString)
        output = self.out.getvalue().strip()
        self.assertTrue(expectedString, output)

    def testEmptyConstructor(self):
        expectedString = 'No config found'
        ds = DeploySplunk(out=self.out)
        ds.deploy('client')
        output = self.out.getvalue().strip()
        self.assertTrue(expectedString, output)


