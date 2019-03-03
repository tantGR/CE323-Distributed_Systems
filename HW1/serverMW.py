import socket
import struct 
import sys
import threading

multicast_group = "224.0.0.7"
server_address = ('',2019)  
Receiver = 0

repls_dict = {}
reqs_dict = {}
reqs = 0

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
		#print('received %s bytes from %s' % (len(data), address))

		(key,) = struct.unpack('!I', data[0:4])#data is a tuple 
		print (key)
		data = data[4:]
		if key == 1995: #discovery
			message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
			sent = sock.sendto(message,address)#reply to the Discover Request
			print("You found me!\n")
		elif key == 1997: #request
			[svcid,ID,buf,len] = struct.unpack('!bQsb',data)
			#send ack
			sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
			sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
			message = struct.pack('!b',int("ACK"))
			address = 
			sent = sender.sendto(message,address)
			reqs += 1
			repls_dict[ID] = [buf,len] 
			print("Request ",ID," arrived\n")

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

#def Sender():
#send reply

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