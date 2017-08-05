import pytest
import context

@pytest.fixture
def model_compiler():
    model_proj_path = ''
    conf = ''
    internal_conf = ''
    return context.ModelCompiler(model_proj_path, conf, internal_conf)


def test_build(model_compiler):
    print(dir(model_compiler))
    assert 1 is 2
