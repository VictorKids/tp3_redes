import sys
import socket
import selectors
# #########################################################
# INPUT READ FUNCTION
# #########################################################

def read_input():
    pass

# #########################################################
# SERVER COMUNICATION FUNCTION
# #########################################################

def read_server():
    pass

# #########################################################
# INITIAL SET UP
# #########################################################

sel = selectors.DefaultSelector()
msg_count = 0

id        = sys.argv[1]
serv_ip   = int(sys.argv[2])
serv_port = int(sys.argv[3])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setblocking(False) #!!!!!!!!!!!!!!
sock.connect_ex((serv_ip,serv_port))
print("[SYNC] achei o servidor")
sel.register(sock, selectors.EVENT_READ, data="rede")
sel.register(sys.stdin, selectors.EVENT_READ, data="input")

# #########################################################
# MAIN LOOP
# #########################################################

try:
    while True:
        events = sel.select(timeout=None)
        if events:
            for key, mask in events:
                if key.data == "rede":
                    read_input()
                elif key.data == "input":
                    read_server()
except:
    pass