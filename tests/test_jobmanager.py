import pytest

from mock import call
from dramatiq import Worker
from context import JobManager, AppContext, Broker, ExecutionType, Model
from context import RandomDistribution, Precision, Job, WorkerCommand
from pyhocon import ConfigTree
from collections import OrderedDict


class MockBroker():
    pass


def build_async_mock_results(result):
    async def mock_deploy_results(timeout):
        return result
    return mock_deploy_results


@pytest.fixture
def stub_broker(mocker):
    o = MockBroker()
    o.send_to_queue = mocker.Mock()
    o.broadcast = mocker.Mock()
    o.clear_queue_messages = mocker.Mock()
    o.queue_ids = []
    return o


@pytest.fixture()
def stub_worker(stub_broker):
    worker = Worker(stub_broker.dramatiq_broker, worker_timeout=100)
    worker.start()
    yield worker
    worker.stop()


@pytest.mark.asyncio
async def test_submit_model_not_deployed(stub_broker):
    # TODO Remove ExecutionType from AppContext, it's not required
    ctx = AppContext(None, None, None)
    model = Model(name='testmodel',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  opt_globals=None,
                  functions=[])
    configs = [{}]

    jobmanager = JobManager(ctx, stub_broker, [model], configs)

    with pytest.raises(AssertionError):
        await jobmanager.submit()


@pytest.mark.asyncio
async def test_wait_empty_jobs(stub_broker):
    ctx = AppContext(None, None, None)
    model = Model(name='testmodel',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  opt_globals=None,
                  functions=[])
    configs = [{}]

    jobmanager = JobManager(ctx, stub_broker, [model], configs)

    with pytest.raises(AssertionError):
        await jobmanager.wait_for_results()


@pytest.mark.asyncio
async def test_deploy_single_model_single_conf(mocker, stub_broker):
    ctx = AppContext(None, None, None)
    model = Model(name='testmodel',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  opt_globals=None,
                  functions=[])

    stub_broker.queue_ids = ['queue1']

    stub_broker.get_all_results = build_async_mock_results(
        {'queue1': ['model_deployed']})
    configs = [{'test': 'deploy_single_model_multi_conf'}]

    jobmanager = JobManager(ctx, stub_broker, [model], configs)
    await jobmanager.deploy_model()

    stub_broker.broadcast.assert_called_with(
        WorkerCommand.DeployModel, model.to_dict())
    assert jobmanager.models_deployed is True


@pytest.mark.asyncio
async def test_deploy_single_model_single_conf_failed_missing_response(mocker, stub_broker):
    ctx = AppContext(None, None, None)
    model = Model(name='testmodel',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  opt_globals=None,
                  functions=[])

    stub_broker.queue_ids = ['queue1', 'queue2']

    stub_broker.get_all_results = build_async_mock_results(
        {'queue1': ['model_deployed']})
    configs = [{'test': 'deploy_single_model_multi_conf'}]

    jobmanager = JobManager(ctx, stub_broker, [model], configs)
    with pytest.raises(AssertionError):
        await jobmanager.deploy_model()

    stub_broker.broadcast.assert_called_with(
        WorkerCommand.DeployModel, model.to_dict())
    assert jobmanager.models_deployed is False


@pytest.mark.asyncio
async def test_deploy_single_model_single_conf_failed_with_error(mocker, stub_broker):
    ctx = AppContext(None, None, None)
    model = Model(name='testmodel',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  opt_globals=None,
                  functions=[])

    stub_broker.queue_ids = ['queue1', 'queue2']

    stub_broker.get_all_results = build_async_mock_results(
        {'queue1': ['model_deployed'], 'queue2': ['lol, error']})
    configs = [{'test': 'deploy_single_model_multi_conf'}]

    jobmanager = JobManager(ctx, stub_broker, [model], configs)
    with pytest.raises(AssertionError):
        await jobmanager.deploy_model()

    stub_broker.broadcast.assert_called_with(
        WorkerCommand.DeployModel, model.to_dict())
    assert jobmanager.models_deployed is False


@pytest.mark.asyncio
async def test_deploy_single_model_multi_conf(mocker, stub_broker):
    ctx = AppContext(None, None, None)
    model = Model(name='testmodel',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  opt_globals=None,
                  functions=[])

    configs = [{'test': 'deploy_single_model_multi_conf'},
               {'test': 'deploy_single_model_multi_conf'}]

    stub_broker.queue_ids = ['queue1', 'queue2']

    stub_broker.get_all_results = build_async_mock_results(
        {'queue1': ['model_deployed'], 'queue2': ['model_deployed']})

    jobmanager = JobManager(ctx, stub_broker, [model], configs)
    await jobmanager.deploy_model()

    stub_broker.broadcast.assert_called_with(
        WorkerCommand.DeployModel, model.to_dict())
    assert jobmanager.models_deployed is True


