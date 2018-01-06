import imp
import logging
import sys
import string
import inspect

from . import ValidationError
from random import choice

logger = logging.getLogger(__name__)


def _empty_function():
    pass


empty_function_bytecode = _empty_function.__code__.co_code


def _random_str(length):
    chars = string.ascii_letters + string.punctuation + string.digits
    return ''.join(choice(chars) for x in range(length))


class ModelLoader():
    def __init__(self, conf, internal_conf):
        self.model_path = conf['model_path']

        with open(self.model_path, 'r') as f:
            model_source = f.read()
            model_name = conf.get('model.name', 'optimization' + _random_str(6))
            self.model = self._create_module(model_name, source=model_source)

        if not conf.get('model.skip_validation'):
            self._validate(self.model)

    def get_model(self):
        return self.model

    def _create_module(self, name: str, source: str) -> any:
        module = imp.new_module(name)
        sourcelines = source.splitlines()
        print('Executing source:\n')
        i = 1
        for line in sourcelines:
            print('{} {}'.format(i, line))
            i += 1
        exec(source, module.__dict__)

        if module is None:
            raise AssertionError('Model could not be loaded.')
        sys.modules[name] = module
        return module

    def _validate(self, model):
        # https://docs.python.org/3/library/inspect.html
        
        errors = []
        # Check that all functions are there
        cool_f = model.cool

        if cool_f is None:
            errors.append(ValidationError('Definition of function `cool` not found.'))

        if cool_f.__code__.co_code == empty_function_bytecode:
            raise AssertionError('Definition of function `cool` is empty.')

        # Check that all signatures are correct
        cool_sig = inspect.signature(cool_f)
        
        if len(cool_sig.parameters) != 1:
            raise AssertionError('Definition of function `cool` should have 1 parameter')

        # Check that functions are non empty
