import threading

ids = 0
Req = 0
Repl = 0

reqs_dict = {}

def Requests():
	print "requests" , ids


def Replies():
	print "replies"


class MyThread(threading.Thread):
	def __init__(self, funcToRun, threadID, name, *args):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self._funcToRun = funcToRun
		self._args = args
	def run(self):
		self._funcToRun(*self._args)


def sendRequest(svcid, buf, len):
	global ids, Repl, Req, reqs_dict
	if not(Req != 0 and Repl!=0 and Req.isAlive() and Repl.isAlive()):
		Req = MyThread(Requests, 1, "Requests")
		Repl = MyThread(Replies, 2, "Replies")
		Req.start()
		Repl.start()

	ids += 1
	reqs_dict[ids] = (svcid,buf,len) 
	return ids

def getReply(reqid, buf, len, block):
	print 