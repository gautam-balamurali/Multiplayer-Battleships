"""
This is the object used by the server to keep track of every user
	* stores the user name
	* contains the sockets used to communicate with the player TCP/UDP
	* 
"""


import time


class Player:
	def __init__(self,name,ssl_socket,tcp_address,udp_address_sending,udp_address_receiving):
		self.name = name 
		self.tcp_address = tcp_address 			# a tuple
		self.udp_address_sending = udp_address_sending
		self.udp_address_receiving = udp_address_receiving
		self.threads = []
		self.msg_spool = []
		self.game = -1 							# when the game < 0 the player is not playing (used to improve efficiency)
		self.board = None						# when the board is None the player is not playing 
		self.team = ""							# team the player plays to
		self.playing = True						# denotes the player is not in deadlock
		self.games_won = 0 						# games won
		self.games_lost = 0 					# games lost
		self.games_quit = 0 					# games quit

		#ssl socket
		self.ssl_socket = ssl_socket


	# The player is leaving the game
	def quit(self):
		self.playing = False
		for t in self.threads:
			t.join()
		self.ssl_socket.close()


	# the player is not playing
	def is_inactive(self):
		return self.game == -1

	def take_to_menu(self):
		self.game = 0		

	# the player was registered in a game		
	def activate(self,game):
		self.game = game

	# the player is playing any longer
	def deactivate(self):
		self.game = -1
		self.board = None

	# lets start counting the time
	def set_initial_time(self):
		self.time = time.time()

	# is time over?
	def time_is_over(self,time,time_frame):
		return time - self.time > time_frame

	# receive messages
	def send(self,msg):
		self.ssl_socket.send(msg)

	# send messages
	def receive(self):
		return self.ssl_socket.recv(1024)


	# for statistics
	def won_game(self):
		self.games_won += 1

	# for statistics
	def lost_game(self):
		self.games_lost += 1

	# for statistics
	def quit_game(self):
		self.games_quit += 1



	
		

