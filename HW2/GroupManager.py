import socket
import struct
import threading
import os
multicast_ip = "224.0.0.7"
multicast_addr = ('',2019)
TCP_PORT = os.getpid()+1821
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
		print("Found from ", addr)

		message = struct.pack('!I',TCP_PORT)
		manager.sendto(message,addr)

def informGroupMembers(grpid,memberid,action,BOSS):
	global groups_dict, JOIN, LEAVE

	#sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)'

	message = struct.pack('!III',action,grpid,memberid)
	#sock.settimeout(3)

	i = 0
	for member in groups_dict[grpid]:
		if i== 0 and BOSS == True:
			message = message = struct.pack('!III?',action,grpid,memberid,True)
		else:
			message = struct.pack('!III?',action,grpid,memberid,False)

		sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM) #not optimal
		(ip,port) = groups_dict[grpid][member]
		print(ip,port)
		sock.connect((ip,port))

		sock.send(message) 
		sock.recv(1024) #wait for ack , send again after timeout
		sock.close()
		i=i+1

def ackTonewmember(grpid):
	numofmembers = len(groups_dict[grpid])

	ackmsg = struct.pack('!II',numofmembers,grpid)#grpid= mltcast port for group
	for member in groups_dict[grpid]:
		ackmsg += struct.pack('!I', member)

	return ackmsg

def joinToGroup(grpname,addr,port,memberid):
	global groups_dict, groups_names, GROUPS_PORTS,JOIN

	if grpname in groups_names:
		grpid = groups_names[grpname]
		if memberid in groups_dict[grpid]:
			ack_msg = struct.pack('!I',-1)# id iparxei, vres allo		+
			return ack_msg
		else:
			boss=False
			informGroupMembers(grpid,memberid,JOIN,boss) #inform other members, receive acks
			groups_dict[grpid][memberid] = (addr,port)
			ack_msg = ackTonewmember(grpid) #return ack to new member
			return ack_msg
	else:
		grp_port = GROUPS_PORTS + 5
		groups_names[grpname] = grp_port
		groups_dict[grp_port] = {}
		groups_dict[grp_port][memberid] = (addr,port) #member's address
		ack_msg = struct.pack('!II',1,grp_port)#1 = group members		
		return ack_msg

def leaveGroup(grpid,memberid,BOSS):
	global LEAVE

	#grpid = groups_names[grpname]
	numofmembers = len(groups_dict[grpid]) - 1

	if numofmembers == 0:
		#del groups_dict[id][memberid]
		del groups_dict[grpid]
		for name in groups_names:
			if groups_names[name] == grpid:
				keytoDel = name
				break
		del groups_names[keytoDel]
	else:
		informGroupMembers(grpid,memberid,LEAVE,BOSS)
		del groups_dict[grpid][memberid]
		
	ack_msg = struct.pack('!b',1)
	return ack_msg		

def TcpCommunication():
	global TCP_PORT,JOIN,LEAVE
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(5)
	sock.bind(('',TCP_PORT))
	sock.listen(1)

	while True:
		try:
			conn,(addr,port) = sock.accept()
			print(addr,port)
			data = conn.recv(1024)
			(key,) = struct.unpack('!I',data[0:4])
			data = data[4:]
			if key == JOIN:          
				(grpid,tcp_port,memberid) = struct.unpack('!III',data)
				message = joinToGroup(grpid,addr,tcp_port,memberid)
				conn.send(message)
			elif key  == LEAVE: 
				(grpid,memberid,BOSS) = struct.unpack('!II?',data)
				message = leaveGroup(grpid,memberid,BOSS)
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

if __name__ == "__main__":
    main()



#add global vars