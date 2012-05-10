import subprocess
import sys
import cirrus_cmdb

__author__ = 'jakub.zygmunt'

class DeploySplunk(object):
    def __init__(self, config=None, out=sys.stdout):
        self.config = config
        self.out = out

    def log(self, msg):
        self.out.write(msg)

    def testOutput(self, msg):
        self.log(msg)

    def deploy(self, clientName):
        if self.config:
            pass
        else:
            self.log('No config found')
