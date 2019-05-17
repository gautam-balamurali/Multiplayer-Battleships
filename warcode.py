
import sys, traceback

"""
numbers used

100"	# War is on!
101"	# Server is full, try later
102"	# This is shot
103"	# this is your turn
104"  	# Acknowledgement
108"	# Enemy missed
109"	# You've being hit
110"	# You hit a ship
111"	# You missed
113"	# Player down!!
120"	# Victory
121"	# You lost
122       boards
123     server is down
124     wrong shot values need validation
125     # There was an error
126 	#  games
127 	#  selected game to join
128 	# no open games
129 	# main menu
130  	
131
132
133
134		# main menu option
135 	# join option 
136 	# players counting
137 	# players count option
138 	# shoot option

140 	# this is your board
141 	# name
142 	# chat message
143 	# abort waiting


150"	# Quitting

"""
# menu options
SINGLE_PLAYER_OPTION 	= "1"
MULTI_PLAYER_OPTION 	= "2"
JOIN_PLAYER_OPTION 		= "3"
MEDAL_OPTION 			= "4"
HELP_OPTION 			= "5"
QUIT_OPTION 			= "6"
QUIT_LETTER				= "Q"
FRIENDS 				= "F"
ENEMIES 				= "E"
PLAYER 					= "P"


BLUE_TEAM = "BLUE"
RED_TEAM = "RED"
YELLOW_TEAM = "YELLOW"
GREEN_TEAM = "GREEN"
SINGLE_PLAYER_TEAM = "WHITE"

