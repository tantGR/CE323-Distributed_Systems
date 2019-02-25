import clientMW as mw

def main():
	print "Client APP started.\n"

	while True:
		ans = input("What to do next?\n((1) to give a new number/(2) to get an answer/(3) to exit): ")
		print "ans", ans
		if ans==1:
			num = int(raw_input("Give an number: "))
			id = mw.sendRequest(10,num,1)
		elif ans==2:
			num = int(raw_input("For which nunber? "))
			blk = raw_input("Do you want to wait until I have the answer?(y/n) ")
			if blk=='y':
				block = True
			else:
				block = False	
			res = mw.getReply(id,num,len,block)	
		elif ans==3:
			break   

if __name__ == "__main__":
    main()

