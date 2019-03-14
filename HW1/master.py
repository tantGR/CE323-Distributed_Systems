#import serverMW as mw
import time
import struct
import sys
import socket
import threading

multicast_group = "224.0.0.7"
serverSide_address = ('',2019)
clientSide_address = ('',2020)
SVCID = 50;buf = 0;len = 0 
Thr1 = 0; Thr2 = 0
curr_load=0
curr_slaves = 0
numOfSlaves=0
slaves=[]
MAX_LOAD=10
clients = 0
servers = 0
servers_list=[]
	
def ip2int(ip):
    return struct.unpack("!I",socket.inet_aton(ip))[0]

def int2ip(ip):
    return socket.inet_ntoa(struct.pack("!I",ip))

  
def ClientSide():
    global clients, messageQueue,MAX_LOAD,curr_slaves,curr_load, numOfSlaves,servers_list
    clients = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    clients.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    clients.bind(clientSide_address)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    while True:
        (data, (address,port)) = clients.recvfrom(1024)
        (key,) = struct.unpack('!I', data[0:4])
        if key == 1995 : #discovery-client
            if numOfSlaves > 0:
                message = struct.pack('!b',1)#Server respondes true/false, depending if it is going to serve
                sent = clients.sendto(message,(address,port))#reply to the Discover Request
                print("Client",(address,port), ", you found me!")
            else:
                print("Insufficient slaves")

        elif key == 1997: # Request client.Increase load and forward to Slave-Server
            [key,svcid,reqTosend,buf,len]=struct.unpack('!IbQQb',data)
            message = struct.pack('!IQIbQQb',key, ip2int(address),port,SVCID,reqTosend,buf,len)
            #messageQueue.addtoq(message)
            server = 0
            for i in range(numOfSlaves):
                if servers_list[i][2] == True:
                    server = i
                    break
            addr = servers_list[server][0]
            port = servers_list[server][1]
            server_addr = (addr,port)
            sock.sendto(message,server_addr)
            
            
            
def ServerSide():
    global servers, messageQueue,MAX_LOAD,curr_slaves,curr_load, numOfSlaves,servers_list
    
    servers = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    servers.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    servers.bind(serverSide_address)
    
    print("Waiting for clients or slave-servers...")
    
    while True:
        (data, (address,port)) = servers.recvfrom(1024)
        (key,) = struct.unpack('!I', data[0:4])#data is a tuple 
      #  print(key)
        if key == 1999:  #new server
            print("Slave",(address,port), ", you found me!")
            if numOfSlaves==0:
                isVisible = True
            else:
                isVisible = False
            servers_list.append([address,port,isVisible])
            numOfSlaves=numOfSlaves+1
        elif key == 2001: #on or off server
          #  print("Hello")
            [key,load] = struct.unpack('!I?',data)
            if load == True:
                print("Full server")
                for i in range(numOfSlaves):
                  # print(servers_list[i][0],servers_list[i][1])
                   if address == servers_list[i][0] and port == servers_list[i][1]:
                        print("off")
                        servers_list[i][2] = False #off server
                        break
                if curr_slaves < numOfSlaves:          #energopoihse slave
                    curr_slaves = curr_slaves+1
                    servers_list[curr_slaves][2] = True
            else:
                print("server available")
                for i in range(numOfSlaves):
                    if address == servers_list[i][0] and port == servers_list[i][1]:
                        servers_list[i][2] = True #on server
                        break
                if curr_slaves > 1:
                    servers_list[curr_slaves][2] = False
                    curr_slaves -= 1 
                                        

class MyThread(threading.Thread):
	def __init__(self, funcToRun, threadID, name, *args):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self._funcToRun = funcToRun
		self._args = args#empty
	def run(self):
		self._funcToRun(*self._args)


def main():
	global Thr1, Thr2
	
	Thr1 = MyThread(ClientSide,1,"ClientSide")
	Thr2 = MyThread(ServerSide,2,"ServerSide")
	Thr1.setDaemon(False)
	Thr2.setDaemon(False)
	Thr1.start()
	Thr2.start()
	

if __name__ == "__main__":
	main()
	
	
