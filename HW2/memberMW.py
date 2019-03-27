import socket
import struct
import os
import threading
import time

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
block_rcv = threading.Semaphore(0)
GRP_CHANGE = 12 #message for changes in group - mw->app
APP_MSG = 21  # message from another member      mw->app
MSG_LOSS = 13 # send multicast - lost a message     member->member
SEQ_NUM = 33 # seq number from boss
GROUP_MSG = 31 # message with data to send to group   meber->member 
received_msgs = {}
msgs_to_send = {}
send_lock = threading.Lock()
TIMEOUT = 4000
msg_num = 0
lists_lock = threading.Lock()
msgLists = {}
BOSS = False
global_seq = 0

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
	global TCP_PORT, groups_dict,GRP_CHANGE,msgLists

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
		with lists_lock:	
			msgLists[grpid].append((GRP_CHANGE,member,key,"")) #type,member,length/action,message_data
class MyThread(threading.Thread):
	def __init__(self, funcToRun, threadID, name, *args):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self._funcToRun = funcToRun
		self._args = args#empty
	def run(self):
		self._funcToRun(*self._args)

def Receiver(port):
	global multicast_addr, received_msgs, global_seq,msgs_to_send, MY_ID, GROUP_MSG,MSG_LOSS,SEQ_NUM,block_rcv

	global_seq = 0
	last_seq_num = 0

	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
	group = socket.inet_aton(multicast_addr)
	mreq = struct.pack('4sL',group,socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,mreq)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind((multicast_addr,port))

	while True:
		data,addr = sock.recvfrom(1024)

		(type,msgID,len,senderID) = struct.unpack('!IIII',data[0:16])#len->length or seq_num or 0
		msg = data[16:]
		if type == GROUP_MSG:         # message with data from a member
			if msgID in received_msgs and BOSS == False:   # if seq_num received earlier - inform dictionary
				received_msgs[msgID][0] = len
				received_msgs[msgID][1] = msg
				received_msgs[msgID][3] = senderID
			else:         #new message
				received_msgs[msgID] = [len,msg,-1,senderID]#len,data,seq_num,sender
			if BOSS == True:
				if msgID not in received_msgs:
					received_msgs[msgID] = [len,msg,-1,senderID]      
					global_seq += 1 
					received_msgs[msgID][2] = global_seq
					message = struct.pack('!IIII',SEQ_NUM,msgID,global_seq,0)+"".encode() # send seq_num to group members
					sock.sendto(message,(multicast_addr,port))
				else:
					#print(received_msgs[msgID][2])
					message = struct.pack('!IIII',SEQ_NUM,msgID,received_msgs[msgID][2],0)+"".encode() # send seq_num to group members
					sock.sendto(message,(multicast_addr,port))
		elif type == MSG_LOSS:
			if msgID in msgs_to_send:   #if it is mine send again
				[type,grp,len,msg,sent,with_ack,timeout] = msgs_to_send[msgID]
				message = struct.pack('!IIII',type,msgID,len,MY_ID)+msg
				sock.sendto(message,addr)
		elif type == SEQ_NUM:
			received_seq = len
			if msgID in msgs_to_send:
				msgs_to_send[msgID][5] = True
			if msgID not in received_msgs:   #if message not received
				received_msgs[msgID] = [0,"",received_seq,0]
			else:                 #if message received earlier
				received_msgs[msgID][2] = received_seq
				if received_seq == (last_seq_num + 1):
					member = received_msgs[msgID][3]
					length = received_msgs[msgID][0]
					data = received_msgs[msgID][1]
					msgLists[port].append((APP_MSG,member,length,data))
					block_rcv.release()
					del received_msgs[msgID]
					last_seq_num = received_seq
					#send_ready_msgs()

def grp_join(name,addr,port,myid):
	global JOIN, LEAVE,groups_dict, manager,MY_ID,threadsexist,BOSS,msgLists

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
		BOSS = True
	else:
		(grp_port,) = struct.unpack('!I',data[0:4])
		print(grp_port)
		data = data[4:]
		groups_dict[grp_port] = []
		for i in range(grp_members):
			(member,) = struct.unpack('!I',data[0:4])
			data = data[4:]
			groups_dict[grp_port].append(member)

	msgLists[grp_port] = []
	Thr3 = MyThread(Receiver,3,"Receiver",grp_port) 
	Thr3.setDaemon(True)
	Thr3.start() # start receiver
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
	global msgs_to_send,TIMEOUT,sender_sem,send_lock,multicast_addr
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

	sender_sem.acquire()

	while True:
		with send_lock:
			msgTosend = next_msg()
			if msgTosend == -1:
				continue
			else:
				[type,grp,len,msg,sent,with_ack,timeout] = msgs_to_send[msgTosend]

		timeout = TIMEOUT
		sent = True
		with_ack = False
		print(msg,"@")
		message = struct.pack('!IIII',type,msgTosend,len,MY_ID) + msg
		msgs_to_send[msgTosend] = [type,grp,len,msg,sent,with_ack,timeout]
		sock.sendto(message,(multicast_addr,grp))

def grp_send(gsock,msg,len):
	global senderThr, msgs_to_send,msg_num,TIMEOUT,send_lock

	if senderThr == -1:
		Thr2 = MyThread(Sender,2,"Sender")
		Thr2.setDaemon(True)
		Thr2.start()
		senderThr = 1

	msg_num += 1	
	msgID = int(str(MY_ID) + str(msg_num))
	with send_lock:
		msgs_to_send[msgID] = [GROUP_MSG,gsock,len,msg,False,False,TIMEOUT] #(message_type,group,length,message,sent,with_ack,timeout)
	sender_sem.release()	
	return 1

def grp_recv(gsock,block):
	global msgLists, block_rcv

	if block == False:
		with lists_lock:
			if gsock not in msgLists or len(msgLists[gsock]) == 0:
				return -1,-1,-1,-1
			else:
				message = msgLists[gsock][0] #message = (type,member,action/length,msg)
				del msgLists[gsock][0]
				return message
	else:
		if gsock not in msgLists or len(msgLists[gsock]) == 0:
			block_rcv.acquire()
		with lists_lock:
			message = msgLists[gsock][0] #message = (type,member,action/length,msg)
			del msgLists[gsock][0]
			return message





