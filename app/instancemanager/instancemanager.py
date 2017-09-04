import requests
import random
import string
import abc


def _get_own_ip():
    return requests.get('https://api.ipify.org/').text


def _get_random_string(length=8):
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(length)])


class InstanceManager():
    def __init__(self):
        pass

    @abc.abstractmethod
    def _provision_instances(self, count=2, **kwargs):
        """Start and configure instances"""

    @abc.abstractmethod
    def _get_running_instances(self):
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
