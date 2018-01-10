import socket
import string
from random import choice
from pyhocon import ConfigFactory


def random_str(length):
    chars = string.ascii_letters + string.digits
    return ''.join(choice(chars) for x in range(length))


def internet_connectivity_available(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    Source: https://stackoverflow.com/a/33117579/2822762
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        print(ex.message)
        return False


def get_configs(conf_path):
    return ConfigFactory.parse_file(conf_path)
