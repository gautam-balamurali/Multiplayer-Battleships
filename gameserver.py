import board as b
import chatroom
import threading
import time
import sys, traceback
import gameserverstatus as gss
import warcode as wc


# menu options
SINGLE_PLAYER_OPTION 	= "1"
MULTI_PLAYER_OPTION 	= "2"
JOIN_PLAYER_OPTION 		= "3"
QUIT_OPTION 			= "4"


class TheGameServer:

	def __init__(self, max,udp_socket):
		self.log("Initializing the game server")

		# special structure: GAMES
		# this is the main data structure(variable) of the game server
		# details inside ServerStatus object
		self.games = gss.ServerStatus(max)	
		self.board = 0		

		self.server_quitting = False			# used to gracefully stop the server 
		self.threads = []						# all the treads will be enlisted here
		self.code = wc.WarCode()				# war codes translator
		self.lock = threading.Lock()			# to lock my threads

		# prepare moderator process
		traffic_t = threading.Thread(target=self.moderator)
		self.add_thread(traffic_t)

		# prepare police process
		police_t = threading.Thread(target=self.police)
		self.add_thread(police_t)
		
		# prepare the chat room
		# chat room uses the GAMES structure to direct messages among users
		# messages can be: public, per game, per team, private 
		self.chat_room = chatroom.ChatRoom(self.games,udp_socket)
		

	# add a new thread to the threads list
	def add_thread(self,t):
		t.daemon = True
		t.start()
		self.threads.append(t)

	# stops the server gracefully joins all threads
	def quit(self):
		self.log("Closing chat room")
		self.chat_room.quit()

		self.log("Closing game server")
		self.server_quitting = True
		for t in self.threads:
			t.join() 


	# Threaded processes
	"""
	the moderator the background process that will be running while the game_server is active
	it will check for the INACTIVE status of every connected player 
	if it is INACTIVE the player is sent to a new threaded menu
	"""
	def moderator(self):
		self.log("\tMODERATOR: TID = " + str(threading.current_thread()))
		while not self.server_quitting:
			player = self.games.detect_inactive_player()
			if (player):
				self.log("MODERATOR: Player "+ player.name + " was taken to the menu")
				player.take_to_menu()					# The player is not playing but in the menu (voids MODERATOR actions)
				menu_t = threading.Thread(target=self.menu, args=(player,))
				self.add_thread(menu_t)
		self.log("\tMODERATOR: thread finished")


	"""
	the police is a background process that checks the status of every active game
	if the game is in a deadlock it will unlock the game 
	"""
	def police(self):
		self.log("\tPOLICE: TID = " + str(threading.current_thread()))
		while not self.server_quitting:
			#self.games.detect_fix_finished_games(self.code.game_won("You (or your team) won the game"))
			self.games.detect_fix_deadLocks()
		self.log("\tPOLICE: thread finished") 


	# log in the system report
	def log(self,msg):
		print(msg)
		#### save to a file

				
	# main menu
	def menu(self,player):
		self.log("Menu: TID = " + str(threading.current_thread()))
		player.send(self.code.main_menu())
		self.code.translate(player.receive())
		try:
			if (self.code.is_single_player_option): 				# single player
				self.single_player_game(player,self.new_game_id())
				return

			if (self.code.is_multiplayer_option): 					# multi-player
				self.multiplayer_game(player,self.new_game_id())
				return

			if (self.code.is_join_option): 							# join a game (sub-menu)
				self.join_game(player)
				return

			if (self.code.is_medal_option):							# medals
				self.medals(player)
				player.deactivate()
				return

			if (self.code.is_help_option): 							# help
				self.help(player)
				player.deactivate()
				return

			# if the players reaches here, then the player seleted quit					 
			player.send(self.code.acknowledgement("Bye"))				# send last messsage
			player.quit() 												# finish player

		except Exception as e:
			player.send("Server: Please enter a valid option")



	"""
	regular methods
	"""		
	
	""" 
		adds a new player to the list of players 
		this player will be found later by the moderator thread
		and will be guided to the main menu
	"""
	def add_player(self,player):
		self.games.add_player(player)

	""" 
	Update game_id in only one place 
	used locks to make sure every id is unique
	"""
	def new_game_id(self):
		self.lock.acquire() 
		g_id = self.games.new_game_id()
		self.lock.release()
		return str(g_id)


	# on id for every board
	def new_board_id(self):
		self.lock.acquire() 
		self.board += 1
		board_id = str(self.board)
		self.lock.release()
		return board_id

	""" 
	This is the single player game  method that wont be in deadlock as soon as the 
	user select quit game will be taken back to the main menu 
	"""
	def single_player_game(self,player,this_game_id):

		won = False
		quit = False
		lost = False
		player.game = int(this_game_id)
		player_game = b.Board(self.new_board_id())						# new game
		self.games.add_singleplayer_game(this_game_id,player)
		computer_game = b.Board(self.new_board_id(),True)				# automatic player

		while 	not self.server_quitting and \
				not won and not lost and not quit:
			player_tuple 	=   player_game.board_id, 	player_game.serialize(True)
			computer_tuple 	= computer_game.board_id, computer_game.serialize(True)
			player.send(self.code.boards_msg([player_tuple],[computer_tuple]))

			msg = player.receive() 
			self.code.translate(msg)
			
			# quit game
			if(self.code.is_quitting_option):
				quit = True
				continue

			if(self.code.is_a_shoot):  							# this verifies if the CODE is a shoot
				_,x,y = self.code.shot() 						# if it is extracts the x,y
				if(computer_game.valid(x,y)): 					# verify range of the coordinates
					won = computer_game.shoot(x,y)  			# player's turn
					if(not won):
						x,y = computer_game.generate_coordinates() 	# computer's turn
						lost = player_game.shoot(x,y)

				else:
					player.send(self.code.invalid_shot("Enter a valid shot"))

		player.send(self.get_result(player,won,lost,quit)) 		# prepares and send message to the player
		self.games.set_deadlock(this_game_id) 					# POLICE process is in cherge from now on
		

	# prepares message to be sent to  the player after a game is finished
	def get_result(self,player,won,lost,quit):
		if(self.server_quitting):
			msg = self.code.server_down("Server is down")
		elif(won):
			msg = self.code.game_won("Congratulations, you won the game")
			player.won_game()
		elif(lost):
			msg = self.code.game_lost("You lost, try next time")
			player.lost_game()
		else:
			msg = self.code.game_quitting("I knew you gonna quit!!")
			player.quit_game()
		return msg
		

	"""
	This the multi-player game. 
	Every NEW multi-player game  will be running in a separated thread
	this method will wait for new players to REGISTER to this game 
		these new player must have choose the join option in the main menu
		when the list of players is full , the game is started
		if the player(the creator of the game) decides to abort
		the game is marked as a DEADLOCK then
		the main loop of this method wont start and 
	after the main loop: all the REGISTERED players to this game are marked as INACTIVE
	once the team is formed

	"""
	def multiplayer_game(self,player,this_game_id):
		player.send(self.code.players_count())
		self.code.translate(player.receive())
		players_count = self.code.players

		player.send(self.code.teams())
		msg = player.receive()
		self.code.translate(msg)
		team = self.code.team

		self.games.add_multiplayer_game(this_game_id,player,players_count,team) 					# update server status
		wait = self.wait_for_players(this_game_id,player)

		if(wait):
			players = self.games.player_game_players(player) 										# get every player in this game
			for p in players:
				p.board = b.Board(self.new_board_id())											# is assigned a board for each player
				p.send(self.code.serve_board(p.board.serialize(True))) 					# every player is served
				p.receive() 																	# this answer is an ACK automatic generated by the client

			while not self.server_quitting and not self.games.is_in_deadlock(this_game_id) \
				  and not self.games.is_finished(this_game_id):

				friends = self.games.get_friends(this_game_id,player)
				enemies = self.games.get_enemies(this_game_id,player)

				# get all the boards in all versions: friendly and not friendly for enemies and friends
				friendly = True
				f_for_f = [(f.board.board_id,f.board.serialize(friendly)) for f in friends]			# friends boards to be sent to the friends
				f_for_e = [(f.board.board_id,f.board.serialize(not friendly)) for f in friends]		# friends boards to be sent to enemies
				e_for_f = [(e.board.board_id,e.board.serialize(not friendly)) for e in enemies]		# enemies boards to be sent to friends
				e_for_e = [(e.board.board_id,e.board.serialize(friendly)) for e in enemies]			# enemies boards to be sent to enemies

				self.inform_teams(friends,f_for_f,e_for_f,player) 									# send boards to the team mates
				self.inform_teams(enemies,e_for_e,f_for_e)											# send boards to enemies

				valid_shot = False
				while not valid_shot:
					self.code.translate(player.receive())
					valid_shot = self.code.is_a_shoot

					if (valid_shot):
						board_index,x,y = self.code.shot()											# retrieve the board and shot coordinates
						enemy = next((e for e in enemies if e.board.board_id == str(board_index)), None)
						if(enemy.board.valid(x,y)):													# if it is a valid shoot
							this_player_lost = enemy.board.shoot(x,y)  								# shoot the board

							self.lock.acquire()
							if (this_player_lost):
								enemy.send(self.code.game_lost("Game lost, good luck the next one"))# last communication with the player
								enemy.lost_game()
								self.games.remove_player(this_game_id,enemy) 						# remove the player

							if (self.games.is_finished(this_game_id)):
								self.games.inform_players(this_game_id,self.code.game_won("You or your team won the game"))
								self.games.set_deadlock(this_game_id)
								self.lock.release()
								return
							self.lock.release()

							self.games.next_player(this_game_id) 									# move to next player
							player = self.games.get_player_in_turn(this_game_id)					# get the player
						else:
							self.log("Not valid shot")

					else:
						player.send(self.code.invalid_shot("Enter a valid shot"))




	# informs to every single player about the game boards
	# 	* player : the player to be informed
	#	* boards_from_friends : boards from team mates
	#	* boards_from_enemies : boards from enemies
	def inform_teams(self,players,boards_from_friends,boards_from_enemies,current_player=None):
		for player in players:
			if(player != current_player):
				player.send(self.code.boards_msg(boards_from_friends,boards_from_enemies))
				player.receive() 																	# acknowledgement received
			else:
				player.send(self.code.in_turn(self.code.boards_msg(boards_from_friends,boards_from_enemies)))


	# this is the lobby where the players wait for others to connect, max wait one minute
	def wait_for_players(self,this_game_id,player):
		while self.games.is_game_open(this_game_id):												# repeat while game is open
			if (self.games.waiting_too_long(this_game_id,time.time())):								# if waiting too much (> 1 munite)
				players = self.games.player_game_players(player)									# all the player in this game
				for p in players:
					p.send(self.code.waiting_termination())											# inform all that the waiting is over
					p.receive()
				self.games.set_deadlock(this_game_id)												# send the POLICE to fix it
				return False
		return True


	
	# join an existing game
	def join_game(self,player):
		available_games = self.games.open_games()
		if (len(available_games)== 0):																# sorry not available games
			player.send(self.code.no_open_games()) 													# msg = "no game"
			player.deactivate() 																	# send back to the main menu (MODERATOR)
			return

		player.send(self.code.open_games(available_games)) 											# there are available games
		self.code.translate(player.receive())

		if (not self.code.is_quitting_option):
			game_selected = self.code.game_to_join	

			player.send(self.code.teams())
			msg = player.receive()
			self.code.translate(msg)

			player.set_initial_time()
			self.games.update_game_player(game_selected, player,self.code.team)
			return 																					# wait for the game to start
		player.deactivate()


	# medals option
	def medals(self,player):
		player.send(self.code.medals(player.games_won ,
									 player.games_lost,
									 player.games_quit))

	# help
	def help(self,player):
		player.send(self.code.acknowledgement())

