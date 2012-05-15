
import logging
import socket
import sys
import httplib2
import json
import urllib
from time import sleep

__author__ = 'richard'

class Http500Exception(Exception):
    def __init__(self, value=None):
        self.parameter = value

    def __str__(self):
        return repr(self.parameter)

class CirrusCmdb(object):

    def __init__(self, base_api_url, user, password, ignore_ssl=False):
        self._base_api_url = base_api_url

        self._http = httplib2.Http(disable_ssl_certificate_validation=ignore_ssl, timeout=5)
        self._http.add_credentials(user, password)

        self._logger = logging.getLogger('AuditEc2')

    def _throttle(self, delay, name):
        self._logger.warning('%s throttling - sleeping for %s seconds' % (name, str(delay)))
        sleep(delay)

    def __prep_url(self, url, page):
        if page is not 1:
            return url + '&page=%s' % str(page)
        else:
            return url

    def __process_content(self, content):
        try:
            if content != '[]':
                tmp = json.loads(content)
            else:
                tmp = None

        except ValueError, err:
            self._logger.warning('cmdb result error url=%s' % content)
            self._logger.warning(err)
            return False
        else:
            return tmp

    def __run_query(self, query_url):
        j_results = []

        delay = 0
        delay_increment = 5


        page_loop = True

        page = 1

        while page_loop:

            working_url = self.__prep_url(query_url, page)
            retry_count = 0
            timeout_loop = True
            while timeout_loop:
                try:
                    response, content = self._http.request(working_url)

                    if response.status == 500:
                        raise Http500Exception

                except socket.timeout:
                    delay += delay_increment
                    self._throttle(delay, 'cmdb socket timeout')
                except Http500Exception:
                    delay += delay_increment
                    self._throttle(delay, 'cmdb http 500')
                else:

                    res = self.__process_content(content)

                    if res is not False:
                        timeout_loop = False
                        if res is not None:
                            j_results += res
                            self._logger.info('cmdb - results found')
                            if len(res) > 1:
                                page += 1
                                timeout_loop = False
                            else:
                                page_loop = False
                        else:
                            if j_results is not None and len(j_results) == 0:
                                self._logger.info('cmdb - no results found return None %s' % query_url)
                                j_results = None
                            else:
                                #we get here if we have come to the end of a multi page loop
                                page_loop = False

                    elif retry_count == 5:
                        timeout_loop = False
                    else:
                        retry_count += 1

        return j_results

    def __get_aws_account_id(self, aws_account_number):
        j_results = self.get_aws_account_details(aws_account_number)

        if j_results is not None:
            return j_results[0]['id']
        else:
            return None

    def get_instance_all_by_aws_account_number(self, aws_account_number):
        cmdb_account_id = self.__get_aws_account_id(aws_account_number)
        query_url = self._base_api_url + '/aws_instances.json?q[aws_account_id_equals]=%s' % cmdb_account_id

        content = self.__run_query(query_url)

        if content is not None:
            return content
        else:
            return None


    def get_aws_account_details(self, aws_account_number):
        query_url = self._base_api_url + '/aws_accounts.json?q[number_equals]=%s' % aws_account_number
        #response, content = self._http.request(query_url)
        content = self.__run_query(query_url)

        if content is not None:
            return content
        else:
            self._logger.critical('aws account details not found: %s' % aws_account_number)
            return None


    def get_aws_keys(self, aws_account_number):

        j_results = self.get_aws_account_details(aws_account_number)

        if j_results is not None:
            return j_results[0]['access_key_id'], j_results[0]['secret_key']
        else:
            return None, None

    def get_instance_by_id(self, instance_id):
        query_url = self._base_api_url + '/aws_instances.json?q[instance_id_equals]=%s' % instance_id
        #response, content = self._http.request(query_url)
        content = self.__run_query(query_url)

        if content is not None:
            return content
        else:
            return None


    def get_instance_reviewed_dates(self, instance_id):
        results = self.get_instance_by_id(instance_id)

        if results is not None:
            return results[0]['reviewed_at'], results[0]['reviewed_sizing_at']
        else:
            return None, None

#TODO currently not used, can be used to be more generic, run out of time to use this, also needs to be re written using self.__run_query
#    def get_instance_field_equals(self, instance_id, field_name):
#        query_url = self._base_api_url + '/aws_instances.json?q[%s_equals]=%s' % (field_name ,instance_id)
#
#        response, content = self._http.request(query_url)
#
#        try:
#            j_results = json.loads(content)
#        except ValueError:
#            self._logger.warning('cmdb err - instance - %s - field - %s' % (instance_id, field_name))
#            j_results = []
#
#        if len(j_results) is not 0:
#            return j_results[0][field_name]
#        else:
#            return None


    def get_volume_reviewed_at(self, volume_id):
        query_url = self._base_api_url + '/aws_volumes.json?q[volume_id_equals]=%s' % volume_id

        content = self.__run_query(query_url)

        if content is not None:
            return content[0]['reviewed_at']
        else:
            return None

    def get_snapshot_reviewed_at(self, snapshot_id):
        query_url = self._base_api_url + '/aws_snapshots.json?q[snapshot_id_equals]=%s' % snapshot_id

        j_results = self.__run_query(query_url)

        if j_results is not None:
            return j_results[0]['reviewed_at']
        else:
            return j_results


    def get_security_group_reviewed_at(self, security_group_id):
        query_url = self._base_api_url + '/aws_security_groups.json?q[aws_security_group_id_equals]=%s' % security_group_id

        content = self.__run_query(query_url)

        if content is not None:
            return content[0]['reviewed_at']
        else:
            return None

    def get_all_security_groups_by_aws_account_number(self, aws_account_number):
        cmdb_account_id = self.__get_aws_account_id(aws_account_number)
        query_url = self._base_api_url + '/aws_security_groups.json?q[aws_account_id_equals]=%s' % cmdb_account_id

        content = self.__run_query(query_url)

        return content


    def get_all_security_group_rules_by_aws_account_number(self, aws_account_number):
        security_groups = self.get_all_security_groups_by_aws_account_number(aws_account_number)

        rules = []

        for sg in security_groups:
            rules_query = self._base_api_url + '/aws_security_group_rules.json?q[security_group_id_equals]=%s&q[ip_range_contains]=0.0.0.0' % sg['id']

            sg_rules = self.__run_query(rules_query)

            if sg_rules is not None:
                #add data from security group to each rule, as the out put for SG's have this data formatted like this
                #for output to splunk's event based
                for a in sg_rules:
                    a['description'] = sg['description']
                    a['region'] = sg['region']
                    a['name'] = sg['name']

                rules.extend(sg_rules)

        if rules is not None:
            return rules
        else:
            return None

    def get_customer_details(self, customer_name):
        params_url = urllib.urlencode({'q[name_equals]':customer_name})
        query_url = self._base_api_url + '/customers.json?%s' % params_url
        content = self.__run_query(query_url)

        if content is not None and len(content) > 0:
            return content[0]
        else:
            self._logger.critical('customer details not found: %s' % customer_name)
            return None

    def get_all_aws_account_numbers(self, customer_name):
        content = []
        customer = self.get_customer_details(customer_name)
        if customer is not None:
            query_url = self._base_api_url + '/aws_accounts.json?q[customer_id_equals]=%s' % customer['id']

            content = self.__run_query(query_url)
        return content

    def can_connect(self):
        try:
            c = self._http.request(self._base_api_url)
            return True
        except socket.timeout:
            return False
        except socket.error:
            return False
        except httplib2.ServerNotFoundError:
            return False