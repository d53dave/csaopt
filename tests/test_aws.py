import pytest
import responses

from moto import mock_ec2
from context import AWSTools, AppContext, ConsolePrinter


@pytest.fixture
def internal_conf():
    return {
        'cloud.aws.message_queue_ami': 'queue_ami_1234',
        'cloud.aws.worker_ami': 'worker_ami_1234'
    }

@pytest.fixture
def conf():
    return {
        'cloud.aws.region': 'eu-central-1',
        'cloud.aws.secret_key': '123456',
        'cloud.aws.access_key': '123456',
        'cloud.aws.worker_count': 2,
        'cloud.aws.timeout': 500
        }

@pytest.fixture
def context(conf, internal_conf):
    return AppContext(ConsolePrinter(), conf, internal_conf)

@pytest.fixture
def awstools(context):
    return AWSTools(context, context.config, context.internal_config)

def test_create_security_group(awstools):
    with mock_ec2():
        responses.add(responses.GET, 'https://api.ipify.org/', body='192.168.0.1', status=200)
        groupId = awstools._create_sec_group(name='testsecgroup')
        
        assert len(responses.calls) == 1
        assert awstools.ec2_resource.SecurityGroup(groupId).group_name == 'testsecgroup'

def test_remote_security_group(awstools):
    with mock_ec2():
        response = awstools.ec2_client.create_security_group(
            GroupName="test_group",
            Description='Security Group for CSAOpt')

        security_group_id = response['GroupId']
        awstools._remove_sec_group(security_group_id)

        security_group_iterator = awstools.ec2_resource.security_groups.all()
        for sec_grp in security_group_iterator:
            print(sec_grp)
            assert sec_grp.id is not security_group_id


def test_start_instances(awstools):
    with mock_ec2():
        awstools.security_group_id = 'test_sec_group'
        queue, workers = awstools._provision_instances(timeout_ms=100, count=2)

        assert len(workers) == 2
        assert queue is not None
        assert sum([len(r['Instances']) for r in awstools.ec2_client.describe_instances()['Reservations']]) == 3

def test_get_instances(awstools):
    with mock_ec2():
        awstools.security_group_id = 'test_sec_group'
        queue_and_workers = awstools._provision_instances(timeout_ms=100, count=4)
        awstools.message_queue = queue_and_workers[0]
        awstools.workers = queue_and_workers[1]


        instances = awstools._get_running_instances()

        assert len(instances) == 5

        message_queue_count = 0
        for instance in instances:
            assert instance.public_ip is not None
            assert instance.inst_id is not None

            if instance.is_message_queue:
                message_queue_count += 1

        assert message_queue_count == 1


def test_context_manager(context):
    with mock_ec2():
        responses.add(responses.GET, 'https://api.ipify.org/',
                      body='192.168.0.1', status=200)
        with AWSTools(context, context.config, context.internal_config) as awstools:
            worker_instance_ids = [w.id for w in awstools.workers]
            queue_id = awstools.message_queue.id
            assert len(awstools.ec2_client.describe_instances()) == 2
        
        for instance in awstools.ec2_resource.instances.all():
            if instance.id in worker_instance_ids or instance.id == queue_id:
                assert instance.state['Name'] == 'terminated'
