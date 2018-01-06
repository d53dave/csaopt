import inspect

from . import ValidationError


def _empty_function():
    pass


empty_function_bytecode = _empty_function.__code__.co_code


class ModelValidator:
    def validate(self, model):
        # https://docs.python.org/3/library/inspect.html

        errors = []
        # Check that all functions are there
        cool_f = model.cool

        

        # Check that all signatures are correct
        

        # Check that functions are non empty

    def _validate_cool(self, cool_f):
        if cool_f is None:
            return ValidationError(
                'Definition of function `cool` not found.')

        if cool_f.__code__.co_code == empty_function_bytecode:
            return ValidationError('Definition of function `cool` is empty.')

        cool_sig = inspect.signature(cool_f)

        if len(cool_sig.parameters) != 1:
            return ValidationError(
                'Definition of function `cool` should have 1 parameter')

    def _validate_dim(self, dim_f):
        pass

    def _validate_acceptance(self, accept_f):
        pass

    def _validate_init(self, init_f):
        pass

    def _validate_eval(self, eval_f):
        pass

    def _validate_next(self, next_f):
        pass
