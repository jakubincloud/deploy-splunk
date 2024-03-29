from StringIO import StringIO
import os
import shutil
import unittest
import ConfigParser
import fnmatch
import re
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
        self.prepareGitIgnoreFile()
        self.prepareAuthorizeConfFiles()

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

    def getFiles(self, folder, filter):
        matches = []
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, filter):
                matches.append(os.path.join(root, filename))
        return matches

    def cleanConfFiles(self):
        matches = self.getFiles(folder = 'test_files', filter='*.conf')
        for file in matches:
            os.remove(file)

    def prepareGitIgnoreFile(self):
        with open('test_files/.gitignore', 'w') as f:
            f.write("# this line shouldn't be removed\n")

    def prepareAuthorizeConfFiles(self):
        files = ['test_files/authorize.no-role.generator', 'test_files/authorize.with-role.generator']
        for file in files:
            newfile = re.sub('\.generator$', '.conf', file)
            shutil.copyfile(file, newfile)

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
        templateFile = 'test_files/local/savedsearches.conf.template'
        expectedFile = 'test_files/local/savedsearches.conf'
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
        templateFile = 'test_files/local/savedsearches.conf.template'
        expectedFile = 'test_files/local/savedsearches.conf'
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
        templateFile = 'test_files/local/inputs.conf.template'
        expectedFile = 'test_files/local/inputs.conf'
        data = { 'client' : 'wigywigy',
                'aws_accounts' : [ { 'number': '1111-2222-3333'} , { 'number': '2222-3333-4444'} ]
               }

        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)

        ds.parseTemplate(templateFile, data )
        fr=open(expectedFile,'r')
        outputString = fr.read().strip()
        self.assertEqual(expectedString, outputString)

    def testShouldReturnListOfTemplates(self):
        expectedList = [ 'test_files/local/inputs.conf.template',
                         'test_files/local/savedsearches.conf.template',
                         'test_files/metadata/local.meta.template']
        app_folder = 'test_files'

        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        outputList = ds.getTemplateFiles(app_folder)
        self.assertEquals(expectedList, outputList)

    def testShouldConvertAllTemplates(self):
        expectedList = [ 'test_files/local/inputs.conf',
                         'test_files/local/savedsearches.conf',
                         'test_files/metadata/local.meta' ]
        data = { 'client' : 'wigywigy',
                 'aws_accounts' : [ { 'number': '1111-2222-3333'} , { 'number': '2222-3333-4444'} ]
        }
        app_folder = 'test_files'

        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        ds.convertAllTemplates(app_folder, data)
        convertedFiles = self.getFiles(folder=app_folder, filter='*.*')
        for file in expectedList:
            self.assertTrue(file in convertedFiles, msg='Checking if file %s exists' % file)


    def testShouldAppendToGitIgnore(self):
        expectedString = "# this line shouldn't be removed\n"
        data = { 'client' : 'wigywigy',
                 'aws_accounts' : [ { 'number': '1111-2222-3333'} , { 'number': '2222-3333-4444'} ]
        }
        app_folder = 'test_files'

        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        ds.convertAllTemplates(app_folder, data)
        f = open('test_files/.gitignore')
        lines = [x for x in f.readlines()]
        self.assertTrue(expectedString in lines)

    def testShouldAppendToGitIgnoreListOfConvertedTemplates(self):
        expectedList = [ 'test_files/local/inputs.conf\n',
                         'test_files/local/savedsearches.conf\n',
                         'test_files/metadata/local.meta\n' ]
        data = { 'client' : 'wigywigy',
                 'aws_accounts' : [ { 'number': '1111-2222-3333'} , { 'number': '2222-3333-4444'} ]
        }
        app_folder = 'test_files'

        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        ds.convertAllTemplates(app_folder, data)
        f = open('test_files/.gitignore')
        lines = [x for x in f.readlines()]
        for file in expectedList:
            self.assertTrue(file in lines, msg='Checking if file %s is in .gitignore' % file)

    def testShouldAddUserRoletoFile(self):
        expectedKeyValuePairs = { 'rtSrchJobsQuota' : '20',
                                  'srchIndexesAllowed' : 'client-wigywigy client-wigywigy-si',
                                  'srchIndexesDefault' : 'client-wigywigy'
        }
        data = { 'client' : 'wigywigy' }
        app_folder = 'test_files'
        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        conf_file = '%s/authorize.no-role.conf' % app_folder
        ds.addUserRole(conf_file, data)
        parser = self.loadConfigFile(conf_file)
        sections = parser.sections()
        self.assertTrue('role_client-wigywigy' in sections)
        for k in expectedKeyValuePairs.keys():
            expectedValue = expectedKeyValuePairs[k]
            outputValue = parser.get('role_client-wigywigy', k)
            self.assertEqual(expectedValue, outputValue, msg='Checking parameter %s (exp:"%s", out:"%s")' % (k, expectedValue, outputValue))


    def testShouldntAddUserRoletoFile(self):
        notExpectedItem = 'srchindexesallowed'
        data = { 'client' : 'wigywigy' }
        app_folder = 'test_files'
        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        conf_file = '%s/authorize.with-role.conf' % app_folder
        ds.addUserRole(conf_file, data)
        parser = self.loadConfigFile(conf_file)
        sections = parser.sections()
        parameters = [ x[0] for x in parser.items('role_client-wigywigy') ]
        self.assertFalse( notExpectedItem in parameters)

    def testShouldOutputErrorNoauthentication(self):
        expectedString = 'no authentication credentials found.'
        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out)
        data = { 'client' : 'wigywigy' }
        ds.splunk_bin = 'test_files/test_splunk.sh'
        ds.addUser(data)
        output = self.getOutput()
        self.assertEqual(expectedString, output)

    def testShouldOutputErrorWrongPassword(self):
        expectedString = 'wrong username or password.'
        ds = DeploySplunk(file='credentials/.valid_cmdb', out=self.out, user='user', password='nopassword')
        data = { 'client' : 'wigywigy' }
        ds.splunk_bin = 'test_files/test_splunk.sh'
        ds.addUser(data)
        output = self.getOutput()
        self.assertEqual(expectedString, output)





