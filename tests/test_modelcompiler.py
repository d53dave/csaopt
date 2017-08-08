import pytest
import context

from collections import defaultdict


@pytest.fixture
def model_compiler():
    model_proj_path = ''
    conf = defaultdict(str)

    conf['build.exec_paths'] = []

    internal_conf = defaultdict(str)

    internal_conf['build.exec_names'] = ['cmake', 'make']
    internal_conf['build.required_artifacts'] = 'model.o'
    internal_conf['build.timeouts.cmake'] = 30
    internal_conf['build.timeouts.make'] = 30

    return context.ModelCompiler(model_proj_path, conf, internal_conf)


def test_build(model_compiler):
    result = model_compiler.build()

    assert result.failed()
    
