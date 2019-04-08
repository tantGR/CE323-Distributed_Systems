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
SEQ_LOSS = 44
SEQ_NUM = 33 # seq number from boss
CURR_SEQ_Q = 56 
CURR_SEQ_A = 65
GROUP_MSG = 31 # message with data to send to group   meber->member 
received_msgs = {}
msgs_to_send = {}
send_lock = threading.Lock()
TIMEOUT = 9000
msg_num = 0
lists_lock = threading.Lock()
msgLists = {}
BOSS = False
arrival_time = {}
global_seq = 0
NEW_BOSS=4321
OK=1234
LOADING_CHANGE=52341

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
	global TCP_PORT, groups_dict,GRP_CHANGE,msgLists,BOSS,arrival_time

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#sock.settimeout(5)
	sock.bind(('',TCP_PORT))
	sock.listen(1)

	while True:
		conn,addr = sock.accept()
		data = conn.recv(1024)
		(key,grpid,member) = struct.unpack('!III',data)
		ack = struct.pack('!b',1)
		#conn.send(ack)
		if key == JOIN:
			groups_dict[grpid].append(member)
			if BOSS == True:
					arrival_time[member] = global_seq
		elif key == LEAVE:
			#groups_dict[grpid].delete(member)
			c = 0
			for m in groups_dict[grpid]:
				if m == member:	 
					break
				c += 1
			del groups_dict[grpid][c]
		conn.send(ack)
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

def check_for_losses(port,last_seq_num,sock):
	global MSG_LOSS,SEQ_LOSS,multicast_addr,MY_ID,received_msgs, GROUP_MSG
	for m in received_msgs:
		if received_msgs[m][0] == 0 and received_msgs[m][2] != -1:
			print("\t\tMSG")
			seq = received_msgs[m][2]
			message = struct.pack('!IIII',MSG_LOSS,m,seq,MY_ID)+"".encode()
			sock.sendto(message,(multicast_addr,port))
		elif received_msgs[m][2] == -1:
			print("\t\tSEQ")
			message = struct.pack('!IIII',SEQ_LOSS,last_seq_num,last_seq_num+2,MY_ID)+"".encode()
			sock.sendto(message,(multicast_addr,port))

	print("\t\t\tANYTHING LOST??")
	print("\t\t",last_seq_num)
	message = struct.pack('!IIII',GROUP_MSG,0,0,MY_ID) #send the global seq
	sock.sendto(message,(multicast_addr,port))
def send_ready_msgs(port,last_seq_num):
	global received_msgs, msgLists,BOSS,msgs_to_send,global_seq
	flag = 1
	toDel = []
	
	while flag == 1:
		flag = 0
		for m in received_msgs:
			if received_msgs[m][2] == last_seq_num + 1 and received_msgs[m][0] > 0:
				msgLists[port].append((APP_MSG,received_msgs[m][3],received_msgs[m][0],received_msgs[m][1]))
				if BOSS == False:	
					toDel.append(m)
				last_seq_num += 1
				flag = 1
	
	#for i in toDel:
	#	del received_msgs[i]

	return last_seq_num

