import nfs_RPC as rpc

server_ip = ""
server_port = 0
CACHE_SIZE = 0
VALIDITY = 0
open_files = {} #[fd,server_code,pos,name,isOpen]
fds = 0 #local file descriptors
fds_BOUND = 50
O_RDONLY = 40
O_WRONLY = 30
O_RDWR = 34

def set_srv_addr(ip, port):
	global server_ip, server_port

	server_ip = ip
	server_port = port

	rpc.set_server_addr(server_ip,server_port)

def set_cache(size, validity):
	global CACHE_SIZE, VALIDITY

	CACHE_SIZE = size
	VALIDITY = validity

def open(filename, flags):
	global open_files, fds,O_RDONLY,O_WRONLY,O_RDWR,fds_BOUND

	if len(open_files) >= fds_BOUND:
		return -5

	code = rpc.open(filename,flags[:-1])

	if code < 0:
		return code

	fd = fds + 1

	open_files[fd] = [-1,0,filename,False,flags[-1]]#server_code,pos,fname,isOpen,flags

	if code != -1:
		open_files[fd][0] = code 
		open_files[fd][3] = True

	return fd	

def read(fd,nbytes):
	global open_files,O_WRONLY

	if fd not in open_files:
		return -1
	elif open_files[fd][4] == O_WRONLY:
		return -2

	fid = open_files[fd][0]
	curr_pos = open_files[fd][1]

	buf,bytes_read = rpc.read(fid,curr_pos,nbytes)

	if bytes_read == -1:
		#print("Error in read")
		return -1,-1
	elif bytes_read == 0:
		#print("EOF")
		return -1,0
	else:
		open_files[fd][1] += bytes_read
		return buf,bytes_read

def write(fd,buf,nbytes):
	global open_files,O_RDONLY

	if fd not in open_files:
		return -1
	elif open_files[fd][4] == O_RDONLY:
		return -2

	fid = open_files[fd][0]
	curr_pos = open_files[fd][1]

	bytes_written = rpc.write(fid,curr_pos,buf,nbytes)
	if bytes_written != -1:
		open_files[fd][1] += bytes_written

	return bytes_written

def seek(fd,pos,whence):
	global open_files

	if fd in open_files:
		if whence == "SEEK_SET":
			open_files[fd][1] = pos
		elif whence == "SEEK_CUR":
			open_files[fd][1] += pos
		elif whence == "SEEK_END":
			open_files[fd][1] = 0-pos
		return 0
	else:
		return -1

def close(fd):
	global open_files

	if fd in open_files:
		del open_files[fd]
		return 0
	else:
		return -1
