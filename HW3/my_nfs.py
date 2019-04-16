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
cache_keys = []
block_size = 512
cache = {}

def set_srv_addr(ip, port):
	global server_ip, server_port

	server_ip = ip
	server_port = port

	rpc.set_server_addr(server_ip,server_port)

def set_cache(size, validity):
	global CACHE_SIZE, VALIDITY

	CACHE_SIZE = size*1024
	VALIDITY = validity
	cache_keys = [i for i in range(size/block_size)]

def open(filename, flags):
	global open_files, fds,O_RDONLY,O_WRONLY,O_RDWR,fds_BOUND

	if len(open_files) >= fds_BOUND:
		return -5

	code = rpc.open(filename,flags[:-1])

	if code < 0:
		return code

	fds = fds + 1
	fd = fds
	
	open_files[fd] = [-1,0,filename,False,flags[-1]]#server_code,pos,fname,isOpen,flags

	if code != -1:
		open_files[fd][0] = code 
		open_files[fd][3] = True

	return fd	

def searchCache(fid,pos,nbytes):
	global cache_keys,CACHE_SIZE,cache,validity,block_size

	missing_blocks = []
	needed_blocks = []
	found_blocks = []

	for i in range(pos,nbytes,block_size+):
		needed_blocks.append((pos // block_size)*block_size)

	key = -1
	for k in cache:
		if cache[k][0] == fid:
			if time.time() - cache[k][3] > validity:
				cache_keys.append(k)
			else:
				if cache[k][1] in needed_blocks:
					found_blocks.append(k)
		
				

	return "",-1,-1

def addtoCache(fid,pos,buf,timestamp):
	global cache_keys,CACHE_SIZE,cache,validity

	if len(cache_keys) == 0:
		curr_time = time.time()
		max_time = curr_time - cache[0][3]
		key = 0
		for k in cache:
			if curr_time - cache[k][3] > validity:
				cache_keys.append(k)
				key = -1
			if key != -1 and curr_time - cache[k][3] > max_time:
				max_time =  curr_time - cache[k][3]
				key = k
		if key != -1:
			cache_keys.append(key)	

	key = cache_keys[0]
	del cache_keys[0]
	cache[key] = [fid,pos,buf,timestamp]

def read(fd,nbytes):
	global open_files,O_WRONLY, block_size,cache,cache_keys

	if fd not in open_files:
		return -1
	elif open_files[fd][4] == O_WRONLY:
		return -2

	fid = open_files[fd][0]
	curr_pos = open_files[fd][1]
	pos_to_read = curr_pos

	buf,pos,bytes_read,missing_blocks = searchCache(fid,curr_pos,nbytes)
	#buf,bytes_read = rpc.read(fid,curr_pos,block_size)
		
	if bytes_read == nbytes:
		#ok
	#elif bytes_read == -1:
	#	missing = True
	#	while missing==True:
	#		if curr_pos < block_size:
	#			start = 0
	#		else:
	#			start = (curr_pos // block_size) * block_size
	#		buf,bytes_read = rpc.read(fid,start,block_size)#nothing in cache
	#		addtoCache(fid,start,buf,time.time())
	#		if curr_pos + nbytes <= start + bytes_read:
	#			missing = False
	#		else:
	#			curr_pos = start+bytes_read
	else:
		for b in missing_blocks:
			start = b * block_size
			buf,bytes_read = rpc.read(fid,start,block_size)
			addtoCache(fid,start,buf,time.time())

	buf,pos,bytes_read = searchCache(fid,pos_to_read,nbytes)

		#missing_blocks = buf
		#if pos > curr_pos:
		#	missing = True
		#	tmp = curr_pos
		#	while missing:
		#		start = (tmp // block_size) * block_size
		#		buf,bytes_read = rpc.read(fid,start,block_size)
		#		addtoCache(fid,start,buf,time.time())
		#		if tmp < start:
		#			tmp = start

		#if curr_pos+nbytes > pos+bytes_read:
		#	missing = True
		#	tmp = curr_pos
		#	while missing:
		#		start = ((tmp // block_size) + 1) * block_size
		#		buf,bytes_read = rpc.read(fid,start,block_size)
		#		addtoCache(fid,start,buf,time.time())


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


# seek negative pos (handle in server)