import socket
TCP_PORT = 2018
def tcpCommunicatiom():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(5)
	sock.bind(('127.0.0.1',TCP_PORT))
	sock.listen(1)

	while True:
		try:
			conn,addr = sock.accept()
			data = conn.recvfrom(1024)
			print data
			data1 = "reply"
			conn.send(data1)
		except socket.timeout:
			continue

tcpCommunicatiom()