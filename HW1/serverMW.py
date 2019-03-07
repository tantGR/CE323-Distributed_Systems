import socket
import struct 
import sys
import threading
import time

multicast_group = "224.0.0.7"
server_address = ('',2019)  
Rcv = 0
Snd = 0

repls_dict = {}
reqs_dict = {}
reqs = 0
new_repls = threading.Semaphore(0)
dict_lock = threading.Lock()


def int2ip(ip):
    return socket.inet_ntoa(struct.pack("!I",ip))



def Receiver():
	global reqs
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	group = socket.inet_aton(multicast_group)
	mreq = struct.pack('4sL', group, socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	sock.bind(server_address)

	while True:
		print('\nwaiting to receive message')
		data, address = sock.recvfrom(1024)
		#print(address)
		#print('received %s bytes from %s' % (len(data), address))

		(key,) = struct.unpack('!I', data[0:4])#data is a tuple 
		print (key)
		data = data[4:]
		if key == 1995: #discovery
			message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
			sent = sock.sendto(message,address)#reply to the Discover Request
			print("You found me!\n")
		elif key == 1997: #request, send ACK
			[svcid,ID,buf,len] = struct.unpack('!bQQb',data)
			#print("buffer: ",type(buf))
			#send ack
			sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			message = struct.pack('!IQ',00000,ID) #ack 11111 reply
			sent = sender.sendto(message,address)
			reqs += 1
			with dict_lock: 
				reqs_dict[ID] = [buf,len,address,False]# [buf,len,client_address,served] 
				print("Request ",ID," arrived\n")
		else:
			continue

def Sender():
	sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	while True:
		new_repls.acquire()		
		for id in repls_dict:
			if repls_dict[id][2] == False:
				buf,len,sent = repls_dict[id]
				repls_dict[id][2] = True
				message = struct.pack('!IQsb',11111,id,buf,len)
				sender.sendto(message,reqs_dict[id][2])			


class MyThread(threading.Thread):
	def __init__(self, funcToRun, threadID, name, *args):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self._funcToRun = funcToRun
		self._args = args#empty
	def run(self):
		self._funcToRun(*self._args)

def register(svcid):
	global Rcv,Snd
	#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	#group = socket.inet_aton(multicast_group)
	#mreq = struct.pack('4sL', group, socket.INADDR_ANY)
	#sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	#sock.bind(server_address)

	Snd = MyThread(Sender,1,"Sender")
	Rcv = MyThread(Receiver,2,"Receiver")
	Snd.start()
	Rcv.start()

	return 1 

	
#def unregister(svcid):
def getRequest(svcid):
	if reqs == 0:
		return -1,-1,-1
	else:
		with dict_lock: 
			for id in reqs_dict:
				if reqs_dict[id][3] == False:
					reqs_dict[id][3] = True
					buf = reqs_dict[id][0]
					len = reqs_dict[id][1]
					return id,buf,len
	return -1,-1,-1

def sendReply(reqid,buf,len):
	repls_dict[reqid] = [buf,len,False]#sent
	new_repls.release()
