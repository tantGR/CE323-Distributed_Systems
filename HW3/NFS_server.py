import threading
import struct
import socket
import os
import time
import threading
import errno

IP = "224.0.06"
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
	global open_files,file_codes

	(fid,pos,size) = struct.unpack('!III',request)

	if fid not in file_codes:
		return -1	

	fd = file_codes[fid]
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
	global open_files,file_codes

	(fid,pos,size) = struct.unpack('!III',request[0:12])
	data = request[12:]

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

	for fname in open_files:
		if time.time() - open_files[fname][1] >= 3:#200:
			toDel.append(fname)

	for f in toDel:
		fd = open_files[fname][0]
		for c in file_codes:
			if file_codes[c] == fd:
				toDel1.append(c)
		del open_files[f]

	for c in toDel1:
		del file_codes[c]
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

def main():
	global IP,PORT, open_files,files_BOUND

	Thr1 = MyThread(UdpDiscover,1,"UdpDiscover")
	Thr1.start()

	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	#ip = sock.getsockname()[0]
	#print(ip)
	sock.bind(("",SERVER_PORT))
	timeout = 10
	sock.settimeout(5)
	start_time = time.time()
	while True:
		try:
			(data,addr) = sock.recvfrom(1024)
		except socket.timeout:
			if len(open_files) >= files_BOUND:
				garbage_collection()
				start_time = time.time()
			continue

		(type,) = struct.unpack('!I',data[0:4])
		data = data[4:]

		if type == OPEN:
			code = serve_open(data)
			msg = struct.pack('!i',code)
		elif type == READ:
			buf = serve_read(data)
			if buf == -1:
				msg = struct.pack('!i',-1)
			else:
				msg = struct.pack('!i',len(buf)) + buf
		elif type == WRITE:
			nbytes = serve_write(data)
			msg = struct.pack('!i',nbytes)

		sock.sendto(msg,addr)

		print(len(open_files))
		if time.time() - start_time >= timeout:
			if len(open_files) >= files_BOUND:
				garbage_collection()
				start_time = time.time()

if __name__ == "__main__":
    main()
