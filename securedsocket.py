"""
This code implemets a simple encryption between the server and all its clients
The encryption method is RSA
"""

class RSASocket:
	def __init__(self,socket):
		self.socket = socket
		p = 3
		q = 5
		n = p*q 			# 15
		z = (p-1)*(q-1)		# 8
		e = 7 				# e < z and coprime with z
		d = 7 				# d*e mod z = 1 => 901 mod 60 = 1
		self.encrypted = False
		self.public_key = e,n
		self.private_key = d,n


	def connect(self,regular_parameters):
		self.socket.connect(regular_parameters)

	def send(self,msg):
		if(self.encrypted):
			self.socket.send(self.encrypt(msg).encode())
		else:
			self.socket.send(msg.encode())

	def recv(self,num):
		if (self.encrypted):
			return self.decrypt(self.socket.recv(num).decode())
		else:
			return self.socket.recv(num).decode()

	def sendto(self,msg,address):
		if (self.encrypted):
			self.socket.sendto(self.encrypt(msg).encode(), address)
		else:
			self.socket.sendto(msg.encode(), address)

	def recvfrom(self,num):
		msg, addr = self.socket.recvfrom(num)
		if (self.encrypted):
			return self.decrypt(msg.decode()), addr
		else:
			return msg.decode(), addr


	def decrypt(self,cipher_text):
		d, n = self.private_key
		print("before :" + cipher_text)###############
		nums = [int(num) for num in cipher_text[1:-1].split(",")]
		print("nums before :" + str(nums))################
		plain = [chr((num) ** d) % n for num in nums]
		#plain = [chr((char ** d) % n) for char in cipher_text]
		return ''.join(plain)

	def encrypt(self,msg):
		e, n = self.public_key
		cipher_text = [(ord(char) ** e) % n for char in msg]
		print( "cipher text :" + str(cipher_text))
		return str(cipher_text)

	def close(self):
		self.socket.close()



