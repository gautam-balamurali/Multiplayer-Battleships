import threading
from socket import *
import warcode as wc
import configurationmanager as cm


class ChatRoom:

	def __init__(self,games,udp_socket):
		print ("Initializing the chat room")
		self.running = True
		self.server_port = cm.udp_server_port
		self.code = wc.WarCode()				# war codes translator

		self.games = games
		self.msg_spool = []
		self.socket = udp_socket
		self.threads = []

		#prepare the messages spool
		msg_spool_t = threading.Thread(target=self.handle_msg_spool)
		msg_spool_t.start()
		self.threads.append(msg_spool_t)

		#prepare the msg reception
		msg_reception_t = threading.Thread(target=self.handle_msg_reception)
		msg_reception_t.start()
		self.threads.append(msg_reception_t)


	"""
	Player quits game all thread are finished setting running to False
	for the reception thread I auto send a last message to quit the socket receive deadlock
	all threads are joined
	all sockets are terminated
	"""
	def quit(self):
		self.running = False	
		print("quiting from the chat room inside")#################333
		
		# auto send a message to abort the reception loop gracefully	
		temp_socket = socket(AF_INET, SOCK_DGRAM)
		temp_socket.sendto( "Bye".encode(), (cm.server_host,self.server_port))

		for t in self.threads:
			t.join() 
		self.socket.close()
		temp_socket.close()
		

	"""
	this process will be running in the background until the server is stopped
	will be receiving messages and addresses from the players and adding them 
	to the msg_spool, that will be handled by: handle_msg_spool method
	"""
	def handle_msg_reception(self):
		print ("\tChat room msg receptions: TID = ",threading.current_thread())
		while self.running:
			try:
				decoded_msg, address = self.socket.recvfrom(1024)
				self.code.translate(decoded_msg)
				if (self.code.is_acknowledgement):
					print("Is ACK")
					continue 														# if it is an acknowledgement don't add it to the spool
				self.socket.sendto(self.code.acknowledgement(),address)	# send acknowledgement if it is a regular message
				self.msg_spool.append((decoded_msg,address)) 						# adds the msg and the add to the spool
			except:
				pass
		print ("\tChat room msg receptions finishing")


	"""
	this method will be running in the background and
	will send the messages in the msg spool to the active players
	"""
	def handle_msg_spool(self):
		print ("\tChat room spool handler: TID = ",threading.current_thread())
		while self.running:
			self.send_messages()
		print ("\tChat room spool handler finishing")


	# every message in the spool will be sent to the proper player(s)
	def send_messages(self):
		while self.msg_spool != []:
			coded_msg,from_address = self.msg_spool.pop()
			msg = self.code.translate(coded_msg)
			print("mesage  " + msg)
			if (self.code.is_public_msg):
				self.send_to_all(msg,from_address)
			elif (self.code.is_game_message):
				self.send_to_current_game(msg, self.games.find_player_by_udp_sending_address(from_address),from_address)
			elif (self.code.is_team_message):
				self.send_to_team(msg, self.games.find_player_by_udp_sending_address(from_address),from_address)
			else:
				self.send_to_player_name(msg, self.games.find_player_by_name(self.code.to_player))
				


	# send to an specific player with the address specified
	def send_to_player(self,msg,player):
		self.socket.sendto(msg, player.udp_address_receiving)

	# send message to all players in the list
	def send_to_all_in_list(self,msg,players,from_address):
		for player in players:
			if (player.udp_address_sending != from_address):
				self.send_to_player(msg, player)


	# sends a message to all players
	def send_to_all(self,msg,from_address):
		self.send_to_all_in_list(msg,self.games.server_players(),from_address)

	# sends the message msg to all the players in the list
	def send_to_all_players(self,msg,players,from_address):
		self.send_to_all_in_list(msg,players,from_address)

	# sends the message msg to all the players in the current game
	def send_to_current_game(self,msg,player,from_address):
		self.send_to_all_in_list(msg,self.games.player_game_players(player),from_address)

	# sends the message msg to all the players in the team
	def send_to_team(self,msg,player,from_address):
		self.send_to_all_in_list(msg,self.games.player_team_players(player),from_address)

	# sends a private message msg to a player
	def send_to_player_name(self, msg, player):
		if player:
			self.send_to_player(msg, player)

	


