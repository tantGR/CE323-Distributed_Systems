import serverMW as mw
import time
import struct
import sys

import socket

def ip2int(ip):
    return struct.unpack("!I",socket.inet_aton(ip))[0]

def int2ip(ip):
    return socket.inet_ntoa(struct.pack("!I",ip))

def calculateLoad(buf):

	#isws thelei sundiasmo megethous arithmou kai arithmou requests stin apothiki
	if buf%2 == 0:
		return 1
	else:
		count = 0
		while (buf > 0):
			buf = buf//10.
			count = count + 1.
	return int(count)
	

	
def main():
	multicast_group = "224.0.0.7"
	server_address = ('',2019)  
	SVCID = 50;buf = 0;len = 0 
	#bind to multicast
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	group = socket.inet_aton(multicast_group)
	mreq = struct.pack('4sL', group, socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	sock.bind(server_address)
	
	#manipulate network traffic
	print("Waiting for clients or slave-servers...")
	curr_load=0
	curr_slaves = 0
	numOfSlaves=0
	slaves=[]
	MAX_LOAD=10
	while True:
		(data, (address,port)) = sock.recvfrom(1024)
		(key,) = struct.unpack('!I', data[0:4])#data is a tuple 
		#data = data[4:]
		print("Current Load: ",curr_load,".Num of slaves running: ",curr_slaves)
		if key == 1995 : #discovery-client
			if numOfSlaves > 0:
				message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
				sent = sock.sendto(message,(address,port))#reply to the Discover Request
				print("Client",(address,port), ", you found me!")
			else:
				print("Insufficient slaves")

		elif key == 1997: # Request client.Increase load and forward to Slave-Server
			[key,svcid,reqTosend,buf,len]=struct.unpack('!IbQQb',data)
			curr_load = curr_load + calculateLoad(buf)
			if curr_load > curr_slaves*MAX_LOAD:#energopoihse slave
				curr_slaves = curr_slaves+1


			message = struct.pack('!IQIbQQb',key, ip2int(address),port,SVCID,reqTosend,buf,len)
			sent = sock.sendto(message,slaves[curr_slaves-1])#Forward to Slave
		elif key== 1999: #discovery-server
			slaves.append((address,port))
			numOfSlaves=numOfSlaves+1
			

			message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
			sent = sock.sendto(message,(address,port))#reply to the Discover Request
			print("Slave",(address,port), ", you found me!")
		elif key==2001:#Reduce load
			[key,load] = struct.unpack('!IQ',data)
			curr_load = curr_load - load
			if curr_load<(curr_slaves-1)*MAX_LOAD:#apenergopoihse slave
				curr_slaves = curr_slaves-1


		else:
			continue


if __name__ == "__main__":
	main()