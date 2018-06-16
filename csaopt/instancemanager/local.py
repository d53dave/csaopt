import logging 

from .instancemanager import InstanceManager
from . import Instance
from typing import Tuple, List, Any

logger = logging.getLogger()


class Local(InstanceManager):
    def __init__(self):
        try:
            import docker
        except:
            raise ImportError('docker-py required for local execution')
        self.instances: List[Instance] = []

    def _provision_instances(self, timeout_ms, count=2, **kwargs) -> Tuple[Any, Any]:
        """Start and configure instances, return queue and list of workers"""
        # TODO start instances with docker
        raise NotImplementedError

    def _get_running_instances(self) -> List[Instance]:
        """Returns the currently managed instances"""
        # TODO get docker instances and map to Instance
        raise NotImplementedError

    def _terminate_instances(self, timeout_ms) -> None:
        """Terminate managed instances"""
        # TODO docker kill
        raise NotImplementedError

    def _run_start_scripts(self, timeout_ms) -> None:
        """Run scripts to start queue and worker applications after startup"""
        # TODO Probably not applicable
        pass

    def __enter__(self) -> None:
        """InstanceManager is a ContextManager"""
        queue, worker = self._provision_instances(timeout_ms=1000, count=1)
        self.instances = [queue, worker]

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Cleanup resources on exit"""
        self._terminate_instances(timeout_ms=1000)
