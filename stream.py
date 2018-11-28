#!/usr/bin/env python
import datetime
import os
from io import BytesIO
import sys
import struct

def getPCR (data):
        filehandle = BytesIO(data)
        PacketHeader = readFile(filehandle, 0, 4)
        syncByte = (PacketHeader>>24)
        if (syncByte != 0x47):
            return False, 0.0
        PID = ((PacketHeader>>8) & 0x1FFF)
        if PID == 0x1FFF:
            return False, 0.0

        adaptation_fieldc_trl = ((PacketHeader>>4)&0x3)
        if (adaptation_fieldc_trl == 0x2)|(adaptation_fieldc_trl == 0x3):
            has, pcr_base = parseAdaptation_Field(filehandle,4)
            return has, pcr_base

        return False, 0.0
       



        
def readFile(filehandle, startPos, width):
    filehandle.seek(startPos,0)
    if width == 4:
        string = filehandle.read(4)
        if len(string) != 4:
            #raise IOError
            return 0
        return struct.unpack('>L',string[:4])[0]
    elif width == 2:
        string = filehandle.read(2)
        if len(string) != 2:
            #raise IOError
            return 0
        return struct.unpack('>H',string[:2])[0]
    elif width == 1:
        string = filehandle.read(1)
        if len(string) != 1:
            #raise IOError
            return 0
        return struct.unpack('>B',string[:1])[0]

def parseAdaptation_Field(filehandle, startPos):
    n = startPos
    flags = 0
    adaptation_field_length = readFile(filehandle,n,1)
    if adaptation_field_length > 0:
        flags = readFile(filehandle,n+1,1)
        PCR_flag = (flags>>4)&0x1
        if PCR_flag == 1:
            PCR1 = readFile(filehandle,n+2,4)
            PCR2 = readFile(filehandle,n+6,2)
            PCR_base = (PCR1<<1)+ ((PCR2>>15)&0x1)
            #PCR_ext = PCR2&0x1FF
            return True, PCR_base/90000.0

    return False, 0.0

if __name__ == '__main__':
    f = open('1.ts')
    while True:
        d = f.read(188)
        has, pcr = getPCR(d)
        if has:
            print pcr/90000.0
