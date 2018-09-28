"""
This module provides the necessary functionality to provision instances for use with CSAOpt.

Instances can be either local, docker-based containers or proper cloud instances. The module offers a abstract base
class :class:`instancemanager.InstanceManager` from which actual instance managers need to inherit.
"""

import ipaddress
import json

from typing import Union, Dict, Any

IpAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]


class Instance():
    """Platform agnostic abstraction for an instance

    Args:
        inst_id: An instance identifier
        public_ip: IPv4 IP Address
        port: Port associated with this instance, e.g. Redis
        is_broker: Flag distinguishing broker or worker instance
        kwargs: Any other keyword arguments will be passed to an internal `props` field
    """

    def __init__(self, inst_id: str, public_ip: str, port=-1, is_broker: bool = False,
                 **kwargs: Dict[str, Any]) -> None:
        self.public_ip = public_ip
        self.port: int = port
        self.inst_id: str = inst_id
        self.is_broker: bool = is_broker
        self.props: Dict[str, Any] = kwargs

    @property
    def public_ip(self) -> IpAddress:
        """
        Public Ip property
        """
        return self._public_ip

    @public_ip.setter
    def public_ip(self, ip: str) -> None:
        self._public_ip = ipaddress.ip_address(ip)

    def __str__(self):
        return 'Instance[id={}, public_ip={}, broker={}, props={}'.format(self.inst_id, self.public_ip, 'True'
                                                                          if self.is_broker else 'False',
                                                                          json.dumps(self.props))
