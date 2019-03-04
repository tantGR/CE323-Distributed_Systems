import clientMW as mw 
import struct
svcid = 5

requests = {}

def main():
	print("Client APP started.")
	while True:
		ans = int(input("What to do next?\n(1) to give a new number/(2) to get an answer/(3) to exit: "))
		if ans==1:
			num = int(input("Give an number: "))
			buf = num
			print("!",buf,"!")
			#buf = struct.pack('i',num)
			id = mw.sendRequest(svcid,buf,0)#len(buf)
			requests[num] = id
		elif ans==2:
			num = int(input("For which nunber? "))
			if num not in requests:
				print("I cant find this number in your requests!")
				continue
			blk = input("Do you want to wait until I have the answer?(y/n) ")
			if blk=='y':
				block = True
			else:
				block = False	
			ok,buf,len = mw.getReply(requests[num],block)
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
