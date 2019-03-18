import socket


multicast_ip = "224.0.0.7"
multicast_addr = ('',2019)
TCP_PORT = 2018
groups_dict = {} #leksiko me groups -> leksiko me tuples ton members
groups_names = {} #antistoixisi group_port me group_name 
GROUPS_PORTS = 10000 # port gia kathe group

def UdpDiscover():
	global multicast_addr, multicast_ip
	manager = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	group = socket.inet_aton(multicast_ip)
	mreq = struct.pack('4sL',group,socket.INADDR_ANY)
	manager.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,mreq)
	manager.bind(multicast_addr)

	while True:
		(data, addr) = manager.recvfrom(1024)

		message = struct.pack('!b',1)
		manager.sendto(message,addr)

def informGroupMembers(grpid):
	global groups_dict

	for member in groups_dict[grpid]:
		



def joinToGroup(grpid,addr,port,memberid):
	global groups_dict, groups_names, GROUPS_PORTS

	if grpid in groups_names:
		if memberid in groups_dict[grpid]:
			ack_msg = struct.pack('!I',-1)# id iparxei, vres allo		+
			return ack_msg
		else:
			id = groups_names[grpid]
			informGroupMembers(id) #inform other members, receive acks
			groups_dict[id][memberid] = (addr,port)
			#return ack to new member
	else:
		grp_port = GROUPS_PORTS + 5
		groups_names[grpid] = grp_port
		groups_dict[grp_port] = {}
		groups_dict[grp_port][memberid] = (addr,port) #member's address
		ack_msg = struct.pack('!II',1,grp_port)#1 = group members		
		return ack_msg

def TcpCommunicatiom():
	global TCP_PORT
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(5)
	sock.bind('',TCP_PORT)
	sock.listen(1)

	while True:
		try:
			conn,addr = sock.accept()
			data = conn.recvfrom(1024)
			if data == "JOIN":          # allagi
			#unpack
				message = joinToGroup(grpid,tcp_addr,tcp_port,memberid)
				conn.send(message)
			elif data  == "LEAVE": 

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
	
	Thr1 = MyThread(UdpDiscover,1,"udpDiscover")
	Thr2 = MyThread(TcpCommunicatiom,2,"tcpCommunicatiom")


if __name__ == "__main__":
    main()



