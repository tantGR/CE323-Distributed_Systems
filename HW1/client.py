import clientMW as mw 
import struct
import sys
svcid = 50
requests = {}

def main():
	print("Client APP started.")
	while True:
		ans = int(input("What to do next?\n(1) to give a new number/(2) to get an answer/(3) to exit: "))
		if ans==1:
			num = int(input("Give an number: "))
			#string = str(num)
			#print("!",buf,"!")
			#buf = struct.pack('i',num)
			#length = sys.getsizeof(string)
			#print(length)
			#buf = string.encode()
			id = mw.sendRequest(svcid,num,0)#len(buf)
			requests[num] = id
		elif ans==2:
			num = int(input("For which nunber? "))
			if num not in requests:
				print("I cant find this number in your requests!")
				continue
			blk = input("Do you want to wait until I have the answer?(1 for yes, 0 for no) ")
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
				print(ans)
		elif ans==3:
			print("Goodbye!\n")
			break        
			#kill threads
		

if __name__ == "__main__":
    main()

'''to do: dict for ids-nums
          unpack reply
		  print reply : Is prime or not 
'''
