#!/usr/bin/env python
import pat
import datetime
import os
from io import BytesIO
import sys
import struct
import qniu

class PROGRAM :

    CDN_URL = "http://videoa.southtv.cn"
    M3U8_HEADER = """#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-ALLOW-CACHE:YES\n#EXT-X-MEDIA-SEQUENCE:%d\n#EXT-X-TARGETDURATION:10"""
    M3U8_ITEM = "\n#EXTINF:%.3f,\n"
    M3U8_NAME = "live.m3u8"
    TMP_NAME = "live.m3u8.tmp"

    def __init__(self, program_number, gid):
        self.pat = pat.PAT()
        self.pat.set_prg_number(program_number)
        self.pnum = program_number
        #need to be setted
        self.pmt_pid = 0x1fff
        self.video_pid = 0x1fff
        self.audio_pid = 0x1fff
        self.segment = 0
        #millisecond
        self.last_pts = 0
        self.gid = gid
        #live-2018-10-20_20-10-22.ts
        #live-2018-10-20_20-10-32.ts
        #live-2018-10-20_20-10-42.ts
        self.ts_files = list()
        self.ts_fd = None
        self.ts_name = ""
        self.pmt_packet = None
        self.check_path()

    def check_path(self):
        if os.path.exists(self.gid) != True:
            os.mkdir(self.gid)

    def set_va_pids(self, video_pid, audio_pid):
        self.video_pid = video_pid
        self.audio_pid = audio_pid

    def set_pmt_pid(self, pmt_pid):
        self.pmt_pid = pmt_pid

    def __write_m3u8(self):
        m3u8_header = self.M3U8_HEADER%(self.segment)
        path = os.path.join(self.gid, self.TMP_NAME)
        dpath = os.path.join(self.gid, self.M3U8_NAME)
        with open(path, 'w') as fd:
            fd.write(m3u8_header)
            for ts, duration in self.ts_files[:5]:
                fd.write(self.M3U8_ITEM%(duration))
                url = os.path.join(self.CDN_URL, self.gid, ts)
                surl = qniu.Sign_URL(url)
                fd.write(surl)

        if len(self.ts_files) > 9:
            self.ts_files.pop(0)
            self.segment += 1

        os.rename(path, dpath)

    def write_psi(self):
        self.ts_fd.write(self.pat.get_output())
        self.ts_fd.write(self.pmt_packet)

    def write_va_ts(self, data, PTS, IDR):
        #the very first time
        if (IDR == True) & (self.ts_fd == None):
            now = datetime.datetime.now()
            self.ts_name = now.strftime("live-%Y-%m-%d_%H-%M-%S.ts")
            self.ts_fd = open(os.path.join(self.gid, self.ts_name), "wb")
            self.write_psi()
            self.ts_fd.write(data)
            self.last_pts = PTS
            return

        if ((IDR == True) & (PTS >= (self.last_pts + 90000 * 10))):
            duration = (PTS - self.last_pts) / 90000.0
            self.ts_fd.close()
            self.ts_files.append((self.ts_name, duration))
            print self.ts_files
            self.__write_m3u8()
            #new ts 
            now = datetime.datetime.now()
            self.ts_name = now.strftime("live-%Y-%m-%d_%H-%M-%S.ts")
            self.ts_fd = open(os.path.join(self.gid, self.ts_name), "wb")
            self.write_psi()
            self.ts_fd.write(data)
            self.last_pts = PTS
        elif self.ts_fd != None:
            self.ts_fd.write(data)

    def parse_PAT(self, data):
        #alread parsed PAT
        if self.pmt_pid != 0x1fff:
            return

        filehandle = BytesIO(data)
        PacketHeader = readFile(filehandle, 0, 4)
        syncByte = (PacketHeader>>24)
        if (syncByte != 0x47):
            return 
        payload_unit_start_indicator = (PacketHeader>>22)&0x1
        PID = ((PacketHeader>>8)&0x1FFF)
        if (PID != 0x0):
            return
       
        adaptation_fieldc_trl = ((PacketHeader>>4)&0x3)
        Adaptation_Field_Length = 0

        if (adaptation_fieldc_trl == 0x2)|(adaptation_fieldc_trl == 0x3):
            [Adaptation_Field_Length, flags] = parseAdaptation_Field(filehandle,n+4)
        if (adaptation_fieldc_trl == 0x1)|(adaptation_fieldc_trl == 0x3):
            PESstartCode = readFile(filehandle,Adaptation_Field_Length+4,4)
            if (((PESstartCode&0xFFFFFF00) != 0x00000100)& (payload_unit_start_indicator == 1)):
                pointer_field = (PESstartCode >> 24)
                k = Adaptation_Field_Length+4+1+pointer_field
                pmt_pid = parsePATSection(filehandle, k, self.pnum)
                if pmt_pid != 0x1fff:
                    self.pmt_pid = pmt_pid
                    self.pat.set_pmt_pid(pmt_pid)

    def parse_PMT(self, data):
        #alread parsed PAT
        if self.video_pid != 0x1fff:
            return
        filehandle = BytesIO(data)
        PacketHeader = readFile(filehandle,0,4)
        syncByte = (PacketHeader>>24)
        if (syncByte != 0x47):
            return 
        payload_unit_start_indicator = (PacketHeader>>22)&0x1
        PID = ((PacketHeader>>8)&0x1FFF)
        if (PID != self.pmt_pid):
            return
       
        adaptation_fieldc_trl = ((PacketHeader>>4)&0x3)
        Adaptation_Field_Length = 0

        if (adaptation_fieldc_trl == 0x2)|(adaptation_fieldc_trl == 0x3):
            [Adaptation_Field_Length, flags] = parseAdaptation_Field(filehandle,n+4)
        if (adaptation_fieldc_trl == 0x1)|(adaptation_fieldc_trl == 0x3):
            PESstartCode = readFile(filehandle,Adaptation_Field_Length+4,4)
            if (((PESstartCode&0xFFFFFF00) != 0x00000100)& (payload_unit_start_indicator == 1)):
                pointer_field = (PESstartCode >> 24)
                k = Adaptation_Field_Length+4+1+pointer_field
                self.video_pid, self.audio_pid = parsePMTSection(filehandle, k)
                if self.video_pid == 0x1fff:
                    self.video_pid = self.audio_pid

        self.pmt_packet = data

    def write_TS_Packet(self, data):
        #alread parsed PAT
        if self.video_pid == 0x1fff:
            return
        filehandle = BytesIO(data)
        PacketHeader = readFile(filehandle,0,4)
        syncByte = (PacketHeader>>24)
        if (syncByte != 0x47):
            return 
        payload_unit_start_indicator = (PacketHeader>>22)&0x1
        PID = ((PacketHeader>>8)&0x1FFF)
        PTS = self.last_pts
        IDR = False
        if (PID == self.video_pid):
            PESPktInfo = PESPacketInfo()
            adaptation_fieldc_trl = ((PacketHeader>>4)&0x3)
            Adaptation_Field_Length = 0
            if (adaptation_fieldc_trl == 0x2)|(adaptation_fieldc_trl == 0x3):
                [Adaptation_Field_Length, flags] = parseAdaptation_Field(filehandle,4)
            if Adaptation_Field_Length > 158:
                self.write_va_ts(data, PTS, IDR)
                return 
            if (adaptation_fieldc_trl == 0x1)|(adaptation_fieldc_trl == 0x3):
                if (payload_unit_start_indicator == 1):
                    PESstartCode = readFile(filehandle,Adaptation_Field_Length+4,4)
                    if ((PESstartCode&0xFFFFFF00) == 0x00000100):
                        parsePESHeader(filehandle, Adaptation_Field_Length+4, PESPktInfo)
                        if (self.video_pid == self.audio_pid):
                            PESPktInfo.setAUType("IDR")
                        if (PESPktInfo.getAUType() == "IDR"):
                            print "IDR"
                            IDR = True
                            if PTS  > PESPktInfo.PTS_lo:
                                self.last_pts = PESPktInfo.PTS_lo 
                            PTS = PESPktInfo.PTS_lo 
            self.write_va_ts(data, PTS, IDR)

        elif (PID == self.audio_pid):
            self.write_va_ts(data, PTS, IDR)


