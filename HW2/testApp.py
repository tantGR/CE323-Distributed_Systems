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
start_time=0
SENDER = False
def Send(k):
	global gsock,start_time,SENDER

	start_time = time.time()
	while k>=0:
		SENDER = True
		try:
			message=str(k)#message = input()
			message = message.encode()
			res = mw.grp_send(gsock,message,len(message))
		except EOFError:
			time.sleep(1000)
		else:
			k=k-1
			continue
def Receive():
	global gsock, GRP_CHANGE, APP_MSG,LEAVE,JOIN,SENDER
	global start_time
	count = 0
	recv_time = 0
	c = 0
	while True:
		type,member,key,msg = mw.grp_recv(gsock,False)
		if type == GRP_CHANGE:
			if key == LEAVE:
				print(member, "left from group")
			else:
				print(member,"joined group")
		elif type == APP_MSG:
			msg = msg.decode()
			#print("[",member,"] ",msg)
			count = count+1
			#if msg == "0":
				#print(msg)
				#print("received ",count,"messages")
				#length=len(msg)
				#msg=msg.encode()
				#mw.grp_send( gsock,msg,length)
			if count == 1000:
				msg = "ALL RECEIVED"
				sent_count = mw.getSendCounter()
				print("All received!\n Packets sent:"+str(sent_count))
				msg = msg.encode()
				res = mw.grp_send(gsock,msg,len(msg))
			if msg == "ALL RECEIVED" and SENDER:
				recv_time += time.time() - start_time 
				c += 1
				print("[",member,"] ",msg)
			if c == 2:
				print(recv_time/1000)
class MyThread(threading.Thread):
	def __init__(self, funcToRun, threadID, name, *args):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self._funcToRun = funcToRun
		self._args = args#empty
	def run(self):
		self._funcToRun(*self._args)

def main(duration,k):
	global gsock

	gsock = mw.grp_join(0,manager_ip,manager_port,ID)
	Thr1 = MyThread(Send,1,"Send",k)
	Thr2 = MyThread(Receive,2,"Receive")
	Thr1.setDaemon(True)
	Thr2.setDaemon(True)
	Thr1.start()
	Thr2.start()

	if duration > 0:
		time.sleep(duration)
		mw.grp_leave(gsock)
	else:
		while True:
			pass

if __name__ == "__main__":
	duration = int(sys.argv[1])
	k = int(sys.argv[2])
	main(duration,k)
