import re
from . import ip as ip_utils

def check_ssh_hostname_valid(hostname: str) -> bool:
    res = hostname.split("@")
    if len(res) != 2:
        return False
    return ip_utils.is_ip_valid(res[1])