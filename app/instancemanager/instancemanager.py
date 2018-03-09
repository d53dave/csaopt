import requests
import random
import string
import abc

from typing import List

from . import Instance

class InstanceManager():
    def __init__(self):
        pass

    @abc.abstractmethod
    def _provision_instances(self, count=2, **kwargs):
        """Start and configure instances"""

    @abc.abstractmethod
    def _get_running_instances(self) -> List[Instance]:
        """Returns the currently managed instances"""

    @abc.abstractmethod
    def _terminate_instances(self):
        """Terminate managed instances"""

    @abc.abstractmethod
    def __enter__(self):
        """InstanceManager is a ContextManager"""

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        """Cleanup resources on exit"""
