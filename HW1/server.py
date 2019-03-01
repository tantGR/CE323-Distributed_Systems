import Primality_Test as lib
import serverMW as mw
<<<<<<< HEAD
SVCID = 50
buf = 0
len = 0 
=======
import struct

>>>>>>> master

SVCID = 50

def main():

	a = mw.register(SVCID)
	if a == -1:
		print("error with registration. Try again later.\n")
		return
	while True:
		reqid = mw.getRequest(SVCID,buf,len)
		 





if __name__ == "__main__":
    main()

