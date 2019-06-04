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
        'initialize': 2,
        'generate_next': 4,
        'cool': 3,
        'evaluate': 1,
        'acceptance_func': 4,
        'empty_state': 0
    }

    def validate_functions(self, functions: Dict[str, Callable], internal_config: ConfigTree) -> List[ValidationError]:
        """Run validators on optimization functions

        Args:
            functions: Dictionary mapping function name to function object
            internal_config: Internal CSAOpt configuration

        Returns:
            A list of ValidationsErrors. This list will be empty when all restrictions are met.
        """
        errors: List[ValidationError] = []

        self.reserved_keywords: List[str] = internal_config['model.validation.reserved_keywords']

        for func in RequiredFunctions:
            val_errors = self._validate_function(func.value, functions[func.value],
                                                 self.required_param_counts[func.value])

            errors.extend([err for err in val_errors if err is not None])

        return errors

    def _validate_function(self, name: str, fun: Callable, param_count: int) -> List[Optional[ValidationError]]:
        """Run all validators on the input function

        Args:
            name: Name of function
            fun: Function object
            param_count: Number of expected function arguments
        """
        return [
            self._validate_missing_fun(name, fun),
            self._validate_empty_fun(name, fun),
            # TODO review if this is required
            self._validate_return_statement(name, fun),
            self._validate_fun_signature_len(name, fun, param_count),
            self._check_for_reserved_keywords(name, fun)
        ]

    def validate_typing(self, file_path: str) -> Optional[ValidationError]:
        """Validates the input file using mypy

        Args:
            file_path: Path to file

        Returns:
            :class:`~model_loader.ValidationError` if validation fails, otherwise `None`
        """
        mypy_result = subprocess.run(['mypy', file_path], stdout=subprocess.PIPE)

        if mypy_result.returncode != 0:
            return ValidationError(mypy_result.stdout.decode('utf-8'))
        return None

    def _check_for_reserved_keywords(self, name: str, fun: Callable) -> Optional[ValidationError]:
        """Returns ValidationError if function contains reserved keywords

        Args:
            name: Name of function that is checked
            fun: Function object to be checked

        Returns:
            :class:`~model_loader.ValidationError` if validation fails, otherwise `None`
        """
        for reserved_keyword in self.reserved_keywords:
            if reserved_keyword in inspect.getsource(fun):
                return ValidationError('Reserved Keyword {} found in function \'{}\''.format(reserved_keyword, name))
        return None

    def _validate_missing_fun(self, name: str, fun: Callable) -> Optional[ValidationError]:
        """Returns a ValidationError if function is missing

        Args:
            name: Name of function that is checked
            fun: Function object to be checked

        Returns:
            :class:`~model_loader.ValidationError` if validation fails, otherwise `None`
        """
        if fun is None:
            return ValidationError('Definition of function `{}` not found.'.format(name))
        return None

    def _validate_empty_fun(self, name: str, fun: Callable) -> Optional[ValidationError]:
        """Returns a ValidationError if function has no body (i.e. only pass, return)

        Args:
            name: Name of function that is checked
            fun: Function object to be checked

        Returns:
            :class:`~model_loader.ValidationError` if validation fails, otherwise `None`
        """
        if fun.__code__.co_code == self.empty_function_bytecode:
            return ValidationError('Definition of function `{}` is empty.'.format(name))
        return None

    def _validate_fun_signature_len(self, name: str, fun: Callable, num_params: int) -> Optional[ValidationError]:
        """Validates that a given function accepts the correct number of arguments

        Args:
            name: Name of function that is checked
            fun: Function object to be checked

        Returns:
            :class:`~model_loader.ValidationError` if validation fails, otherwise `None`
        """
        if len(inspect.signature(fun).parameters) != num_params:
            return ValidationError(
                'Signature of `{}` has an incorrect number of parameters (expected {}, found {})'.format(
                    name, num_params, len(inspect.signature(fun).parameters)))
        return None

    def _validate_return_statement(self, name: str, fun: Callable) -> Optional[ValidationError]:
        """Validates that a given function includes a return statement

        Args:
            name: Name of function that is checked
            fun: Function object to be checked

        Returns:
            :class:`~model_loader.ValidationError` if validation fails, otherwise `None`
        """
        if 'return' not in inspect.getsource(fun):
            return ValidationError('Body of function `{}` does not contain a `return` statement. '.format(name))
        return None
