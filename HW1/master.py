import serverMW as mw
import time
import struct
import sys

import socket

def ip2int(ip):
    return struct.unpack("!I",socket.inet_aton(ip))[0]

def int2ip(ip):
    return socket.inet_ntoa(struct.pack("!I",ip))


def Receive():
	global numOfSlaves,slaves,multicast_group,SVCID,buf,len

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	group = socket.inet_aton(multicast_group)
	mreq = struct.pack('4sL', group, socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	sock.bind(server_address)
	while True:
		print('\nMaster:waiting to receive message')
		data, (address,port) = sock.recvfrom(1024)
		(key,) = struct.unpack('!I', data[0:4])#data is a tuple 
		#data = data[4:]
		if key == 1995 : #discovery-client
			if numOfSlaves > 0:
				message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
				sent = sock.sendto(message,(address,port))#reply to the Discover Request
				print("Client, you found me!\n")
		elif key== 1999: #discovery-server
			slaves.append((address,port))
			numOfSlaves=numOfSlaves+1
			message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
			sent = sock.sendto(message,(address,port))#reply to the Discover Request
			print("Slave, you found me!\n")
		elif key == 1997: # o client kanei request.Proothise to ston swsto Slave
			[svcid,reqTosend,buf,len]=struct.unpack('!IbQQb',data)
			message = struct.pack('!sIIbQQb',1997, address,port,SVCID,reqTosend,buf,len)
			sent = sock.sendto(message,Slaves[0])
		else:
			continue



def main():
	multicast_group = "224.0.0.7"
	server_address = ('',2019)  
	numOfSlaves=0;slaves=[]
	SVCID = 50;buf = 0;len = 0 
	#bind to multicast
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	group = socket.inet_aton(multicast_group)
	mreq = struct.pack('4sL', group, socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	sock.bind(server_address)
	
	print("Waiting for clients or slave-servers...")
	while True:
		(data, (address,port)) = sock.recvfrom(1024)
		(key,) = struct.unpack('!I', data[0:4])#data is a tuple 
		#data = data[4:]
		if key == 1995 : #discovery-client
			if numOfSlaves > 0:
				message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
				sent = sock.sendto(message,(address,port))#reply to the Discover Request
				print("Client",(address,port), ", you found me!\n")
			else:
				print("Insufficient slaves\n")
		elif key == 1997: # Request client,forwarding to slave
			[key,svcid,reqTosend,buf,len]=struct.unpack('!IbQQb',data)
			message = struct.pack('!IQIbQQb',key, ip2int(address),port,SVCID,reqTosend,buf,len)
			sent = sock.sendto(message,slaves[0])#Forward to Slave
			message=struct.pack('!IQ',00000,reqTosend)
			sent = sock.sendto(message,(address,port))#ACK to Client
		elif key== 1999: #discovery-server
			slaves.append((address,port))
			numOfSlaves=numOfSlaves+1
			message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
			sent = sock.sendto(message,(address,port))#reply to the Discover Request
			print("Slave",(address,port), ", you found me!\n")
		else:
			continue


#	a = mw.register(SVCID)
#	if a == -1:
#		print("error with registration. Try again later.\n")
#		return
#	Recv = MyThread(Receive, 1, "Receive")#, threading.get_ident())#gia python2=threading.current_thread()
#	Recv.setDaemon(True)
#	Recv.start()
#	SVCID = svcid

	

if __name__ == "__main__":
	main()