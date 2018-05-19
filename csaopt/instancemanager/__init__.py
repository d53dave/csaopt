import ipaddress

from typing import Union, Dict, Any

IpAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]


class Instance():
    """Cloud platform agnostic abstraction for an instance"""
    def __init__(self, inst_id: str, public_ip: str, is_message_queue: bool=False, **props: Dict[str, Any]) -> None:
        self._public_ip: IpAddress = ipaddress.ip_address(public_ip)
        self.inst_id: str = inst_id
        self.is_message_queue: bool = is_message_queue
        self.props: Dict[str, Any] = props

    @property
    def public_ip(self) -> IpAddress:
        return self._public_ip

    @public_ip.setter
    def public_ip(self, ip: str) -> None:
        self._public_ip = ipaddress.ip_address(ip)