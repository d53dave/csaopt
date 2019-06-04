import pytest
import imp

from pyhocon import ConfigFactory

from context import ModelLoader, ModelValidator, ValidationError, Precision, RandomDistribution


@pytest.fixture
def internal_conf():
    return ConfigFactory.parse_file('csaopt/internal/csaopt-internal.conf')


@pytest.fixture
def conf():
    return ConfigFactory.parse_string("""
        {
            model {
                name = testopt
                path = examples/langermann/langermann_opt.py
                skip_typecheck = True
                dimensions = 2
            }
        }
        """)


def test_build_model(conf, internal_conf, mocker):
    validator = ModelValidator()
    validator.validate_functions = mocker.stub(name='validate_functions_stub')
    loader = ModelLoader(conf, internal_conf, validator)
    model = loader.get_model()

    assert model is not None
    assert len(model.functions) == 6
    validator.validate_functions.assert_called_once()


def test_validator_has_errors(conf, internal_conf, mocker):
    validator = ModelValidator()
    validator.validate_functions = mocker.Mock(return_value=[ValidationError('this is a test error')])
    loader = ModelLoader(conf, internal_conf, validator)
    model = loader.get_model()

    assert model is None
    assert len(loader.errors) == 1


def test_should_run_type_check(conf, internal_conf, mocker):
    conf['model']['skip_typecheck'] = False

    validator = ModelValidator()
    validator.validate_functions = mocker.stub(name='validate_functions_stub')
    validator.validate_typing = mocker.stub(name='validate_typing_stub')

    ModelLoader(conf, internal_conf, validator)
    validator.validate_functions.assert_called_once()
    validator.validate_typing.assert_called_once()


def test_loading_py_model_failed(conf, internal_conf, mocker):
    mocker.patch('imp.load_source', return_value=None)

    validator = ModelValidator()
    validator.validate_functions = mocker.stub(name='validate_functions_stub')

    with pytest.raises(AssertionError):
        ModelLoader(conf, internal_conf, validator)

    imp.load_source.assert_called_once_with('testopt', 'examples/langermann/langermann_opt.py')


def test_globals(conf, internal_conf, mocker):
    validator = ModelValidator()
    validator.validate_functions = mocker.stub(name='validate_functions_stub')
    validator.validate_typing = mocker.stub(name='validate_typing_stub')

    loader = ModelLoader(conf, internal_conf, validator)
    validator.validate_functions.assert_called_once()

    model = loader.get_model()
    assert 'm = 5' in model.globals
    assert 'c = (1, 2, 5, 2, 3)' in model.globals
    assert 'A = ((3, 5), (5, 2), (2, 1), (1, 4), (7, 9))' in model.globals

    assert 'from math import pi' not in model.globals


def test_model_params(conf, internal_conf, mocker):
    validator = ModelValidator()
    validator.validate_functions = mocker.stub(name='validate_functions_stub')
    validator.validate_typing = mocker.stub(name='validate_typing_stub')

    loader = ModelLoader(conf, internal_conf, validator)
    validator.validate_functions.assert_called_once()

    model = loader.get_model()
    assert Precision.Float32 == model.precision
    assert RandomDistribution.Uniform == model.distribution
    assert 2 == model.dimensions
