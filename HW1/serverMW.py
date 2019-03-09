import socket
import struct 
import sys
import threading
import time

 
Rcv = 0
Snd = 0

repls_dict = {}
reqs_dict = {}
reqs = 0
new_repls = threading.Semaphore(0)
dict_lock = threading.Lock()
reply_lock=threading.Lock()
svcid=50

def discover_master():
	global myserver
	TTL = 1
	multicast_group = ("224.0.0.7", 2019)
	#client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	#client.settimeout(2)
	#ttl = struct.pack('b', TTL)# ttl=1=local network segment.
	#client.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
	try:
		message = struct.pack('!I',1999)
		while True:
			#print("waiting to receive..\n")
			try:
				sent = myserver.sendto(message, multicast_group)
				data, server = myserver.recvfrom(16)
			except socket.timeout:
				print("No server found\n")
				#return -1
			else:
				#client.close()
				return server
	finally:
		#print('closing socket')
		pass


def ip2int(ip):
    return struct.unpack("!I",socket.inet_aton(ip))[0]

def int2ip(ip):
    return socket.inet_ntoa(struct.pack("!I",ip))



def Receiver():
	global reqs,myserver,reqs_dict,svcid

	print('\nwaiting to receive message')
	while True:
		data, _ = myserver.recvfrom(1024)
		(key,) = struct.unpack('!I', data[0:4])#data = data[4:]#data is a tuple 
		if key == 1997 and svcid==50: #request, send ACK
			[key, address,port,svcid,ID,buf,len] = struct.unpack('!IQIbQQb',data)
			address=int2ip(address)#address.decode()
			message=struct.pack('!IQ',00000,ID)
			sent = myserver.sendto(message,(address,port))#ACK to Client
			with dict_lock:
				reqs_dict[ID] = [address,port,buf,len,False]#false is not serviced
				reqs += 1
		else:
			continue

def Sender():
	global new_repls,repls_dict,myserver,reply_lock

	#repls_dict[reqid] = [address,port,buf,len,False]
	while True:
		new_repls.acquire()		
		#isws thelei lock()
		id=-1
		found=False
		with reply_lock:
			for id in repls_dict:
				if repls_dict[id][4] == False:
					[address,port,buf,len,status] = repls_dict[id]
					repls_dict[id][4] = True
					message = struct.pack('!IQsb',11111,id,buf,len)
					myserver.sendto(message,(address,port))
					found=True
					break
			if id != -1 and found == True:
				del repls_dict[id]


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
	global Rcv,Snd,myserver
	#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	#group = socket.inet_aton(multicast_group)
	#mreq = struct.pack('4sL', group, socket.INADDR_ANY)
	#sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	#sock.bind(server_address)
	myserver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	discover_master()

	Snd = MyThread(Sender,1,"Sender")
	Rcv = MyThread(Receiver,2,"Receiver")
	Snd.start()
	Rcv.start()

	return 1 

	
#def unregister(svcid):
def getRequest(svcid):
	global reqs,reqs_dict,dict_lock

	if reqs == 0:
		return -1,-1,-1
	else:
		with dict_lock: 
			for id in reqs_dict:#reqs_dict[ID] = [address,port,buf,len,False]
				if reqs_dict[id][4] == False:
					reqs_dict[id][4] = True
					buf=reqs_dict[id][2]
					len=reqs_dict[id][3]
					return id,buf,len
	return -1,-1,-1

def sendReply(reqid,buf,len):
	global repls_dict,new_repls,dict_lock,reply_lock
	#overwrite some data before releasing

	[address,port,_,_,_]=reqs_dict[reqid]
	with reply_lock:
		repls_dict[reqid] = [address,port,buf,len,False]


	new_repls.release()
	with dict_lock:
		del reqs_dict[reqid]

	
