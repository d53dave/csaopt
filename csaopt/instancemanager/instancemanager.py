import abc

from typing import List, Tuple, Any, TypeVar, Generic

from . import Instance


T = TypeVar('T')


class InstanceManager(abc.ABC, Generic[T]):
    def __init__(self):
        pass

    @abc.abstractmethod
    def _provision_instances(self, timeout_ms, count=2, **kwargs) -> Tuple[T, List[T]]:
        """Start and configure instances, return queue and list of workers"""

    @abc.abstractmethod
    def get_running_instances(self) -> Tuple[Instance, List[Instance]]:
        """Returns the currently managed instances"""

    @abc.abstractmethod
    def _terminate_instances(self, timeout_ms) -> None:
        """Terminate managed instances"""

    @abc.abstractmethod
    def _run_start_scripts(self, timeout_ms) -> None:
        """Run scripts to start queue and worker applications after startup"""

    @abc.abstractmethod
    def __enter__(self):
        """InstanceManager is a ContextManager"""
        # This needs to return an InstanceManager, so the return Type should state the same
        # However, Instancemanager cannot be referenced before the class has been evaluated

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """Cleanup resources on exit"""
