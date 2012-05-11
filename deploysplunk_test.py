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

    def getOutput(self):
        return self.out.getvalue().strip()

    def testRedirectOutput(self):
        expectedString = 'This is a logging test'
        ds = DeploySplunk(out=self.out)
        ds.testOutput(expectedString)
        output = self.getOutput()
        self.assertEquals(expectedString, output)

    def testEmptyConstructor(self):
        expectedString = 'No config found'
        ds = DeploySplunk(out=self.out)
        ds.deploy('client')
        output = self.getOutput()
        self.assertEquals(expectedString, output)

    def testConstructorInvalidConfig(self):
        expectedString = 'Cannot connect to CMDB'
        config = {  'base_url': 'http://127.0.0.1',
                    'user': 'a',
                    'password': 'b',
        }

        ds = DeploySplunk(config=config, out=self.out)
        self.assertFalse(ds.is_connected)
    def testConstructorInvalidFileConfigNoCMDBSection(self):
            configFile = 'credentials/.invalid_cmdb1'
            expectedString = 'Invalid config file {0}'.format(configFile)
            ds = DeploySplunk(file=configFile, out=self.out)
            output = self.getOutput()
            self.assertEquals(expectedString, output)
            self.assertFalse(ds.is_connected)

    def testConstructorInvalidFileConfigInvalidCredentials(self):
        expectedString = 'Cannot connect to cmdb.'
        ds = DeploySplunk(file='credentials/.invalid_cmdb', out=self.out)
        ds.deploy('client');
        output = self.getOutput()
        self.assertEquals(expectedString, output)

    def testConstructorValidFileConfig(self):
        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        self.assertTrue(ds.is_connected)


