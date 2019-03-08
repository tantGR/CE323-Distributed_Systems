import serverMW as mw
import time
import struct
import sys
SVCID = 50
buf = 0
len = 0 
multicast_group = "224.0.0.7"
server_address = ('',2019)  


def SendToServers()

def Receive():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	group = socket.inet_aton(multicast_group)
	mreq = struct.pack('4sL', group, socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	sock.bind(server_address)
	while True:
		print('\nMaster:waiting to receive message')
		data, address = sock.recvfrom(1024)
		(key,) = struct.unpack('!I', data[0:4])#data is a tuple 
		data = data[4:]
		if key == 1995 : #discovery-client
			if numOfSlaves > 0:
				message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
				sent = sock.sendto(message,address)#reply to the Discover Request
				print("Client, you found me!\n")
		elif key== 1999: #discovery-server
			slaves.append(address)
			message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
			sent = sock.sendto(message,address)#reply to the Discover Request
			print("Slave, you found me!\n")
		elif key == 1997: # o client kanei request.Proothise to ston swsto Slave
			#steile ston slave ta stoixeia tou client
			print(type(address[0]))
			print(type(address[1]))
			message = struct.pack('!iis',address[0],address[1],data)
			#forwarding packet
			sent = sock.sendto(message,Slaves[0])




		else:
			continue


	while True:
	
			
		elif key == 1997: #request, send ACK
			[svcid,ID,buf,len] = struct.unpack('!bQQb',data)
			sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			message = struct.pack('!IQ',00000,ID) #ack 11111 reply
			sent = sender.sendto(message,address)
			reqs += 1
			with dict_lock: 
				reqs_dict[ID] = [buf,len,address,False]# [buf,len,client_address,served] 
				print("Request ",ID," arrived\n")
		elif key == 1999: #slave-server joins
			pass
		#	pass
		#	nslaves=nslaves+1
		#	slaves.append(address)
		#elif key == 2001: #slave-server returns data
		#	pass
		else:
			continue

def SendToServers():



def main():
	a = mw.register(SVCID)
	if a == -1:
		print("error with registration. Try again later.\n")
		return
	myclient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	Recv = MyThread(Replies, 1, "Receive")#, threading.get_ident())#gia python2=threading.current_thread()
	Snd = MyThread(Requests, 2, "SendToServers")
	Req.setDaemon(True)
	Repl.setDaemon(True)
	Req.start()
	Repl.start()
	threads_exist = 1
	SVCID = svcid

	

if __name__ == "__main__":
	main()