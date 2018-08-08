import pytest

from mock import call
from context import JobManager, AppContext, QueueClient, ExecutionType, Model, RandomDistribution, Precision, Job
from pyhocon import ConfigTree
from collections import OrderedDict


class MockQueueClient(object):
    pass


async def return_async_value(val):
    return val


@pytest.fixture
def queue_client(mocker):
    o = MockQueueClient()
    o.deploy_model = mocker.Mock()
    o.broadcast_deploy_model = mocker.Mock()
    o.model_deployed = mocker.Mock(return_value=True)
    return o


@pytest.mark.asyncio
async def test_submit_model_not_deployed(queue_client):
    ctx = AppContext(None, None, None, ExecutionType.SingleModelSingleConf)
    model = Model(name='testmodel',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  functions=[])
    configs = [{}]

    jobmanager = JobManager(ctx, queue_client, [model], configs)

    with pytest.raises(AssertionError):
        await jobmanager.submit()


@pytest.mark.asyncio
async def test_wait_empty_jobs(queue_client):
    ctx = AppContext(None, None, None, ExecutionType.SingleModelSingleConf)
    model = Model(name='testmodel',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  functions=[])
    configs = [{}]

    jobmanager = JobManager(ctx, queue_client, [model], configs)

    with pytest.raises(AssertionError):
        await jobmanager.wait_for_results()


@pytest.mark.asyncio
async def test_deploy_single_model_single_conf(queue_client):
    ctx = AppContext(None, None, None, ExecutionType.SingleModelSingleConf)
    model = Model(name='testmodel',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  functions=[])

    configs = [{'test': 'deploy_single_model_multi_conf'}]

    jobmanager = JobManager(ctx, queue_client, [model], configs)
    await jobmanager.deploy_model()

    queue_client.broadcast_deploy_model.assert_called_with(model)
    assert jobmanager.models_deployed is True


@pytest.mark.asyncio
async def test_deploy_single_model_multi_conf(queue_client):
    ctx = AppContext(None, None, None, ExecutionType.SingleModelMultiConf)
    model = Model(name='testmodel',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  functions=[])

    configs = [{'test': 'deploy_single_model_multi_conf'},
               {'test': 'deploy_single_model_multi_conf'}]

    jobmanager = JobManager(ctx, queue_client, [model], configs)
    await jobmanager.deploy_model()

    queue_client.broadcast_deploy_model.assert_called_with(model)
    assert jobmanager.models_deployed is True


@pytest.mark.asyncio
async def test_deploy_multi_model_single_conf(queue_client):
    ctx = AppContext(None, None, None, ExecutionType.MultiModelSingleConf)
    model = Model(name='testmodel1',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  functions=[])

    model2 = Model(name='testmodel2',
                   dimensions=3,
                   precision=Precision.Float32,
                   distribution=RandomDistribution.Uniform,
                   functions=[])

    configs = [{'test': 'deploy_multi_model_single_conf'}]

    queue_client.workers = OrderedDict()
    queue_client.workers['worker1'] = {}
    queue_client.workers['worker2'] = {}

    jobmanager = JobManager(ctx, queue_client, [model, model2], configs)
    await jobmanager.deploy_model()

    queue_client.deploy_model.assert_has_calls(
        [call('worker1', model), call('worker2', model2)])
    assert jobmanager.models_deployed is True


@pytest.mark.asyncio
async def test_deploy_multi_model_multi_conf(queue_client):
    ctx = AppContext(None, None, None, ExecutionType.MultiModelSingleConf)
    model = Model(name='testmodel1',
                  dimensions=3,
                  precision=Precision.Float32,
                  distribution=RandomDistribution.Uniform,
                  functions=[])

    model2 = Model(name='testmodel2',
                   dimensions=3,
                   precision=Precision.Float32,
                   distribution=RandomDistribution.Uniform,
                   functions=[])

    configs = [{'test': 'deploy_single_model_multi_conf'}]

    queue_client.workers = OrderedDict()
    queue_client.workers['worker1'] = {}
    queue_client.workers['worker2'] = {}

    jobmanager = JobManager(ctx, queue_client, [model, model2], configs)
    await jobmanager.deploy_model()

    queue_client.deploy_model.assert_has_calls(
        [call('worker1', model), call('worker2', model2)])
    assert jobmanager.models_deployed is True