def Receiver(port):
	global multicast_addr, received_msgs, global_seq,msgs_to_send, MY_ID,block_rcv,send_lock,msgLists,BOSS,arrival_time
	global CURR_SEQ,GROUP_MSG,MSG_LOSS,SEQ_NUM, SEQ_LOSS
	global OK,NEW_BOSS,LOADING_CHANGE
	global_seq = 0
	timeout = 4
	if BOSS == True:
		new_in_grp=0
		last_seq_num = 0
	else:
		last_seq_num = -1
		new_in_grp = 1

	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
	group = socket.inet_aton(multicast_addr)
	mreq = struct.pack('4sL',group,socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,mreq)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.settimeout(timeout)
	sock.bind((multicast_addr,port))

	start_time = time.time()
	while True:
		if BOSS == False and new_in_grp == 1:
			message = struct.pack('!IIII',CURR_SEQ_Q,0,0,MY_ID)
			sock.sendto(message,(multicast_addr,port))
		try:
			data,addr = sock.recvfrom(1024)
		except socket.timeout:
			check_for_losses(port,last_seq_num,sock)
			start_time = time.time()
			#print("timeout")
			continue
		else:
			(type,msgID,len,senderID) = struct.unpack('!IIII',data[0:16])#len->length or seq_num or 0
			msg = data[16:]
			if type == GROUP_MSG:         # message with data from a member
				if BOSS == False and msgID > 0 :
					if msgID in received_msgs:   # if seq_num received earlier - inform dictionary
						received_msgs[msgID][0] = len
						received_msgs[msgID][1] = msg
						received_msgs[msgID][3] = senderID
						last_seq_num = send_ready_msgs(port,last_seq_num)
					else:         #new message
						received_msgs[msgID] = [len,msg,-1,senderID]#len,data,seq_num,sender
				elif BOSS == True:
					if msgID == 0: #check for losses - send back global_seq
						message = struct.pack('!IIII',SEQ_NUM,msgID,global_seq,0)+"".encode() # send seq_num to group members
						sock.sendto(message,(multicast_addr,port))
					elif msgID in received_msgs:
						message = struct.pack('!IIII',SEQ_NUM,msgID,received_msgs[msgID][2],0)+"".encode() # send seq_num to group members
						sock.sendto(message,(multicast_addr,port))
					else:
						received_msgs[msgID] = [len,msg,-1,senderID]      
						global_seq += 1 
						received_msgs[msgID][2] = global_seq
						#print("\t\t",global_seq)
						message = struct.pack('!IIII',SEQ_NUM,msgID,global_seq,0)+"".encode() # send seq_num to group members
						sock.sendto(message,(multicast_addr,port))
						
			elif type == MSG_LOSS:
				if msgID in msgs_to_send:   #if it is mine send again
					[mtype,grp,len,msg,sent,with_ack,timeout] = msgs_to_send[msgID]
					message = struct.pack('!IIII',mtype,msgID,len,MY_ID)+msg
					sock.sendto(message,(multicast_addr,port))
					#print("LOSS")
			elif type == SEQ_NUM:
				#print("\t",len)
				received_seq = len
				with send_lock:
					if msgID in msgs_to_send:
						msgs_to_send[msgID][5] = True
				if msgID not in received_msgs and msgID > 0:   #if message not received
					received_msgs[msgID] = [0,"",received_seq,0]
					message = struct.pack('!IIII',MSG_LOSS,msgID,len,MY_ID)+"".encode()
					sock.sendto(message,(multicast_addr,port))
					#print("\t\tMSG_LOSS")
				else:                 #if message received earlier
					if msgID > 0:
						received_msgs[msgID][2] = received_seq
						last_seq_num = send_ready_msgs(port,last_seq_num)
						block_rcv.release()

				if received_seq > (last_seq_num + 1) and last_seq_num != -1:
					#print("\t\t",last_seq_num, received_seq)
					message = struct.pack('!IIII',SEQ_LOSS,last_seq_num,received_seq,MY_ID)+"".encode()
					sock.sendto(message,(multicast_addr,port))
					#print("\t\tSEQ_LOSS")

			elif type == CURR_SEQ_Q or type == CURR_SEQ_A:
				if BOSS == True and type == CURR_SEQ_Q:
					if senderID in arrival_time:
						seq = arrival_time[senderID]
					else:
						print((type,msgID,len,senderID))	
					message = struct.pack('!IIII',CURR_SEQ_A,0,seq,MY_ID)+"".encode()
					sock.sendto(message,(multicast_addr,port))#reference before assignment
				elif BOSS == False and type == CURR_SEQ_A and new_in_grp == 1:
					new_in_grp = 0
					last_seq_num = len
			elif type == SEQ_LOSS and BOSS == True:
				#print ("SEQ_LOSS")
				last = msgID
				received = len
				for m in received_msgs:
					if received_msgs[m][2] in range(last+1,received+1):
						message = struct.pack('!IIII',SEQ_NUM,m,received_msgs[m][2],MY_ID)+"".encode()
						sock.sendto(message,(multicast_addr,port))
			elif type == NEW_BOSS:
				if senderID == MY_ID:
					(global_seq,)=struct.unpack("!I",msg)
					packetsToReceive = global_seq -last_seq_num#TypeError: unsupported operand type(s) for -: 'tuple' and 'int'
					if packetsToReceive == 0:
						#message = struct.pack('!IIII',OK,0,0,groups_dict[grpid][1])#+"".encode() 
						message = struct.pack('I',OK)
						sock.sendto(message,addr)
						BOSS = True
						print("NEW BOSS")
					else:
						message = struct.pack("!I",last_seq_num)
						sock.sendto(message,addr)

			elif type == LOADING_CHANGE:
				received_msgs[msgID]=[len,msgID,len,senderID]
				packetsToReceive -= 1
				if packetsToReceive==0:
					message = struct.pack('I',OK)
					sock.sendto(message,addr)
					BOSS = True
					print("NEW BOSS")

		if (time.time() - start_time) >= 10:
			#print("TIMEOUT")
			check_for_losses(port,last_seq_num,sock)
			start_time = time.time()

