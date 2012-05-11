import subprocess
import sys
import ConfigParser
from cirrus_cmdb import CirrusCmdb

__author__ = 'jakub.zygmunt'

class Struct:
    """
    convert dictionary to object, thanks to StackOverflow
    """
    def __init__(self, **entries):
        self.__dict__.update(entries)

class DeploySplunk(object):
    def __init__(self, config=None, file=None, out=sys.stdout):
        self.out = out

        self.config = Struct(**config) if isinstance(config, dict) else config
        if file:
            self.readConfigFile(file)

        self.is_connected = False

        if self.config:
            self.cmdb = CirrusCmdb(base_api_url=self.config.base_url, user=self.config.user, password=self.config.password)
            self.is_connected = self.cmdb.can_connect()

    def log(self, msg):
        self.out.write(msg)

    def testOutput(self, msg):
        self.log(msg)

    def readConfigFile(self, file):
        parser=ConfigParser.SafeConfigParser()
        parser.read(file)
        if 'cmdb' in parser.sections():
            self.config = Struct(**{f:parser.get('cmdb',f) for f in ('base_url', 'user', 'password')})
        else:
            self.log('Invalid config file {0}'.format(file))

    def deploy(self, clientName):
        if self.config:
            if self.is_connected:
                pass
            else:
                self.log('Cannot connect to cmdb.')
        else:
            self.log('No config found')
