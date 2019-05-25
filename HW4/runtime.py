import threading
import os
import struct
import socket

#prog_info = [name,fd,pcount,argc,argv,labels,pvars,sleeping,state] state = READY | RUN | SLEEP | DEAD | BLOCKED | MIGRATED
multicast_addr = ('224.0.0.6',2019)
balancing_multi = ('224.0.0.7',2020)
READY = 10
RUN = 15
SLEEP = 20
DEAD = 25
BLOCKED = 30
MIGRATED = 35
runtimes = {}
runtimes_id = 0
runtimes_info = {}
team_id = os.getpid()
TCP_PORT = 2019+os.getpid()
TCP_IP = ''
running_progs = {} #t,p_id:prog_info = MIGRATED
threads_list = [] #[(team,thread)]
messages_received = {} #{(grp,sender,receiver):msg}
udp_sends = {}
udp_sender = threading.Semaphore(0)
migrate_info = {} #{(team,thr):[ip,port,prog_info]}
empty_list = threading.Semaphore(0)
migrate_block = threading.Semaphore(0)
wait = threading.Semaphore(0)
Schedule = 5
NOP = 0
OK = 1
ERROR = -1
END = -2
COMING = 0

def searchLabels(fd,prog):
	global running_progs
	while True:
		pos = fd.tell()
		line = fd.readline()
		if len(line) == 0:
			return
		label = line.split()[0]
		if label[0] == "#" and label != "#SIMPLESCRIPT": 
			running_progs[prog][5][label] = pos

def recvUdp():
	global udp_received,multicast_addr,running_progs,READY,MIGRATED,threads_list,messages_received,DEAD,TCP_PORT
	ACK = 98
	NORMAL = 89

	(ip,p) = multicast_addr
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
	group = socket.inet_aton(ip)
	mreq = struct.pack('4sL',group,socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,mreq)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind(multicast_addr)

	while True:
		print("Receiving...")
		data,addr = sock.recvfrom(1024)

		[mtype,team,sender,recver] = struct.unpack('!IIII',data[0:16])
		data = data[16:]
		if mtype == DEAD:
			for key in threads_list:
				(t,p) = key
				if t == team:
					running_progs[(t,p)][8] = DEAD
		elif (team,recver) in threads_list and running_progs[(team,recver)][8] != MIGRATED:
			if mtype == ACK:
				#print("ACK Received from",team, sender)
				running_progs[(team,recver)][8] = READY
			elif mtype == NORMAL:
				(length,) = struct.unpack('!I',data[:4])
				data = data[4:]
				vals = []
				for i in range(length):
					(num,) = struct.unpack('!I',data[:4])
					vals.append(num)
					data = data[4:]
				messages_received[(team,sender,recver)] = vals
				running_progs[(team,recver)][8] = READY

def sendUdp():
	global udp_sender,udp_sends,multicast_addr,DEAD,balancing_multi
	ACK = 98
	NORMAL = 89
	HELLO = 99
	LOAD = 88
	SYNC = 100
	MYTHREADS = 101

	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	del_list = []
	while True:
		udp_sender.acquire()
		for s in udp_sends:
			if s == LOAD:
				mtype = udp_sends[s][0]
				#msg = "".encode()
				if mtype == HELLO:
					ip = udp_sends[s][1]
					port = udp_sends[s][2]
					msg = struct.pack('!II',HELLO,port) + ip.encode()
				elif mtype == MYTHREADS:
					num = udp_sends[s][1]
					ip = udp_sends[s][2]
					port = udp_sends[s][3]
					msg = struct.pack('!III',MYTHREADS,num,port)+ip.encode()
				elif mtype == SYNC:
					msg = struct.pack('!I',SYNC)
				sock.sendto(msg,balancing_multi)
			else:
				(team,sender,recver) = udp_sends[s]
				if udp_sends[s] == ACK:
					message = struct.pack('!IIII',ACK,team,sender,recver)
					#print("sent ack to",team,recver)
				elif udp_sends[s] == DEAD:
					message = struct.pack('!IIII',DEAD,team,0,0) 
				else:
					message = struct.pack('!IIII',NORMAL,team,sender,recver) + udp_sends[s][1]
				sock.sendto(message,multicast_addr)
			# receive ack --------------------------------------------------------
			del_list.append(s)
		for i in del_list:
			del udp_sends[i]
			del_list.remove(i)

