import imp
import logging
import sys
import string

from typing import Dict, List
from . import ValidationError, Model
from model_validator import ModelValidator
from random import choice

logger = logging.getLogger(__name__)


def _random_str(length):
    chars = string.ascii_letters + string.punctuation + string.digits
    return ''.join(choice(chars) for x in range(length))


class ModelLoader():
    def __init__(self, conf, internal_conf):
        self.model_path = conf['model_path']

        with open(self.model_path, 'r') as f:
            model_source = f.read()
            model_name = conf.get('model.name', 'optimization' + _random_str(6))
            self.model_module = self._create_module(model_name, source=model_source)

        functions = self._extract_functions(self.model_module)
        # if not conf.get('model.skip_validation'):
        errors: List[ValidationError] = []
        errors.extend(ModelValidator.validate_typing())
        errors.extend(ModelValidator.validate_functions(functions))

        # TODO raise errors or something
        if len(errors) == 0:
            self.model = self._create_model(self.model_module)

    def _create_model(self, module: object) -> Model:
        pass

    def _extract_functions(self, module: object) -> Dict[str, callable]:
        functions: Dict[str, callable] = {}
        functions['dimensions'] = module.dimensions
        functions['precision'] = module.precision
        functions['distribution'] = module.distribution
        functions['generate_next'] = module.generate_next 
        functions['initialize'] = module.initialize
        functions['cool'] = module.cool
        functions['acceptance'] = module.acceptance_func
        functions['evaluate'] = module.evaluate

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
