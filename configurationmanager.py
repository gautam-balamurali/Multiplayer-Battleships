import configparser

# Globals
CONFIG_FILE = 'gameserver.cfg'
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_FILE)

def default_config(name):
    return CONFIG['DEFAULT'][name]

tcp_server_port = int(default_config("TCP_SERVER_PORT"))
tcp_server_min_port = int(default_config("TCP_SERVER_MIN_PORT"))
tcp_server_max_port = int(default_config("TCP_SERVER_MAX_PORT"))
udp_server_port = tcp_server_port + 50000
udp_ping_port = tcp_server_port + 5000
server_host = default_config("SERVER_HOST")
client_is_running = default_config("CLIENT_RUNNING") == "True"
maximum_connected = int(default_config("MAX_USER_SUPPORT"))
