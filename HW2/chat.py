import memberMW as mw 
import threading
import os,sys
import time

manager_ip = "224.0.0.7"
manager_port = 2019
ID = os.getpid()
gsock = 0
GRP_CHANGE = 12 #message for changes in group - mw->app
APP_MSG = 21  # message from another member      mw->app
JOIN = 6
LEAVE = 9

def Send():
	global gsock
	while True:
		try:
			message = input()
			message = message.encode()
			res = mw.grp_send(gsock,message,len(message))
		except EOFError:
			sleep(1000)
		else:
			continue
def Receive():
	global gsock, GRP_CHANGE, APP_MSG,LEAVE,JOIN

	while True:
		type,member,key,msg = mw.grp_recv(gsock,False)
		if type == GRP_CHANGE:
			if key == LEAVE:
				print(member, "left from group")
			else:
				print(member,"joined group")
		elif type == APP_MSG:
			msg = msg.decode()
			print("[",member,"] ",msg)

class MyThread(threading.Thread):
	def __init__(self, funcToRun, threadID, name, *args):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self._funcToRun = funcToRun
		self._args = args#empty
	def run(self):
		self._funcToRun(*self._args)

def main(duration):
	global gsock

	gsock = mw.grp_join(0,manager_ip,manager_port,ID)
	Thr1 = MyThread(Send,1,"Send")
	Thr2 = MyThread(Receive,2,"Receive")
	Thr1.setDaemon(True)
	Thr2.setDaemon(True)
	Thr1.start()
	Thr2.start()

	time.sleep(duration)
	mw.grp_leave(gsock)

if __name__ == "__main__":
	duration = int(sys.argv[1])
main(duration)