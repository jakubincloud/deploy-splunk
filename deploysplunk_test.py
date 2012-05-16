from StringIO import StringIO
import os
import shutil
import unittest
import ConfigParser
import fnmatch
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
    def tearDown(self):
        shutil.rmtree('output')
        os.makedirs('output')
        self.cleanConfFiles()

    def getOutput(self):
        return self.out.getvalue().strip()

    def loadConfigFile(self, file):
        parser=ConfigParser.SafeConfigParser()
        parser.read(file)
        return parser

    def cleanConfFiles(self):
        matches = []
        for root, dirnames, filenames in os.walk('test_templates'):
            for filename in fnmatch.filter(filenames, '*.conf'):
                matches.append(os.path.join(root, filename))
        for file in matches:
            os.remove(file)

    def testShouldReturnValidClientAppName(self):
        client_name = 'New StrIng-client appName'
        expectedString = 'newstring-clientappname'
        ds = DeploySplunk(out=self.out)
        outputString = ds.getClientAppName(client_name)
        self.assertEquals(expectedString, outputString)

    def testShouldRedirectOutput(self):
        expectedString = 'This is a logging test'
        ds = DeploySplunk(out=self.out)
        ds.testOutput(expectedString)
        output = self.getOutput()
        self.assertEquals(expectedString, output)

    def testEmptyConstructorShouldReturnMessage(self):
        expectedString = 'No config found'
        ds = DeploySplunk(out=self.out)
        ds.deploy('client')
        output = self.getOutput()
        self.assertEquals(expectedString, output)

    def testShouldReturnMessageOnConstructorWithInvalidConfig(self):
        expectedString = 'Cannot connect to CMDB'
        config = {  'base_url': 'http://completelywrong.dns.name.to.be.sure.it.wont.work',
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

    def testShouldOutputMessageAppDirectoryNotFound(self):
        expectedString = 'App directory not found'
        config = {x[0]:x[1] for x in self.loadConfigFile('credentials/.valid_cmdb').items('cmdb') }
        ds = DeploySplunk(config=config, out=self.out)
        client_name = 'wigywigy'
        ds.cloneAppFromGithub('totally_invalid_folder', client_name)
        output = self.getOutput()
        self.assertEquals(expectedString, output)

    def testShouldOutputMessageOnEmptyGithubUrl(self):
        expectedString = 'No Github URL defined'
        config = {x[0]:x[1] for x in self.loadConfigFile('credentials/.valid_cmdb').items('cmdb') }
        config['github_url']=''
        ds = DeploySplunk(config=config, out=self.out)
        parser = self.loadConfigFile('credentials/.confidential_data')
        app_folder = parser.get('app', 'app_home')
        client_name = 'wigywigy'
        ds.cloneAppFromGithub(app_folder, client_name)
        output = self.getOutput()
        self.assertEquals(expectedString, output)

    def testShouldOutputMessageOnWrongGithubRepoUrl(self):
        expectedString = "Cannot clone the repository"
        config = {x[0]:x[1] for x in self.loadConfigFile('credentials/.valid_cmdb').items('cmdb') }
        config['github_url'] = 'http://there.is.no.repo.under.this.url/'
        ds = DeploySplunk(config=config, out=self.out)
        parser = self.loadConfigFile('credentials/.confidential_data')
        app_home = parser.get('app', 'app_home')
        client_name = 'wigywigy'
        ds.cloneAppFromGithub(app_home, client_name)
        output = self.getOutput()
        self.assertEquals(expectedString, output)

    def testShouldReportEmptyMessageOnValidGithubUrl(self):
        expectedString = ''
        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        parser = self.loadConfigFile('credentials/.confidential_data')
        app_home = parser.get('app', 'app_home')
        client_name = 'wigywigy'
        ds.cloneAppFromGithub(app_home, client_name)
        output = self.getOutput()
        self.assertEquals(expectedString, output)



    def testFileTemplateclientShouldReturnFile(self):
        templateFile = 'test_templates/local/savedsearches.conf.template'
        expectedFile = 'test_templates/local/savedsearches.conf'
        data = { 'client' : 'wigywigy' }
        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        ds.parseTemplate(templateFile, data )
        self.assertTrue(os.path.exists(expectedFile))


    def testFileTemplateClientShouldReturnModifiedText(self):
        expectedString =  '''[instanceReservationExpiryRecommendation]
alert.suppress = 0
alert.track = 1
cron_schedule = 0 0 * * *
search = index="wigywigy" test test | other text index-wigywigy'''
        templateFile = 'test_templates/local/savedsearches.conf.template'
        expectedFile = 'test_templates/local/savedsearches.conf'
        data = { 'client' : 'wigywigy' }
        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        ds.parseTemplate(templateFile, data )
        fr=open(expectedFile,'r')
        outputString = fr.read()
        self.assertEqual(expectedString, outputString)

    def testFileTemplateMultipleAccountsShouldReturnModifiedFile(self):
        expectedString =  '''[script://script 1111-2222-3333 arg]
disabled = false
index = wigywigy
interval = 0 * * * *
source = some_source
sourcetype = some_sourcetype

[script://script 2222-3333-4444 arg]
disabled = false
index = wigywigy
interval = 0 * * * *
source = some_source
sourcetype = some_sourcetype'''
        templateFile = 'test_templates/local/inputs.conf.template'
        expectedFile = 'test_templates/local/inputs.conf'
        data = { 'client' : 'wigywigy',
                'aws_accounts' : [ { 'number': '1111-2222-3333'} , { 'number': '2222-3333-4444'} ]
               }

        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)

        ds.parseTemplate(templateFile, data )
        fr=open(expectedFile,'r')
        outputString = fr.read().strip()
        self.assertEqual(expectedString, outputString)












