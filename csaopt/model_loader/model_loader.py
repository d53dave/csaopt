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
    def __init__(self, conf, internal_conf) -> None:
        self.model_path = conf['model.path']

        model_name = conf.get('model.name', 'optimization_' + random_str(8))
        self.model_module: ModuleType = self._create_module(model_name,
                                                            self.model_path)

        functions: Dict[str, Callable] = self._extract_functions(self.model_module)
        errors: List[ValidationError] = []

        if not conf.get('model.skip_typecheck'):
            logger.debug('Skipping typecheck')
            typecheck_error = ModelValidator.validate_typing(self.model_path)
            if typecheck_error is not None:
                errors.append(typecheck_error)

        errors.extend(ModelValidator.validate_functions(functions))

        if len(errors) == 0:
            self.model = self._create_model(model_name, self.model_module, functions)
        else:
            logger.error('Validation failed for model `{}`: {}'.format(self.model_path, errors))

    def _create_model(self, name: str, module: Any, functions: Dict[str, Callable]) -> Model:
        return Model(name,
                     module.dimensions(),
                     module.precision(),
                     module.distribution(),
                     # The model is prepared for sending it to the workers
                     # and contains raw source instead of the real functions
                     {f_name: inspect.getsource(functions[f_name])
                      for f_name in functions.keys()})

    def _extract_functions(self, module: ModuleType) -> Dict[str, Callable]:
        functions: Dict[str, Callable] = {}

        for func in RequiredFunctions:
            functions[func.value] = module.__getattribute__(func.value)

        return functions

    def get_model(self) -> Model:
        if not self.model:
            raise RuntimeError('Model not yet loaded')
        return self.model

    def _create_module(self, name: str, file: str) -> ModuleType:
        module = imp.load_source(name, file)

        if module is None:
            raise AssertionError('Model could not be loaded.')

        return module
