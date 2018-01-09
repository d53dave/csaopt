import inspect
import subprocess

from typing import Optional, List, Dict, Callable
from ..model import RequiredFunctions
from . import ValidationError


def _empty_function():
    pass


class ModelValidator:

    empty_function_bytecode = _empty_function.__code__.co_code

    required_param_counts = {
        'distribution': 0,
        'precision': 0,
        'dimensions': 0,
        'initialize': 2,
        'generate_next': 2,
        'cool': 1,
        'evaluate': 1,
        'acceptance_func': 3
    }

    @staticmethod
    def validate_functions(functions: Dict[str, Callable]) -> List[ValidationError]:
        errors: List[ValidationError] = []

        for func in RequiredFunctions:
            val_errors = ModelValidator._validate_function(
                func.value,
                functions[func.value],
                ModelValidator.required_param_counts[func.value])

            errors.extend([err for err in val_errors if err is not None])

        return errors

    @staticmethod
    def validate_typing(file_path) -> Optional[ValidationError]:
        mypy_result = subprocess.run(
            ['mypy', file_path], stdout=subprocess.PIPE)

        if mypy_result.returncode != 0:
            return ValidationError(mypy_result.stdout.decode('utf-8'))
        return None

    @staticmethod
    def _validate_function(name: str, fun: Callable, param_count: int) -> List[Optional[ValidationError]]:
        return [
            ModelValidator._validate_missing_fun(name, fun),
            ModelValidator._validate_empty_fun(name, fun),
            ModelValidator._validate_return_statement(name, fun),
            ModelValidator._validate_fun_signature_len(name, fun, param_count)
        ]

    @staticmethod
    def _validate_missing_fun(name, fun) -> Optional[ValidationError]:
        """Returns a ValidationError if function is missing"""
        if fun is None:
            return ValidationError(
                    'Definition of function `{}` not found.'.format(name))
        return None

    @staticmethod
    def _validate_empty_fun(name, fun) -> Optional[ValidationError]:
        """Returns a ValidationError if function has no body (i.e. pass, return)"""
        if fun.__code__.co_code == ModelValidator.empty_function_bytecode:
            return ValidationError(
                    'Definition of function `{}` is empty.'.format(name))
        return None

    @staticmethod
    def _validate_fun_signature_len(name, fun, num_params) -> Optional[ValidationError]:
        if len(inspect.signature(fun).parameters) != num_params:
            return ValidationError(
                'Signature of `{}` has an incorrect number of parameters (expected {}, found {})'
                .format(name, num_params, len(inspect.signature(fun).parameters)))
        return None

    @staticmethod
    def _validate_return_statement(name, fun) -> Optional[ValidationError]:
        if 'return' not in inspect.getsource(fun):
            return ValidationError(
                'Body of function `{}` does not contain a `return` statement. '.format(name))
        return None
