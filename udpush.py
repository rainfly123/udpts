#!/usr/bin/env python
import json
import os
import sys
import daemon
import subprocess
import socket
import random
import select
import socket
import stream
import daemon
import traceback
import argparse
import time

class UDPSender(object):
    def __init__(self, handle):
        self.Startime = time.time()
        self.PCRtime = 0.0
        self.handle = handle

    def setPCR(self, PCR):
        if PCR <= self.PCRtime:  #file seek to the begining
            self.PCRtime = PCR
            self.Startime = time.time()
        elif self.PCRtime == 0.0:  #the very first time
            self.PCRtime = PCR
            self.Startime = time.time()

    def needSleep(self, PCR):
        PCRduration = PCR - self.PCRtime
        duration = time.time() - self.Startime
        if PCRduration < duration:
            return 0
        else:
           return PCRduration - duration
 
    def worker(self, skt, dest):
        while True:
            data = self.handle.read(188)
            if len(data) < 188:
                #read error ,seek to the beginning
                self.handle.seek(0, 0) 
                return -1
            else:
                has, PCR = stream.getPCR(data)
                if has:
                    self.setPCR(PCR)
                    howlong = self.needSleep(PCR)
                    time.sleep(howlong)
                skt.sendto(data, dest)

  
def OpenSocket(port):
    server = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    server.setblocking(False)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR  , 1)
    server_address = ('0.0.0.0', port)
    server.bind(server_address)
    return server
  


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--port', required=True, type=int, help="Destination Server's Port")
    parser.add_argument('-d','--dest', required=True, type=str, help="Destination Server's IP Address")
    parser.add_argument('-f','--files', required=True, type=str, help="Input Files's Name", nargs="*")
    parser.add_argument('-b','--daemon', help="go backround", action="store_true")
    args = parser.parse_args()

    if args.daemon:
        daemon.daemonize("/tmp/udpush.pid")

    print args.dest, args.port, args.files, args.daemon

    skt = OpenSocket(args.port + 1)
    dest = (args.dest, args.port)
    senders = []
    for filename in args.files: 
        try:
            f = open(filename, "rb")
            sender = UDPSender(f)
            senders.append(sender)
        except:
            print "open file error"
            sys.exit(0)

    while True: 
        for s in senders: 
            val = s.worker(skt, dest)
            if val < 0 :
                continue
         

    #data = s.recv(1316)
    #if data :
    #packet = len(data) / 188
    #for chan in multi_channels[sock_port]:
