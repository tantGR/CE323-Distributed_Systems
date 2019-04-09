import my_nfs

O_CREAT = 12
O_EXCL = 21
O_TRUNC = 22
O_RDONLY = 40
O_WRONLY = 30
O_RDWR = 34

my_nfs.set_srv_addr('127.0.0.1',11987)
fd = my_nfs.open("file.txt",[O_CREAT,O_TRUNC,O_EXCL,O_RDWR])
str = "Hello World!"
buf = str.encode()
bytes = my_nfs.write(fd,buf,len(buf))
print(bytes)
my_nfs.seek(fd,3,"SEEK_SET")
buf,nbytes = my_nfs.read(fd,7)
buf = buf.decode()
print(buf,nbytes)