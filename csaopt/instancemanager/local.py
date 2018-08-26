
import logging
import uuid
import time
import sys

from pyhocon import ConfigTree
from typing import Tuple, List, Any, Dict, Union, Type

from .instancemanager import InstanceManager
from . import Instance
from ..utils import get_free_tcp_port, random_str

log = logging.getLogger()


def _map_docker_to_instance(container, port=-1, is_broker: bool=False) -> Instance:
    return Instance(str(container.name), '127.0.0.1', port=port, is_broker=is_broker, **container.labels)


try:
    import docker
    DockerContainerT = Type[docker.models.containers.Container]
    docker_available = True
except ImportError:
    pass


class Local(InstanceManager[DockerContainerT]):
    def __init__(self, conf: ConfigTree, internal_conf: ConfigTree) -> None:
        if not docker_available:
            raise AssertionError(
                'Trying to instantiate Local InstanceManager, but docker-py is not available.')
        self.docker_client = docker.from_env()
        self.broker: DockerContainerT = None
        self.worker: DockerContainerT = None

        self.run_id = run_id = random_str(8)
        self.broker_container_name = 'CSAOpt-Broker-' + run_id
        self.worker_container_name = 'CSAOpt-Worker-' + run_id
        self.broker_port: int = get_free_tcp_port()
        self.debug_on_cpu = conf.get('debug.gpu_simulator')

    def _provision_instances(self, timeout_ms, count=2, **kwargs) -> Tuple[DockerContainerT, List[DockerContainerT]]:
        self.broker = self.docker_client.containers.run(
            'bitnami/redis',
            ports={'6379/tcp': kwargs['HOST_REDIS_PORT']},
            detach=True,
            # network=self.docker_network.name,
            environment={
                'ALLOW_EMPTY_PASSWORD': 'yes'
            },
            name=self.broker_container_name)

        broker_ip = ''

        while broker_ip is None or len(broker_ip.strip()) == 0:
            time.sleep(0.3)
            self.broker.reload()
            broker_ip = self.broker.attrs['NetworkSettings']['Networks']['bridge']['IPAddress']

        time.sleep(1.5)
        kwargs['REDIS_HOST'] = broker_ip

        self.worker = self.docker_client.containers.run(
            'd53dave/csaopt-worker',
            detach=True,
            # network=self.docker_network.name,
            environment=kwargs,
            labels={'queue_id': self.worker_container_name},
            name=self.worker_container_name)

        while self.broker.status != 'running' or self.worker.status != 'running':
            # TODO this needs to respect timeout
            time.sleep(1)
            self.broker, self.worker = self.__refresh_containers()

        return self.broker, [self.worker]

    def __refresh_containers(self) -> Tuple[DockerContainerT, DockerContainerT]:
        broker = self.docker_client.containers.get(self.broker_container_name)
        worker = self.docker_client.containers.get(self.worker_container_name)

        return broker, worker

    def get_running_instances(self) -> Tuple[Instance, List[Instance]]:
        """Returns the currently managed instances"""
        broker, worker = self.__refresh_containers()
        return (
            _map_docker_to_instance(
                broker, port=self.broker_port, is_broker=True),
            [_map_docker_to_instance(worker)]
        )

    def _terminate_instances(self, timeout_ms) -> None:
        self.worker.kill()
        self.broker.kill()
        self.worker.wait()
        self.broker.wait()

    def _run_start_scripts(self, timeout_ms) -> None:
        pass

    def __enter__(self) -> InstanceManager:
        try:
            # No broker password for the local, docker-driven case
            env: Dict[str, Union[str, int]] = {
                'REDIS_HOST': self.broker_container_name,
                'WORKER_QUEUE_ID': self.worker_container_name
            }

            if self.broker_port is not None:
                env['HOST_REDIS_PORT'] = self.broker_port

            if self.debug_on_cpu:
                env['NUMBA_ENABLE_CUDASIM'] = '1'

            self.docker_network = self.docker_client.networks.create(
                name='CSAOpt' + self.run_id)

            self.broker, workers = self._provision_instances(
                timeout_ms=10000, **env)
            self.worker = workers[0]

            return self
        except Exception as e:
            log.exception(
                'An exception occured while starting docker containers')
            raise SystemError(
                'An exception occured while starting docker containers: {}'.format(repr(e)))

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        try:
            # TODO replace warn with debug
            log.warn('Broker logs: \n' +
                     self.broker.logs().decode('utf-8'))
            log.warn('Worker logs: \n' +
                     self.worker.logs().decode('utf-8'))
            self._terminate_instances(timeout_ms=10000)
            self.docker_network.remove()
        except Exception as e:
            log.warn(
                'An exception occured while killing docker containers: ' + str(e))
        return False
