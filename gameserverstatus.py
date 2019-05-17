import time
import player
import warcode as wc
import sys, traceback


BLUE_INDEX = 0
RED_INDEX = 1
YELLOW_INDEX = 2
GREEN_INDEX = 3
WHITE_INDEX = 4


BLUE_TEAM = "BLUE"
RED_TEAM = "RED"
YELLOW_TEAM = "YELLOW"
GREEN_TEAM = "GREEN"
WHITE_TEAM = "WHITE"

class ServerStatus:

	def __init__(self,max):
		self.game_id = 0											# game id will increase for every game initiated
		self.players = []											# list of all active players in the game
		self.max_player_connected = max 							# maximum amount of connected players
		self.code = wc.WarCode()

		# contains a list with all players connected to the server
		# an index (game_id) to identify each game

		# special structure: games (dictionary)
		# this instance variable has all the information about all games in the server
		# the keys are accessed through game_id (integer incremented every tome a game is created)
		# the values are formed by:
		# 	teams : dictionary of players per team (dictionary of players lists)
		#	max_player : maximum amount of player allowed (integer) in this game
		# 	open : game status true = receiving players (boolean)
		#	deadlock : indicates if the game is in deadlock (boolean)
		# 	timestamp : to control the waiting time of the user to avoid deadlock (time)
		self.games = {}


	# "creates" another key for a new game and returns it
	def new_game_id(self):
		self.game_id += 1
		return self.game_id

	# adds a single player game
	def add_singleplayer_game(self,this_game_id,player):
		self.add_multiplayer_game(this_game_id,player,1,WHITE_TEAM)

	# adds a new game & player to the server_games		
	def add_multiplayer_game(self,this_game_id,player,max_players,team):
		player.team = team 											# redundant(below) but used to improve efficiency
		player.activate(this_game_id)								# player was assigned a board
		teams = {}	 												# a dictionary of players per teams
		teams[team] = [player],0									# first player in this team, player in turn
		is_open = team != WHITE_TEAM

		self.games[this_game_id] = 	\
			{							
				"teams" 	: teams,								# game teams 
				"pl_count" 	: 1, 									# how many players desired
				"max_player": max_players, 							# max players allowed
				"open"		: is_open,								# an open game is missing players
				"deadlock" 	: False,								# a new game is never in deadlock
				"timestamp" : time.time(),							# to control how long this user is waiting for other players
				"turn"		: self.get_team_index(team)				# first turn for this player
			}


	# is the player waiting too much?
	def waiting_too_long(self,this_game_id,time):
		return time - self.games[this_game_id]["timestamp"] > 60 	# one minute is OK, no more


	# adds a player to a team in an open game in the server_games
	def update_game_player(self,this_game_id, player,team):
		teams = self.games[this_game_id]["teams"]
		player.game = this_game_id 									# to improve efficiency
		player.team = team 											# to improve efficiency

		if (team in teams): 										# is there are players in the team
			players,turn = teams[team] 								# get the players
			players.append(player) 									# add them to the team
		else:
			players = [] 											# no players in that team create a list
			players.append(player) 									# append this player
			teams[team] = players,0 								# create the team in the tree

		self.games[this_game_id]['open'] = 	len(self.player_game_players(player)) < self.games[this_game_id]["max_player"]


	def remove_player(self,game_id,player):
		players,turn = self.games[game_id]["teams"][player.team]
		index = players.index(player)

		players.remove(player)
		if turn >= index:
			turn -= 1
		player.deactivate()
		if(players): 											# more players in the team???
			self.games[game_id]["teams"][player.team] = players, turn
		else:
			self.games[game_id]["teams"].pop(player.team,None)		# no more players, remove the team


	# fix any game in deadlock
	def detect_fix_deadLocks(self):
		for game_id in list(self.games):
			if(self.is_in_deadlock(game_id)): 
				self.release_game_resources(game_id)

	# rule that define a game in deadlock
	def is_in_deadlock(self, game_id):
		return self.games[game_id]["deadlock"]

	# Inactivates all the players in the specified game and removes the game from the server
	def release_game_resources(self, this_game_id):
		teams = list(self.games[this_game_id]["teams"])  				# all the team in the game
		game_won = not self.games[this_game_id]["open"]  				# the gae was played if it is not open: there is a winner
		for team in list(teams):
			team_players, _ = self.games[this_game_id]["teams"][team]  	# all the player in that team
			for player in team_players:
				player.deactivate()  									# inactivate all the player
		self.games[this_game_id]["teams"] = {}  						# just clears the team list and doesn't destroy the players
		self.games.pop(this_game_id, None)  							# remove this game from the variable


	# games finished
	def detect_fix_finished_games(self,msg):
		for game_id in list(self.games):
			if (self.is_finished(game_id)):
				self.inform_players(game_id,msg)
				self.release_game_resources(game_id)

	# rule that define a finished game
	def is_finished(self,game_id):
		teams = list(self.games[game_id]["teams"])
		return (len(teams) == 1  and  (teams[0]!= WHITE_TEAM  and not  self.games[game_id]["open"]))

	# inform the players of the game
	def inform_players(self,game_id,msg):
		for player in list(self.players):
			if(player.game == game_id):
				player.won_game()
				player.send(msg)
				str = player.receive()


	# this game is in deadlock
	def set_deadlock(self,game_id):
		teams = self.games[game_id]["deadlock"] = True


	# returns the all the players connected
	def server_players(self):
		return self.players

	# returns a list with all the players in the same game of the player
	def player_game_players(self,player):
		return [p for p in list(self.players) if p.game == player.game]

	# returns the list of all the player in the same team of the player 
	def player_team_players(self,player):
		return [p for p in list(self.players) if p.game == player.game and p.team == player.team]

	# adds a new player to the game server
	def add_player(self,player):
		self.players.append(player)

	# find a player by the name
	def find_player_by_name(self,name):
		try:
			if (not self.players):
				return None
			return next((p for p in list(self.players) if p.name == name),None)
		except Exception as e:
			print(e)
			traceback.print_exc(file=sys.stdout)

	# find a player by the addr in the list
	def find_player_by_tcp_address(self, address):
		if(not self.players):
			return None
		return next(p for p in list(self.players) if p.tcp_address == address)

	# find a player by the addr in the list
	def find_player_by_udp_sending_address(self, address):
		if (not self.players):
			return None
		return next(p for p in list(self.players) if p.udp_address_sending == address)

	# is server full?
	def is_full(self):
		return self.max_player_connected == len(self.players)

	# all the players
	def detect_inactive_player(self):
		for player in self.players:
			if(player.is_inactive()):
				return player
		return None

	# returns all open games
	def open_games(self):
		return [g_id for g_id in list(self.games) if self.games[g_id]["open"]]

	# returns if the game is open
	def is_game_open(self,game_id):
		return self.games[game_id]["open"]



	# returns the player in turn
	def get_player_in_turn(self,game_id):
		game = self.games[game_id] 							# this game
		teams = game["teams"]								# its teams
		team = self.get_team_str(game["turn"]) 				# team in turn
		players,turn = teams[team]							# get its players and turn
		if (players):
			turn = turn % len(players)
			return players[turn]
		return None


	# get next team in turn with players
	def next_team(self,game_id):
		if (game_id in self.games):
			game = self.games[game_id]   					# get the game
			teams = game["teams"]							# get the teams in that game
			turn = game["turn"] 							# get the team in turn
			there_is_team = False 							#
			while not there_is_team:						# iterate until there is a team with players
				turn = (turn + 1) % 4 						# next team
				team_str = self.get_team_str(turn) 			#
				there_is_team = team_str in teams 			# found the team
			return turn 									# return it
		return -1

	# changes the values of the internal variables to the next player
	def next_player(self,game_id):
		if (game_id in self.games):
			game = self.games[game_id] 										# this game
			teams = game["teams"]											# its teams
			turn = self.next_team(game_id)
			if (turn>=0):
				game["turn"] = self.next_team(game_id)						# next team
				players,turn = teams[self.get_team_str(game["turn"])]		# get its players and turn
				teams[self.get_team_str(game["turn"])] = players,turn+1 	# next player


	# returns the string representation for the team index
	def get_team_str(self,index):
		if (index == BLUE_INDEX):
			return BLUE_TEAM
		elif (index == RED_INDEX):
			return RED_TEAM
		elif (index == YELLOW_INDEX):
			return YELLOW_TEAM
		elif (index == GREEN_INDEX):
			return GREEN_TEAM
		else:
			return WHITE_TEAM

	# returns the index of the team
	def get_team_index(self,team):
		if (team == BLUE_TEAM):
			return BLUE_INDEX
		elif (team == RED_TEAM):
			return RED_INDEX
		elif (team == YELLOW_TEAM):
			return YELLOW_INDEX
		elif (team == GREEN_TEAM):
			return GREEN_INDEX
		else:
			return WHITE_INDEX

	# returns the player's teammates 
	def get_friends(self,game_id,player):
		team_mates,_ = self.games[game_id]["teams"][player.team] 		# all the players in the player's team
		return team_mates 												

	# return the list of all the player's enemies in the game
	def get_enemies(self,game_id,player):
		result = []
		teams = self.games[game_id]["teams"]							# this game's teams
		for team in list(teams):										# for all
			if (player.team == team):									# compare with player's team
				continue												# if it is the same team then get next team and do nothing
			players,turn = teams[team]									# get the players
			result.extend(players) 										# adds all the players of this team to the list
		return result 													# returns all the players


	


		








			




	

