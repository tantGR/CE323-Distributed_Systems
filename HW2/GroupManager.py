import socket
import struct
import threading

multicast_ip = "224.0.0.7"
multicast_addr = ('',2019)
TCP_PORT = 2018
groups_dict = {} #leksiko me groups -> leksiko me tuples ton members
groups_names = {} #antistoixisi group_port me group_name 
GROUPS_PORTS = 10000 # port gia kathe group
JOIN = 6
LEAVE = 9

def UdpDiscover():
	global multicast_addr, multicast_ip
	manager = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	group = socket.inet_aton(multicast_ip)
	mreq = struct.pack('4sL',group,socket.INADDR_ANY)
	manager.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,mreq)
	manager.bind(multicast_addr)

	print(multicast_addr)
	while True:
		(data, addr) = manager.recvfrom(1024)
		print("Found")

		message = struct.pack('!I',TCP_PORT)
		manager.sendto(message,addr)

def informGroupMembers(grpid,memberid,action):
	global groups_dict

	sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	if action == JOIN:
		message = ('!II',JOIN,memberid)
	elif action == LEAVE:
		message = ('!II',LEAVE,memberid)
	
	for member in groups_dict[grpid]:
		(ip,port) = groups_dict[grpid][member]
		sock.connect((ip,port))
		sock.send(message) 
		sock.recv(1024) #wait for ack
		
	sock.close()

def ackTonewmember(grpid):
	numofmembers = len(groups_dict[grpid])

	ackmsg = struct.pack('!II',numofmembers,grpid)#grpid= mltcast port for group
	for member in groups_dict[grpid]:
		ackmsg += struct.pack('I', member)

	return ackmsg

def joinToGroup(grpid,addr,port,memberid):
	global groups_dict, groups_names, GROUPS_PORTS

	if grpid in groups_names:
		if memberid in groups_dict[grpid]:
			ack_msg = struct.pack('!I',-1)# id iparxei, vres allo		+
			return ack_msg
		else:
			informGroupMembers(groups_names[grpid],memberid,JOIN) #inform other members, receive acks
			groups_dict[groups_names[grpid]][memberid] = (addr,port)
			ack_msg = ackTonewmember(groups_names[grpid]) #return ack to new member
			return ack_msg
	else:
		grp_port = GROUPS_PORTS + 5
		groups_names[grpid] = grp_port
		groups_dict[grp_port] = {}
		groups_dict[grp_port][memberid] = (addr,port) #member's address
		ack_msg = struct.pack('!II',1,grp_port)#1 = group members		
		return ack_msg

def leaveGroup(grpname,memberid):
	id = groups_names[grpname]
	numofmembers = len(groups_dict[id]) - 1

	if numofmembers == 0:
		#del groups_dict[id][memberid]
		del groups_dict[id]
		del groups_names[grpname]
	else:
		informGroupMembers(id,memberid,LEAVE)
		del groups_dict[id][memberid]
		
	ack_msg = struct.pack('!b',1)
	return ack_msg		

def int2ip(ip):
    return socket.inet_ntoa(struct.pack("!I",ip))

def TcpCommunication():
	global TCP_PORT
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(5)
	sock.bind(('',TCP_PORT))
	sock.listen(1)

	while True:
		try:
			conn,(addr,port) = sock.accept()
			data = conn.recv(1024)
			(key,) = struct.unpack('!I',data[0:4])
			data = data[4:]
			if key == JOIN:          
				(grpid,tcp_port,memberid) = struct.unpack('!III',data)
				message = joinToGroup(grpid,addr,tcp_port,memberid)
				conn.send(message)
			elif key  == LEAVE: 
				(grpid,memberid) = struct.unpack('!II',data)
				message = leaveGroup(grpid,memberid)
				conn.send(message)
			conn.close()
		except socket.timeout:
			continue


class MyThread(threading.Thread):
    def __init__(self, funcToRun, threadID, name, *args):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self._funcToRun = funcToRun
        self._args = args#empty
    def run(self):
        self._funcToRun(*self._args)

def main():
	
	Thr1 = MyThread(UdpDiscover,1,"UdpDiscover")
	Thr2 = MyThread(TcpCommunication,2,"TcpCommunication")
	Thr1.setDaemon(False)
	Thr2.setDaemon(False)
	Thr1.start()
	Thr2.start()
	#while True:
		#pass


if __name__ == "__main__":
    main()



#add global vars