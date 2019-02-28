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
SVCID = 50
TTL = 1
server_connected = 0
Req = 0;Repl=0;ids=0
def discover_servers():
    multicast_group = (MCAST_ADDR, '')
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #client.settimeout(3)

    ttl = struct.pack('b', TTL)# ttl=1=local network segment.
    client.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    try:
        message = struct.pack('!b',SVCID)
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
                return server
    finally:
        print('closing socket')
        client.close()

def next_req():
    for id in reqs_dict:
        if reqs_dict[id][4] == 0:
            return id
        elif with_ack == False: #and timeout
            return id 


def Requests():
    sent_reqs = 0

    print("requests\n")
    if server_connected==0:
        server_addr = discover_servers()
        server.socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        #lock
        sent_reqs +=1
        reqTosend = next_req()
        (svcid,buf,len,sent,with_ack,times_sent) = reqs_dict[sent_reqs]
        #unlock
        if sent == True:
            del reqs_dict[ids]
        else:
            times_sent += 1

            packet = struct.pack('!bbsb',svcid,sent_reqs,buf,len)#type of buf
            reqs_dict[sent_reqs] = (svcid,buf,len,sent,with_ack,times_sent)
            server.sendto(packet,server_addr)
            
    

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
    global Req,Repl,ids
    #Apothikefsi tou Request sto arxeio. Eggrafes tis morfis(reqid,svcid,buf,len,nlife)
    #if (saveInRequestFile(reqid,svcid,buf,len,nlife)==-1):
    #    return -1

    
    if not(Req != 0 and Repl!=0 and Req.isAlive() and Repl.isAlive()):
        Req = MyThread(Requests, 1, "Requests")
        Repl = MyThread(Replies, 2, "Replies")
        Req.start()
        Repl.start()
    ids += 1
    reqs_dict[ids] = (svcid,buf,len,False,False,0)#send,ack_received 
    
    return ids

def getReply(reqid, buf, len, block):
	print("popa") 