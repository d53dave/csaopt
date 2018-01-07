import inspect
import subprocess

from typing import Optional, List, Dict
from . import ValidationError


class ModelValidator:
    validators = []

    def _empty_function():
        pass

    empty_function_bytecode = _empty_function.__code__.co_code

    @staticmethod
    def validate_functions(functions: Dict[str, callable]) -> List[ValidationError]:
        # https://docs.python.org/3/library/inspect.html

        errors: List[ValidationError] = []
        errors.extend(ModelValidator._validate_dim(functions['dimensions']))
        errors.extend(ModelValidator._validate_dim(functions['precision']))
        errors.extend(ModelValidator._validate_dim(functions['distribution']))
        errors.extend(ModelValidator._validate_dim(functions['generate_next']))
        errors.extend(ModelValidator._validate_dim(functions['initialize']))
        errors.extend(ModelValidator._validate_dim(functions['cool']))
        errors.extend(ModelValidator._validate_dim(functions['acceptance']))
        errors.extend(ModelValidator._validate_dim(functions['evaluate']))

        return [e for e in errors if e is not None]

    @staticmethod
    def validate_typing(file_path) -> Optional[ValidationError]:
        mypy_result = subprocess.run(
            ['mypy', file_path], stdout=subprocess.PIPE)

        if mypy_result.returncode != 0:
            return ValidationError(mypy_result.stdout.decode('utf-8'))

    @staticmethod
    def _validate_dim(dim_f: callable) -> List[Optional[ValidationError]]:
        name = 'dimensions'
        return [
            ModelValidator._validate_missing_fun(name, dim_f),
            ModelValidator._validate_empty_fun(name, dim_f),
            ModelValidator._validate_return_statement(name, dim_f),
            ModelValidator._validate_fun_signature_len(name, dim_f, 2)
        ]

    @staticmethod
    def _validate_acceptance(accept_f: callable) -> List[Optional[ValidationError]]:
        name = 'acceptance_func'
        return [
            ModelValidator._validate_missing_fun(name, accept_f),
            ModelValidator._validate_empty_fun(name, accept_f),
            ModelValidator._validate_return_statement(name, accept_f),
            ModelValidator._validate_fun_signature_len(name, accept_f, 3)
        ]

    @staticmethod
    def _validate_init(self, init_f):
        name = 'init_f'
        return [
            ModelValidator._validate_missing_fun(name, init_f),
            ModelValidator._validate_empty_fun(name, init_f),
            ModelValidator._validate_return_statement(name, init_f),
            ModelValidator._validate_fun_signature_len(name, init_f, 2)
        ]

    @staticmethod
    def _validate_eval(self, eval_f):
        name = 'eval_f'
        return [
            ModelValidator._validate_missing_fun(name, eval_f),
            ModelValidator._validate_empty_fun(name, eval_f),
            ModelValidator._validate_return_statement(name, eval_f),
            ModelValidator._validate_fun_signature_len(name, eval_f, 1)
        ]

    @staticmethod
    def _validate_next(self, next_f):
        name = 'next_f'
        return [
            ModelValidator._validate_missing_fun(name, next_f),
            ModelValidator._validate_empty_fun(name, next_f),
            ModelValidator._validate_return_statement(name, next_f),
            ModelValidator._validate_fun_signature_len(name, next_f, 2)
        ]

    @staticmethod
    def _validate_missing_fun(name, fun) -> Optional[ValidationError]:
        """Returns a ValidationError if function is missing"""
        if fun is None:
            return ValidationError(
                    'Definition of function `{}` not found.'.format(name))

    @staticmethod
    def _validate_empty_fun(name, fun) -> Optional[ValidationError]:
        """Returns a ValidationError if function has no body (i.e. pass, return)"""
        if fun.__code__.co_code == ModelValidator.empty_function_bytecode:
            return ValidationError(
                    'Definition of function `{}` is empty.'.format(name))

    @staticmethod
    def _validate_fun_signature_len(name, fun, num_params) -> Optional[ValidationError]:
        if len(inspect.signature(fun).parameters) != num_params:
            return ValidationError(
                'Signature of `{}` has an incorrect number of parameters (expected {}, found {})'
                .format(name))

    @staticmethod
    def _validate_return_statement(name, fun) -> Optional[ValidationError]:
        if 'return' not in inspect.getsource(fun):
            return ValidationError(
                'Body of function `{}` does not contain a `return` statement. ')
