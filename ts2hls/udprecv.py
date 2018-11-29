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
  
inputs = list()
excepts = list()
timeout = 30
channels = list()
multi_channels = dict()

def OpenServer(port):
    server = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    server.setblocking(False)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR  , 1)
    server_address = ('0.0.0.0', port)
    server.bind(server_address)
    return server
  


if __name__ == '__main__':

    if len(sys.argv) <= 1:
        print "Usage:\n ",sys.argv[0], "use configuration file"
        print "For Example:"
        print " %s channels.cfg"%(sys.argv[0])
        sys.exit(0);


    cfg = sys.argv[1]
    data = ""
    with open(cfg, "r") as files:
        lines = files.readlines()
        data = "".join(lines)

    daemon.daemonize("/tmp/udprecv.pid")
    os.chdir("/data") 

    all_config = json.loads(data)
    port = all_config["udp"]
    for channel in all_config["channels"]:
        number = channel['program_number'] 
        print  number
        gid = channel['channel'] 
        print  channel
        p = stream.PROGRAM(number, gid)
        channels.append(p)
        cport = number + 10000
        multi_channels[cport] = [p]
        inputs.append(OpenServer(cport))

    multi_channels[port] = channels
    inputs.append(OpenServer(port))

    while True:
        try:
            excepts = inputs
            readable , writable , exceptional = select.select(inputs, [], excepts, timeout)
  
            if not (readable or exceptional) :
                continue;   

            for s in readable:
                data = s.recv(188)
                sock_port = s.getsockname()[1]
                if data :
                    for chan in multi_channels[sock_port]:
                        chan.parse_PAT(data)
                        chan.parse_PMT(data)
                        chan.write_TS_Packet(data)
                else:
                    s.close()
                    inputs.remove(s)
                    inputs.append(OpenServer(sock_port))

            for s in exceptional:
                sock_port = s.getsockname()[1]
                s.close()
                inputs.remove(s)
                inputs.append(OpenServer(sock_port))

        except Exception:
            f = open("/tmp/erro", "a")
            traceback.print_exc(file=f)
            f.close()

