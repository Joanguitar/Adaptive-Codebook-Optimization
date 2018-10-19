"""Helper Functions.
"""

import re
import struct

def mac_addr_to_bytearray(addr):
    rx = re.compile('([0-9a-fA-F]+)\:([0-9a-fA-F]+)\:([0-9a-fA-F]+)\:' +
                    '([0-9a-fA-F]+)\:([0-9a-fA-F]+)\:([0-9a-fA-F]+)')
    if not rx.match(addr):
        raise AttributeError('Not a valid MAC Address %s' % addr)
    addr_exp = rx.findall(addr)[0]
    addr_hex = struct.pack(
        "BBBBBB", int(addr_exp[0], 16),
        int(addr_exp[1], 16), int(addr_exp[2], 16),
        int(addr_exp[3], 16), int(addr_exp[4], 16),
        int(addr_exp[5], 16))
    return bytearray(addr_hex)

def mac_addr_to_int(addr):
    mac = mac_addr_to_bytearray(addr)
    return int.from_bytes(mac, 'little')