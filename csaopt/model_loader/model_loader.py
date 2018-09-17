import imp
import logging
import inspect

from types import ModuleType
from pyhocon import ConfigTree
from typing import Dict, List, Callable, Any, Optional

from . import ValidationError
from .model_validator import ModelValidator
from ..model import Model, RequiredFunctions
from ..utils import random_str

logger = logging.getLogger(__name__)


class ModelLoader():
    """Class responsible for loading the provided optimization model into the internal representation of a model.

    The input model is loaded as a python module. After validation, each function's source code is extracted and
    packed into a :class:`model.Model` object.

    Args:
        conf: Configuration of optimization run
        internal_conf: Internal CSAOpt Configuration
        validator: Instance of ModelValidator that should be used for validation
    """

    def __init__(self, conf: ConfigTree, internal_conf: ConfigTree, validator=ModelValidator()) -> None:
        self.model_path = conf['model.path']

        model_name = conf.get('model.name', 'optimization_' + random_str(8))

        # TODO: interpreting arbitrary code is a bad idea. This should, in the least,
        # do one pass of validation, maybe checking for forbidden keywords.
        self.model_module: ModuleType = self._create_module(model_name, self.model_path)
        self.globals_token = internal_conf.get('model.validation.globals_token', '# -- Globals')

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
        """Extracts the globals section from a model file

        Model files may have a globals section that will be carried over to the worker machines. This will be extracted here.
        """
        with open(model_path, 'r') as model_file:
            model_source_lines = model_file.read().splitlines()
            token_idxs = [idx for idx, line in enumerate(model_source_lines) if self.globals_token in line]
            if len(token_idxs) == 2 and token_idxs[0] != token_idxs[1]:
                begin, end = token_idxs
                return '\n'.join(model_source_lines[begin + 1:end])
        return ''

    def _create_model(self, name: str, module: ModuleType, opt_globals: str, functions: Dict[str, Callable]) -> Model:
        """Creates a :class:`model.Model` object containing all relevant information for an optimization run

        Args:
            name: Name of optimization
            module: Module containing the optimization functions that were provided by the user
            opt_globals: Global variables that should be available during optimization
            functions: Map of function name to function object of all required optimization functions

        Returns:
            Internal representation of a Model. Ready to be transmitted to the workers.
        """
        return Model(
            name,
            module.dimensions(),  # type: ignore
            module.precision(),  # type: ignore
            module.distribution(),  # type: ignore
            opt_globals,
            len(module.empty_state()),  # type: ignore
            # The model is prepared for sending it to the workers
            # and contains raw source instead of the real python functions
            {f_name: inspect.getsource(functions[f_name])
             for f_name in functions.keys()})

    def _extract_functions(self, module: ModuleType) -> Dict[str, Callable]:
        """Extracts required functions from the intermediate python module

        Args:
            module: Module into which the provided optimization functions were interpreted into

        Returns:
            Dictionary of function name to function object of all required functions
        """
        functions: Dict[str, Callable] = {}

        for func in RequiredFunctions:
            functions[func.value] = module.__getattribute__(func.value)

        return functions

    def get_model(self) -> Optional[Model]:
        try:
            return self.model
        except AttributeError:
            return None

    def _create_module(self, name: str, file: str) -> ModuleType:
        """Interprets a given file into a python module

        Args:
            name: Name of module to be created
            file: Path to file

        Returns:
            Python module that contains the interpreted code of the input file
        """
        module = imp.load_source(name, file)

        if module is None:
            raise AssertionError('Model could not be loaded.')

        return module
