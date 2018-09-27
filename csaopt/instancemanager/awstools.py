import boto3
import logging

from string import Template
from pyhocon import ConfigTree
from botocore.exceptions import ClientError
from typing import List, Any, Tuple, Dict

from . import Instance
from .instancemanager import InstanceManager
from ..utils import get_own_ip, random_str, random_int

log = logging.getLogger()


def _interpolate_userscript_template_vals(script: bytes, **kwargs: str) -> bytes:
    return Template(script.decode('utf-8')).substitute(kwargs).encode()


class AWSTools(InstanceManager):
    """The AWSTools class provides an abstraction over boto3 and EC2 for the use with CSAOpt

    This is a context manager and creates required instances on `__enter__()`, disposing of the managed instances in
    `__exit__()`. These two methods as well as :meth:`instancemanager.awstools.AWSTools.get_running_instances` are the
    only methods called by the Runner (i.e. the only public methods).

    This class will use boto3 to (1) create a security group, (2) configure ingress from either the current IP address
    range, or the whole internet to the broker backend (currently Redis, as used by Dramatiq). It then (3) creates
    as many worker instances as requested and runs 'user-data' scripts after startup, which is to say, some bash
    scripts that set up and the required software (Redis, CSAOpt Worker, etc.). After the run AWSTools (4) terminates
    all managed instances and removes the security group.

    Note:
        If the AWS credentials are not provided in the config file, boto3 will look into
        the following environment variables: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`

    How to create IAM credentials (i.e. AWS keys):
        * Create (or reuse) IAM user with programmatic access
        * Assign to a (potentially new) group with AmazonEC2FullAccess
        * Store the access key and secret key

    Args:
        config: Configuration for current optimization run
        internal_conf: Internal CSAOpt configuration
    """

    def __init__(self, config: ConfigTree, internal_conf: ConfigTree) -> None:
        self.region = config.get('remote.aws.region', internal_conf['remote.aws.default_region'])

        if config.get('remote.aws.secret_key', False) and config.get('remote.aws.access_key', False):
            self.ec2_resource: boto3.session.Session.resource = boto3.resource(
                'ec2',
                aws_access_key_id=config['remote.aws.access_key'],
                aws_secret_access_key=config['remote.aws.secret_key'],
                region_name=self.region)

        else:
            # This will look for the env variables
            self.ec2_resource: boto3.session.Session.resource = boto3.resource('ec2', region_name=self.region)

        self.ec2_client = self.ec2_resource.meta.client

        # ec2.Instance is of <class 'boto3.resources.factory.ec2.Instance'> but this cannot be
        # used as a type hint here because it is generated by the factory at runtime, I assume.
        self.workers: List[Any] = []
        self.broker: Any = None
        self.security_group_prefix: str = internal_conf.get('remote.aws.security_group_prefix', 'csaopt_')
        self.security_group_id: str = ''

        self.worker_count: int = config['remote.aws.worker_count']

        worker_ami_key = 'remote.aws.worker_ami'
        broker_ami_key = 'remote.aws.broker_ami'

        self.broker_ami = config.get(broker_ami_key, internal_conf[broker_ami_key])
        self.worker_ami = config.get(worker_ami_key, internal_conf[worker_ami_key])

        self.timeout_provision = config.get('remote.aws.timeout_provision',
                                            internal_conf['remote.aws.timeout_provision'])
        self.timeout_startup = config.get('remote.aws.timeout_startup', internal_conf['remote.aws.timeout_startup'])

        self.broker_port = internal_conf.get('broker.defaults.remote_port')
        self.broker_password = random_str(32)

        self.debug_on_cpu = config.get('debug.gpu_simulator', '')

        self.provision_args: Dict[str, str] = {
            'broker_image':
            config.get('remote.broker_image', internal_conf['remote.broker_image']),
            'worker_image':
            config.get('remote.worker_image', internal_conf['remote.worker_image']),
            'broker_instance_type':
            config.get('remote.aws.broker_instance_type', internal_conf['remote.aws.broker_instance_type']),
            'worker_instance_type':
            config.get('remote.aws.worker_instance_type', internal_conf['remote.aws.worker_instance_type'])
        }

        data_base = internal_conf['remote.aws.userdata_rel_path']
        with open(data_base + '-broker.sh', 'rb') as broker_data, open(data_base + '-worker.sh', 'rb') as worker_data:
            self.user_data_scripts: Dict[str, bytes] = {'broker': broker_data.read(), 'worker': worker_data.read()}

    def _provision_instances(self, timeout_ms: int, count: int = 2, **kwargs: str) -> Tuple[Any, Any]:
        """Start and configure instances

        Args:
            timeout_ms: General timeout for the provisioning of requested instances
            count: number of worker instances to be created
            kwargs: Any other parameters that are required for startup
        """

        broker_userdata = _interpolate_userscript_template_vals(
            self.user_data_scripts['broker'], external_port=self.broker_port, redis_password=self.broker_password)

        broker = self.ec2_resource.create_instances(
            ImageId=kwargs['broker_image'],
            MinCount=1,
            MaxCount=1,
            UserData=broker_userdata,
            SecurityGroupIds=[self.security_group_id],
            InstanceType=kwargs['broker_instance_type'])[0]

        # TODO: get internal hostname or IP from broker
        worker_userdata = _interpolate_userscript_template_vals(
            self.user_data_scripts['worker'],
            debug='1' if self.debug_on_cpu else 'off',
            redis_host=broker.private_ip_address,
            redis_port=self.broker_port,
            redis_password=self.broker_password)

        workers = self.ec2_resource.create_instances(
            ImageId=kwargs['worker_image'],
            MinCount=count,
            MaxCount=count,
            InstanceType=kwargs['worker_instance_type'],
            UserData=worker_userdata,
            SecurityGroupIds=[self.security_group_id])

        return broker, workers

    def __map_ec2_instance(self, instance: Any, is_broker: bool = False, **kwargs: Any) -> Instance:
        """Maps a boto/EC2 instance to the internal Instance type

        Args:
            instance: Instance object returned by boto3 (which has a runtime type and therefore untyped here)
            is_broker: Flag indicating whether a given instance is a broker or not
            kwargs: Any other parameters that should be available on the produced object

        Returns:
            An abstract instance object
        """
        return Instance(instance.id, instance.public_ip_address, is_broker=is_broker, **kwargs)

    def get_running_instances(self) -> Tuple[Instance, List[Instance]]:
        """Get currently managed instances
        
        Returns:
            A tuple of broker, [worker]
        """
        return self.__map_ec2_instance(
            instance=self.broker, is_broker=True, port=self.broker_port,
            password=self.broker_password), [self.__map_ec2_instance(w) for w in self.workers]

    def _terminate_instances(self, timeout_ms: int) -> None:
        """Terminate all instances managed by AWSTools

        Args:
            timeout_ms: Timeout, in milliseconds, for the termination
        """
        instance_ids = [self.broker.id] + \
            [instance.id for instance in self.workers]
        self.ec2_client.terminate_instances(InstanceIds=instance_ids)

    def _wait_for_instances(self) -> None:
        """Block until broker and workers are up"""
        self.broker.wait_until_running()

        for instance in self.workers:
            instance.wait_until_running()

    def _run_start_scripts(self, timeout_ms: int) -> None:
        """Run any required setup procedures after the initial startup of managed instances

        Args:
            timeout_ms: Timeout, in milliseconds, for the termination
        """
        raise NotImplementedError

    def __enter__(self) -> InstanceManager:
        """On enter, AWSTools prepares the AWS security group and spins up the required intances

        """
        self.security_group_id = self._create_sec_group(self.security_group_prefix + random_str(10))

        self.broker, self.workers = self._provision_instances(
            count=self.worker_count, timeout_ms=self.timeout_provision, **self.provision_args)

        self._wait_for_instances()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """On exit, AWSTools terminates the started instances and removes security groups"""
        self._terminate_instances(self.timeout_provision)
        for instance in self.workers:
            instance.wait_until_terminated()
        self.broker.wait_until_terminated()
        self._remove_sec_group(self.security_group_id)
        return False

    def _remove_sec_group(self, group_id: str) -> None:
        """Removes the security group created by CSAOpt

        Args:
            group_id: Security group Id of group to be deleted
        """

        if group_id is not None:
            try:
                self.ec2_client.delete_security_group(GroupId=group_id)
                log.debug('Security group [{}] deleted'.format(group_id))
            except ClientError as e:
                log.error('Could not remove security group: {}'.format(e))
        else:
            log.warn('Cannot remove security group, because none was created. Skipping...')

    def _create_sec_group(self, name: str) -> str:
        """Creates an AWS security group and assigns ingress permissions from the current network

        Args:
            name: Name of the security group

        Returns:
            AWS Identifier `GroupId` of the created security group
        """
        try:
            response = self.ec2_client.create_security_group(GroupName=name, Description='Security Group for CSAOpt')

            security_group_id = response['GroupId']

            data = self.ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[{
                    'IpProtocol': 'tcp',
                    'FromPort': self.broker_port,
                    'ToPort': self.broker_port,
                    'IpRanges': [{
                        'CidrIp': '0.0.0.0/0'
                    }]
                }])

            log.debug('Authorized Security Group Ingress with result: {}'.format(data))

            return security_group_id
        except ClientError as e:
            log.exception('Could not create Security Group')
            raise
