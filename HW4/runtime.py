import threading
import os

#prog_info = [name,fd,pcount,argc,argv,labels,pvars,sleeping,state] state = READY | RUN | SLEEP | DEAD
READY = 10
RUN = 15
SLEEP = 20
DEAD = 25
team_id = os.getpid()
running_progs = {} #id:prog_info
threads_list = []
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

def run_prog():
	global running_progs,Schedule,OK,ERROR,NOP,END,threads_list,empty_list,RUN,DEAD,SLEEP,READY

	c = -1
	#k = -1
	while True:
		c += 1
		#k += 1
		#if k >= len(threads_list[c]):
			#c = 0
		#	c += 1
		#	k = 0
		if c >= len(threads_list):
			c = 0
		#	k = 0
		if threads_list == []:
			empty_list.acquire()
			c=0
		#	k = 0
		#prog = (c)
		prog = threads_list[c]
		if running_progs[prog][8] == DEAD:
			del running_progs[prog]
			#(t,p) = prog
			del threads_list[c]
			continue

		if running_progs[prog][7] > 0: #sleeping
			 running_progs[prog][7] -= 1
			 continue
		s = 0
		running_progs[prog][8] = RUN
		while s < Schedule and running_progs[prog][8] != DEAD:
			[name,fd,pcount] = running_progs[prog][:3]
			if fd == -1:
				fd = open(name,'r')
				searchLabels(fd,prog)
				fd.seek(0,0)
			pcount = fd.tell()
			#fd.seek(pcount,0)
			command = fd.readline()
			if len(command) == 0:
				#threads_list.append(prog)
				continue
			running_progs[prog][:3] = [name,fd,pcount]
			res = run_command(command,prog)
			if res == ERROR:
				(t,p) = prog
				print("Error in prog,",p,"of team",t)
				running_progs[prog][1].close()
				running_progs[prog][8] = DEAD
				#del threads_list[c]
				break
			elif res == END:
				running_progs[prog][1].close()
				running_progs[prog][8] = DEAD
				#del threads_list[c]
				break
			elif res == SLEEP:
				running_progs[prog][8] = SLEEP
				break
			else:
				s += 1
				continue
		if running_progs[prog][8] == RUN:
			running_progs[prog][8] = READY
		#threads_list.append(prog)


def run_command(cmd,prog):
	global OK,END,ERROR,NOP,SLEEP

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
		res = NOP

	elif cmd[k] == "RCV":
		res = NOP

	elif cmd[k] == "SLP":
		arg1 = cmd[k+1]
		sleeping = int(arg1)*2000
		res = SLEEP
	elif cmd[k] == "PRN":
		t,p = prog
		print("[",t,"]:","[",p,"]:")
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
	global prog_id,running_progs,threads_list,READY,RUN,SLEEP,DEAD,team_id

	Thr1 = MyThread(run_prog,1,"run_prog")
	Thr1.start()

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
			for r in runtime_cmd:
				r = r.split()
				id += 1
				argv = r[1:]
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
			if len(threads_list) == 1:
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
				(team,prog) = p
				print(team,"\t\t",prog,"\t\t",running_progs[p][0],"\t\t",state)
		elif cmd == "kill":
				team_id = int(runtime_cmd[0].split()[1])
				thr_id = int(runtime_cmd[0].split()[2])
				key = (team_id,thr_id)
				if key in threads_list:
					print("Killed")
					running_progs[key][8] = DEAD
				else:
					print("Thread not found")
		else:
			print("Command not found")
if __name__ == "__main__":
    main()
