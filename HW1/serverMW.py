import socket
import struct 
import sys

multicast_group = "224.0.0.7"
server_address = ('',2019)
SVCID = 50

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
#sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
sock.bind(server_address)



while True:
	print '\nwaiting to receive message'
	data, address = sock.recvfrom(1024)

	#print 'received %s bytes from %s' % (len(data), address)
	#print data 
	id = struct.unpack('!b',data)
	print id[0]
	if id[0] == SVCID:
		reply = "Yes it's me!"
	else:
		reply = "Not me!"	   
	print 'sending acknowledgement to', address
	sock.sendto(reply, address)

