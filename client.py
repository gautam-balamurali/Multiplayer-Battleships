"""
This is the client of the Battlefield game
it is implemented to be a dummy client
just receive and send messages (no game logic)
reponsibilities:
	* connect to the server(TCP)
		this is the actual game
		select game mode (SINGLE|MULTIPLAYER|JOIN)
		shoot (send coordinates and board)
		show current board to the player (MULTIPLAYER)
		interprets server's warcodes

	* communicate to the server's chat room (UDP)
		send messages to the chat room (all will be public messages)
		receive messages frm the chat room and display them to the player

"""
#client
import traceback
from socket import *
import warcode as wc
import sys
import configurationmanager as cm
from random import randint
import battleshiphelp as h
import securedsocket as ss 





SINGLE_PLAYER_OPTION 	= "1"
MULTI_PLAYER_OPTION 	= "2"
JOIN_PLAYER_OPTION 		= "3"
QUIT_OPTION 			= "4"


class User:

	def __init__(self,name):
		self.name = name
		self.host_name = cm.server_host
		self.tcp_port = cm.tcp_server_port
		self.threads = []
		self.messages = []
		self.running = True
		self.code = wc.WarCode()									# war codes translator


	def quit(self):
		self.running = False
		for t in self.threads:
			t.join() 
		try:
			self.sslsocket.close()
		except:
			pass


	def set_connections_threads(self):
		print("Connecting server to port ..." + str(self.tcp_port))
		temp_socket = socket(AF_INET, SOCK_STREAM)
		temp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		temp_socket.connect((self.host_name,self.tcp_port))

		temp_socket = ss.RSASocket(temp_socket)
		temp_socket.send(self.name)

		# preparing new port
		plain_socket = socket(AF_INET, SOCK_STREAM)
		plain_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		self.sslsocket = ss.RSASocket(plain_socket) 					# encrypted socket

		error = True
		while error:
			try:
				port = int(temp_socket.recv(1024))
				self.sslsocket.connect((self.host_name, port))					# connect to the new port
				error = False
			except Exception as e:
				print(e)
				traceback.print_exc(file=sys.stdout)
				return False

		temp_udp_port = randint(2000,60000)
		temp_udp_server_socket = socket(AF_INET, SOCK_DGRAM)
		temp_udp_server_socket.bind(('', temp_udp_port))

		# to find out what port is assigned to the udp sender socket
		temp_send_udp_client_socket = socket(AF_INET, SOCK_DGRAM)
		temp_send_udp_client_socket.sendto("Test".encode(), (cm.server_host, temp_udp_port))

		_,chat_sending_address =  temp_udp_server_socket.recvfrom(1024)
		self.sslsocket.send(str(chat_sending_address))
		self.sslsocket.recv(1024)

		# to find out what port is assigned to the udp receiver socket
		temp_recv_udp_client_socket = socket(AF_INET, SOCK_DGRAM)
		temp_recv_udp_client_socket.sendto("Test".encode(), (cm.server_host, temp_udp_port))

		_,chat_receiving_address =  temp_udp_server_socket.recvfrom(1024)
		self.sslsocket.send(str(chat_receiving_address))
		self.sslsocket.recv(1024)

		try:
			code = str(randint(0,10000))
			chat_file_name = "client" + code
			with open(chat_file_name, "a") as my_file:
				my_file.write(self.name + "\n")
				my_file.write(str(chat_sending_address)[1:-1] + "\n")
				my_file.write(str(chat_receiving_address)[1:-1])
			print("If you want to use the chat use this code: " + code)
		except Exception as e:
			traceback.print_exc(file=sys.stdout)
			print(e)
			print("Unexpected error, not chat client available")

		temp_socket.close()
		temp_recv_udp_client_socket.close()
		temp_send_udp_client_socket.close()
		return True



	# run
	def run(self):
		while self.running:
			self.menu()
			if(self.code.is_quitting_option):
				print("Good bye")
			elif (self.code.is_single_player_option):
				self.play_single()
			elif(self.code.is_multiplayer_option):
				self.play_multiplayer()
			elif(self.code.is_join_option):
				self.join_game()
			elif(self.code.is_medal_option):
				self.medals()
			elif(self.code.is_help_option):
				self.help()
			else:
				print("Wrong, please enter again")



	# follows the communication steps through the menu
	def menu(self):
		menu = self.code.translate(self.receive())
		print(menu)
		answer = str(input(": ")).upper()
		coded = self.code.main_option(answer)
		self.send(coded)
		self.code.translate(coded)
		self.running = not self.code.is_quitting_option


	# follows the communication steps through the game
	def play_single(self):
		quit = False
		while not quit :
			server_msg = self.receive()
			msg = self.code.translate(server_msg)
			if (self.code.is_boards):
				self.print_boards(msg)
			else:
				print(msg)
			enemies = self.code.enemies

			if(self.code.game_finished()):
				return

			valid = False
			ans = ""
			formatted_answer = ""
			while not valid:
				ans = input("Enter your coordinates x(0-5) y(0-5):")
				quit = ans.upper() == QUIT_OPTION
				if(quit):														# player wants to quit
					formatted_answer = self.code.quit() 						# code the quit message
					break 														# no validation needed
				if (len(ans.split())==2):
					ans = "4 " + ans
				valid = self.code.valid_shot(ans.strip(),enemies)

				if (not valid):
					print("Not valid values, please enter valid coordinates")
			if(not quit): 														# we are not quiting
				formatted_answer = self.code.shoot(ans.strip()) 				# we have a valid shoot
			self.send(formatted_answer) 										# send the resulting answer


	# creates a multiplayer game
	def play_multiplayer(self):
		valid_players = False
		msg = self.receive()
		while not valid_players:
			ans = input(self.code.translate(msg))
			try:
				quit = str(ans) == "Q"
				if (quit):
					return
				num = int(ans)
				valid_players = num > 1
			except Exception as e :
				print("Not a valid option, please enter valid number")
		self.send(self.code.players_option(num))
		self.play_game_together()


	# joins a game
	def join_game(self):
		valid_game = False
		msg = self.receive()
		self.code.translate(msg)
		if(self.code.no_game):
			print("No game open. Sending back to the main menu...")
			return
		while not valid_game:
			ans = input(self.code.translate(msg))
			try:
				quit = str(ans) == "Q"
				num = int(ans)
				valid_game = self.code.valid_game_option(str(ans)) or quit
			except Exception as e :
				print(e)
				traceback.print_exc(file=sys.stdout)
				print("Not a valid option, please enter valid number")
		self.send(self.code.game_option(str(num)))
		self.play_game_together()


	# this is the shared code for multiplayer-join options
	def play_game_together(self):
		valid_team = False
		msg = self.receive()

		while not valid_team:
			ans = input(self.code.translate(msg))
			try:
				quit = str(ans) == "Q"
				team = int(ans)
				valid_team = team > 0 and team < 6
			except:
				print("Not a valid team, please enter valid option")

		self.send(self.code.teams_option(team))
		print("Waiting for others players to connect...")


		msg = self.code.translate(self.receive())							# receive the initial board or waiting termination
		if(not self.code.abort_waiting):
			print(self.code.translate(msg)) 								# show to the player
			self.send(self.code.acknowledgement()) 							# send acknowledgement back

			while not quit :
				in_turn = False

				while not in_turn:
					msg = self.receive()
					all_boards_msg = self.code.translate(msg)
					in_turn = self.code.is_in_turn

					if (in_turn):
						self.print_boards(self.code.translate(all_boards_msg))
						enemies = self.code.enemies

					if (not in_turn and not (self.code.won or self.code.lost)):
						self.send(self.code.acknowledgement())			# send acknowledgement back
						print("Wait for your turn " + self.name)

					if (self.code.won or self.code.lost):  				# nothing else to do
						won_msg = "Congratulation you won!!"
						lost_msg = "You lost, good luck next time"
						print(won_msg if self.code.won else lost_msg)  # feedback to player
						if (self.code.won):
							self.send(self.code.acknowledgement())
						return


				valid = False
				formatted_answer = ""

				while not valid:
					ans = input("Enter the team and the coordinates team(#) x(0-5) y(0-5):")
					quit = ans.upper() == QUIT_OPTION
					if(quit):												# player wants to quit
						formatted_answer = self.code.quit() 				# code the quit message
						break 												# no validation needed
					valid = self.code.valid_shot(ans.strip(),enemies)
					if (not valid):
						print("Not valid, please enter again")
				if(not quit): 												# we are not quiting
					formatted_answer = self.code.shoot(ans.strip()) 		# we have a valid shoot
				self.send(formatted_answer) 								# send the resulting answer
		else:
			self.send(self.code.acknowledgement())

	# medals
	def medals(self):
		print(self.code.translate(self.receive()))

	# show help
	def help(self):
		self.receive()
		h.show_help()

	# sends a packet thru the sslsocket
	def send(self,msg):
		self.sslsocket.send(msg)

	# receive a packet thru the sslsocket
	def receive(self):
		return self.sslsocket.recv(1024)

	# formats the boards on the shell
	def print_boards(self,boards):
		e_index = boards.index("E")
		friend_section = boards[:e_index].strip().split(" ")
		enemy_section = boards[e_index:].strip().split(" ")
		self.print_section(friend_section)
		print("------------------------------------------------------------------")
		self.print_section(enemy_section)
		print("------------------------------------------------------------------")

	# prints one row of boards either the enemies of the friends
	def print_section(self,section):
		print("Friends" if section[0].strip() == "F" else "Enemies")
		lines = ["" for _ in range(7)]
		for board in section[1:]:
			comma = board.index(",")
			lines[0] += board[:comma].strip() + "        "
			board_line = board[comma+1:].split()
			for i in range(0,6):
				lines[i+1] += board_line[i] + "   "
		for line in lines:
			print(line)


def verification():
	udp_socket = socket(AF_INET, SOCK_DGRAM)
	verif =False
	try:
		udp_socket.sendto("OPEN".encode(),(cm.server_host,cm.udp_ping_port))
		udp_socket.settimeout(20)
		_,_ = udp_socket.recvfrom(1024)
		verif = True
	except socket.timeout:
		print("Server is down!!!")
	finally:
		udp_socket.close()
	return verif


# Entry point
def main():
	print("Welcome to the battleship game")
	sys.stdout.write("Verifying if the server is ready...")
	if(not verification()):
		return
	print("Done!!")

	user_name = input("Please enter your user name: ")
	print("Thank you " + user_name)
	u = User(user_name)
	try:
		ok = u.set_connections_threads()
		if not ok:
			return
		u.run()
	except KeyboardInterrupt:
		print("Keyboard Interrupt. Time to say goodbye!!!")
	except Exception as e:
		print(e)
		traceback.print_exc(file=sys.stdout)
		print("There was a problem. Game aborted")
	finally:
		u.quit()
		sys.exit(0) 
	

if __name__ == "__main__":
	main()