def parsePATSection(filehandle, k, pnum):

    local = readFile(filehandle,k,4)
    table_id = (local>>24)
    if (table_id != 0x0):
        print 'Ooops! error in parsePATSection()!'
        return 0x1fff

    print 'PAT:'
    section_length = (local>>8)&0xFFF

    transport_stream_id = (local&0xFF) << 8;
    local = readFile(filehandle, k+4, 4)
    transport_stream_id += (local>>24)&0xFF
    transport_stream_id = (local >> 16)
    version_number = (local>>17)&0x1F
    current_next_indicator = (local>>16)&0x1
    section_number = (local>>8)&0xFF
    last_section_number = local&0xFF;

    length = section_length - 4 - 5
    j = k + 8
    while (length > 0):
        local = readFile(filehandle, j, 4)
        program_number = (local >> 16)
        program_map_PID = local & 0x1FFF
        if (program_number == 0):
            #print 'program_number = 0x%X' %program_number
            #print 'network_PID = 0x%X' %program_map_PID
            pass
        elif (program_number == pnum):
            print 'program_number = %d' %program_number
            print 'program_map_PID = %d' %program_map_PID
            return program_map_PID 
        length = length - 4;
        j += 4
    return 0x1ffff

def parsePMTSection(filehandle, k):
    video_pid = 0x1fff
    audio_pid = 0x1fff
    local = readFile(filehandle,k,4)

    table_id = (local>>24)
    if (table_id != 0x2):
        print 'Ooops! error in parsePATSection()!'
        return

    print 'PMT:'
    section_length = (local>>8)&0xFFF
    program_number = (local&0xFF) << 8;
    local = readFile(filehandle, k+4, 4)
    program_number += (local>>24)&0xFF
    print 'program_number = %d' %program_number
    version_number = (local>>17)&0x1F
    current_next_indicator = (local>>16)&0x1
    section_number = (local>>8)&0xFF
    last_section_number = local&0xFF;
    local = readFile(filehandle, k+8, 4)
    PCR_PID = (local>>16)&0x1FFF
    program_info_length = (local&0xFFF)

    n = program_info_length
    m = k + 12;
    while (n>0):
        descriptor_tag = readFile(filehandle, m, 1)
        descriptor_length = readFile(filehandle, m+1, 1)
        n -= descriptor_length + 2
        m += descriptor_length + 2

    j = k + 12 + program_info_length
    length = section_length - 4 - 9 - program_info_length

    while (length > 0):
        local1 = readFile(filehandle, j, 1)
        local2 = readFile(filehandle, j+1, 4)
        stream_type = local1;
        elementary_PID = (local2>>16)&0x1FFF
        ES_info_length = local2&0xFFF

        print 'stream_type = 0x%X, elementary_PID = 0x%X' %(stream_type, elementary_PID)
        if stream_type == 0x1b:
            video_pid = elementary_PID 
        elif stream_type == 0x0f:
            audio_pid = elementary_PID 
        else:
            print 'Not Support stream type, Only support H264 AAC'
        #n = ES_info_length
        #m = j+5;
        #while (n>0):
            #descriptor_tag = readFile(filehandle, m, 1)
            #descriptor_length = readFile(filehandle, m+1, 1)
            #n -= descriptor_length + 2
            #m += descriptor_length + 2
        j += 5 + ES_info_length
        length -= 5 + ES_info_length
    return video_pid, audio_pid


        
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

