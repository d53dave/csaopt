"""
This module offers the core CSAOpt modelling component: the :class:`~model.Model` class.
"""
import ujson

from enum import Enum
from typing import Dict, Any


class Precision(Enum):
    """Enum for available calculation precisions"""
    Float32 = 'float32'
    Float64 = 'float64'


class RandomDistribution(Enum):
    """Enum for available distributions of random values used during optimization"""
    Normal = 'normal'
    Uniform = 'uniform'


class RequiredFunctions(Enum):
    """Enum for required functions that a model has to provide"""
    Distribution = 'distribution'
    Precision = 'precision'
    Dimensions = 'dimensions'
    Initialize = 'initialize'
    GenerateNext = 'generate_next'
    Cool = 'cool'
    Evaluate = 'evaluate'
    Acceptance = 'acceptance_func'
    EmptyState = 'empty_state'


class Model:
    """Core class containing functions and parameters for optimization

    Args:
        name: Optimization name
        dimensions: Number of dimensions of optimization domain
        precision: Required precision
        distribution: Required distribution of random values that will be provided by CSAOpt to the optimization
        opt_globals: Global variables available during optimization
        functions: Functions modelling the domain

    Attributes:
        name: Optimization name
        dimensions: Number of dimensions of optimization domain
        precision: Required precision
        distribution: Required distribution of random values that will be provided by CSAOpt to the optimization
        opt_globals: Global variables available during optimization
        functions: Functions modelling the domain
    """

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        """
        Create model object from a dictionary (i.e. the serialized form)

        Args:
            d: Serialized model dictionary

        Returns:
            Model: A model object
        """
        assert 'distribution' in d
        assert 'precision' in d
        assert 'globals' in d
        assert 'functions' in d

        distribution: RandomDistribution = d['distribution']
        precision: Precision = d['precision']

        return Model(d['name'], d['dimensions'], precision.value, distribution.value, d.get('globals', {}),
                     d['functions'])

    def __init__(self, name: str, dimensions: int, precision: Precision, distribution: RandomDistribution,
                 opt_globals: str, functions: Dict[str, str]) -> None:
        self.name: str = name
        self.dimensions: int = dimensions
        self.distribution: RandomDistribution = distribution
        self.precision: Precision = precision
        self.globals: str = opt_globals
        self.functions: Dict[str, str] = functions

    def to_dict(self) -> Dict[str, Any]:
        """Serializes model to dictionary (e.g. for transmission to workers)

        Returns:
            Dictionary representation of model
        """
        return {
            'name': self.name,
            'dimensions': self.dimensions,
            'distribution': self.distribution.value,
            'precision': self.precision.value,
            'globals': self.globals,
            'functions': self.functions
        }

    def __repr__(self) -> str:
        return ujson.dumps(self, indent=4)