def sendRPC():
	global migrate_info
	MIGRATE = 12
	PROG_COMM = 21
	ASK = 55
	ANSWER = 44

	# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	while True:
		migrate_block.acquire()
		done = []
		for key in migrate_info:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			if key == "ASK":
				(ip,port) = migrate_info[key][0]
				num = migrate_info[key][1]
				avg = migrate_info[key][2]
				msg = struct.pack('!IIII',ASK,num,avg,TCP_PORT)
				sock.connect((ip,port))
				sock.send(msg)
			elif key == ANSWER:
				[addr,num] = migrate_info[key]
				msg = struct.pack('!II',ANSWER,num)
				print(addr)
				sock.connect(addr)
				sock.send(msg)
			else:
				(t,p) = key
				ip = migrate_info[key][0]
				port = migrate_info[key][1]
				thr_info = migrate_info[key][2]
				old_state = migrate_info[key][3]
				print(ip,port)
				sock.connect((ip,port))
				 #name,pcount,argc,sleeping,state,labels length,pvars length
				name = thr_info[0]
				msg = struct.pack('!IIIIIIIIII',MIGRATE,t,p,thr_info[2],thr_info[3],thr_info[7],old_state,len(thr_info[5]),len(thr_info[6]),len(name))+name.encode()
				#labels
				for l in thr_info[5]:
					pos = thr_info[5][l]
					l = l.encode()
					msg += struct.pack('!I',len(l)) + l + struct.pack('!I',pos)

				for v in thr_info[6]:
					val = thr_info[6][v]
					v = v.encode()
					val = (str(val)).encode()
					msg += struct.pack('!II',len(v),len(val)) + v + val

				sock.send(msg)

				f = open(thr_info[0],'rb')
				line = f.readline()
				while line:
					sock.send(line)
					line = f.readline()
			sock.shutdown(socket.SHUT_RDWR)
			sock.close()
			done.append(key)

		for k in done:
			del migrate_info[k]

def receiveRPC():
	global TCP_PORT,running_progs,threads_list,migrate_block,COMING,wait
	MIGRATE = 12
	ASK = 55
	ANSWER = 44

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.bind(('',TCP_PORT))
	# print(socket.gethostbyname(s,TCP_PORT))
	# print(socket.gethostbyname(socket.gethostname()))
	
	sock.listen(1)

	while True:
		conn,addr = sock.accept()
		data = conn.recv(1024)
		(flag,) = struct.unpack('!I',data[:4])
		data = data[4:] 
		if flag == MIGRATE:
			(team,thr_id,pcount,argc,sleeping,state,l_length,v_length,name_len) = struct.unpack('!IIIIIIIII',data[:36])
			data = data[36:]
			name = data[:name_len].decode()
			data = data[name_len:]
			labels = {}
			for i in range(l_length):
				(len,) = struct.unpack('!I',data[:4])
				data = data[4:]
				l = data[:len].decode()
				data = data[len:]
				(pos,) = struct.unpack('!I',data[:4])
				data = data[4:]
				labels[l] = pos
			#print(labels)

			pvars = {}
			for v in range(v_length):
				(l_var,l_val,) = struct.unpack('!II',data[:8])
				data = data[8:]
				v = data[:l_var].decode()
				data = data[l_var:]
				val = data[:l_val].decode()
				data = data[l_val:]
				pvars[v] = val

			#print(pvars)

			with open('sum_test', 'wb') as f:
				while True:
					line = conn.recv(1024)
					if not line:
						break
					f.write(line)
			threads_list.append((team,thr_id))
			empty_list.release()
			running_progs[(team,thr_id)] = ["sum_test",-1,pcount,argc,{},labels,pvars,sleeping,state]
		elif flag == ASK:
			(asked,average,dst_port) = struct.unpack('!III',data[:12])
			counter = 0
			for key in threads_list:
				if running_progs[key][8] != MIGRATED and running_progs[key][8] != DEAD:
					counter += 1
			can_give = counter - average
			[dst_ip,p] = addr
			if can_give <= 0:
				migrate_info[ANSWER] = [(dst_ip,dst_port),0]
			else:
				if can_give >= asked:
					migrate_info[ANSWER] = [(dst_ip,dst_port),asked]
					final = asked
				else:
					migrate_info[ANSWER] = [(dst_ip,dst_port),can_give]
					final = can_give

				q = 0
				for key in running_progs:
					if running_progs[key][8] != RUN and running_progs[key][8] != DEAD and running_progs[key][8] != MIGRATED:
						state = running_progs[key][8]
						running_progs[key][8] = MIGRATED
						migrate_info[key] = [dst_ip,dst_port,running_progs[key],state]
						running_progs[key][1].close()
						q += 1
						if q == final:
							break

			migrate_block.release()
		elif flag == ANSWER:
			(num,) = struct.unpack('!I',data[:4])
			COMING = num
			wait.release()

