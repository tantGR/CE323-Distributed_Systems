import socket
import struct
import os
import threading
import time
import queue

MANAGER_TCP_PORT = 0
multicast_addr = '224.0.0.6'
TCP_PORT = 12345 + os.getpid()
groups_dict = {}
manager = 0
JOIN = 6
LEAVE = 9
MY_ID = 0
threadsexist = -1
senderThr = -1
sender_sem = threading.Semaphore(0)
GRP_CHANGE = 12 #message for changes in group
APP_MSG = 21  # message from another member
MSG_LOSS = 13 # send multicast - lost a message
MSG_OK = 31 # message with data to send to group
received_msgs = {}
msgs_to_send = {}
send_lock = threading.Lock()
TIMEOUT = 4000
msg_num = 0
msgLists = {}

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

def TcpConnection():
	global TCP_PORT, groups_dict,GRP_CHANGE,msgList

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#sock.settimeout(5)
	sock.bind(('',TCP_PORT))
	sock.listen(1)

	while True:
		conn,addr = sock.accept()
		data = conn.recv(1024)
		(key,grpid,member) = struct.unpack('!III',data)
		ack = struct.pack('!b',1)
		conn.send(ack)
		if key == JOIN:
			groups_dict[grpid].append(member)
		elif key == LEAVE:
			groups_dict[grpid].delete(member)

		msgList[grpid].append((GRP_CHANGE,member,key,"")) #type,member,length/action,message_data
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
	global JOIN, LEAVE,groups_dict, manager,MY_ID,threadsexist

	MY_ID = myid

	manager = discoverManager(addr,port)

	#create thread for receiving from manager
	if threadsexist == -1:
		Thr1 = MyThread(TcpConnection,1,"TcpConnection")
		Thr1.setDaemon(True)
		Thr1.start()
		threadsexist = 1

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
		groups_dict[grp_port] = [myid] 
	else:
		(grp_port,) = struct.unpack('!I',data[0:4])
		print(grp_port)
		data = data[4:]
		groups_dict[grp_port] = []
		for i in range(grp_members):
			(member,) = struct.unpack('!I',data[0:4])
			data = data[4:]
			groups_dict[grp_port].append(member)

	return grp_port

def grp_leave(gsock):
	global groups_dict, manager, MY_ID
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(manager)

	message = struct.pack('!III',LEAVE,gsock,MY_ID)
	sock.send(message)
	sock.recv(1024)
	del groups_dict[gsock]

def next_msg():
	global msgs_to_send

	for msg in msgs_to_send:
		msgs_to_send[msg][6] -= 1 #timeout
		if msgs_to_send[msg][5] == False and msgs_to_send[msg][6] <= 0: #with ack, timeout
			return msg
		elif msgs_to_send[msg][4] == False: #sent
			return msg
		else:
			return -1

def Sender():
	global msgs_to_send,TIMEOUT,sender_sem,send_lock
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

	sender_sem.acquire()

	with send_lock:
		msgTosend = next_msg()
		[type,grp,len,msg,sent,with_ack,timeout] = msgs_to_send[msgTosend]

	timeout = TIMEOUT
	sent = True
	with_ack = False
	message = struct.pack('!IIIIs',type,msgTosend,len,MY_ID,data)
	msgs_to_send[msgTosend] = [type,grp,len,msg,sent,with_ack,timeout]
	sock.send(message,(multicast_addr,grp))

def grp_send(gsock,msg,len)
	global senderThr, msgs_to_send,msg_num,TIMEOUT,send_lock

	if senderThr == -1:
		Thr2 = MyThread(Sender,2,"Sender")
		Thr2.setDaemon(True)
		Thr2.start()
		senderThr = 1

	msg_num += 1	
	msgID = int(str(MY_ID) + str(msg_num))
	with send_lock:
		msgs_to_send[msgID] = (MSG_OK,gsock,len,msg,,False,False,TIMEOUT)#(message_type,group,length,message,sent,with_ack from group boss,timeout)


	sender_sem.release()	
	return 1

#def grp_recv(int gsock,int *type, void *msg,int *len, int block)
# return type,msg,len
grp = grp_join(1,"224.0.0.7",2019,os.getpid())
print("[",os.getpid(),"] "," In group 1")
for m in groups_dict:
	print(groups_dict[m])

time.sleep(3)
print("Leaving")
grp_leave(grp)
for m in groups_dict:
	print(groups_dict[m])

#sender thread
#read from mem
#send
