<<<<<<< HEAD
=======
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
nlife=0;
reqs_dict = {}
MCAST_ADDR = "224.0.0.7"
MCAST_PORT = 2019
SVCID = 50
TTL = 1
Req = 0;Repl=0;ids=0
timeout=2  
reqs_nack=0
new_reqs=0

dict_lock = threading.Lock()
sem=threading.Semaphore(0)


def discover_servers():
    multicast_group = (MCAST_ADDR, MCAST_PORT)
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #client.settimeout(3)https://wiki.python.org/moin/UdpCommunication

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
                print("timeout. No more responses\n")
                break
            else:
                #print("received %s from %s" % (data, server) )
                client.close()
                return server
    finally:
        #print('closing socket')
        client.close()

def next_req():
    if ids == 0:
        return -1
    for id in reqs_dict:
        if reqs_dict[id][4] == 0:
            return id
        elif with_ack == False: #and timeout
            return id 


def Requests():
    global new_reqs, reqs_nack
    server_addr = discover_servers()
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        if new_reqs == 0 and reqs_nack == 0:
            sem.acquire()
        with dict_lock: #LOCK AND UNLOCK IN THE END 
            reqTosend = next_req()
            if reqTosend == -1:
                continue #or use a semaphore(or signal) to know when ther is a new req 
            (svcid,buf,len,sent,with_ack,times_sent,timeout) = reqs_dict[reqTosend]
            if times_sent == 0:
                new_reqs -= 1
            #unlock

        if sent == True:
            del reqs_dict[ids]
        else:
            times_sent += 1
            packet = struct.pack('!Ibbsb',1997, svcid,reqTosend,buf,len)#type of buf "lakis"
            reqs_dict[reqTosend] = (svcid,buf,len,sent,with_ack,times_sent,timeout)
            server.sendto(packet,server_addr)
            



def Replies():
	return #print("replies\n")

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
    global Req,Repl,ids,new_reqs
    #Apothikefsi tou Request sto arxeio. Eggrafes tis morfis(reqid,svcid,buf,len,nlife)
    #if (saveInRequestFile(reqid,svcid,buf,len,nlife)==-1):
    #    return -1

    
    if not(Req != 0 and Repl!=0 and Req.isAlive() and Repl.isAlive()):
        Req = MyThread(Requests, 1, "Requests")
        Repl = MyThread(Replies, 2, "Replies")
        Req.start()
        Repl.start()

    with dict_lock:    #LOCK AND UNLOCK IN THE END
        ids += 1
        new_reqs += 1
        reqs_dict[ids] = (svcid,buf,len,False,False,0,timeout)#send,ack_received
        if new_reqs == 1:
            sem.release()
    return ids #isos to buf  prepei na einai se koini thesi sti mnimi



def getReply(reqid, buf, len, block):
	print("popa")
>>>>>>> christos
