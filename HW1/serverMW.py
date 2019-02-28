import socket
import struct 
import sys
import threading

multicast_group = "224.0.0.7"
server_address = ('',2019)
reqs_dict = {}

def Receiver():
	while True:
		print '\nwaiting to receive message'
		data, address = sock.recvfrom(1024)

		id = struct.unpack('!b',data)
		print id[0]
		if id[0] == SVCID:
			reply = "Yes it's me!"
		else:
			reply = "Not me!"	   
		print 'sending ack to', address
		sock.sendto(reply, address)


		
		






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


