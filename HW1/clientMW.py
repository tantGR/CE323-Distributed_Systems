#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import struct
import socket
nlife=0;
reqid=0;
reqs_dict = {}
repls_dict= {}  #{'reqid',(buf,len)} buf = true/false len =1(nomizo)
MCAST_ADDR = "224.0.0.7"
MCAST_PORT = 2019
SVCID = 50
TTL = 1
reqs_nack = 0 #num of requests for which we have bot recieved ack yet (CS)!!
server_connected = 0
timeout = 2

dict_lock = threading.Lock()

def discover_servers():
    multicast_group = (MCAST_ADDR, '')
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    client.settimeout(10)

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
                print("No server found\n")
                return -1
            else:
                print("received %s from %s" % (data, server) )
                return server
    finally:
        print 'closing socket'
        client.close()

def next_req():
    for id in reqs_dict:
        reqs_dict[id][5] -=1
        if reqs_dict[id][4] == 0:
            return id
        elif with_ack == False and reqs_dict[id][5] <= 0: #and timeout
            return id
        else:
            return -1    


def Requests():
    sent_reqs = 0

    print("requests\n")
    if server_connected==0:
        server_addr = discover_servers()
        server.socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    while True:
        with dict_lock:         #LOCK AND UNLOCK IN THE END
            sent_reqs +=1
            reqTosend = next_req()
            if reqTosend == -1:
                continue      #or use a semaphore(or signal) to know when ther is a new req 
            (svcid,buf,len,sent,with_ack,times_sent,timeout) = reqs_dict[sent_reqs]

        if sent == True:
            del reqs_dict[ids]
        else:
            times_sent += 1
            reqs_nack += 1 #(CS)
            timeout = 10
            packet = struct.pack('!bbsb',svcid,sent_reqs,buf,len)#type of buf
            reqs_dict[sent_reqs] = (svcid,buf,len,sent,with_ack,times_sent,timeout)
            server.sendto(packet,server_addr)
            
    

def Replies():
	print("replies\n")
    server.socket.socket(sock.AF_INET, socket.SOCK_DGRAM)
    server.bind(server_addr)




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
    with dict_lock:    #LOCK AND UNLOCK IN THE END
        ids += 1
        reqs_dict[ids] = (svcid,buf,len,False,False,0,timeout)#send,ack_received 
    return ids          #isos to buf  prepei na einai se koini thesi sti mnimi

def getReply(reqid, buf, len, block):
    
    if reqid in repls_dict:
        #epestrepse tin apantisi - se koini thesi sti mnimi
    else:
        if block == False:
            return 0 #no reply available
        else:
            #block
            while reqid not in repls_dict:    #isos, alla oxi poli kalo
                sleep(2)
            


# remember TODO errors check!!!