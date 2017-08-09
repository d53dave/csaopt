import pytest
import context

from collections import defaultdict


@pytest.fixture
def conf():
    conf = defaultdict(str)
    conf['build.exec_paths'] = []
    return conf


@pytest.fixture
def internal_conf():
    internal_conf = defaultdict(str)

    internal_conf['build.exec_names'] = ['cmake', 'make']
    internal_conf['build.required_artifacts'] = 'model.o'
    internal_conf['build.timeouts.cmake'] = 30
    internal_conf['build.timeouts.make'] = 30
    return internal_conf


def test_build(conf, internal_conf):
    model_proj_path = ''
    model_compiler = context.ModelCompiler(model_proj_path, conf, internal_conf)

    result = model_compiler.build()

    assert result.failed()
