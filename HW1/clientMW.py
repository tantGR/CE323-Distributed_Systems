#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##### allages poy ekana ####
# 0) sxolia se merika simeia
# 1) evgala to server_connected apo global se local variable
# 2) an connected, to vala = 1
# 3) stin 67, allaksa tin seira tou sent++. Prepei apo miden na ksekina
# 4) stin 47(next_req() ), prepei na xoume ena while(1).Episis prepei na kratame mia
# static metavliti, wste na nai dikaio to search sto dictionary 
# 5) an times_sent > MAX_TIMEOUT, tote, del[reqid]
# 6) sto pack() to format einai sigoura swsto?!
# 7) prosthiki semaphores
import threading
import struct
import socket
import os
nlife=0;
reqs_dict = {}
MCAST_ADDR = "224.0.0.7"    
MCAST_PORT = 2019
SVCID = 50
TTL = 1
threads_exist = 0
Req = -2;Repl=-2;ids=0
TIMEOUT = 1000000
reqs_nack=0
new_reqs=0
AT_MOST_N = 10000
all_sents = 0    #TODO change name
repls_dict = {}
my_addr = 0
dict_lock = threading.Lock()
sem=threading.Semaphore(0)
receiver_sem = threading.Semaphore(0)
blocking_sem = threading.Semaphore(0)
#myclient={}
def ip2int(ip):
    return struct.unpack("!I",socket.inet_aton(ip))[0]

def int2ip(ip):
    return socket.inet_ntoa(struct.pack("!I",ip))

def discover_servers():
    multicast_group = (MCAST_ADDR, MCAST_PORT)
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #client.settimeout(3)

    ttl = struct.pack('b', TTL)# ttl=1=local network segment.
    client.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    try:
        message = struct.pack('!Ib',1995,SVCID) 
        sent = client.sendto(message, multicast_group)

        while True:
            #print("waiting to receive..\n")
            try:
                data, server = client.recvfrom(16)
            except socket.timeout:
                print("No server found\n")
                return -1
            else:
                #print("received %s from %s" % (data, server) )
                client.close()
                return server
    finally:
        #print('closing socket')
        client.close()

def next_req():
    if ids == 0 or all_sents >= AT_MOST_N:
        return -1
    for id in reqs_dict:
        reqs_dict[id][5] -= 1 #timeout
        if reqs_dict[id][4] == 0:    #times_sent
            return id
        elif reqs_dict[id][3] == False and reqs_dict[id][5] <= 0 and new_reqs==0: #and timeout kai an den iparxoun kainoyries
            return id
    return -1 

def Requests():
    global new_reqs, reqs_nack, all_sents, my_addr,myclient
    server_addr = discover_servers()

    #my_addr = socket.getnameinfo(socket.gethostbyname(socket.gethostname()),)
    receiver_sem.release()
    


    while True:
        if new_reqs == 0 and reqs_nack == 0:
            sem.acquire()
        with dict_lock: #LOCK AND UNLOCK IN THE END 
            reqTosend = next_req()
            if reqTosend == -1:
                continue    #or use a semaphore(or signal) to know when ther is a new req 
            [svcid,buf,len,with_ack,times_sent,timeout] = reqs_dict[reqTosend]
            if times_sent == 0:
                new_reqs -= 1
                reqs_nack += 1

        times_sent += 1
        timeout = TIMEOUT
        all_sents += 1      #sunolo apostolon (At most once)
        packet = struct.pack('!IbQib',1997, svcid,reqTosend,buf,len)#type of buf
        reqs_dict[reqTosend] = [svcid,buf,len,with_ack,times_sent,timeout] # isos lock
        myclient.sendto(packet,server_addr)



            
def Replies():
    global myclient
    receiver_sem.acquire()

    while True:
        data, address = myclient.recvfrom(1024)#receiver.recvfrom(1024)
        (key,) = struct.unpack('!I', data[0:4])
        data = data[4:]
        if key == 00000: #ack
            (id,) = struct.unpack('!Q',data)
            with dict_lock:
                print(id)
                reqs_dict[id][3] = True
                del reqs_dict[id]
                reqs_nack -= 1
                print("ack received")
        elif key == 11111:  #reply
            print("Reply received.")
            id,buf,len = struct.unpack('!Qsb',data)
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
    global Req,Repl,ids,new_reqs,threads_exist,myclient
    #Apothikefsi tou Request sto arxeio. Eggrafes tis morfis(reqid,svcid,buf,len,nlife)
    #if (saveInRequestFile(reqid,svcid,buf,len,nlife)==-1):
     #   return -1
    
    if threads_exist==0:
        myclient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        Repl = MyThread(Replies, 1, "Replies")
        Req = MyThread(Requests, 2, "Requests")
        Req.start()
        Repl.start()
        threads_exist = 1

    with dict_lock:    #LOCK AND UNLOCK IN THE END
        ids += 1
        uniqueID = int(str(ip2int(socket.gethostbyname(socket.gethostname()))) + str(os.getpid())  + str(ids))
        new_reqs += 1
        reqs_dict[uniqueID] = [svcid,buf,len,False,0,TIMEOUT]#send,ack_received
        if new_reqs == 1:
            sem.release()
    return uniqueID #isos to buf  prepei na einai se koini thesi sti mnimi


def getReply(reqid,block):
    if reqid in repls_dict:
        (buf,len) = repls_dict[reqid]
        return 1,buf,len    
    else:
        if block == False:
            return -1 #no reply available
        else:
            while reqid not in repls_dict:    #isos, alla oxi poli kalo
                blocking_sem.acquire()
            (buf,len) = repls_dict[reqid]

    return buf,len 

# remember TODO errors check!!!
#error check in app layer
#at most once, kill threads, arxeia, 
# server ping se clients
#diagrafi aitiseon apo palia zoi se server kai client