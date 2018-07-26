import inspect
import subprocess

from pyhocon import ConfigTree
from typing import Optional, List, Dict, Callable
from ..model import RequiredFunctions
from . import ValidationError


def _empty_function():
    pass


class ModelValidator:

    empty_function_bytecode = _empty_function.__code__.co_code

    # TODO: review these
    required_param_counts = {
        'distribution': 0,
        'precision': 0,
        'dimensions': 0,
        'initialize': 2,
        'generate_next': 3,
        'cool': 1,
        'evaluate': 1,
        'acceptance_func': 3
    }

    def validate_functions(self, functions: Dict[str, Callable], internal_config: ConfigTree) -> List[ValidationError]:
        errors: List[ValidationError] = []

        self.reserved_keywords: List[str] = internal_config['model.validation.reserved_keywords']

        for func in RequiredFunctions:
            val_errors = self._validate_function(
                func.value,
                functions[func.value],
                self.required_param_counts[func.value])

            errors.extend([err for err in val_errors if err is not None])

        return errors

    def validate_typing(self, file_path) -> Optional[ValidationError]:
        mypy_result = subprocess.run(
            ['mypy', file_path], stdout=subprocess.PIPE)

        if mypy_result.returncode != 0:
            return ValidationError(mypy_result.stdout.decode('utf-8'))
        return None

    def _validate_function(self, name: str, fun: Callable, param_count: int) -> List[Optional[ValidationError]]:
        return [
            self._validate_missing_fun(name, fun),
            self._validate_empty_fun(name, fun),
            # TODO review if this is required
            self._validate_return_statement(name, fun),
            self._validate_fun_signature_len(name, fun, param_count),
            self._check_for_reserved_keywords(name, fun)
        ]

    def _check_for_reserved_keywords(self, name, fun) -> Optional[ValidationError]:
        """Returns ValidationError if function contains reserved keywords"""
        for reserved_keyword in self.reserved_keywords:
            if reserved_keyword in inspect.getsource(fun):
                return ValidationError('Reserved Keyword {} found in function \'{}\''.format(reserved_keyword, name))
        return None

    def _validate_missing_fun(self, name, fun) -> Optional[ValidationError]:
        """Returns a ValidationError if function is missing"""
        if fun is None:
            return ValidationError(
                    'Definition of function `{}` not found.'.format(name))
        return None

    def _validate_empty_fun(self, name, fun) -> Optional[ValidationError]:
        """Returns a ValidationError if function has no body (i.e. only pass, return)"""
        if fun.__code__.co_code == self.empty_function_bytecode:
            return ValidationError(
                    'Definition of function `{}` is empty.'.format(name))
        return None

    def _validate_fun_signature_len(self, name, fun, num_params) -> Optional[ValidationError]:
        if len(inspect.signature(fun).parameters) != num_params:
            return ValidationError(
                'Signature of `{}` has an incorrect number of parameters (expected {}, found {})'
                .format(name, num_params, len(inspect.signature(fun).parameters)))
        return None

    def _validate_return_statement(self, name, fun) -> Optional[ValidationError]:
        if 'return' not in inspect.getsource(fun):
            return ValidationError(
                'Body of function `{}` does not contain a `return` statement. '.format(name))
        return None
