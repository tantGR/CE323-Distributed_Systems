import Primality_Test as lib
import serverMW as mw
import time
import struct
import sys
SVCID = 50
buf = 0
len = 0 


def main():

	a = mw.register(SVCID)
	if a == -1:
		print("error with registration. Try again later.\n")
		return
	while True:
		reqid,buf,len = mw.getRequest(SVCID)
		if reqid == -1:
			pass
			#print("No requests available.\n")
		else:	
			#print("Serving: ",reqid)
			#number = struct.unpack('i',buf)
			#print(number)
			#number = int(number)
			#number = int.from_bytes(buf,byteorder = 'little')
			number = buf
			#print(number)
			result = lib.simplePrimaryTest(number)
			print("number ",number, " is prime: ",result)
			
			#res=result
			res = struct.pack('?',result)
			mw.sendReply(reqid,res,1)
		#time.sleep(5)

if __name__ == "__main__":
	main()