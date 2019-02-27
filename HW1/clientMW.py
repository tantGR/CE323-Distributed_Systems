#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import struct
import socket
nlife=0;
reqid=0;
reqs_dict = {}
MCAST_ADDR = "224.0.0.7"
MCAST_PORT = 2019
TTL = 1

def discover_servers():
    #message = "Hello from client! Lalis is laughing with you!"
    multicast_group = (MCAST_ADDR, MCAST_PORT)
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #client.settimeout(3)

    ttl = struct.pack('b', TTL)# ttl=1=local network segment.
    client.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    try:
        print'sending "%s"' % message
        sent = client.sendto(message, multicast_group)

        while True:
            print("waiting to receive..\n")
            try:
                data, server = client.recvfrom(16)
            except socket.timeout:
                print("timeout. No more responses\n")
                break
            else:
                print("received %s from %s" % (data, server) )
    finally:
        print 'closing socket'
        client.close()

def Requests():
    
    print("requests\n") 
    
    

def Replies():
	print("replies\n")

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
        print(format_string % data)

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
	#global ids, Repl, Req, reqs_dict
    
    #Apothikefsi tou Request sto arxeio. Eggrafes tis morfis(reqid,svcid,buf,len,nlife)
    if (saveInRequestFile(reqid,svcid,buf,len,nlife)==-1):
        return -1

    
    #TODO: Steile sto 1o Thread Requests kai sto 2o ta replies
    #req_t = MyThread(Requests, 1, "Requests")
    #rep_t = MyThread(Replies, 2, "Replies")
    

    print("reqid is: "+str(reqid)+"\n")
    
    if not(Req != 0 and Repl!=0 and Req.isAlive() and Repl.isAlive()):
        Req = MyThread(Requests, 1, "Requests")
        Repl = MyThread(Replies, 2, "Replies")
        Req.start()
        Repl.start()
    ids += 1
    reqs_dict[ids] = (svcid,buf,len) 
    return ids

def getReply(reqid, buf, len, block):
	print("popa") 