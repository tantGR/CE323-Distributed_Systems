import socket
import struct

OPEN = 5
READ = 10
WRITE = 15
O_CREAT = 12
O_EXCL = 21
O_TRUNC = 22
server_addr = ("",0)
server_incarnation = -1
req_id = 0

def set_server_addr(ip,port):
	global server_addr
	server_addr = (ip,port)

def send_to_server(incarn,type,fid,pos=0,flags=-1,buf="",len=-1): #fid = file descriptor or file name if it is used to open
	global OPEN,READ,WRITE,server_addr,O_TRUNC,O_EXCL,O_CREAT,server_incarnation,req_id

	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) 
	sock.settimeout(3)

	req_id += 1
	if type == OPEN:
		flag = ""
		m=0
		for f in flags:
			if f == O_CREAT:
				flag += "c"
				m += 1
			elif f == O_EXCL:
				flag += "x"
				m += 1
			elif f == O_TRUNC:
				flag += "t"
				m += 1

		#m = len(flag)
		flag += " "*(3-m)
		fid = fid.encode()
		flag = flag.encode()
		message = struct.pack('!II',req_id,type) + flag + fid
		f = 0
		while True:
			try:
				if f == 1:
					f = 0
				else:
					sock.sendto(message,server_addr)
				data = sock.recv(1024)
			except socket.timeout:
				continue
			else:
				(id,file_code,incarn_num) = struct.unpack('!IiI',data)
				if id != req_id:
					f = 1
					print("\t\thi!!!")
					continue
				else:
					break
		
		return file_code,incarn_num
	elif type == READ:
		message = struct.pack('!IIIIiI',req_id,type,incarn,fid,pos,len)
		f = 0
		while True:
			try:
				if f==1:
					f=0
				else:
					sock.sendto(message,server_addr)
				data = sock.recv(1080)
			except socket.timeout:
				continue
			else:
				(id,nbytes,) = struct.unpack('!Ii',data[0:8])
				if id != req_id:
					f = 1
					print("\t\thi!!!")
					continue
				if nbytes < 0:
					return nbytes,""
				buf = data[8:]
				break

		return nbytes,buf
	elif type == WRITE:
		message = struct.pack('!IIIIII',req_id,type,incarn,fid,pos,len) + buf
		f = 0
		while True:
			try:
				if f == 1:
					f =0 
				else:
					sock.sendto(message,server_addr)
				data = sock.recv(1024)
			except socket.timeout:
				continue
			else:
				(id,bytes_written,) = struct.unpack('!Ii',data)
				if id != req_id:
					print("\t\thi!!!")
					f = 1
				break
		return  bytes_written

def open(fname, flags):

	return send_to_server(-1,OPEN,fname,flags = flags)

def read(fid, pos, nbytes,incarn):

	if fid <= 0:
		print("Invalid file descriptor.")
		return -1,""

	bytes_read,buf = send_to_server(incarn,READ,fid,pos,len = nbytes)

	return buf,bytes_read

def write(fid,pos,buf,len,incarn):

	if fid <= 0:
		print("Invalid file descriptor.")
		return -1

	return send_to_server(incarn,WRITE,fid,pos,buf = buf,len = len)

