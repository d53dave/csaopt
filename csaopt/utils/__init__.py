import socket
import string
import requests
import os
import logging

from typing import Optional
from random import choice, randint
from pyhocon import ConfigFactory
from pyhocon.config_tree import ConfigTree

log = logging.getLogger(__name__)


def docker_available() -> bool:
    try:
        import docker
        df = docker.from_env().df()
        return df is not None
    except Exception:
        return False


def is_pytest_run() -> bool:
    return os.environ.get('UNIT_TESTS') == '1'


def random_int(lower: int, upper: int) -> int:
    return randint(lower, upper)


def random_str(length: int) -> str:
    """
    Generates a random string using ascii letters and digits
    """
    chars = string.ascii_letters + string.digits
    return ''.join(choice(chars) for x in range(length))


def internet_connectivity_available(host: str = "8.8.8.8", port: int = 53, timeout_seconds: float = 3.0) -> bool:
    """
    Checks if internet connectivity is available.

    Default values opening connection to the Google DNS server at:
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    Source: https://stackoverflow.com/a/33117579/2822762
    """
    try:
        socket.setdefaulttimeout(timeout_seconds)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as e:
        log.exception('Exception in internet_connectivity_available()')
        return False


def get_configs(conf_path: str) -> Optional[ConfigTree]:
    """Parse a hocon file into a ConfigTree"""
    return ConfigFactory.parse_file(conf_path)


def get_free_tcp_port() -> Optional[int]:
    """Get a free tcp port from the OS"""
    try:
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.bind(('', 0))
        addr, port = tcp.getsockname()
        tcp.close()
        return port
    except Exception:
        log.exception('Exception in get_free_tcp_port()')
        return None


def clamp(min_val, val, max_val) -> float:
    return max(min_val, min(max_val, val))


class FakeCuda():
    def __init__(self):
        pass

    def jit(*args, **kwargs):
        def f(fun):
            return fun

        return f
