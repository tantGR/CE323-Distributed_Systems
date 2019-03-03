import Primality_Test as lib
import serverMW as mw
SVCID = 50
buf = 0
len = 0 
import struct



SVCID = 50
def main():
<<<<<<< HEAD
=======

>>>>>>> origin/master
	a = mw.register(SVCID)
	if a == -1:
		print("error with registration. Try again later.\n")
		return
	while True:
		reqid = mw.getRequest(SVCID,buf,len)
		 
<<<<<<< HEAD
=======




>>>>>>> origin/master

if __name__ == "__main__":
	main()