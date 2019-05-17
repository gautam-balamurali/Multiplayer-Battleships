#server

import sys
import player
import threading
import traceback
from socket import *
import gameserver as gs
from random import randint
import securedsocket as ss
import configurationmanager as cm

PORT = randint(0,5000) 		# starts from a random port


def get_new_socket(player_socket):
	global PORT
	PORT += 1
	port_min = cm.tcp_server_min_port
	port_max = cm.tcp_server_max_port
	tcp_port = (port_min + PORT) % port_max

	temp_socket = socket(AF_INET, SOCK_STREAM)
	temp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

	try:
		player_socket.send(str(tcp_port))
		temp_socket.bind(('', tcp_port))
		temp_socket.listen(15)
		new_player_socket,address = temp_socket.accept()
	except socket.timeout:
		print("Socket timeout. Port may have been used recently. wait and try again!")
		return None,tcp_port
	except:
		print("Socket error. Try again")
		return None,tcp_port
	finally:
		temp_socket.close()
	return ss.RSASocket(new_player_socket),address


# creates a server side player_object
def prepare_player(player_socket,game_server):
	name = player_socket.recv(1024)
	new_player_socket = None
	while not new_player_socket:
		new_player_socket,new_address = get_new_socket(player_socket)

	udp_sending = new_player_socket.recv(1024)
	new_player_socket.send("ACK")
	ump_split = udp_sending[1:-1].split(",")
	udp_address_sending = ump_split[0][1:-1],int(ump_split[1])

	udp_receiving = new_player_socket.recv(1024)
	new_player_socket.send("ACK")
	ump_split = udp_receiving[1:-1].split(",")
	udp_address_receiving = ump_split[0][1:-1],int(ump_split[1])

	p = player.Player(name,new_player_socket,new_address,udp_address_sending,udp_address_receiving)

	game_server.add_player(p)
	player_socket.close()

# to use the UDP socket
def ping_response():
	ping_socket = socket(AF_INET, SOCK_DGRAM)
	ping_socket.bind(('', cm.udp_ping_port))   # for pinging
	while not server_quitting:
		msg,address = ping_socket.recvfrom(1024)
		if (msg.decode() == "OPEN"):
			ping_socket.sendto(msg,address)
	ping_socket.close()


# 
def main():
	global server_quitting 								# for the future
	threads = []
	game_server = None

	try:
		server_quitting = False

		# this is to verify if the server is up (UPD)
		t = threading.Thread(target=ping_response)
		t.start()
		threads.append(t)

		maximum_connected = cm.maximum_connected
		server_socket = socket(AF_INET,SOCK_STREAM)
		server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		server_socket.bind(('',cm.tcp_server_port)) 				# game socket
		server_socket.listen(maximum_connected)

		chat_socket = socket(AF_INET, SOCK_DGRAM)
		chat_socket.bind(('', cm.udp_server_port))					# chat room socket
		chat_socket = ss.RSASocket(chat_socket)

		# create the game server
		game_server = gs.TheGameServer(maximum_connected,chat_socket)
		
		# entry door for incoming players
		while not server_quitting:
			playersocket, addr = server_socket.accept()
			if (not server_quitting):
				ss_socket = ss.RSASocket(playersocket)
				t = threading.Thread(target=prepare_player,args=(ss_socket,game_server))
				t.start()
				threads.append(t)
				print("New player registered and waiting for more")
			else: 
				# no more connections allowed
				playersocket.send("no more connections allowed".encode())
				playersocket.close()
	except KeyboardInterrupt:
		if (game_server):
			game_server.quit()
		game_down = True
		print("Keyboard Interrupt. Time to say goodbye!!!")
	except Exception as e:
		print(e)
		traceback.print_exc(file=sys.stdout)
	finally:
		for t in threads:
			t.join()
		if (game_server):
			game_server.quit()
		print("Waiting for all active games to finish")
	print("The end")
	sys.exit(0) 


if __name__ == "__main__":
	main()
