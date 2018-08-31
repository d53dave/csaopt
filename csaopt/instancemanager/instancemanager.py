import abc

from typing import List, Tuple, Any, TypeVar, Generic

from . import Instance

T = TypeVar('T')


class InstanceManager(abc.ABC, Generic[T]):
    """Abstract class for the instance management performed by CSAOpt.

    This class provides calls that are usually required for privisioning and configuration of instances running broker
    or worker code. Per Python conventions, methods prefixed by an underscore are not meant to be public. They are
    here to make the developer think about what steps are usually required for a complete setup of cloud or docker
    instances. The public methods of this class are :meth:`~InstanceManager.get_running_instances` as well as it's
    context manager methods, `__enter__` and `__exit__`.
    """

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
        # This needs to return an InstanceManager, so the return Type should state the same.
        # However, Instancemanager cannot be referenced before the class has been evaluated.

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """Cleanup resources on exit"""
