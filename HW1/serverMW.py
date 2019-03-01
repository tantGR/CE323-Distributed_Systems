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
	print('\nwaiting to receive message')
	data, address = sock.recvfrom(1024)
	print('received %s bytes from %s' % (len(data), address))

	data = struct.unpack('!b',data)#data is a tuple
	print("tuple size is "+str(len(data)))
	print("data received from are: "+str(len(data)))
	if len(data)==1 and data[0] == SVCID:#we sent only SVCID in discovery
		print("Yes it's me!(Discovery mode)\n")
		ttl = struct.pack('b', 1)# ttl=1=local network segment.
		server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		server.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
		message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
		sent = server.sendto(message,address)#reply to the Discover Request

	elif len(data)==4 and data[0] ==SVCID: #normal packet. Send more data now
		print("Yes its me!(Communication mode)\n") 
		sock.sendto(reply, address)
	else:
		reply = print("Not me!\n")	  


	#afto gia kanonika paketa. Twra mono to discovery
	#(svcid,sent_reqs,buf,len) = struct.unpack('!bbsb',data)#type of buf
	#print("data received from "+address+" are: "+buf)

	#print('sending acknowledgement to', address)
	#sock.sendto(reply, address)

