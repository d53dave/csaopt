import pytest

from pyhocon import ConfigFactory

from context import ModelValidator


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
                    secret_key = a123456
                    access_key = b123456
                    worker_count = 2
                    timeout = 500
                }
            }
        }
        """)


@pytest.fixture
def validator():
    return ModelValidator()


def test_validate_functions_return(validator: ModelValidator):
    def f_empty():
        pass

    def f_two(a, b):
        return a + b

    error_empty = validator._validate_fun_signature_len('testfun1', f_empty, 0)
    error_empty_2 = validator._validate_fun_signature_len('testfun2', f_empty, 1)
    error_two = validator._validate_fun_signature_len('testfun3', f_two, 2)

    assert error_empty is None
    assert error_empty_2 is not None
    assert error_two is None
