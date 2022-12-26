import sys
import socket
import selectors

# #########################################################
# UTILITIES
# #########################################################

def to_size(inte, size):
    while len(inte) < size:
        inte = '0' + inte
    return inte

def make_header(t, did):
    global msg_count
    if   t == 1:
        type = "01" 
    elif t == 2:
        type = "02"
    elif t == 3:
        type = "03"
    elif t == 4:
        type = "04"
    else:
        type = "05"
    return type + id + to_size(did, 5) + to_size(str(msg_count), 5)

def send_OK(did, sock, numseq):
    global id
    str_msg = "01" + id + did + numseq + "OK"
    sent = sock.send(str_msg.encode())

# #########################################################
# INPUT READ FUNCTION
# #########################################################

def read_input(sock):
    in_str = input()
    if in_str[0] == "M":
        global msg_count
        in_str = in_str.split(" ", 2)
        #flag  = in_str[0]
        d_id   = in_str[1]
        msg    = in_str[2] 
        ready_msg = make_header(5, d_id) + to_size(str(len(msg)), 4) + msg
        sent   = sock.send(ready_msg.encode())
        while True:
            ack = sock.recv(1024)
            ack = ack.decode()
            if ack[0:2] == "01":
                break
            else:
                print("[ERROR] Servidor mandou uma msg que não é um ACK.")
        msg_count += 1
    elif in_str[0] == "S":
        global sel
        end_msg = make_header(4, "65535") + "END"
        sent    = sock.send(end_msg.encode())
        while True:
            ack = sock.recv(1024)
            ack = ack.decode()
            if ack[0:2] == "01":
                break
            else:
                print("[ERROR] Servidor mandou uma msg que não é um ACK.")
        sel.unregister(sock)
        sel.unregister(sys.stdin.fileno())
        sock.close()
        sys.exit("[END] Encerrando cliente.")
    else:
        print(f"[ERROR] {in_str[0]} não é um comando válido.")

# #########################################################
# SERVER COMUNICATION FUNCTION
# #########################################################

def read_server(sock):
    data = sock.recv(1024)
    if data:
        data = data.decode()
        msg_type  = data[0:2]
        origin_id = data[2:7]
        destin_id = data[7:12]
        seq_num   = data[12:17]
        _message   = data[17:]
        if msg_type == "05": # MSG
            msg_tam = _message[0:4]
            message = _message[4:]
            print(f"[RECV] Mensagem de {origin_id}: {message}.")
            send_OK("65535", sock, seq_num)
        elif msg_type == "02": # ERRO
            print("[ERROR] Servidor reportou um erro.")
        else:
            print("[ERROR] Servidor mandou uma mensagem de tipo indefinido.")
    else:
        pass

# #########################################################
# INITIAL SET UP
# #########################################################

sel = selectors.DefaultSelector()
msg_count = 0

id        = to_size(str(sys.argv[1]), 5)
serv_ip   = sys.argv[2]
serv_port = int(sys.argv[3])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect_ex((serv_ip,serv_port))
print("[SYNC] Achei o servidor.")
hello_msg = make_header(3, "65535") + "oi"
_ = sock.send(hello_msg.encode())
while True:
    _ack = sock.recv(1024)
    _ack = _ack.decode()
    if _ack[0:2] == "01":
        print("[CONN] Conexão com o servidor estabelecida.")
        break
    else:
        print("[ERROR] Servidor mandou uma msg que não é um ACK.")
sel.register(sock, selectors.EVENT_READ, data="rede")
sel.register(sys.stdin, selectors.EVENT_READ, data="input")

# #########################################################
# MAIN LOOP
# #########################################################

while True:
    events = sel.select(timeout=None)
    if events:
        for key, mask in events:
            if key.data == "input":
                read_input(sock)
            elif key.data == "rede":
                read_server(sock)