def balance():
	global TCP_PORT,TCP_IP,running_progs,threads_list,migrate_info,migrate_block,COMING,wait,runtimes

	sum = 0 

	for r in runtimes:
 		sum += runtimes[r]

	average = sum // len(runtimes)
	print("average",average)

	my_threads = runtimes[(TCP_IP,TCP_PORT)]

	if my_threads < average:
		for key in runtimes:
			if runtimes[key] > average:
				wanted = average - my_threads
				he_gives = runtimes[key] - average
				if wanted <= he_gives:
					migrate_info["ASK"] = [key,wanted,average]
					print("ask ",wanted)
				else:
					migrate_info['ASK'] = [key,he_gives,average]
					print("ask ",he_gives)
				migrate_block.release()
				wait.acquire()
				if COMING > 0:
					my_threads += COMING
					if my_threads == average:
						break

def Load_balancing():
	global udp_sends,udp_sender,threads_list,balancing_multi,TCP_PORT,running_progs,MIGRATED,TCP_IP,runtimes
	HELLO = 99
	LOAD = 88
	SYNC = 100
	MYTHREADS = 101
	runtimes = {}
	period = 5
	# runtime_id = 0

	(ip,port) = balancing_multi
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
	group = socket.inet_aton(ip)
	mreq = struct.pack('4sL',group,socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,mreq)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind(balancing_multi)
	sock.settimeout(period)

	udp_sends[LOAD] = [HELLO,TCP_IP,TCP_PORT]
	udp_sender.release()
	#print("HELLO")
	flag = False
	while True:
		try:
			data,addr = sock.recvfrom(1024)
			#print(addr)
			(t_ip,po) = addr
		except socket.timeout:
			if flag == True:
				print("balance")
				balance()
				#udp_sends[LOAD] = [SYNC]
				#udp_sender.release()
				flag = False
				#print("--------")
			else:
				print("TIMEOUT")
				c = 0
				for t in threads_list:
					if running_progs[t][8] != MIGRATED and running_progs[t][8] != DEAD:
						c += 1
				print("thrs",c)
				udp_sends[LOAD] = [MYTHREADS,c,TCP_IP,TCP_PORT]
				udp_sender.release()
				#print("#########")
				flag = True
		else:
			(mtype,) = struct.unpack('!I',data[:4])
			data = data[4:]
			if mtype == HELLO:
				(port,) = struct.unpack('!I',data[:4])
				ip = data[4:].decode()
				#print(ip,port)
				if (t_ip,port) not in runtimes:
					if port == TCP_PORT:
						TCP_IP = t_ip
					runtimes[(t_ip,port)] = 0
				#print(TCP_IP,TCP_PORT)
				if t_ip!=TCP_IP or port != TCP_PORT:
					udp_sends[LOAD] = [SYNC]
					udp_sender.release()
					print(t_ip,port,"is here!")  
			elif mtype == SYNC:
				sock.settimeout(period)
			elif mtype == MYTHREADS:
				(thrs,port) = struct.unpack('!II',data[:8])
				data = data[8:]
				#ip = data.decode()
				runtimes[(t_ip,port)] = thrs


