#!/usr/bin/env python
from ctypes import cdll

lib = cdll.LoadLibrary('./libcrc.so')

def CRC(data, size):
    crc = lib.crc(data, size)
    return crc

if __name__ == '__main__':
    print hex(CRC(chr(0x47), 1))
    print hex(CRC(chr(0x47), 1))