def grp_join(name,addr,port,myid):
	global JOIN, LEAVE,groups_dict, manager,MY_ID,threadsexist,BOSS,msgLists,senderThr

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
		print("You created this group.")
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

	if senderThr == -1:
		Thr2 = MyThread(Sender,2,"Sender")
		Thr2.setDaemon(True)
		Thr2.start()
		senderThr = 1
	
	return grp_port

def setNewBoss(grpid):
	global groups_dict,NEW_BOSS,multicast_addr,OK,global_seq
	global NEW_BOSS
	global LOADING_CHANGE
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	sock.settimeout(3)
	try:
		message = struct.pack('!IIIII',NEW_BOSS,0,0,groups_dict[grpid][1],global_seq)#+"".encode() 
		sent = sock.sendto(message,(multicast_addr,grpid))
		data, address = sock.recvfrom(16)

		(status,) = struct.unpack("!I",data)
		if status == OK:
			sock.close()
			return
		else:
			last_seq_num = status		
			for m in received_msgs:
				if received_msgs[m][2] in range(last_seq_num+1,global_seq+1):
					#message = struct.pack('!IIII',SEQ_NUM,m,received_msgs[m][2],groups_dict[grpid][1])+"".encode()
					message = struct.pack('!IIII',LOADING_CHANGE,m,received_msgs[m][2],groups_dict[grpid][1])+"".encode()
					sock.sendto(message,(multicast_addr,grpid))
			sock.recvfrom(16)
			(status,) = struct.unpack("!I",data)
			if status == OK:
				sock.close()
				return

	except socket.timeout:
		print("No manager found\n")
		return 


def grp_leave(gsock):
	global groups_dict, manager, MY_ID
	global BOSS,new_in_grp

	if BOSS==True and len(groups_dict[gsock]) > 1:
		new_in_grp = 0
		BOSS=False
		setNewBoss(gsock)

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(manager)
	message = struct.pack('!III',LEAVE,gsock,MY_ID)
	sock.send(message)
	sock.recv(1024)
	del groups_dict[gsock]

def next_msg():
	global msgs_to_send

	with send_lock:
		for msg in msgs_to_send:
			if msgs_to_send[msg][6] >= 0:
				msgs_to_send[msg][6] -= 1 #timeout
			if msgs_to_send[msg][4] == False:
				return msg
			elif msgs_to_send[msg][5] == False and msgs_to_send[msg][6] <= 0: 
				return msg
			
	return -1

def Sender():
	global msgs_to_send,TIMEOUT,sender_sem,send_lock,multicast_addr
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

	sender_sem.acquire()

	while True:
		
		msgTosend = next_msg()
		if msgTosend == -1:
			continue
		else:
			[type,grp,len,msg,sent,with_ack,timeout] = msgs_to_send[msgTosend]

		timeout = TIMEOUT
		sent = True
		with_ack = False
		message = struct.pack('!IIII',type,msgTosend,len,MY_ID) + msg
		with send_lock:
			msgs_to_send[msgTosend] = [type,grp,len,msg,sent,with_ack,timeout]
		sock.sendto(message,(multicast_addr,grp))

def grp_send(gsock,msg,len):
	global senderThr, msgs_to_send,msg_num,TIMEOUT,send_lock

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
