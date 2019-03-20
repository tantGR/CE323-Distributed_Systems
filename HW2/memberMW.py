import socket
import struct
import os
import threading
import time
MANAGER_TCP_PORT = 0
TCP_PORT = 0
#grp_members = 0
members_dict = {}
manager = 0
JOIN = 6
LEAVE = 9
MY_ID = 0

def discoverManager(addr,port):
	global manager
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.settimeout(3)
	TTL = 1
	ttl = struct.pack('b', TTL)# ttl=1=local network segment
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

	message = struct.pack('!b',1) 

	try:
		while True:
			try:
				print("Discover: ", addr,port)
				sent = sock.sendto(message, (addr,port))
				data, manager = sock.recvfrom(16)
				(man_addr,man_port) = manager
				(MANAGER_TCP_PORT,) = struct.unpack('!I',data)
			except socket.timeout:
				print("No manager found\n")
			else:
				sock.close()
				return (man_addr,MANAGER_TCP_PORT)
	finally:
		sock.close()

class MyThread(threading.Thread):
	def __init__(self, funcToRun, threadID, name, *args):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self._funcToRun = funcToRun
		self._args = args#empty
	def run(self):
		self._funcToRun(*self._args)


def grp_join(name,addr,port,myid):
	global JOIN, LEAVE,members_dict, manager,MY_ID

	MY_ID = myid

	manager = discoverManager(addr,port)

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(manager)
	message = struct.pack('!IIII',JOIN,name,TCP_PORT,myid)
	sock.send(message)
	data = sock.recv(1024)# ack from manager
	(grp_members,) = struct.unpack('!I',data[0:4])
	data = data[4:]
	if grp_members == -1:
		print("Change your name!")
		return -1
	elif grp_members ==  1:
		(grp_port,) = struct.unpack('!I',data)
		print(grp_port)
		members_dict[grp_port] = [myid]  # or [myid]
	else:
		(grp_port,) = struct.unpack('!I',data[0:4])
		print(grp_port)
		data = data[4:]
		members_dict[grp_port] = []
		for i in range(grp_members):
			(member,) = struct.unpack('!I',data[0:4])
			data = data[4:]
			members_dict[grp_port].append(member)

	return grp_port

def grp_leave(gsock):
	global members_dict, manager, MY_ID
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(manager)

	message = struct.pack('!III',LEAVE,gsock,MY_ID)
	sock.send(message)
	sock.recv(1024)
	members_dict[gsock].remove(MY_ID)

#def grp_send(int gsock,void *msg, int len)

#def grp_recv(int gsock,int *type, void *msg,int *len, int block)

grp = grp_join(1,"224.0.0.7",2019,os.getpid())
print("[",os.getpid(),"] "," In group 1")
for m in members_dict:
	print(members_dict[m])

time.sleep(3)
print("Leaving")
grp_leave(grp)
for m in members_dict:
	print(members_dict[m])