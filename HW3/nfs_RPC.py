import socket
import struct

OPEN = 5
READ = 10
WRITE = 15
O_CREAT = 12
O_EXCL = 21
O_TRUNC = 22
server_addr = ("",0)

def set_server_addr(ip,port):
	global server_addr
	server_addr = (ip,port)

def send_to_server(type,fid,pos=0,flags=-1,buf="",len=-1): #fid = file descriptor or file name if it is used to open
	global OPEN,READ,WRITE,server_addr,O_TRUNC,O_EXCL,O_CREAT

	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) 

	if type == OPEN:
		flag = ""
		for f in flags:
			if f == O_CREAT:
				flag += "c"
			elif f == O_EXCL:
				flag += "x"
			elif f == O_TRUNC:
				flag += "t"
		print(flag)
		message = struct.pack('!Iss',type,fid,flag)
		sock.sendto(message,server_addr)
		data = sock.recv(1024)
		(file_code,) = struct.unpack('!I',data)

		return file_code
	elif type == READ:
		message = struct.pack('!IIII',type,fid,pos,len)
		sock.sendto(message,server_addr)
		data = sock.recv(1024)
		(nbytes,) = struct.unpack('!I',data[0:4])
		buf = data[4:]

		return nbytes,buf
	elif type == WRITE:
		message = struct.pack('!IIII',type,fid,pos,len) + buf
		sock.sendto(message,server_addr)
		data = sock.recv(1024)
		(bytes_written,) = struct.unpack('!I',data)

		return  bytes_written

def open(fname, flags):

	return send_to_server(OPEN,fname,flags = flags)

def read(fid, pos, nbytes):

	bytes_read,buf = send_to_server(READ,fid,pos,len = nbytes)

	return bytes_read,buf

def write(fid,pos,buf,len):

	return send_to_server(WRITE,fid,pos,buf = buf,len = len)

