import pytest

from context import Runner, ExecutionType


@pytest.fixture
def invocation_options():
    return {
        'internal_conf': {}
    }


def test_get_execution_type_multimulti(invocation_options):
    with pytest.raises(AssertionError):
        confs = ['conf/1', 'conf/2', 'conf/3']
        models = ['model/1', 'model/2']
        Runner(models, confs, invocation_options)._get_execution_type(models, confs)

    with pytest.raises(AssertionError):
        confs = ['conf/1', 'conf/2']
        models = ['model/1', 'model/2', 'model/3']
        Runner(models, confs, invocation_options)._get_execution_type(models, confs)

    confs = ['conf/1', 'conf/2']
    models = ['model/1', 'model/2']
    exec_type = Runner(models, confs, invocation_options)._get_execution_type(models, confs)

    assert exec_type is ExecutionType.MultiModelMultiConf


def test_get_execution_type_singlemulti(invocation_options):
    confs = ['conf/1', 'conf/2']
    models = ['model/1']
    exec_type = Runner(
        models, confs, invocation_options)._get_execution_type(models, confs)

    assert exec_type is ExecutionType.SingleModelMultiConf


def test_get_execution_type_singlesingle(invocation_options):
    confs = ['conf/1']
    models = ['model/1']
    exec_type = Runner(
        models, confs, invocation_options)._get_execution_type(models, confs)

    assert exec_type is ExecutionType.SingleModelSingleConf


def test_get_execution_type_multisingle(invocation_options):
    confs = ['conf/1']
    models = ['model/1', 'model/2']
    exec_type = Runner(
        models, confs, invocation_options)._get_execution_type(models, confs)

    assert exec_type is ExecutionType.MultiModelSingleConf


def test_get_execution_type_nomodel(invocation_options):
    confs = ['conf/1']
    models = []

    with pytest.raises(AssertionError):
        Runner(models, confs, invocation_options)._get_execution_type(models, confs)


def test_get_execution_type_noconf(invocation_options):
    confs = []
    models = ['model/1']

    with pytest.raises(AssertionError):
        Runner(models, confs, invocation_options)._get_execution_type(
            models, confs)
