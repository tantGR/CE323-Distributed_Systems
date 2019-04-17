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
	return buf,start,len(buf),missing_blocks

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

def read(fd,nbytes):
	global open_files,O_WRONLY, block_size,cache,cache_keys

	if fd not in open_files:
		return -1
	elif open_files[fd][4] == O_WRONLY:
		return -2

	fid = open_files[fd][0]
	curr_pos = open_files[fd][1]
	pos_to_read = curr_pos

	buf,start,buf_len,missing_blocks = searchCache(fid,curr_pos,nbytes)
			
	if missing_blocks == [] and buf_len > 0:
		s = curr_pos - start
		e = s + nbytes
		buf = buf[s:e]
		bytes_read = len(buf)

		open_files[fd][1] += bytes_read
		return buf,bytes_read	
	elif buf_len > 0:
		s = curr_pos - start
		buf = buf[s:]
		bytes_read = len(buf)

		if len(missing_blocks) > 0:
			needed_bytes = nbytes - bytes_read
			next_block = missing_blocks[0]
			tmp_buf,bytes_read = rpc.read(fid,next_block,block_size)
			if bytes_read > 0:
				addtoCache(fid,next_block,tmp_buf,time.time())
				if block_size > needed_bytes:
					buf += tmp_buf[:needed_bytes]
				else:
					buf += tmp_buf

		bytes_read = len(buf)		
		open_files[fd][1] += bytes_read
		return buf,bytes_read	

	else:
		start = (curr_pos//block_size) * block_size
		buf,bytes_read = rpc.read(fid,start,block_size)
		if bytes_read == 0:
			return -1,0
		elif bytes_read == -1:
			return -1,-1
		else:
			addtoCache(fid,start,buf,time.time())
			s = curr_pos - start
			e = s + nbytes
			buf = buf[s:e]
			bytes_read = len(buf)

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
#use cache in write
#multithreading 