def run_prog():
	global running_progs,Schedule,OK,ERROR,NOP,END,threads_list,empty_list,RUN,DEAD,SLEEP,READY,BLOCKED,MIGRATED,udp_sends,udp_sender

	c = -1
	while True:
		c += 1
		if c >= len(threads_list):
			c = 0
		if threads_list == []:
			empty_list.acquire()
			c=0
		prog = threads_list[c]
		if running_progs[prog][8] == DEAD:
			del running_progs[prog]
			#(t,p) = prog
			del threads_list[c]
			continue
		if running_progs[prog][8] == BLOCKED or running_progs[prog][8] == MIGRATED :
				continue

		if running_progs[prog][7] > 0: #sleeping
			 running_progs[prog][7] -= 1
			 continue
		s = 0
		running_progs[prog][8] = RUN
		while s < Schedule and running_progs[prog][8] != DEAD and running_progs[prog][8] != BLOCKED and running_progs[prog][8] != MIGRATED :
			[name,fd,pcount] = running_progs[prog][:3]
			if fd == -1:
				fd = open(name,'r')
				searchLabels(fd,prog)
				fd.seek(pcount,0)
			pcount = fd.tell()
			#fd.seek(pcount,0)
			curr_pos = pcount
			command = fd.readline()
			if len(command) == 0:
				#threads_list.append(prog)
				continue
			running_progs[prog][:3] = [name,fd,pcount]
			# print(command)
			res = run_command(command,prog)
			if res == ERROR:
				(t,p) = prog
				print("Error in prog,",p,"of team",t)
				running_progs[prog][1].close()
				running_progs[prog][8] = DEAD
				(t,p) = prog
				for key in running_progs:
					(a,b) = key
					if a == t:
						running_progs[key][8] = DEAD
				udp_sends[(t,p,0)] = DEAD
				break
			elif res == END:
				running_progs[prog][1].close()
				running_progs[prog][8] = DEAD
				break
			elif res == SLEEP:
				running_progs[prog][8] = SLEEP
				break
			elif res == BLOCKED:
				running_progs[prog][1].seek(curr_pos,0)
				#print(pcount,running_progs[prog][1].tell())
				break
			else:
				s += 1
				continue
		#running_progs[prog][:3] = [name,fd,pcount]
		if running_progs[prog][8] == RUN:
			running_progs[prog][8] = READY
		#threads_list.append(prog)

