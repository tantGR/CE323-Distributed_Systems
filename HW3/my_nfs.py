import nfs_RPC as rpc
import time

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
block_size = 1024
cache = {}

def set_srv_addr(ip, port):
	global server_ip, server_port

	server_ip = ip
	server_port = port

	rpc.set_server_addr(server_ip,server_port)

def set_cache(size, validity):
	global CACHE_SIZE, VALIDITY,cache_keys,block_size

	CACHE_SIZE = size*1024
	VALIDITY = validity
	cache_keys = [i for i in range(CACHE_SIZE//block_size)]

def open(filename, flags):
	global open_files, fds,O_RDONLY,O_WRONLY,O_RDWR,fds_BOUND

	if len(open_files) >= fds_BOUND:
		return -4

	code,server_incarn = rpc.open(filename,flags[:-1])

	if code < 0:
		return code

	fds = fds + 1
	fd = fds
	
	open_files[fd] = [-1,0,filename,False,flags[-1],server_incarn]#server_code,pos,fname,isOpen,flags

	if code != -1:
		open_files[fd][0] = code 
		open_files[fd][3] = True

	return fd	

def searchCache(fid,pos,nbytes):
	global cache_keys,CACHE_SIZE,cache,VALIDITY,block_size

	missing_blocks = []
	needed_blocks = []
	found_blocks = []

	first = (pos//block_size)
	last = ((pos+nbytes)//block_size)
	for i in range(first,last+1):
		needed_blocks.append(i*block_size)
	
		

	print(needed_blocks)
	start = needed_blocks[0]

	key = -1
	buf = b''
	for k in cache:
		if cache[k][0] == fid:
			if time.time() - cache[k][3] > VALIDITY:
				cache_keys.append(k)
				cache[k][4] = False
			else:
				c = 0
				if cache[k][1] in needed_blocks and cache[k][4] == True:
					found_blocks.append(cache[k][1])
					if cache[k][1] == needed_blocks[c]:
						c += 1
						buf += cache[k][2] 
	
	for b in needed_blocks:
		if b not in found_blocks:
			missing_blocks.append(b)				
	print(missing_blocks)
	return buf,start,len(buf),missing_blocks,found_blocks

def addtoCache(fid,pos,buf,timestamp):
	global cache_keys,CACHE_SIZE,cache,VALIDITY

	if len(cache_keys) == 0:
		curr_time = time.time()
		max_time = curr_time - cache[0][3]
		key = 0
		for k in cache:
			if curr_time - cache[k][3] > VALIDITY:
				cache[k][4] = False
				cache_keys.append(k)
				key = -1
			if key != -1 and curr_time - cache[k][3] > max_time:
				max_time =  curr_time - cache[k][3]
				key = k
		if key != -1:
			cache_keys.append(key)	

	key = cache_keys[0]
	del cache_keys[0]
	cache[key] = [fid,pos,buf,timestamp,True]

def open_again(fd):
	global open_files,cache

	print("Open again", open_files[fd][2])
	[code,pos,fname,isOpen,flags,incarn] = open_files[fd]
	tmp_flags = []
	new_code,server_incarn = rpc.open(fname,tmp_flags)
	open_files[fd] = [new_code,pos,fname,isOpen,flags,server_incarn]
	for f in open_files: 
		if f == fd:
			open_files[f][0] = new_code
			open_files[f][5] = server_incarn
	for k in cache:
		if cache[k][0] == code:
			cache[k][0] = new_code

def read(fd,nbytes):
	global open_files,O_WRONLY, block_size,cache,cache_keys

	if fd not in open_files:
		return -1
	elif open_files[fd][4] == O_WRONLY:
		return -2

	fid = open_files[fd][0]
	curr_pos = open_files[fd][1]
	pos_to_read = curr_pos

	print("--",curr_pos)
	missing_blocks = []
	if curr_pos>=0:
		buf,start,buf_len,missing_blocks,found = searchCache(fid,curr_pos,nbytes)
			
	if curr_pos >= 0 and missing_blocks == [] and buf_len > 0:
		print("@@@")
		s = curr_pos - start
		e = s + nbytes
		buf = buf[s:e]
		bytes_read = len(buf)

		open_files[fd][1] += bytes_read
		return buf,bytes_read	
	elif curr_pos >= 0 and buf_len > 0:
		print("###")
		s = curr_pos - start
		buf = buf[s:]
		bytes_read = len(buf)

		if len(missing_blocks) > 0:
			needed_bytes = nbytes - bytes_read
			next_block = missing_blocks[0]
			while True:
				tmp_buf,bytes_read = rpc.read(fid,next_block,block_size,open_files[fd][5])
				if bytes_read > 0:
					addtoCache(fid,next_block,tmp_buf,time.time())
					if block_size > needed_bytes:
						buf += tmp_buf[:needed_bytes]
					else:
						buf += tmp_buf
					break
				elif bytes_read == -5:
					open_again(fd)
				else:
					break		

		bytes_read = len(buf)		
		open_files[fd][1] += bytes_read
		return buf,bytes_read	

	else:
		print("&&&")
		if curr_pos >= 0:
			start = (curr_pos//block_size) * block_size
		else:
			start  = 0 - block_size
			# print(start)
		flag = True
		while start < curr_pos and flag == True:
			if curr_pos>=0:
				flag = False
			while True:
				buf,bytes_read = rpc.read(fid,start,block_size,open_files[fd][5])
				if bytes_read == 0:
					return -1,0
				elif bytes_read == -1:
					return -1,-1
				elif bytes_read == -5:
					open_again(fd)
				else:
					addtoCache(fid,abs(start),buf,time.time())
					if curr_pos>=0:
						s = curr_pos - abs(start)
						e = s + nbytes
						buf = buf[s:e]
						bytes_read = len(buf)
					else:
						print(buf)
						size = len(buf)
						buf = buf[size+curr_pos:size+curr_pos+nbytes]
						bytes_read = len(buf)
						print(buf)

					open_files[fd][1] += bytes_read
					return buf,bytes_read	
			start -= block_size
		
def write(fd,buf,nbytes):
	global open_files,O_RDONLY, cache, block_size

	if fd not in open_files:
		return -1
	elif open_files[fd][4] == O_RDONLY:
		return -2

	fid = open_files[fd][0]
	curr_pos = open_files[fd][1]

	buf1,start,buf_len,missing_blocks,found_blocks = searchCache(fid,curr_pos,nbytes)

	for b in cache:
		if cache[k][1] in found_blocks:
			cache[k][4] = False

	while True:
		bytes_written = rpc.write(fid,curr_pos,buf,nbytes,open_files[fd][5])
		if bytes_written != -1:
			open_files[fd][1] += bytes_written
			break
		if bytes_written == -5:
			open_again(fd)
		else:
			break

	return bytes_written

def seek(fd,pos,whence):
	global open_files

	if fd in open_files:
		if whence == "SEEK_SET":
			open_files[fd][1] = pos
		elif whence == "SEEK_CUR":
			open_files[fd][1] += pos
		elif whence == "SEEK_END":
			open_files[fd][1] = 0+pos
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


# seek negative pos (handle in server)--------(done - not tested)
#use cache in write
#multithreading 
#server death --------------------------------(done - working)
#at least once, protocols
#many_clients/files
#same message multiple times