class WarCode:

	def __init__(self):
		# general mesages
		self.CODE_ACK   = "104"  	# Acknowledgement
		self.CODE_SRV_F = "101"		# Server is full, try later
		self.CODE_SVR_D = "123"		# Server is down
		self.CODE_ERROR = "125"		# Error
		self.CODE_NAME  = "141" 	# name

		# main menu messages
		self.CODE_MAINM = "129" 	# main menu
		self.CODE_MAINO = "134" 	# main menu option
		self.CODE_AVA_G = "126"		# available games
		self.CODE_GAMEO = "127" 	# selected game to join
		self.CODE_NO_GA = "128" 	# no open games
		self.CODE_PL_CN = "136" 	# how many players?
		self.CODE_PL_CO = "137"		# how many players option
		self.CODE_PL_TM = "138" 	# which team?
		self.CODE_PL_TO = "139" 	# this is the team
		self.CODE_QIT   = "150"		# Quitting
		self.CODE_QUI_W = "138" 	# quit waiting?
		self.CODE_ABRTW = "143"		# abort waiting

		#games messages
		self.CODE_SHO   = "102"		# This is shot
		self.CODE_INV_S = "124" 	# invalid shot
		self.CODE_TURN  = "103"		# this is your turn
		self.CODE_E_MIS = "108"		# Enemy missed
		self.CODE_HIT   = "110"		# You hit a ship
		self.CODE_LST   = "121"		# You lost
		self.CODE_E_HIT = "109"		# You've being hit
		self.CODE_MIS   = "111"		# You missed
		self.CODE_PLD   = "113"		# Player down!!
		self.CODE_WAR   = "100"		# War is on!
		self.CODE_WON   = "120"		# Victory
		self.CODE_BRDS  = "122"		# Boards
		self.CODE_BOARD = "140" 	# this is your board
	
		# chat messages		
		self.CODE_CHATM = "142"		# chat message
		self.CODE_PUB_M = "130" 	# public message
		self.CODE_TEA_M = "131" 	# team message
		self.CODE_GAM_M = "132" 	# messages for the players in the current game
		self.CODE_PLA_M = "133" 	# private message
		
		# state variables
		self.reset_state()



	def receive_shoot(self,msg):
		tok = msg.split()
		return tok[0] == self.CODE_SHO, int(tok[1]), int(tok[2])

	def reset_state(self):
		self.is_in_turn = False
		self.won = False
		self.lost = False
		self.is_acknowledgement = False
		self.is_valid = False
		self.is_a_shoot = False
		self.is_quitting_option = False
		self.is_single_player_option = False
		self.is_multiplayer_option = False
		self.is_medal_option = False
		self.is_help_option = False
		self.is_boards = False
		self.no_game = False
		self.enemies = ""
		self.is_join_option = False
		self.addr = None
		self.abort_waiting = False
		self.name = None
		self.board = -1
		self.x = -1
		self.y = -1	
		self.players = 0
		self.game = None
		self.game_to_join = ""
		self.games_to_join = []
		self.team = None
		self.is_public_msg = False
		self.is_game_message = False
		self.is_team_message = False
		self.is_player_message = False
		self.to_player = None

	#
	def translate(self,msg):
		self.reset_state()
		try:
			tok = msg.split(" ")
			returning_msg = ""

			if (len(tok)>1):
				returning_msg = msg.split(" ",1)[1]
			if (tok[0] == self.CODE_SHO):
				self.board = int(tok[1])
				self.x = int(tok[2])
				self.y = int(tok[3])
				self.is_valid = True
				self.is_quitting_option = False
				self.is_a_shoot = True
			elif (tok[0] == self.CODE_HIT):
				return returning_msg
			elif (tok[0] == self.CODE_MIS):
				return returning_msg
			elif (tok[0] == self.CODE_E_HIT):
				return returning_msg
			elif (tok[0] == self.CODE_E_MIS):
				return returning_msg
			elif (tok[0] == self.CODE_BOARD): ###
				return returning_msg
			elif (tok[0] == self.CODE_BRDS): ###
				self.is_boards = True
				enemies_section = msg.split("E")				# get the enemies
				s_tok = enemies_section[1].split(" ")			
				self.enemies = ""
				for t in s_tok:
					if "," in t:
						self.enemies += (t.split(",")[0]).strip() + " "
				self.enemies = self.enemies.strip()
				return returning_msg
			elif (tok[0] == self.CODE_AVA_G):
				self.games_to_join = tok[1:]
				return returning_msg
			elif (tok[0] == self.CODE_MAINM):
				return returning_msg
			elif (tok[0] == self.CODE_TURN):
				self.is_in_turn = True
				return returning_msg
			elif (tok[0] == self.CODE_MAINO):
				opt = tok[1]
				self.is_quitting_option 		= opt == QUIT_OPTION
				self.is_single_player_option 	= opt == SINGLE_PLAYER_OPTION
				self.is_multiplayer_option 		= opt == MULTI_PLAYER_OPTION
				self.is_join_option   			= opt == JOIN_PLAYER_OPTION
				self.is_medal_option 			= opt == MEDAL_OPTION
				self.is_help_option 			= opt == HELP_OPTION
				return returning_msg
			elif (tok[0] == self.CODE_WON):
				self.won = True
				return returning_msg
			elif (tok[0] == self.CODE_LST):
				self.lost = True
				return returning_msg
			elif (tok[0] == self.CODE_QIT):
				self.is_quitting_option = True
				return returning_msg
			elif (tok[0] == self.CODE_QUI_W):
				self.is_quitting_option = True
				return returning_msg
			elif (tok[0] == self.CODE_INV_S):
				return returning_msg
			elif (tok[0] == self.CODE_ERROR):
				return returning_msg
			elif (tok[0] == self.CODE_ACK):
				self.is_acknowledgement = True
				return returning_msg
			elif (tok[0] == self.CODE_GAMEO):
				self.game_to_join = tok[1]
				self.is_quitting_option = tok[1] == QUIT_LETTER
				self.is_valid = True
				return None
			elif (tok[0] == self.CODE_CHATM):
				if(tok[1] == "-p"):
					self.is_player_message = True
					if (len(tok)>2):
						self.to_player = tok[1]
				elif (tok[1] == "-g"):
					self.is_game_message = True
				elif (tok[1] == "-t"):
					self.is_team_message = True
				else:
					self.is_public_msg = True
				return returning_msg.split(" ",1)[1]
			elif (tok[0] == self.CODE_GAM_M):
				self.is_game_message = True
				return returning_msg
			elif (tok[0] == self.CODE_PUB_M):
				self.is_public_msg = True
				return returning_msg
			elif (tok[0] == self.CODE_TEA_M):
				self.is_team_message = True
				return returning_msg
			elif (tok[0] == self.CODE_PLA_M):
				self.is_player_message = True
				self.to_player = tok[1]
				return returning_msg.split(" ",1)[1]
			elif (tok[0] == self.CODE_PL_CN):
				return returning_msg 
			elif (tok[0] == self.CODE_PL_CO):
				self.players = int(tok[1])
				return returning_msg 
			elif (tok[0] == self.CODE_PL_TM):
				return returning_msg
			elif (tok[0] == self.CODE_PL_TO):
				self.team = tok[1]
				return returning_msg
			elif (tok[0] == self.CODE_NO_GA):
				self.no_game = True
				return returning_msg
			elif (tok[0] == self.CODE_NAME):
				self.name = tok[1]
				return returning_msg
			elif (tok[0] == self.CODE_ABRTW):
				self.abort_waiting = True
				return returning_msg
			else:
				return " ".join(tok)
			
		except Exception as e:
			print(e)
			traceback.print_exc(file=sys.stdout)
			self.reset_state()


	#returns the coordinates of the last shot
	def shot(self):
		return self.board,self.x,self.y

	# validates if the shot is to an enemy 
	def valid_shot(self,shot,enemies):
		tok = shot.split()
		try:
			board = tok[0]
			if board not in enemies:
				return False
			self.board = int(board)
			x = int(tok[1])
			y = int(tok[2])
			return True
		except Exception as e:
			print(e)
			return False
	
	# returns the team string from its index
	def get_team(self,team):
		if (team == 1):
			return BLUE_TEAM
		elif (team == 2):
			return RED_TEAM
		elif (team == 3):
			return YELLOW_TEAM
		else:
			return GREEN_TEAM


	# game is over
	def game_finished(self):
		return self.won or self.lost

	# tuple address to str address
	def addr_to_str(self,addr):
		ip,port = addr
		return ip + "," + str(port)

	# from string address to a tuple
	def addr_to_tuple(self,addr):
		nums = addr.split(",")
		ip = nums[0]
		port = int(nums[1])
		return ip,port

	# to validate the join game option 
	def valid_game_option(self,option):
		temp = self.games_to_join
		return option in temp
		



	# This section is to encode messages
	

	# menu section
	# main menu
	def main_menu(self):
		return  self.CODE_MAINM  + " " 				\
				+ "\nMAIN MENU\n" 					\
				+ "1 Single player\n" 				\
				+ "2 Create a multiplayer board\n" 	\
				+ "3 Join a multiplayer board\n" 	\
				+ "4 See status\n"	 				\
				+ "5 Help\n"							\
				+ "6 Quit"

	# main menu selected option
	def main_option(self,option):
		return self.CODE_MAINO + " " + option

	# encode games available
	def open_games(self,game_ids):
		return self.CODE_AVA_G + " " + "Please select the game (enter the #)\n " + " ".join(game_ids) + " \n:"

	# no games open
	def no_open_games(self,msg=""):
		return self.CODE_NO_GA + " " + msg

	# join menu selected option
	def game_option(self,msg):
		return self.CODE_GAMEO + " " + msg

	# how many player for this game
	def players_count(self):
		return self.CODE_PL_CN + " " + "How many players for this game? :"

	# code the players selection
	def players_option(self,players_amount):
		return self.CODE_PL_CO + " " + str(players_amount)

	# wich team
	def teams(self):
		return self.CODE_PL_TM + " "  			\
				+ "\nTeams\n1\t" + BLUE_TEAM  	\
				+ "\n2\t" + RED_TEAM 			\
				+ "\n3\t" + YELLOW_TEAM 		\
				+ "\n4\t"	+ GREEN_TEAM 		\
				+ "\n5\tQuit\n: " 

	# code the players selection
	def teams_option(self,team):
		return self.CODE_PL_TO + " " + self.get_team(team)

	# code the shoot command
	def shoot(self,msg=""):
		return self.CODE_SHOOT + "Enter your shoot: " + msg
	
	# quit waiting
	def quit_waiting(self):
		return self.CODE_QUI_W + " " + "Quit waiting? \n1 yes\n2 no"

	# quit game
	def quit(self):
		return self.CODE_QIT + " Bye"

	# waiting termination
	def waiting_termination(self):
		return self.CODE_ABRTW + " to the main menu"





	# war section

	# inform the player that is in turn
	def in_turn(self,msg=""):
		return  self.CODE_TURN + " " + msg

	# shot message 
	def shoot(self,coords):
		return self.CODE_SHO + " " + coords

	# succeful shoot message 
	def hit(self,msg=""):
		return self.CODE_HIT + " You hit it, good job!! \n" + msg

	# failed shoot message 
	def miss(self,msg=""):
		return self.CODE_MIS + " Failed shot, good luck next time... \n" + msg

	# hit received from theenemy message 
	def enemy_hit(self,msg=""):
		return self.CODE_E_HIT + " May day may day!!... \n" + msg

	# failed shoot from the enemy message 
	def enemy_miss(self,msg=""):
		return self.CODE_E_MIS + " That was close captain!\n" + msg		

	# encode a list of boards
	def boards(self,boards):
		return self.CODE_BRDS + " " + " ".join(boards)

	# encode a board
	def serve_board(self,board):
		return self.CODE_BOARD + " This is your board\n" + board

	# encodes de final message to be sent to the player with all players boards
	def boards_msg(self,boards_from_friends,boards_from_enemies):
		result_list = []

		friends = FRIENDS + "\n"
		for g_id,board_str in boards_from_friends:
			friends += " " + g_id + "\n,\n" + board_str

		enemies = ENEMIES + "\n"
		for g_id,board_str in boards_from_enemies:
			enemies += " " + g_id + "\n,\n" + board_str

		return self.boards([friends,enemies])




	# outcome section
	# game won
	def game_won(self,msg=""):
		return self.CODE_WON + " " + msg

	# game lost
	def game_lost(self,msg=""):
		return self.CODE_LST + " " + msg

	# game quitting
	def game_quitting(self,msg=""):
		return self.CODE_LST + " " + msg	

	# invalid shot
	def invalid_shot(self,msg=""):
		return self.CODE_QIT + " " + msg

	# medals info
	def medals(self,won,lost,quit):
		return "GAMES\tWON\tLOST\tQUIT\n" + "\t" 	\
			   + str(won) + "\t" 					\
			   + str(lost) + "\t" 					\
			   + str(quit) +"\n"






	# chat room section
	# public message
	def public_message(self,msg=""):
		return self.CODE_PUB_M + " " + msg

	# game message
	def game_message(self,msg=""):
		return self.CODE_GAM_M + " " + msg

	# team message
	def team_message(self,msg=""):
		return self.CODE_TEA_M + " " + msg

	# player message
	def player_message(self,player_name,msg=""):
		return self.CODE_PLA_M  + " " + player_name + " " + msg

	# chat message
	def chat_message(self,msg=""):
		return self.CODE_CHATM + " " + msg







	# misc section
	# server is down
	def server_down(self,msg=""):
		return self.CODE_SVR_D + " " + msg
	
	# some error occurred
	def error(self,msg=""):
		return self.CODE_ERROR + " " + msg

	# acknowledgement
	def acknowledgement(self, msg=""):
		return self.CODE_ACK + " " + msg

