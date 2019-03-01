import socket
import struct 
import sys
import threading

multicast_group = "224.0.0.7"
<<<<<<< HEAD
server_address = ('',2019)
reqs_dict = {}

def Receiver():
	while True:
		print '\nwaiting to receive message'
		data, address = sock.recvfrom(1024)
=======
server_address = ('',2019)  
Receiver = 0

repls_dict = {}
>>>>>>> christos

		id = struct.unpack('!b',data)
		print id[0]
		if id[0] == SVCID:
			reply = "Yes it's me!"
		else:
			reply = "Not me!"	   
		print 'sending ack to', address
		sock.sendto(reply, address)

<<<<<<< HEAD

		
		
=======
	#afto gia kanonika paketa. Twra mono to discovery
	#(svcid,sent_reqs,buf,len) = struct.unpack('!bbsb',data)#type of buf
	#print("data received from "+address+" are: "+buf)

	#print('sending acknowledgement to', address)
	#sock.sendto(reply, address)
def Receiver():
>>>>>>> christos

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	group = socket.inet_aton(multicast_group)
	mreq = struct.pack('4sL', group, socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	sock.bind(server_address)

<<<<<<< HEAD




def Sender():


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
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	group = socket.inet_aton(multicast_group)
	mreq = struct.pack('4sL', group, socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	sock.bind(server_address)
	
	Sender = MyThread(Sender,1,"Sender")
	Receiver = MyThread(Receiver,2,"Receiver")

	return 1

#def unregister(svcid):


#def getRequest(svcid,buf,len):




#def sendReply(reqid,buf,len):

register(3)

=======
	while True:
		print('\nwaiting to receive message')
		data, address = sock.recvfrom(1024)
		#print('received %s bytes from %s' % (len(data), address))

		(key,) = struct.unpack('!I', data[4:])#data is a tuple 
		#print("tuple size is "+str(len(data)))
		#print("data received from are: "+str(len(data)))
		if key == 1995:
			message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
			sent = sock.sendto(message,address)#reply to the Discover Request
			print("You found me!\n")
		elif key == 1997:
			(svcid,reqid,buf,len) = struct.unpack('!bbsb',data)
			print("Request ",reqid," arrived!\n")
		else:
			continue
	#	if len(data)==1 and data[0] == SVCID:#we sent only SVCID in discovery
	#		print("Yes it's me!(Discovery mode)\n")
	#		ttl = struct.pack('b', 1)# ttl=1=local network segment.
			#server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
			#server.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
			#message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
	#		sent = server.sendto(message,address)#reply to the Discover Request
	#	else:
	#		reply = print("Not me!\n")
>>>>>>> christos

#def Sender():

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
	global Receiver
	#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	#group = socket.inet_aton(multicast_group)
	#mreq = struct.pack('4sL', group, socket.INADDR_ANY)
	#sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	#sock.bind(server_address)

	#Sender = MyThread(Sender,1,"Sender")
	Receiver = MyThread(Receiver,2,"Receiver")
	Receiver.start()

	return 1 
#def unregister(svcid):

#def getRequest(svcid,buf,len):

#def sendReply(reqid,buf,len):

register(50)