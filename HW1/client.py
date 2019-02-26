import clientMW as mw 
import struct
svcid = 5

def main():
    print("Client APP started.\n")
    while True:
        ans = int(input("What to do next?\n(1) to give a new number/(2) to get an answer/(3) to exit: "))
        if ans==1:
            num = int(input("Give an number: "))
            buf = struct.pack('i',num)
            reqid = mw.sendRequest(svcid,buf,len(buf))
        elif ans==2:
            num = int(input("For which nunber? "))
            blk = input("Do you want to wait until I have the answer?(y/n) ")
            if blk=='y':
                block = True
            else:
                block = False
                res = mw.getReply(reqid,num,len,block)	
        elif ans==3:
            break
        

if __name__ == "__main__":
    main()

'''to do: dict for ids-nums
          unpack reply
		  print reply : Is prime or not 
'''