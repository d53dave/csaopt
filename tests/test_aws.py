import pytest
import responses
import base64

from moto import mock_ec2
from pyhocon import ConfigFactory
from context import AWSTools, AppContext, ConsolePrinter, Instance

from ipaddress import IPv4Address


@pytest.fixture
def internal_conf():
    return ConfigFactory.parse_file('csaopt/internal/csaopt-internal.conf')


@pytest.fixture
def conf():
    return ConfigFactory.parse_string("""
        {
            remote {
                aws {
                    region = eu-central-1
                    secret_key = HQefGxVMHFnKDb7E9SWHlG9RqXFiWHkku2quV8jb
                    access_key = AKXBREA5T5XLSQWEXB4KQ
                    worker_count = 2
                    timeout = 500
                }
            }
        }
        """)


def isBase64(x):
    return base64.b64encode(base64.b64decode(x)) == x.replace('\n', '').encode('ascii')


@pytest.fixture
def context(conf, internal_conf):
    return AppContext(ConsolePrinter(internal_conf), [conf], internal_conf)


@pytest.fixture
def awstools(context):
    return AWSTools(context.configs[0], context.internal_config)


def test_loads_userdata(awstools):
    assert awstools.user_data_scripts['broker'] is not None
    assert awstools.user_data_scripts['worker'] is not None
    assert len(awstools.user_data_scripts['broker']) > 0
    assert len(awstools.user_data_scripts['worker']) > 0


def test_create_security_group(awstools):
    with mock_ec2():
        groupId = awstools._create_sec_group(name='testsecgroup')

        assert awstools.ec2_resource.SecurityGroup(groupId).group_name == 'testsecgroup'


def test_remote_security_group(awstools):
    with mock_ec2():
        response = awstools.ec2_client.create_security_group(
            GroupName="test_group", Description='Security Group for CSAOpt')

        security_group_id = response['GroupId']
        awstools._remove_sec_group(security_group_id)

        security_group_iterator = awstools.ec2_resource.security_groups.all()
        for sec_grp in security_group_iterator:
            print(sec_grp)
            assert sec_grp.id is not security_group_id


def test_start_instances(awstools):
    with mock_ec2():
        awstools.security_group_id = 'test_sec_group'
        awstools.debug_on_cpu = True
        awstools.broker_port = 4242
        awstools.broker_password = 'testpassword'
        broker, workers = awstools._provision_instances(timeout_ms=100, count=2, **awstools.provision_args)

        assert len(workers) == 2
        assert broker is not None
        assert sum([len(r['Instances']) for r in awstools.ec2_client.describe_instances()['Reservations']]) == 3

        broker_userdata = base64.b64decode(
            awstools.ec2_client.describe_instance_attribute(
                Attribute='userData', InstanceId=broker.instance_id)['UserData']['Value']).decode('ascii')

        assert str(awstools.broker_port) in broker_userdata
        assert awstools.broker_password in broker_userdata

        worker0_userdata = base64.b64decode(
            awstools.ec2_client.describe_instance_attribute(
                Attribute='userData', InstanceId=workers[0].instance_id)['UserData']['Value']).decode('ascii')

        assert 'NUMBA_ENABLE_CUDASIM=1' in worker0_userdata
        assert str(broker.private_ip_address) in worker0_userdata
        assert str(awstools.broker_port) in worker0_userdata
        assert awstools.broker_password in worker0_userdata


def test_get_instances(awstools):
    with mock_ec2():
        awstools.security_group_id = 'test_sec_group'
        awstools.broker, awstools.workers = awstools._provision_instances(
            timeout_ms=100, count=4, **awstools.provision_args)

        broker, workers = awstools.get_running_instances()

        assert len(workers) == 4
        assert broker is not None


def test_context_manager(context):
    with mock_ec2():
        responses.add(responses.GET, 'https://api.ipify.org/', body='192.168.0.1', status=200)
        with AWSTools(context.configs[0], context.internal_config) as awstools:
            worker_instance_ids = [w.id for w in awstools.workers]
            broker_id = awstools.broker.id
            assert len(awstools.ec2_client.describe_instances()) == 2

        for instance in awstools.ec2_resource.instances.all():
            if instance.id in worker_instance_ids or instance.id == broker_id:
                assert instance.state['Name'] == 'terminated'


def test_instance_ip():
    instance = Instance('id', '192.168.0.1')

    assert instance.public_ip.is_private is True
    assert instance.public_ip == IPv4Address('192.168.0.1')


def test_instance_ip_bad():
    with pytest.raises(ValueError):
        Instance('id', '442.168.0.1')
