import abc

from typing import List, Tuple, Any

from . import Instance

class InstanceManager(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def _provision_instances(self, timeout_ms, count=2, **kwargs) -> Tuple[Any, List[Any]]:
        """Start and configure instances, return queue and list of workers"""

    @abc.abstractmethod
    def _get_running_instances(self) -> Tuple[Instance, List[Instance]]:
        """Returns the currently managed instances"""

    @abc.abstractmethod
    def _terminate_instances(self, timeout_ms) -> None:
        """Terminate managed instances"""

    @abc.abstractmethod
    def _run_start_scripts(self, timeout_ms) -> None:
        """Run scripts to start queue and worker applications after startup"""

    @abc.abstractmethod
    def __enter__(self) -> None:
        """InstanceManager is a ContextManager"""
        # TODO: this must update configs

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Cleanup resources on exit"""
