import imp
import logging
import inspect

from types import ModuleType
from typing import Dict, List, Callable, Any

from . import ValidationError
from .model_validator import ModelValidator
from ..model import Model, RequiredFunctions
from ..utils import random_str

logger = logging.getLogger(__name__)


class ModelLoader():
    def __init__(self, conf, internal_conf, validator=ModelValidator()) -> None:
        self.model_path = conf['model.path']

        model_name = conf.get('model.name', 'optimization_' + random_str(8))
        self.model_module: ModuleType = self._create_module(model_name,
                                                            self.model_path)
        self.model: Model = None
        self.globals_token = internal_conf.get(
            'model.validation.globals_token', '# -- Globals')

        functions: Dict[str, Callable] = self._extract_functions(self.model_module)
        opt_globals = self._extract_globals(self.model_path)
        self.errors: List[ValidationError] = []

        if not conf.get('model.skip_typecheck'):
            logger.debug('Skipping typecheck')
            typecheck_error = validator.validate_typing(self.model_path)
            if typecheck_error is not None:
                self.errors.append(typecheck_error)

        self.errors.extend(validator.validate_functions(functions, internal_conf))

        if len(self.errors) == 0:
            self.model = self._create_model(model_name, self.model_module, opt_globals, functions)
        else:
            logger.error('Validation failed for model `{}`: {}'.format(self.model_path, self.errors))

    def _extract_globals(self, model_path: str) -> str:
        with open(model_path, 'r') as model_file:
            model_source_lines = model_file.read().splitlines()
            token_idxs = [idx for idx, line in enumerate(model_source_lines) if self.globals_token in line]
            if len(token_idxs) == 2 and token_idxs[0] != token_idxs[1]:
                begin, end = token_idxs
                return '\n'.join(model_source_lines[begin + 1:end])
        return ''

    def _create_model(self, name: str, module: Any, opt_globals: str, functions: Dict[str, Callable]) -> Model:
        return Model(name,
                     module.dimensions(),
                     module.precision(),
                     module.distribution(),
                     opt_globals,
                     # The model is prepared for sending it to the workers
                     # and contains raw source instead of the real python functions
                     {f_name: inspect.getsource(functions[f_name])
                      for f_name in functions.keys()})

    def _extract_functions(self, module: ModuleType) -> Dict[str, Callable]:
        functions: Dict[str, Callable] = {}

        for func in RequiredFunctions:
            functions[func.value] = module.__getattribute__(func.value)

        return functions

    def get_model(self) -> Model:
        return self.model

    def _create_module(self, name: str, file: str) -> ModuleType:
        module = imp.load_source(name, file)

        if module is None:
            raise AssertionError('Model could not be loaded.')

        return module