class PESPacketInfo:
    def __init__(self):
        self.PTS_hi = 0
        self.PTS_lo = 0
        self.streamID = 0
        self.AUType = ""
    def setPTS(self, PTS_hi, PTS_lo):
        self.PTS_hi = PTS_hi
        self.PTS_lo = PTS_lo
    def getPTS(self):
        return self.PTS_hi, self.PTS_lo
    def setStreamID(self, streamID):
        self.streamID = streamID
    def setAUType(self, auType):
        self.AUType = auType
    def getStreamID(self):
        return self.streamID
    def getAUType(self):
        return self.AUType

def getPTS(filehandle, startPos):
    n = startPos
    time1 = readFile(filehandle,n,1)
    time2 = readFile(filehandle,n+1,2)
    time3 = readFile(filehandle,n+3,2)
    #PTS_hi = (time1>>3)&0x1
    #PTS_low = ((time1>>1)&0x3)<<30
    PTS_low = ((time1>>1)&0x7)<<30
    PTS_low += ((time2>>1)&0x7FFF)<<15
    PTS_low += ((time3>>1)&0x7FFF)

    #return PTS_hi, PTS_low
    return 0, PTS_low

def parseIndividualPESPayload(filehandle, startPos):

    n = startPos
    k = 0
    local = readFile(filehandle,n + k ,4)
    while((local&0xFFFFFFFF) != 0x00000165):
        k += 1;
        if (k > 100):
            return "non_IDR"
        local = readFile(filehandle,n+k,4)
    return "IDR"

