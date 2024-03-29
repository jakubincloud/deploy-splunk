import subprocess
import os
import sys
import ConfigParser
import re
import fnmatch
from cirrus_cmdb import CirrusCmdb
from jinja2 import Template

__author__ = 'jakub.zygmunt'

class Struct:
    """
    convert dictionary to object, thanks to StackOverflow
    """

    def __init__(self, **entries):
        self.__dict__.update(entries)


class DeploySplunk(object):
    splunk_bin = '/opt/splunk/bin/splunk'

    def __init__(self, config=None, file=None, out=sys.stdout, user=None, password=None):
        self.out = out
        self.user = user
        self.password = password

        self.config = Struct(**config) if isinstance(config, dict) else config
        if file:
            self.readConfigFile(file)

        self.is_connected = False

        if self.config:
            self.cmdb = CirrusCmdb(base_api_url=self.config.base_url, user=self.config.user,
                password=self.config.password)
            self.is_connected = self.cmdb.can_connect()

    def log(self, msg):
        self.out.write(msg)

    def testOutput(self, msg):
        self.log(msg)

    def getClientAppName(self, client_name):
        return client_name.replace(' ','').lower()

    def __run(self, cmd):
        """
        returns generator of output lines given by cmd
        """

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while(True):
            retcode = p.poll()
            line = p.stdout.readline()
            yield line
            if(retcode is not None):
                break

    def __runCommand(self, cmd, return_list=False):
        """
        runs command and returns output as string
        """
        outputList = [x for x in self.__run(cmd)]
        output = outputList if return_list else ''.join(outputList)
        return output

    def readConfigFile(self, file):
        parser = ConfigParser.SafeConfigParser()
        parser.read(file)
        if 'cmdb' in parser.sections():
            self.config = Struct(**{f[0]: f[1] for f in parser.items('cmdb')})
        else:
            self.log('Invalid config file {0}'.format(file))

    def getAmazonAccounts(self, client=None):
        aws_accounts = []
        if self.is_connected:
            # get customer id
            aws_accounts = self.cmdb.get_all_aws_account_numbers(client)
        return aws_accounts

    def cloneAppFromGithub(self, folder, client_name):
        if folder is not None and os.path.exists(folder):
            if hasattr(self.config, 'github_url') and self.config.github_url is not '':
                newfolder = folder +client_name
                self.__runCommand(['git','clone', self.config.github_url, newfolder])

                if os.path.exists(newfolder):
                    pass
                else:
                    self.log('Cannot clone the repository')

            else:
                self.log('No Github URL defined')
        else:
            self.log('App directory not found')

    def parseTemplate(self, filename, data):
        fr=open(filename,'r')
        inputSource = fr.read()
        template = Template(inputSource).render(data)
        newfilename = re.sub('\.template$', '', filename)
        with open(newfilename, 'w') as fw:
            fw.write(template)

    def getTemplateFiles(self, folder):
        matches = []
        for root, dirnames, filenames in os.walk(folder):
            for filename in fnmatch.filter(filenames, '*.template'):
                matches.append(os.path.join(root, filename))
        return matches

    def convertAllTemplates(self, folder, data):
        templates = self.getTemplateFiles(folder)
        for file in templates:
            self.parseTemplate(file, data)
        self.updateGitIgnore(folder, templates)


    def updateGitIgnore(self, folder, templateFiles):
        files = [ re.sub('\.template$', '',f) for f in templateFiles ]
        with open('%s/.gitignore' % folder, 'a') as f:
           for filename in files:
               f.write('%s\n' % filename)

    def isUserRoleAlreadyDefined(self, conf_file, role):
        parser=ConfigParser.SafeConfigParser()
        parser.read(conf_file)
        return role in parser.sections()


    def addUserRole(self, conf_file, data):
        user_role = 'role_client-%s' % data['client']
        if not self.isUserRoleAlreadyDefined(conf_file, user_role):
            fr=open('templates/userrole.template','r')
            inputSource = fr.read()
            user_role_template = Template(inputSource).render(data)
            with open(conf_file, 'a') as fw :
                fw.write(user_role_template)

    def addUser(self, data):
        if self.user and self.password:
            failedString = 'Unauthorized\n'
            output = self.__runCommand([self.splunk_bin, 'list', 'user', '-auth', '%s:%s' % (self.user, self.password) ],
                return_list=True)
            if failedString in output:
                self.log("wrong username or password.")
        else:
            self.log("no authentication credentials found.")


    def deploy(self, clientName):
        if self.config:
            if self.is_connected:
                pass
            else:
                self.log('Cannot connect to cmdb.')
        else:
            self.log('No config found')
