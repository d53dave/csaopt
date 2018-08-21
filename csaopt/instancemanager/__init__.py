import ipaddress
import ujson

from typing import Union, Dict, Any

IpAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]


class Instance():
    """Cloud platform agnostic abstraction for an instance"""

    def __init__(self, inst_id: str, public_ip: str, port=-1, is_broker: bool=False, **props: Dict[str, Any]) -> None:
        self.public_ip = public_ip
        self.port: int = port
        self.inst_id: str = inst_id
        self.is_broker: bool = is_broker
        self.props: Dict[str, Any] = props

    @property
    def public_ip(self) -> IpAddress:
        return self._public_ip

    @public_ip.setter
    def public_ip(self, ip: str) -> None:
        self._public_ip = ipaddress.ip_address(ip)

    def __str__(self):
        return 'Instance[id={}, public_ip={}, broker={}, props={}'.format(
            self.inst_id, self.public_ip, 'True' if self.is_broker else 'False', ujson.dumps(self.props))