def parsePESHeader(filehandle, startPos,PESPktInfo):
    n = startPos
    stream_ID = readFile(filehandle, n+3, 1)
    PES_packetLength = readFile(filehandle, n+4, 2)
    PESPktInfo.setStreamID(stream_ID)
    k = 6
    if ((stream_ID != 0xBC)& \
        (stream_ID != 0xBE)& \
        (stream_ID != 0xF0)& \
        (stream_ID != 0xF1)& \
        (stream_ID != 0xFF)& \
        (stream_ID != 0xF9)& \
        (stream_ID != 0xF8)):
        PES_packet_flags = readFile(filehandle, n+5, 4)
        PTS_DTS_flag = ((PES_packet_flags>>14)&0x3)
        PES_header_data_length = PES_packet_flags&0xFF

        k += PES_header_data_length + 3

        if (PTS_DTS_flag == 0x2):
            (PTS_hi, PTS_low) = getPTS(filehandle, n+9)
            PESPktInfo.setPTS(PTS_hi, PTS_low)
        elif (PTS_DTS_flag == 0x3):
            (PTS_hi, PTS_low) = getPTS(filehandle, n+9)
            PESPktInfo.setPTS(PTS_hi, PTS_low)
            (DTS_hi, DTS_low) = getPTS(filehandle, n+14)
        else:
            k = k
            return
        auType = parseIndividualPESPayload(filehandle, n+k)
        PESPktInfo.setAUType(auType)

#def parseAdaptation_Field(filehandle, startPos, PCR):
def parseAdaptation_Field(filehandle, startPos):
    n = startPos
    flags = 0
    adaptation_field_length = readFile(filehandle,n,1)
    if adaptation_field_length > 0:
        flags = readFile(filehandle,n+1,1)
        #PCR_flag = (flags>>4)&0x1
        #if PCR_flag == 1:
            #PCR1 = readFile(filehandle,n+2,4)
            #PCR2 = readFile(filehandle,n+6,2)
            #PCR_base_hi = (PCR1>>31)&0x1
            #PCR_base_lo = (PCR1<<1)+ ((PCR2>>15)&0x1)
            #PCR_ext = PCR2&0x1FF
            #PCR.setPCR(PCR_base_hi, PCR_base_lo, PCR_ext)
    return [adaptation_field_length + 1, flags]


if __name__ == '__main__':
    p = PROGRAM(0x460, "cctv1")
    f = open('m.ts')
    while True:
        d = f.read(188)
        #print f.tell()
        p.parse_PAT(d)
        p.parse_PMT(d)
        p.write_TS_Packet(d)
