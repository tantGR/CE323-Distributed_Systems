import my_nfs
import socket
import struct
import sys
import os
import time

O_CREAT = 12
O_EXCL = 21
O_TRUNC = 22
O_RDONLY = 40
O_WRONLY = 30
O_RDWR = 34
addr = "224.0.0.6"
port = 11987

def DiscoverServer():
	global addr,port
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.settimeout(3)
	TTL = 1
	ttl = struct.pack('b', TTL)# ttl=1=local network segment
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

	message = struct.pack('!b',1) 

	try:
		while True:
			try:
				print("Discover: ", addr,port)
				sock.sendto(message, (addr,port))
				data, server = sock.recvfrom(16)
				(port,) = struct.unpack('!I',data)
			except socket.timeout:
				print("No server found\n")
			else:
				sock.close()
				(ip,mport) = server
				return ip,port
	finally:
		sock.close()

def main():
	ip,port = DiscoverServer()
	my_nfs.set_srv_addr(ip,port)
	my_nfs.set_cache(10,0.1)
	print("blocks needed --- blocks not found in cache")
	fd1 = my_nfs.open("landscape.jpeg",[O_RDWR])
	if fd1 == -1:
		print("Open error")
		return
	elif fd1 == -2:
		print("File exists.")
		return
	
	lfd1 = os.open("landscape.jpeg",os.O_CREAT|os.O_WRONLY)

	b = int(sys.argv[1])
	s = int(sys.argv[2])
	while True:
			
		buf1,nbytes = my_nfs.read(fd1,b)
		if s > 0:
			my_nfs.seek(fd1,(100-len(buf1)),"SEEK_CUR")
	#	print(nbytes)
		if nbytes > 0:
			 os.write(lfd1,buf1)
			 if s > 0: 
			 	os.lseek(lfd1,(100-len(buf1)),os.SEEK_CUR)
		else:
			print("hi")
			break

			
		

if __name__ == "__main__":
    main()
