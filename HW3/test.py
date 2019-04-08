import my_nfs

O_CREAT = 12
O_EXCL = 21
O_TRUNC = 22
O_RDONLY = 40
O_WRONLY = 30
O_RDWR = 34

my_nfs.open("kostas",[O_CREAT,O_TRUNC,O_EXCL,O_RDWR])