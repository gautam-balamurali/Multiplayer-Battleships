
import os
import sys
import threading
from socket import *
import warcode as wc
import configurationmanager as cm
import securedsocket as ss
import sys, traceback




class ClientChat:
    def __init__(self,send_udp_socket,recv_udp_socket,name):
        self.name = name.strip()
        print("Hi " + self.name.upper() + ", welcome to the battleship game!")

        self.running = True
        self.messages = []
        self.threads = []
        self.host_name = cm.server_host
        self.udp_server_port = cm.udp_server_port
        self.code = wc.WarCode()

        # prepare for UDP transmission (chat room)
        self.udp_send_socket = ss.RSASocket(send_udp_socket)
        self.udp_recv_socket = ss.RSASocket(recv_udp_socket)

        # thread to handle messages reception
        msg_reception_t = threading.Thread(target=self.handle_udp_msg_reception)
        msg_reception_t.daemon = True
        msg_reception_t.start()
        self.threads.append(msg_reception_t)

        # thread to handle messages display
        msg_handler_t = threading.Thread(target=self.handle_udp_msg_display)
        msg_handler_t.daemon = True
        msg_handler_t.start()
        self.threads.append(msg_handler_t)

    # finishes all the ports
    def quit(self):
        self.running = False
        temp_socket = socket(AF_INET, SOCK_DGRAM)
        temp_socket.sendto("Bye".encode(), (self.host_name, self.udp_server_port))
        for t in self.threads:                  # stops threads
            t.join()
        try:
            temp_socket.close()
            self.udp_send_socket.close()
            self.udp_recv_socket.close()
        except:
            pass


    # reads message from socket continuously
    def handle_udp_msg_reception(self):
        print("\tRECEPTION: TID = ", threading.current_thread())  ####################
        while self.running:
            decoded_msg, address = self.udp_recv_socket.recvfrom(1024)
            self.code.translate(decoded_msg)
            if (self.code.is_acknowledgement):
                continue 														# if it is an acknowledgement dont addit to the spool
            self.udp_recv_socket.sendto(self.code.acknowledgement(),address)
            self.messages.append(decoded_msg)
        print("\tRECEPTION: thread finished")  ####################

    # pop messages from the messages spool
    def handle_udp_msg_display(self):
        while self.running:
            if (self.messages != []):
                print(self.messages.pop() + "\n")


    # this will send a message to the chat room
    def send_msg(self, message):
        try:
            msg_tokens = message.split(" ")
            com = msg_tokens[0]
            msg = self.name + ": " + " ".join(msg_tokens[1:])
            if (com == "-g"):
                coded_message = self.code.game_message(msg)
            elif (com == "-t"):
                coded_message = self.code.team_message(msg)
            elif (com == "-p"):
                player_name = msg_tokens[1][1:] if msg_tokens[1].find("-")==0 else "*"
                msg = self.name + ": " + " ".join(msg_tokens[2:])
                coded_message = self.code.player_message(player_name,msg)
            else:
                coded_message = self.code.public_message(self.name + ": " + message)
            self.udp_send_socket.sendto(coded_message, (self.host_name, self.udp_server_port))
        except Exception as e:
            print(e)
            traceback.print_exc(file=sys.stdout)


def main():
    code = input("Please enter the given code ")
    try:
        chat_file_name = "client" + code
        with open(chat_file_name, "r") as my_file:
            lines = my_file.readlines()
        os.remove(chat_file_name)
        name = lines[0]
        udp_send = lines[1].split(",")
        print(" sending host " + udp_send[0] + "port   " + udp_send[1])
        udp_recv = lines[2].split(",")
        print(" receiving host " + udp_recv[0] + "port   " + udp_recv[1])

        print(str((udp_send[0][1:-1], int(udp_send[1]))))

        send_udp_socket = socket(AF_INET, SOCK_DGRAM)
        send_udp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        send_udp_socket.bind((udp_send[0][1:-1], int(udp_send[1])))


        recv_udp_socket = socket(AF_INET, SOCK_DGRAM)
        recv_udp_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        recv_udp_socket.bind((udp_recv[0][1:-1], int(udp_recv[1])))

        print("bound")
        client_chat = ClientChat(send_udp_socket,recv_udp_socket,name)
    except Exception as e:
        print(e)
        print("Unexpected error")
        return

    try:
        running = True
        print("Legend to send messages :")
        print("prefix -g\tto all players in this game : '-g Lets start guys ' ")
        print("prefix -t\tto all players in your team : '-t We won guys ' ")
        print("prefix -p\tto a -player in this server : '-p -bob finish him!! ' ")
        while running:
            running = cm.client_is_running
            msg = input(":")
            client_chat.send_msg(msg)
        client_chat.quit()
    except:
        pass
    finally:
        sys.exit(0)



if __name__ == "__main__":
    main()