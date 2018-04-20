import boto3
from botocore.exceptions import ClientError
import logging

from ..instancemanager.instancemanager import InstanceManager
from ..utils import get_own_ip

logger = logging.getLogger()


class AWSTools(InstanceManager):
    """The AWSTools class provides an abstraction over boto3 and EC2 for the use with CSAOpt

    It is intended to be used as a context manager, disposing of instances in it's __exit__()
    call.

    Create IAM credentials:
        * new IAM user with programmatic access
        * assign to a (potentially new) group with AmazonEC2FullAccess
        * write down and store the access key and secret key


    Boto3 will check these environment variables for credentials:

    Note:
        If the AWS credentials are not provided in the config file, boto3 will look into
        the following environment variables:
        * AWS_ACCESS_KEY_ID
        * AWS_SECRET_ACCESS_KEY

    """
    def __init__(self, config, internal_conf):
        if config['aws.secret_key'] and config['aws.access_key']:
            self.ec2 = boto3.client(
                aws_access_key_id=config['aws.access_key'],
                aws_secret_access_key=config['aws.secrey_key']
            )
        else:
            # This will look for the env variables
            self.ec2 = boto3.client('ec2')

        self.region
        self.instances = []
        self.sec_group = None
        self.private_key_path = None
        self.worker_count = config['aws.worker_count']
        self.separate_queue_instance = config['aws.separate_queue_instance']

    def _provision_instances(self, count=2, **kwargs):
        """Start and configure instances"""

        imageId = kwargs.get('imageId', default='ami-1e299d7e')
        instanceType = kwargs.get('instanceType', default='t2.micro')

        self.instances = self.ec2.create_instances(
                ImageId=imageId,
                MinCount=count,
                MaxCount=count,
                InstanceType=instanceType)

    def _get_running_instances(self):
        """Returns the currently managed instances"""

    def _terminate_instances(self):
        """Terminate all instances managed by AWSTools"""
        instance_ids = [instance.id for instance in self.instances]
        self.ec2.instances.filter(InstanceIds=instance_ids).stop()
        self.ec2.instances.filter(InstanceIds=instance_ids).terminate()

    def __enter__(self):
        """On enter, AWSTools prepares the AWS security group and spins up the required intances"""
        self._create_sec_group()
        self._provision_instances()

    def __exit__(self, exc_type, exc_value, traceback):
        """On exit, AWSTools terminates the started instances and removes security groups"""
        self._terminate_instances()

    def get_running_instances(self):
        return self.instances

    def _remove_sec_group(self):
        """Removes the security group created by CSAOpt"""

        if self.security_group_id is not None:
            try:
                self.ec2.delete_security_group(GroupId=self.security_group_id)
                logger.debug('Security Group Deleted')
            except ClientError as e:
                logger.error('Could not remove security group: {}'.format(e))
        else:
            logger.warn('Cannot remove security group, because none was created. Skipping')

    def _create_sec_group(self, name):
        self.own_external_ip = get_own_ip()
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
