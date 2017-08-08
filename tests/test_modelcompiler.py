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

    return context.ModelCompiler(model_proj_path, conf, internal_conf)


def test_build(model_compiler):
    print(dir(model_compiler))

    model_compiler.build()
    assert 1 is 2
