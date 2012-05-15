from StringIO import StringIO
import unittest
import ConfigParser
from deploysplunk import DeploySplunk
import logging

__author__ = 'jakub.zygmunt'

class DeploySplunkTest(unittest.TestCase):
    def setUp(self):
        """
        set up data used in the tests
        """
        self.out = StringIO()

        logging.basicConfig()

    def getOutput(self):
        return self.out.getvalue().strip()

    def loadConfigFile(self, file):
        parser=ConfigParser.SafeConfigParser()
        parser.read(file)
        return parser

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
        """
        valid config with credentials not published in git
        """
        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        self.assertTrue(ds.is_connected)

    def testGetAwsAccountsInvalidClient(self):
        expectedList = []
        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        client = "Invalid Client"
        accounts = ds.getAmazonAccounts(client)
        self.assertEqual(expectedList, accounts)

    def testGetAwsAccountsValidClient(self):
        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        parser = self.loadConfigFile('credentials/.confidential_data')
        client = parser.get('testclient', 'client')
        accounts = ds.getAmazonAccounts(client)
        self.assertTrue(len(accounts) > 0)


