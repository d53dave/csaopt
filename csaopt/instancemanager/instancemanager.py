import abc

from typing import List

from . import Instance

class InstanceManager(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def _provision_instances(self, timeout_ms, count=2, **kwargs) -> List[str]:
        """Start and configure instances, return Ids"""

    @abc.abstractmethod
    def _get_running_instances(self) -> List[Instance]:
        """Returns the currently managed instances"""

    @abc.abstractmethod
    def _terminate_instances(self, timeout_ms) -> None:
        """Terminate managed instances"""

    @abc.abstractmethod
    def __enter__(self) -> None:
        """InstanceManager is a ContextManager"""

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Cleanup resources on exit"""
