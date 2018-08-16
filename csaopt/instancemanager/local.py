
import logging
import uuid

from pyhocon import ConfigTree
from typing import Tuple, List, Any

from .instancemanager import InstanceManager
from . import Instance

logger = logging.getLogger()


def __map_docker_to_instance(container, is_broker: bool=False) -> Instance:
    return Instance(str(container.id), 'localhost', is_broker=is_broker, props=container.labels)


class Local(InstanceManager):
    def __init__(self, conf: ConfigTree, internal_conf: ConfigTree) -> None:
        try:
            import docker
        except:
            raise ImportError('docker-py required for local execution')
        self.docker_client = docker.from_env()
        self.redis: docker.models.Container = None
        self.worker: docker.models.Container = None
        self.run_id = uuid.uuid4()

    def _provision_instances(self, timeout_ms, count=2, **kwargs) -> Tuple[Any, List[Any]]:
        redis = self.docker_client.containers.run(
            'bitnami/redis', detach=True, labels={'csaopt_run': str(self.run_id)})
        worker = self.docker_client.containers.run(
            'd53dave/csaopt-worker', detach=True, environment=kwargs, labels={'csaopt_run': str(self.run_id)})

        return redis, [worker]

    def __refresh_containers(self) -> Tuple[Any, Any]:
        redises = self.docker_client.list(filters={'label': 'csaopt_run=' + str(self.run_id),
                                                   'ancestor': 'bitnami/redis'})
        workers = self.docker_client.list(filters={'label': 'csaopt_run=' + str(self.run_id),
                                                   'ancestor': 'd53dave/csaopt-worker'})

        assert len(redises) == 1 and len(workers) == 1
        return redises[0], workers[0]

    def get_running_instances(self) -> Tuple[Instance, List[Instance]]:
        """Returns the currently managed instances"""
        redis, workers = self.__refresh_containers()
        return __map_docker_to_instance(redis, is_broker=True), [__map_docker_to_instance(workers[0])]

    def _terminate_instances(self, timeout_ms) -> None:
        self.worker.kill()
        self.redis.kill()

    def _run_start_scripts(self, timeout_ms) -> None:
        pass

    def __enter__(self) -> None:
        """InstanceManager is a ContextManager"""

        self.redis, workers = self._provision_instances(timeout_ms=10000)
        self.worker = workers[0]

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Cleanup resources on exit"""
        self._terminate_instances(timeout_ms=10000)