@pytest.mark.asyncio
async def test_job_single_model_single_conf(queue_client, mocker):
    ctx = AppContext(None, None, None, ExecutionType.SingleModelSingleConf)
    queue_client.broadcast_job = mocker.Mock(return_value=return_async_value(None))
    models = [Model(name='testmodel',
                    dimensions=3,
                    precision=Precision.Float32,
                    distribution=RandomDistribution.Uniform,
                    functions=[])]

    configs = [{'test': 'deploy_single_model_multi_conf'}]

    jobmanager = JobManager(ctx, queue_client, models, configs)
    jobmanager.models_deployed = True

    await jobmanager.submit()
    queue_client.broadcast_job.assert_called()

    job = queue_client.broadcast_job.call_args[0][0]
    assert job.model is models[0]
    assert job.params is configs[0]


@pytest.mark.asyncio
async def test_job_multi_model_single_conf(queue_client, mocker):
    ctx = AppContext(None, None, None, ExecutionType.MultiModelSingleConf)
    queue_client.send_job = mocker.Mock()
    queue_client.send_job.side_effect = [return_async_value(None), return_async_value(None)]
    models = [Model(name='testmodel1',
                    dimensions=3,
                    precision=Precision.Float32,
                    distribution=RandomDistribution.Uniform,
                    functions=[]),
              Model(name='testmodel2',
                    dimensions=3,
                    precision=Precision.Float32,
                    distribution=RandomDistribution.Uniform,
                    functions=[])]

    configs = [{'test': 'deploy_single_model_multi_conf'}]

    queue_client.workers = OrderedDict()
    queue_client.workers['worker1'] = {}
    queue_client.workers['worker2'] = {}

    jobmanager = JobManager(ctx, queue_client, models, configs)
    jobmanager.models_deployed = True

    await jobmanager.submit()
    assert queue_client.send_job.call_count == 2

    jobs = queue_client.send_job.call_args_list
    assert jobs[0][0][1].model == models[0]
    assert jobs[1][0][1].model == models[1]
    assert jobs[0][0][1].params == configs[0]
    assert jobs[1][0][1].params == configs[0]


@pytest.mark.asyncio
async def test_job_single_model_multi_conf(queue_client, mocker):
    ctx = AppContext(None, None, None, ExecutionType.SingleModelMultiConf)
    queue_client.send_job = mocker.Mock()
    queue_client.send_job.side_effect = [
        return_async_value(None), return_async_value(None)]
    models = [Model(name='testmodel1',
                    dimensions=3,
                    precision=Precision.Float32,
                    distribution=RandomDistribution.Uniform,
                    functions=[])]

    configs = [{'test': 'deploy_multi_model_multi_conf'},
               {'test2': 'deploy_multi_model_multi_conf'}]

    queue_client.workers = OrderedDict()
    queue_client.workers['worker1'] = {}
    queue_client.workers['worker2'] = {}

    jobmanager = JobManager(ctx, queue_client, models, configs)
    jobmanager.models_deployed = True

    await jobmanager.submit()
    assert queue_client.send_job.call_count == 2

    jobs = queue_client.send_job.call_args_list
    assert jobs[0][0][1].model == models[0]
    assert jobs[1][0][1].model == models[0]
    assert jobs[0][0][1].params == configs[0]
    assert jobs[1][0][1].params == configs[1]


@pytest.mark.asyncio
async def test_job_multi_model_multi_conf(queue_client, mocker):
    ctx = AppContext(None, None, None, ExecutionType.MultiModelMultiConf)
    queue_client.send_job = mocker.Mock()
    queue_client.send_job.side_effect = [return_async_value(None), return_async_value(None)]
    models = [Model(name='testmodel1',
                    dimensions=3,
                    precision=Precision.Float32,
                    distribution=RandomDistribution.Uniform,
                    functions=[]),
              Model(name='testmodel2',
                    dimensions=3,
                    precision=Precision.Float32,
                    distribution=RandomDistribution.Uniform,
                    functions=[])]

    configs = [{'test': 'deploy_multi_model_multi_conf'},
               {'test2': 'deploy_multi_model_multi_conf'}]

    queue_client.workers = OrderedDict()
    queue_client.workers['worker1'] = {}
    queue_client.workers['worker2'] = {}

    jobmanager = JobManager(ctx, queue_client, models, configs)
    jobmanager.models_deployed = True

    await jobmanager.submit()
    assert queue_client.send_job.call_count == 2

    jobs = queue_client.send_job.call_args_list
    assert jobs[0][0][1].model == models[0]
    assert jobs[1][0][1].model == models[1]
    assert jobs[0][0][1].params == configs[0]
    assert jobs[1][0][1].params == configs[1]
