#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import struct
nlife=0;
reqid=0;
svcid=50;
reqs_dict = {}


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
    
    #Prosthiki sto dictionary
    reqs_dict[reqid]=(svcid,buf,len,nlife)     
        
    #Discover UDP Multicast()
    
    #Discovery apo ton Client
    
    
    print("reqid is: "+str(reqid)+"\n")
    
#    if not(Req != 0 and Repl!=0 and Req.isAlive() and Repl.isAlive()):
#        Req = MyThread(Requests, 1, "Requests")
#        Repl = MyThread(Replies, 2, "Replies")
#        Req.start()
#        Repl.start()
#    ids += 1
#    reqs_dict[ids] = (svcid,buf,len) 
#    return ids

def getReply(reqid, buf, len, block):
	print("popa") 