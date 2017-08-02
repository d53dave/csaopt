import boto3
import logging
import requests
import random
import string
from botocore.exceptions import ClientError

logger = logging.getLogger()


def _get_own_ip():
    return requests.get('https://api.ipify.org/').text


def _get_random_string(length=8):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(lenth)])


class AWSTools():
    def __init__(self, config, internal_conf):
        if config['aws.secret_key'] is not None and config['aws.access_key'] is not None:
            self.ec2 = boto3.client(
                aws_access_key_id=config['aws.access_key'],
                aws_secret_access_key=config['aws.secrey_key']
            )
        else:
            # This will look for the env variables
            self.ec2 = boto3.client('ec2')
        self.instances = []
        self.sec_group = None
        self.private_key_path = None

    def _start_instances(self, count=2):
        self.instances = self.ec2.create_instances(
                ImageId='ami-1e299d7e',
                MinCount=count,
                MaxCount=count,
                InstanceType='t2.micro')

    def _terminate_instances(self):
        for instance in self.instances:
            instance = self.ec2.Instance(instance.id)
            response = instance.terminate()
            print(response)

    def get_running_instances(self):
        return self.instances

    def _create_key_pair(self, key_name):
        key = ec2.create_key_pair(KeyName=key_name)
        return key

    def _save_key_material(self, key):
        pass

    def _remove_key(self):
        pass

    def _remove_sec_group(self):
        """Removes the security group created by CSAOpt"""

        if self.security_group_id is not None:
            try:
                self.ec2.delete_security_group(GroupId=self.security_group_id)
                print('Security Group Deleted')
            except ClientError as e:
                logger.error('Could not remove security group: {}'.format(e))
        else:
            logger.warn('Cannot remove security group, because none was created. Skipping')

    def _create_key_pair(self, name):
        self.ec2.create_key_pair(KeyName='KEY_PAIR_NAME')

    def _create_sec_group(self, name):
        self.own_external_ip = _get_own_ip()
        response = self.ec2.describe_vpcs()
        vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

        try:
            response = self.ec2.create_security_group(
                GroupName=name,
                Description='Security Group for CSAOpt',
                VpcId=vpc_id)

            self.security_group_id = response['GroupId']

            data = self.ec2.authorize_security_group_ingress(
                GroupId=self.security_group_id,
                IpPermissions=[  # TODO: 80 and 22 are not needed here. Rather, these should be the zmq ports
                    {'IpProtocol': 'tcp',
                     'FromPort': 80,
                     'ToPort': 80,
                     'IpRanges': [{'CidrIp': '{}/0'.format(self.own_external_ip)}]},
                    {'IpProtocol': 'tcp',
                     'FromPort': 22,
                     'ToPort': 22,
                     'IpRanges': [{'CidrIp': '{}/0'.format(self.own_external_ip)}]}
                ])
            logger.debug('Authorized Security Group Ingress for CidrIp {} with result: {}'.format(
                self.own_external_ip,
                data
                ))
        except ClientError as e:
            logger.error('Could not create Security Group: {}', e)
