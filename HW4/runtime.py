import threading
import os
import struct
import socket

#prog_info = [name,fd,pcount,argc,argv,labels,pvars,sleeping,state] state = READY | RUN | SLEEP | DEAD | BLOCKED | MIGRATED
READY = 10
RUN = 15
SLEEP = 20
DEAD = 25
BLOCKED = 30
MIGRATRED = 35
runtimes = 0
runtimes_info = {}
team_id = os.getpid()
running_progs = {} #t,p_id:prog_info = MIGRATRED
threads_list = [] #[(team,thread)]
messages_to_send = {} #{(grp,sender,receiver):msg}
messages_received = {} #{(grp,sender,receiver):msg}
migrate_info = {(team,thr):prog_info}
empty_list = threading.Semaphore(0)
Schedule = 5
NOP = 0
OK = 1
ERROR = -1
END = -2

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

def sendRPC():
	global migrate_info


#def receiveRPC():


def run_prog():
	global running_progs,Schedule,OK,ERROR,NOP,END,threads_list,empty_list,RUN,DEAD,SLEEP,READY,BLOCKED,MIGRATRED

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
		if running_progs[prog][8] == BLOCKED:
				continue

		if running_progs[prog][7] > 0: #sleeping
			 running_progs[prog][7] -= 1
			 continue
		s = 0
		running_progs[prog][8] = RUN
		while s < Schedule and running_progs[prog][8] != DEAD and running_progs[prog][8] != BLOCKED and running_progs[prog][8] != MIGRATRED :
			[name,fd,pcount] = running_progs[prog][:3]
			if fd == -1:
				fd = open(name,'r')
				searchLabels(fd,prog)
				fd.seek(0,0)
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
				print(pcount,running_progs[prog][1].tell())
				break
			else:
				s += 1
				continue
		#running_progs[prog][:3] = [name,fd,pcount]
		if running_progs[prog][8] == RUN:
			running_progs[prog][8] = READY
		#threads_list.append(prog)


def run_command(cmd,prog):
	global OK,END,ERROR,NOP,SLEEP,BLOCKED,messages_received,messages_to_send

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
		print(vars)
		message = struct.pack('!I',len(vars))
		for a in range(len(vars)):
			if vars[a][0] == '$':
				vars[a] = int(pvars[vars[a]])
			else:
				vars[a] = int(vars[a])

			message += struct.pack('!i',vars[a])

		if (team,recver) in running_progs and running_progs[(team,recver)] != MIGRATRED:
			messages_received[(team,sender,recver)] = vars #message,len(vars)
			print(messages_received)
		else:
			messages_to_send[(team,sender,recver)] = message

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
		print(vars)
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
					del  messages_received[(team,sender,thread)]
				else:
					pass
					#sendRPC(ack...)
				res = OK
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
	global prog_id,running_progs,threads_list,READY,RUN,SLEEP,DEAD,team_id,migrate_info,runtimes,runtimes_info

	Thr1 = MyThread(run_prog,1,"run_prog")
	Thr1.start()
	Thr2 = MyThread(sendRPC,2,"sendRPC")
	Thr2.start()

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
		#	threads_list[team_id] = []
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
				threads_list.append((team_id,id))
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
				if t == team_id:
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
				runtimes += 1
				runtimes_info[0] = [ip,port] 

			while running_progs[(team,prog)][8] == RUN:
				pass
			state = running_progs[(team,prog)][8]
			if state == DEAD:
				print("Thread:",prog,"of team", team,"ended execution")
				continue
			running_progs[(team,prog)][8] = MIGRATED
			migrate_info[(team,prog)] = [ip,port,running_progs[(team,prog)]]

		else:
			print("Command not found")
if __name__ == "__main__":
    main()
