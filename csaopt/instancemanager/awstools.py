import boto3
import logging

from multiprocessing import Process
from botocore.exceptions import ClientError
from typing import List, Dict, Any

from . import Instance
from ..instancemanager.instancemanager import InstanceManager
from ..utils import get_own_ip, random_str

logger = logging.getLogger()

AwsInstance = Dict[str, Any]

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

    

    def __init__(self, context, config, internal_conf) -> None:
        if config['cloud.aws.region'] is not None:
            self.region = config['cloud.aws.region'] 
        else:
            self.region = internal_conf['cloud.aws.region']
        
        if config['cloud.aws.secret_key'] and config['cloud.aws.access_key']:
            self.ec2_resource: boto3.session.Session.resource = boto3.resource('ec2',
                                                aws_access_key_id=config['cloud.aws.access_key'],
                                                aws_secret_access_key=config['cloud.aws.secret_key'],
                                                region_name=self.region)
            self.ec2_client = self.ec2_resource.meta.client

            
        else:
            # This will look for the env variables
            self.ec2_client: boto3.botocore.client.BaseClient = boto3.client('ec2', region=self.region)


        self.aws_instances: List[Dict[str, Any]] = []
        self.message_queue: AwsInstance = {}
        self.security_group_id: str = ''
        self.worker_count: int = config['cloud.aws.worker_count']
        self.default_message_queue_ami = internal_conf['cloud.aws.message_queue_ami']
        self.default_worker_ami = internal_conf['cloud.aws.worker_ami']
        self.console_printer = context.console_printer

    def __provision_instances_with_timeout(self, count, **kwargs) -> None:
        imageId = kwargs.get('imageId', default=self.default_message_queue_ami)
        instanceType = 'm4.large'  # TODO pull from config
        self.message_queue = self.ec2_client.create_instances(ImageId=imageId,
                                                              MinCount=1,
                                                              MaxCount=1,
                                                              InstanceType=instanceType)

        # Workers
        imageId = kwargs.get('imageId', default=self.default_worker_ami)
        # TODO pull from config
        instanceType = kwargs.get('instanceType', default='t2.micro')

        self.instances = self.ec2_client.create_instances(
            ImageId=imageId,
            MinCount=count,
            MaxCount=count,
            InstanceType=instanceType,
            SecurityGroupIds=[self.security_group_id])

    def _provision_instances(self, timeout_ms, count=2, **kwargs) -> List[str]:
        """Start and configure instances"""

        # MessageQueue
        pass
        

    def _get_running_instances(self) -> List[Instance]:
        """Returns the currently managed instances"""
        # TODO: implement

    def _terminate_instances(self, timeout_ms) -> None:
        """Terminate all instances managed by AWSTools"""
        instance_ids = [instance.id for instance in self.instances]
        self.ec2_client.instances.filter(InstanceIds=instance_ids).terminate()

    def __enter__(self) -> None:
        """On enter, AWSTools prepares the AWS security group and spins up the required intances"""
        self._create_sec_group('csaopt_' + random_str(10))

        # TODO: put all required parameters into kwarg
        self._provision_instances(count=self.worker_count)
        self._wait_for_instances()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """On exit, AWSTools terminates the started instances and removes security groups"""
        self._terminate_instances()
        self._remove_sec_group()
    
    def _remove_sec_group(self, group_id: str) -> None:
        """Removes the security group created by CSAOpt"""

        if group_id is not None:
            try:
                self.ec2.delete_security_group(GroupId=self.security_group_id)
                logger.debug('Security group [{}] deleted'.format(group_id))
            except ClientError as e:
                logger.error('Could not remove security group: {}'.format(e))
        else:
            logger.warn('Cannot remove security group, because none was created. Skipping...')

    def _create_sec_group(self, name: str) -> str:
        self.own_external_ip = get_own_ip()
        response = self.ec2_client.describe_vpcs()
        vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

        try:
            response = self.ec2_client.create_security_group(
                GroupName=name,
                Description='Security Group for CSAOpt',
                VpcId=vpc_id)

            security_group_id = response['GroupId']

            data = self.ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
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
            
            return security_group_id
        except ClientError as e:
            logger.error('Could not create Security Group: {}', e)
            return None
