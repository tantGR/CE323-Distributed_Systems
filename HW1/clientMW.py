#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import struct
import socket
import os
import signal
import sys
#from uuid import getnode as get_mac
import time

nlife=0;
reqs_dict = {}
MCAST_ADDR = "224.0.0.7"    
MCAST_PORT = 2020
SVCID = -1
TTL = 1
threads_exist = 0
Req = -2;Repl=-2;ids=0
TIMEOUT = 500000
new_reqs=0;reqs_nack=0
AT_MOST_N = 40
lost_packets = 0    #TODO change name
repls_dict = {}
dict_lock = threading.Lock()
shared_vars = threading.Lock() #lost_packets, reqs_nack, new_reqs
#news_req_lock = threading.Lock()# for changing or reading the var news_reqs
sem=threading.Semaphore(0)
receiver_sem = threading.Semaphore(0)
blocking_sem = threading.Semaphore(0)
#myclient={}
def ip2int(ip):
    return struct.unpack("!I",socket.inet_aton(ip))[0]

def int2ip(ip):
    return socket.inet_ntoa(struct.pack("!I",ip))

def discover_servers():
    global SVCID
    multicast_group = (MCAST_ADDR, MCAST_PORT)
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    client.settimeout(3)

    ttl = struct.pack('b', TTL)# ttl=1=local network segment.
    client.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    try:
        message = struct.pack('!Ib',1995,SVCID) 

        while True:
            #print("waiting to receive..\n")
            try:
                sent = client.sendto(message, multicast_group)
                data, server = client.recvfrom(16)
            except socket.timeout:
                print("No server found\n")
                #return -1
            else:
                #print("received %s from %s" % (data, server) )
                client.close()
                return server
    finally:
        #print('closing socket')
        client.close()

def next_req():
    global lost_packets, AT_MOST_N, new_reqs
    with shared_vars:
        if ids == 0:
            return -1
        for id in reqs_dict:
            reqs_dict[id][5] -= 1 #timeout
            if reqs_dict[id][4] == 0:    #times_sent
                return id
            elif reqs_dict[id][3] == False and reqs_dict[id][5] <= 0 and new_reqs==0: #and timeout kai an den iparxoun kainoyries
                return id
    return -1 

def Requests():
    global new_reqs, reqs_nack,myclient, lost_packets
    server_addr = discover_servers()
    receiver_sem.release()
    
    while True:
        with shared_vars:
            if new_reqs == 0 and reqs_nack ==0 and lost_packets > AT_MOST_N + 1:
                sem.acquire()
        with dict_lock: 
            reqTosend = next_req()
            if reqTosend == -1:
                continue     
            [svcid,buf,len,with_ack,times_sent,timeout] = reqs_dict[reqTosend]
            if times_sent == 0:
                with shared_vars:
                    new_reqs -= 1
                    reqs_nack += 1

        print("again")
        times_sent += 1
        timeout = TIMEOUT
        with shared_vars:
            lost_packets += 1      #sunolo apostolon (At most once)
            #print("Lost: ",lost_packets)
            if lost_packets > AT_MOST_N:
                print("server down")
                lost_packets = 0
                reqs_nack = 0
                with dict_lock:
                    for id in reqs_dict:
                        reqs_dict[id][3] = False       #with_ack
                        reqs_dict[id][4] = 0           #times_sent    
                        reqs_dict[id][5] = TIMEOUT    
                        server_addr = discover_servers()
                continue
        packet = struct.pack('!IbQQb',1997, svcid,reqTosend,buf,len)#type of buf
        reqs_dict[reqTosend] = [svcid,buf,len,with_ack,times_sent,timeout] # isos lock
        myclient.sendto(packet,server_addr)
            
def Replies():
    global myclient, reqs_nack, lost_packets
    receiver_sem.acquire()

    while True:
        data, address = myclient.recvfrom(1024)#receiver.recvfrom(1024)
        (key,) = struct.unpack('!I', data[0:4])
        data = data[4:]
        if key == 00000: #ack
            (id,) = struct.unpack('!Q',data)
            with dict_lock:
                reqs_dict[id][3] = True
                with shared_vars:
                    reqs_nack -= 1
                print("ack received[",id,"]")
        elif key == 11111:  #reply
            with shared_vars:
                lost_packets -= 1
            print("Reply received.[",id,"]")
            id,buf,len = struct.unpack('!Qsb',data)
            with dict_lock:
                del reqs_dict[id]
            repls_dict[id] = [buf,len] #dictionary me tis apantiseis pou irthan
            blocking_sem.release()



class MyThread(threading.Thread):
    def __init__(self, funcToRun, threadID, name, *args):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self._funcToRun = funcToRun
        self._args = args#empty
    def run(self):
        self._funcToRun(*self._args)


def saveInRequestFile(reqid,svcid,buf,len,nlife):
    try:
        # log file to write to
        reqsFile = r'reqsFile.txt'
        data = (reqid,svcid,buf,len,nlife)
        format_string = "%s,%s,%s,%s,%s\n"
        #print(format_string % data)

        #'a' means append at endOfFile 
        with open(reqsFile, 'a') as f:
            # write the new request and it's meta-data
            f.write(format_string % data)
    except IOError:
        print("Error writing at Request File.Exiting\n")
        return -1
     
    f.close()
    return 0

def sendRequest(svcid, buf, len):
    global Req,Repl,ids,new_reqs,threads_exist,myclient,SVCID
    
    if threads_exist==0:
        SVCID = svcid
        myclient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        Repl = MyThread(Replies, 1, "Replies")#, threading.get_ident())#gia python2=threading.current_thread()
        Req = MyThread(Requests, 2, "Requests")
        Req.setDaemon(True)
        Repl.setDaemon(True)
        Req.start()
        Repl.start()
        threads_exist = 1

    with dict_lock:    #LOCK AND UNLOCK IN THE END
        ids += 1
        millis = int(round(time.time() * 1000))
        uniqueID = int(str(millis) + str(os.getpid())  + str(ids))
        reqs_dict[uniqueID] = [svcid,buf,len,False,0,TIMEOUT]
        if new_reqs == 0:
            sem.release()
        with shared_vars:
            new_reqs += 1
    return uniqueID 


def getReply(reqid,block):

    if reqid in repls_dict:
        (buf,len) = repls_dict[reqid]
        return 1,buf,len    
    else:
        if block == False:
            return -1,-1,-1 #no reply available
        else:
            while reqid not in repls_dict:    
                blocking_sem.acquire()
            (buf,len) = repls_dict[reqid]

    return 1,buf,len 

def handler(sig,frame):
    sys.exit(0)
    return

signal.signal(signal.SIGINT,handler)

# remember TODO errors check!!!
#error check in app layer
#at most once, kill threads, arxeia, 
# server ping se clients
#diagrafi aitiseon apo palia zoi se server kai client
