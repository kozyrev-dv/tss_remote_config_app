import re

def is_ip_valid(ip: str) -> bool: 
    if (re.fullmatch("(\d{1,3}\.){3}\d{1,3}", ip) is None):
        return False
    res = list(filter(lambda x: int(x) in range(0, 256), ip.split(".")))
    return len(res) == 4

def generate_ip_list(ip_start: str, ip_last: str):
    """IP list generator"""
    _ip_start = int("".join(["{:02X}".format(int(x)) for x in ip_start.split(".")]), base=16)
    _ip_last  = int("".join(["{:02X}".format(int(x)) for x in ip_last.split(".") ]), base=16)

    for ip_int in range(_ip_start, _ip_last + 1):
        ip = "{:08X}".format(ip_int)
        ip = [int(ip[0:2], base=16), int(ip[2:4], base=16), int(ip[4:6], base=16), int(ip[6:8], base=16)]
        if (
            ip[0] in [0, 1, 255] or 
            ip[1] in [0, 1, 255] or 
            ip[2] in [0, 1, 255] or 
            ip[3] in [0, 1, 255]
        ):
            continue
        yield ".".join(map(str,ip))