def run_command(cmd,prog):
	global OK,END,ERROR,NOP,SLEEP,BLOCKED,messages_received,messages_to_send,udp_sender
	ACK = 98
	NORMAL = 89

	[name,fd,pcount,argc,argv,labels,pvars,sleeping,state] = running_progs[prog]
	k = 0
	cmd = cmd.split()
	if cmd[0] == "#SIMPLESCRIPT":
		res = NOP
	elif cmd[0][0] == '#':
		k = 1
		#labels[cmd[0]] = pcount
	if cmd[k] == "SET":
		arg1,arg2 = cmd[k+1:]
		if arg2[0] == '$':
			pvars[arg1] = int(pvars[arg2])
		else:
			pvars[arg1] = int(arg2)
		res = OK
	elif cmd[k] in ["ADD","SUB","MUL","DIV","MOD"]:
		arg1,arg2,arg3 = cmd[k+1:]
		if arg2[0] == '$':
			val1 =  int(pvars[arg2])
		else: 
			val1 = int(arg2)
		if arg3[0] == '$':
			val2 = int(pvars[arg3])
		else:
			val2 = int(arg3)

		if cmd[k] == "ADD":
			pvars[arg1] = val1 + val2
		elif cmd[k] == "SUB":
			pvars[arg1] = val1 - val2
		elif cmd[k] == "MUL":
			pvars[arg1] = val1 * val2
		elif cmd[k] == "DIV":
			pvars[arg1] = val1 // val2
		elif cmd[k] == "SUB":
			pvars[arg1] = val1 % val2

		res = OK

	elif cmd[k] in ["BGT","BGE","BLT","BLE","BEQ"]:
		arg1,arg2,arg3 = cmd[k+1:]
		if arg1[0] == '$':
			val1 =  int(pvars[arg1])
		else: 
			val1 = int(arg1)
		if arg2[0] == '$':
			val2 = int(pvars[arg2])
		else:
			val2 = int(arg2)

		res = False
		if cmd[k] == "BGT":
			if val1 > val2:
				res = True
		elif cmd[k] == "BGE":
			if val1 >= val2:
				res = True
		elif cmd[k] == "BLT":
			if val1 < val2:
				res = True
		elif cmd[k] == "BLE":
			if val1 <= val2:
				res = True
		elif cmd[k] == "BEQ":
			if val1 == val2:
				res = True

		if res:
			if arg3 in labels:
				pcount = labels[arg3]
				fd.seek(pcount,0)
				res = OK
			else:
				res = ERROR
	elif cmd[k] == "BRA":
		label = cmd[k+1]
		if label in labels:
			pcount = labels[label]
			fd.seek(pcount,0)
		res = OK
	elif cmd[k] == "SND":
		#res = NOP
		(team,sender) = prog
		arg1 = cmd[k+1]
		if arg1[0] == '$':
			recver =  int(pvars[arg1])
		else: 
			recver = int(arg1)

		vars = cmd[k+2:]
		#print(vars)
		message = struct.pack('!I',len(vars))
		#print(vars,len(vars))
		l = len(vars)
		for a in range(l):
			if vars[a][0] == '$':
				vars[a] = int(pvars[vars[a]])
			else:
				vars[a] = int(vars[a])

			#message += struct.pack('!i',vars[a])
		for v in vars:
			message += struct.pack('!I',v)

		if (team,recver) in running_progs and running_progs[(team,recver)][8] != MIGRATED:
			messages_received[(team,sender,recver)] = vars #message,len(vars)
			#print(messages_received)
		else:
			udp_sends[(team,sender,recver)] = [NORMAL,message]
			udp_sender.release()	

		state = BLOCKED
		res = OK

	elif cmd[k] == "RCV":
		#res = NOP

		(team,thread) = prog
		arg1 = cmd[k+1]
		if arg1[0] == '$':
			sender =  int(pvars[arg1])
		else: 
			sender = int(arg1)

		vars = cmd[k+2:]
		#print(vars)
		for a in range(len(vars)):
			if vars[a][0] == '$':
				vars[a] = int(pvars[vars[a]])
			else:
				vars[a] = int(vars[a])

		if (team,sender,thread) in messages_received:
			message = messages_received[(team,sender,thread)]
			if message != vars:
				state = BLOCKED
				res = BLOCKED
			else:
				if (team,sender) in running_progs and running_progs[(team,sender)][8] == BLOCKED:
					running_progs[(team,sender)][8] = READY
				else:
					udp_sends[(team,thread,sender)] = ACK
					udp_sender.release()
				del  messages_received[(team,sender,thread)]
				res = OK
				#print(res)
		else:
			state = BLOCKED
			res = BLOCKED

	elif cmd[k] == "SLP":
		arg1 = cmd[k+1]
		sleeping = int(arg1)*2000
		res = SLEEP
	elif cmd[k] == "PRN":
		t,p = prog
		print("[",t,"]","[",p,"]:",end = '')
		#print(cmd)
		for a in cmd[k+1:]:
			if a[0] == '$':
				#print(a,pvars)
				if a in pvars:
					a = pvars[a]
				else:
					return ERROR
			print(a," ",end = '')		
		print('')
		res = OK

	elif cmd[k] == "RET":
		res = END 

	running_progs[prog] = [name,fd,pcount,argc,argv,labels,pvars,sleeping,state]
	return res

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
	global prog_id,running_progs,threads_list,READY,RUN,SLEEP,DEAD,team_id,migrate_info,runtimes_id,runtimes_info,MIGRATED,runtimes

	Thr1 = MyThread(run_prog,1,"run_prog")
	Thr1.start()
	Thr2 = MyThread(sendRPC,2,"sendRPC")
	Thr2.start()
	Thr3 = MyThread(receiveRPC,3,"receiveRPC")
	Thr3.start()
	Thr4 = MyThread(recvUdp,4,"recvUdp")
	Thr4.start()
	Thr5 = MyThread(sendUdp,5,"sendUdp")
	Thr5.start()
	Thr6 = MyThread(Load_balancing,6,"Load_balancing")
	Thr6.start()

	while True:
		runtime_cmd = input()
		runtime_cmd = runtime_cmd.split("||")
		#if len(runtime_cmd) == 1:
		#	cmd = runtime_cmd.
		#else: 
		cmd = runtime_cmd[0].split()[0]
		if cmd == "run":
			team_id += 1
			id = -1
			print(runtime_cmd)
			runtime_cmd[0] = runtime_cmd[0].split("run")[1]
			print(runtime_cmd)
			for r in runtime_cmd:
				r = r.split()
				id += 1
				argv = r
				name = argv[0]
				argc = len(argv)
				labels = {}
				pvars = {}
				sleeping = 0
				state = READY
				threads_list.append((team_id,id))#team, threasd_id runtime
				pvars["$argc"] = argc
				for i in range(0,argc):
					tmp = "$arg" + str(i)
					pvars[tmp] = argv[i]
				running_progs[(team_id,id)] = [name,-1,0,argc,argv,labels,pvars,sleeping,state] #prog_info = [name,fd,pcount,argc,argv,labels,pvars]
			if len(threads_list) == len(runtime_cmd):
				empty_list.release()
		elif cmd == "list":
			print("TEAM\t\tTHREAD\t\tNAME\t\tSTATE\t\t")
			for p in running_progs:
				if running_progs[p][8] == SLEEP:
					state = "SLEEPING"
				elif running_progs[p][8] == RUN:
					state = "RUNNING"
				elif running_progs[p][8] == READY:
					state = "READY"
				elif running_progs[p][8] == DEAD:
					state = "DEAD"
				elif running_progs[p][8] == BLOCKED:
					state = "BLOCKED"
				elif running_progs[p][8] == MIGRATED:
					continue
					state = "MIGRATED"
				(team,prog) = p
				print(team,"\t\t",prog,"\t\t",running_progs[p][0],"\t\t",state)
		elif cmd == "kill":
			team_id = int(runtime_cmd[0].split()[1])
			#thr_id = int(runtime_cmd[0].split()[2])
			#key = (team_id,thr_id)
			#if key in threads_list:
				#print("Killed")
			for key in threads_list:
				(t,p) = key
				if t == team_id and running_progs[key][8] != MIGRATED:
					running_progs[key][8] = DEAD
		elif cmd == "migrate":
			[team,prog,ip,port] = (runtime_cmd[0].split()[1:])
			team = int(team)
			prog = int(prog)
			port = int(port)

			b = False
			for r in runtimes_info:
				if runtimes_info[r] == [ip,port]:
					b = True
					break
			if not b:	
				runtimes_id += 1
				runtimes_info[runtimes_id] = [ip,port] 

			while running_progs[(team,prog)][8] == RUN:
				pass
			state = running_progs[(team,prog)][8]
			if state == DEAD:
				print("Thread:",prog,"of team", team,"ended execution")
				continue
			running_progs[(team,prog)][8] = MIGRATED
			running_progs[(team,prog)][1].close()
			migrate_info[(team,prog)] = [ip,port,running_progs[(team,prog)],state]
			migrate_block.release()
		elif cmd == "shutdown":
			#print(runtimes)
			if len(runtimes) <= 1 and len(threads_list) > 0:
				print("This is the only runtime running")
				continue

			rlist = []
			for key in runtimes:
				if key != (TCP_IP,TCP_PORT):
					rlist.append(key)

			i = 0
			end = len(rlist)
			for key in running_progs:
				state = running_progs[key][8]
				if state == DEAD  or state == MIGRATED:
					continue
				running_progs[key][8] = MIGRATED
				running_progs[key][1].close()
				(ip,port) = rlist[i]
				migrate_info[key] = [ip,port,running_progs[key],state]
				migrate_block.release()
				i += 1
				if i == end:
					i = 0
		else:
			print("Command not found")
if __name__ == "__main__":
    main()
