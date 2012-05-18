'''
A very dummy imitation of /opt/splunk/bin/splunk
nouser:nouser - should return list without user wigywigy
user:nopassword - invalid password
user:user - valid password user exists
'''

__author__ = 'jakub.zygmunt'
import sys

class SplunkDummy(object):

    def nouser_nouser(self):
        self.display_users(['user'])

    def user_user(self):
        self.display_users(['user', 'wigywigy'])

    def user_nopassword(self):
        print '''Login failed
Login failed
Unauthorized'''

    def display_users(self, user_list):
        output = []
        for username in user_list:
            output.append("username:\t{0}\nfull-name:\t{0}\nrole:\t{0}\n".format(username))
        print '\n'.join(output)

args = sys.argv[1:]

if args[0] == 'list':
    function_name = args[3].replace(':', '_')
    splunk = SplunkDummy()
    if (function_name in dir(splunk)):
        methodToCall = getattr(splunk, function_name)
        methodToCall()
    else :
        print "Function not found. (%s)" % function_name

