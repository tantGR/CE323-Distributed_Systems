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
	my_nfs.set_cache(4,10)
	fd = my_nfs.open("a.txt",[O_RDWR])
	if fd == -1:
		print("Open error")
		return
	elif fd == -2:
		print("File exists.")
		return
	#bytes = my_nfs.write(fd,buf,len(buf))
	#print(bytes)
	#my_nfs.seek(fd,8,"SEEK_END")
	lfd = os.open("hello.txt",os.O_CREAT|os.O_TRUNC|os.O_WRONLY)
	#c = 1
	# time.sleep(5)
	my_nfs.seek(fd,-10,"SEEK_END")
	while True:
		#c += 1
		#if c == 5:
			#my_nfs.seek(fd,100,"SEEK_CUR")
		buf,nbytes = my_nfs.read(fd,1)
		res = my_nfs.seek(fd,-2,"SEEK_CUR")
		if res == -1:
			print("Out of file bounds")
		print(nbytes)
		if nbytes == 0:
			break
		os.write(lfd,buf)

if __name__ == "__main__":
    main()