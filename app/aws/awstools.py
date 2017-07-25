import boto3
import logging
import requests
import random
import string


logger = logging.getLogger()

def _get_own_ip():
     return requests.get('https://api.ipify.org/').text

def _get_random_string(length=8):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(lenth)])

class AWSTools():
    def __init__(self, config):
        if(config.get_string('aws_secret_key')):
            self.ec2 = boto.client()
        else:
            # This will look for the env variables
            self.ec2 = boto3.client('ec2')
        self.instances = []
        self.sec_group = None
        self.private_key_path = None

    def start_instances(self, count=2):
        instances = ec2.create_instances(
                ImageId='ami-1e299d7e',
                MinCount=1,
                MaxCount=1,
                InstanceType='t2.micro')

    def terminate_instances(self):
        for instance in self.instances:
            instance = ec2.Instance(instance.id)
            response = instance.terminate()
            print(response)

    def get_running_instances(self):
        return self.instances

    def _remove_key(self):
        pass

    def _remove_sec_group(self):
        
        # Delete security group
        try:
            response = ec2.delete_security_group(GroupId='SECURITY_GROUP_ID')
            print('Security Group Deleted')
        except ClientError as e:
            logger.error('could not remove security group: {}'.format(e))

    def _create_key_pair(self, name):
        ec2.create_key_pair(KeyName='KEY_PAIR_NAME')

    def _create_sec_group(self, name):
        own_ip = _get_own_ip()
        response = ec2.describe_vpcs()
        vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

        response = ec2.create_security_group(GroupName=name,
                                             Description='Security Group for CSAOpt',
                                             VpcId=vpc_id)


if __name__ == '__main__':
    print(_get_own_ip())