import ipaddress

from typing import Union

IpAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]


class Instance():
    """Cloud Platform agnostic wrapper for an instance"""
    def __init__(self, public_ip: str, hosts_msgq: bool=False) -> None:
        self._public_ip = ipaddress.ip_address(public_ip)
        self._hosts_msgq = hosts_msgq

    @property
    def public_ip(self) -> IpAddress:
        return self._public_ip

    @public_ip.setter
    def public_ip(self, ip: str) -> None:
        self._public_ip = ipaddress.ip_address(ip)