@pytest.mark.asyncio
async def test_deploy_multi_model_single_conf(mocker, stub_broker):
    ctx = AppContext(None, None, None)
    model = Model(name='testmodel1',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  opt_globals=None,
                  functions=[])

    model2 = Model(name='testmodel2',
                   dimensions=3,
                   precision=Precision.Float32,
                   distribution=RandomDistribution.Uniform,
                   opt_globals=None,
                   functions=[])

    configs = [{'test': 'deploy_single_model_multi_conf'}]

    stub_broker.queue_ids = ['queue1', 'queue2']
    stub_broker.get_all_results = build_async_mock_results(
        {'queue1': ['model_deployed'], 'queue2': ['model_deployed']})

    jobmanager = JobManager(ctx, stub_broker, [model, model2], configs)
    await jobmanager.deploy_model()

    stub_broker.send_to_queue.assert_has_calls([
        call('queue1', WorkerCommand.DeployModel, model.to_dict()),
        call('queue2', WorkerCommand.DeployModel, model2.to_dict())])
    assert jobmanager.models_deployed is True


@pytest.mark.asyncio
async def test_deploy_multi_model_multi_conf(mocker, stub_broker):
    ctx = AppContext(None, None, None)
    model = Model(name='testmodel1',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  opt_globals=None,
                  functions=[])

    model2 = Model(name='testmodel2',
                   dimensions=3,
                   precision=Precision.Float32,
                   distribution=RandomDistribution.Uniform,
                   opt_globals=None,
                   functions=[])

    configs = [{'test': 'deploy_single_model_multi_conf'},
               {'test2': 'deploy_single_model_multi_conf_2'}]

    stub_broker.queue_ids = ['queue1', 'queue2']
    stub_broker.get_all_results = build_async_mock_results(
        {'queue1': ['model_deployed'], 'queue2': ['model_deployed']})

    jobmanager = JobManager(ctx, stub_broker, [model, model2], configs)
    await jobmanager.deploy_model()

    stub_broker.send_to_queue.assert_has_calls([
        call('queue1', WorkerCommand.DeployModel, model.to_dict()),
        call('queue2', WorkerCommand.DeployModel, model2.to_dict())])
    assert jobmanager.models_deployed is True


@pytest.mark.asyncio
async def test_job_single_model_single_conf(stub_broker, mocker):
    ctx = AppContext(None, None, None)
    models = [Model(name='testmodel',
                    dimensions=3,
                    precision=Precision.Float32,
                    distribution=RandomDistribution.Uniform,
                    opt_globals=None,
                    functions=[])]

    configs = [{'test': 'deploy_single_model_multi_conf'}]
    stub_broker.queue_ids = ['queue1']

    jobmanager = JobManager(ctx, stub_broker, models, configs)
    jobmanager.models_deployed = True

    jobs = await jobmanager.submit()
    assert len(jobs) == 1

    stub_broker.broadcast.assert_called()

    broadcast = stub_broker.broadcast.call_args[0]
    assert broadcast[0] is WorkerCommand.RunOptimization
    assert broadcast[1]['params'] == configs[0]


@pytest.mark.asyncio
async def test_job_multi_model_single_conf(stub_broker, mocker):
    ctx = AppContext(None, None, None)
    models = [Model(name='testmodel1',
                    dimensions=3,
                    precision=Precision.Float32,
                    distribution=RandomDistribution.Uniform,
                    opt_globals=None,
                    functions=[]),
              Model(name='testmodel2',
                    dimensions=3,
                    precision=Precision.Float32,
                    distribution=RandomDistribution.Uniform,
                    opt_globals=None,
                    functions=[])]

    configs = [{'test': 'deploy_single_model_multi_conf'}]

    stub_broker.queue_ids = ['queue1', 'queue2']

    jobmanager = JobManager(ctx, stub_broker, models, configs)
    jobmanager.models_deployed = True

    await jobmanager.submit()
    assert stub_broker.send_to_queue.call_count == 2

    jobs = stub_broker.send_to_queue.call_args_list
    assert jobs[0][0][0] == 'queue1'
    assert jobs[0][0][1] == WorkerCommand.RunOptimization
    assert jobs[0][0][2]['params'] == configs[0]
    assert jobs[0][0][2]['model'] == 'testmodel1'

    assert jobs[1][0][0] == 'queue2'
    assert jobs[1][0][1] == WorkerCommand.RunOptimization
    assert jobs[1][0][2]['params'] == configs[0]
    assert jobs[1][0][2]['model'] == 'testmodel2'


