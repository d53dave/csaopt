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
        }

@pytest.fixture
def context(conf, internal_conf):
    return AppContext(ConsolePrinter(), conf, internal_conf)



def test_create_security_group(context):
    with mock_ec2():
        responses.add(responses.GET, 'https://api.ipify.org/', body='192.168.0.1', status=200)
        awstools = AWSTools(context, context.config, context.internal_config)
        groupId = awstools._create_sec_group(name='testsecgroup')
        
        assert len(responses.calls) == 1
        assert awstools.ec2_resource.SecurityGroup(groupId).group_name == 'testsecgroup'


