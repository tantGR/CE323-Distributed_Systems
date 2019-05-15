import threading
import struct
import socket
import os
import time
import threading
import errno

IP = "224.0.0.6"
MCAST_PORT = 11987
SERVER_PORT = 2019
OPEN = 5
READ = 10
WRITE = 15
O_CREAT = 12
O_EXCL = 21
O_TRUNC = 22
EEXIST = -2
open_files = {}
files_BOUND = 0#30
file_codes = {}
codes = 0
incarnation_number = -1

def serve_open(request):
	global O_CREAT,O_EXCL,O_TRUNC,open_files,file_codes,codes,EEXIST

	#(flag,) = struct.unpack('!s',request[:3])
	flag = request[:3]
	flag = flag.decode()
	fname = request[3:]
	fname = fname.decode()
	

	if fname not in open_files:
		try:
			if 'x' in flag:
				if 't' in flag:
					fd = os.open(fname,os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_TRUNC) #xct
				else:
					fd = os.open(fname,os.O_CREAT|os.O_EXCL|os.O_RDWR)#xc
			else:
				if 'c' in flag:
					if 't' in flag:
						fd = os.open(fname,os.O_CREAT|os.O_TRUNC|os.O_RDWR)#ct
					else:
						fd = os.open(fname,os.O_CREAT|os.O_RDWR)#c
				else:
					if 't' in flag:
						fd = os.open(fname,os.O_TRUNC|os.O_RDWR)#t
					else:
						fd = os.open(fname,os.O_RDWR)#-			
		except OSError as ex: 		
			if ex.errno == errno.EEXIST:
				return EEXIST
			else:
				return -1
		else:
			open_files[fname] = [fd,time.time()]
			codes += 1
			file_codes[codes] = fd
			return codes
	else:
		open_files[fname][1] = time.time()
		for f in file_codes:
			if file_codes[f] == open_files[fname][0]:
				code = f 
				break
		if 'x' in flag:
			return EEXIST
		elif 't' in flag:
			try:
				os.ftruncate(open_files[fname][0],100)
			except OSError:
				return -1
			else:
				return code
		else:
			return code


def serve_read(request):
	global open_files,file_codes,incarnation_number

	(incarn,fid,pos,size) = struct.unpack('!IIiI',request)

	if incarn < incarnation_number:
		return -5
	if fid not in file_codes:
		return -1	

	fd = file_codes[fid]
	for fname in open_files:
		if open_files[fname][0] == fd:
			break
	fsize = os.stat(fname).st_size
	if pos < 0:
		if fsize < pos:
			os.lseek(fd,0,os.SEEK_SET)
		else:
			os.lseek(fd,pos,os.SEEK_END)
	else:
		os.lseek(fd,pos,os.SEEK_SET)
	try:
		buf = os.read(fd,size)
	except OSError:
		return -1
	else:
		for fname in open_files:
			if fd == open_files[fname][0]:
				open_files[fname][1] = time.time()
				break
	
		return buf

def serve_write(request):
	global open_files,file_codes,incarnation_number

	(incarn,fid,pos,size) = struct.unpack('!IIII',request[0:16])
	data = request[16:]

	if incarn < incarnation_number:
		return -5
	if fid not in file_codes:
		return -1	

	fd = file_codes[fid]
	os.lseek(fd,pos,os.SEEK_SET)
	try:
		nbytes = os.write(fd,data)
	except OSERROR:
		return -1
	else:
		for fname in open_files:
			if fd == open_files[fname][0]:
				open_files[fname][1] = time.time()
				break
		
		return nbytes

def garbage_collection():
	global open_files,file_codes,files_BOUND

	toDel = []
	toDel1 = []
	print(open_files)
	#print(file_codes)

	for fname in open_files:
		if time.time() - open_files[fname][1] >= 10:#200:
			toDel.append(fname)

	for f in toDel:
		fd = open_files[f][0]
		for c in file_codes:
			#print(c)
			if file_codes[c] == fd:
				toDel1.append(c)
		del open_files[f]
	toDel = []	

	for c in toDel1:
		del file_codes[c]

	toDel1 = []
	print(open_files)

def UdpDiscover():
	global IP,MCAST_PORT,sock,SERVER_PORT
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	group = socket.inet_aton(IP)
	mreq = struct.pack('4sL',group,socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,mreq)
	sock.bind((IP,MCAST_PORT))

	while True:
		(data, addr) = sock.recvfrom(1024)
		#print("Found from ", addr)

		message = struct.pack('!I',SERVER_PORT)
		sock.sendto(message,addr)

class MyThread(threading.Thread):
    def __init__(self, funcToRun, threadID, name, *args):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self._funcToRun = funcToRun
        self._args = args#empty
    def run(self):
        self._funcToRun(*self._args)

def new_incarnation():
	global incarnation_number

	if os.path.exists("incarnation_number"):
		with open("incarnation_number",'r+') as f:
			num = int(f.readline())
			incarnation_number = num+1
			f.seek(0,0)
			f.write(str(incarnation_number)+'\n')
	else:
		with open("incarnation_number",'w') as f:
			incarnation_number = 1
			f.write(str(incarnation_number)+'\n')

	f.close()
def main():
	global IP,PORT, open_files,files_BOUND,incarnation_number

	Thr1 = MyThread(UdpDiscover,1,"UdpDiscover")
	Thr1.start()

	incarnation = new_incarnation()

	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	#ip = sock.getsockname()[0]
	#print(ip)
	sock.bind(("",SERVER_PORT))
	timeout = 30
	sock.settimeout(5)
	start_time = time.time()
	while True:
		try:
			(data,addr) = sock.recvfrom(1060)
		except socket.timeout:
			if len(open_files) >= files_BOUND:
				garbage_collection()
				start_time = time.time()
			continue

		(req_id,type,) = struct.unpack('!II',data[0:8])
		data = data[8:]

		if type == OPEN:
			code = serve_open(data)
			msg = struct.pack('!IiI',req_id,code,incarnation_number)
		elif type == READ:
			buf = serve_read(data)
			if buf == -1 or buf == -5:
				msg = struct.pack('!Ii',req_id,buf)
			else:
				msg = struct.pack('!Ii',req_id,len(buf)) + buf
		elif type == WRITE:
			nbytes = serve_write(data)
			msg = struct.pack('!Ii',req_id,nbytes)

		sock.sendto(msg,addr)

		#print(len(open_files))
		if time.time() - start_time >= timeout:
			if len(open_files) >= files_BOUND:
				garbage_collection()
				start_time = time.time()

if __name__ == "__main__":
    main()