@pytest.mark.asyncio
async def test_job_single_model_multi_conf(stub_broker, mocker):
    ctx = AppContext(None, None, None)
    models = [Model(name='testmodel1',
                    dimensions=3,
                    precision=Precision.Float32,
                    distribution=RandomDistribution.Uniform,
                    opt_globals=None,
                    functions=[])]

    configs = [{'test': 'deploy_multi_model_multi_conf'},
               {'test2': 'deploy_multi_model_multi_conf'}]

    stub_broker.queue_ids = ['queue1', 'queue2']

    jobmanager = JobManager(ctx, stub_broker, models, configs)
    jobmanager.models_deployed = True

    await jobmanager.submit()
    assert stub_broker.send_to_queue.call_count == 2

    jobs = stub_broker.send_to_queue.call_args_list
    assert jobs[0][0][0] == 'queue1'
    assert jobs[0][0][1] == WorkerCommand.RunOptimization
    assert jobs[0][0][2]['params'] == configs[0]
    assert jobs[0][0][2]['model'] == 'testmodel1'

    assert jobs[1][0][0] == 'queue2'
    assert jobs[1][0][1] == WorkerCommand.RunOptimization
    assert jobs[1][0][2]['params'] == configs[1]
    assert jobs[1][0][2]['model'] == 'testmodel1'


@pytest.mark.asyncio
async def test_job_multi_model_multi_conf(stub_broker, mocker):
    ctx = AppContext(None, None, None)
    models = [Model(name='testmodel1',
                    dimensions=3,
                    precision=Precision.Float32,
                    distribution=RandomDistribution.Uniform,
                    opt_globals=None,
                    functions=[]),
              Model(name='testmodel2',
                    dimensions=3,
                    precision=Precision.Float32,
                    distribution=RandomDistribution.Uniform,
                    opt_globals=None,
                    functions=[])]

    configs = [{'test': 'deploy_multi_model_multi_conf'},
               {'test2': 'deploy_multi_model_multi_conf'}]

    stub_broker.queue_ids = ['queue1', 'queue2']

    jobmanager = JobManager(ctx, stub_broker, models, configs)
    jobmanager.models_deployed = True

    await jobmanager.submit()
    assert stub_broker.send_to_queue.call_count == 2

    jobs = stub_broker.send_to_queue.call_args_list
    print(jobs[0])
    print('0,0', jobs[0][0])
    assert jobs[0][0][0] == 'queue1'
    assert jobs[0][0][1] == WorkerCommand.RunOptimization
    assert jobs[0][0][2]['params'] == configs[0]
    assert jobs[0][0][2]['model'] == 'testmodel1'

    assert jobs[1][0][0] == 'queue2'
    assert jobs[1][0][1] == WorkerCommand.RunOptimization
    assert jobs[1][0][2]['params'] == configs[1]
    assert jobs[1][0][2]['model'] == 'testmodel2'


def test_get_execution_type_multimulti():
    with pytest.raises(AssertionError):
        confs = ['conf/1', 'conf/2', 'conf/3']
        models = ['model/1', 'model/2']
        JobManager(None, None, models, confs)

    with pytest.raises(AssertionError):
        confs = ['conf/1', 'conf/2']
        models = ['model/1', 'model/2', 'model/3']
        JobManager(None, None, models, confs)

    confs = ['conf/1', 'conf/2']
    models = ['model/1', 'model/2']
    exec_type = JobManager(None, None, models, confs).execution_type

    assert exec_type is ExecutionType.MultiModelMultiConf


def test_get_execution_type_singlemulti():
    confs = ['conf/1', 'conf/2']
    models = ['model/1']
    exec_type = JobManager(None, None, models, confs).execution_type

    assert exec_type is ExecutionType.SingleModelMultiConf


def test_get_execution_type_singlesingle():
    confs = ['conf/1']
    models = ['model/1']
    exec_type = JobManager(None, None, models, confs).execution_type

    assert exec_type is ExecutionType.SingleModelSingleConf


def test_get_execution_type_multisingle():
    confs = ['conf/1']
    models = ['model/1', 'model/2']
    exec_type = JobManager(None, None, models, confs).execution_type

    assert exec_type is ExecutionType.MultiModelSingleConf


def test_get_execution_type_nomodel():
    confs = ['conf/1']
    models = []

    with pytest.raises(AssertionError):
        JobManager(None, None, models, confs)


def test_get_execution_type_noconf():
    confs = []
    models = ['model/1']

    with pytest.raises(AssertionError):
        JobManager(None, None, models, confs)
