#!/usr/bin/env python
import crc

class PAT(object):

    def __init__(self):
        self.data = [
    0x47, 0x40, 0x00, 0x10, 0x00,
    #/* PSI */
    0x00, 0xb0, 0x0d, 0x00, 0x01, 0xc1, 0x00, 0x00,
    #/* PAT */
    0x00, 0x01, 0xe0, 0x01,
    #/* CRC */
    0x2e, 0x70, 0x19, 0x05,
    #/* stuffing 167 bytes */
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]
        
    def set_prg_number(self, program_number):
        self.data[13] = (program_number >> 8) & 0xff
        self.data[14] = program_number & 0xff
        
    def set_pmt_pid(self, pmt_pid):
        h = (pmt_pid & 0x1fff) >> 8
        l = pmt_pid & 0xff
        self.data[15] = 0xe0 | h
        self.data[16] = l
        self.__CRC()

    def __CRC(self):
        crcd = crc.CRC("".join([chr(x) for x in self.data[5:17]]), 12)
        self.data[17] = (crcd >> 24) & 0xff
        self.data[18] = (crcd >> 16)  & 0xff
        self.data[19] = (crcd >> 8) & 0xff
        self.data[20] = crcd & 0xff

    def get_output(self):
        d = [chr(x) for x in self.data]
        return "".join(d)

if __name__ == '__main__':
    c = PAT()
    c.set_pmt_pid(0x490)
    open("t","w").write(c.get_output())
