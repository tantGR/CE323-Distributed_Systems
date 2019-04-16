import my_nfs
import socket
import struct
import sys

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
	fd = my_nfs.open("file.txt",[O_CREAT,O_TRUNC,O_RDWR])
	if fd == -1:
		print("Open error")
		return
	elif fd == -2:
		print("File exists.")
		return
	str = "Ti nea?????????"
	buf = str.encode()
	bytes = my_nfs.write(fd,buf,len(buf))
	print(bytes)
	my_nfs.seek(fd,8,"SEEK_END")
	buf,nbytes = my_nfs.read(fd,7)
	buf = buf.decode()
	print(buf,nbytes)

if __name__ == "__main__":
    main()