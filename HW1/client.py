import clientMW as mw 
import struct
import sys
svcid = 50
requests = {}

def main():
	print("Client APP started.")
	while True:
		#ans = int(input("What to do next?\n(1) new request /(2) get reply/(3) exit: "))
		ans = int(input())
		if ans==1:
			#num = int(input("Give an number: "))
			num = int(input())
			buf = num
			#string = str(num)
			#print("!",buf,"!")
			#buf = struct.pack('i',num)
			length = sys.getsizeof(buf)
			#print(length)
			#buf = string.encode()
			id = mw.sendRequest(svcid,buf,length)#len(buf)
			requests[num] = id
		elif ans==2:
			#num = int(input("For which nunber? "))
			num = int(input())
			if num not in requests:
				print("I cant find this number in your requests!")
				continue
			#blk = int(input("Block until answer available?(1-yes, 0-no) "))
			blk = int(input())
			if blk==1:
				block = True
			else:
				block = False
			id = requests[num]
			ok,buf,len = mw.getReply(id,block)
			if ok == -1:
				print("No reply available yet.")
			else:
				(ans,) = struct.unpack('?',buf)
				if ans == True:
					print(num," is prime.")
				else:
					print(num, " is not prime.")
		elif ans==3:
			print("Goodbye!\n")
			break        
			#kill threads
		

if __name__ == "__main__":
    main()
