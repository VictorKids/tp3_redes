import sys
import socket
import selectors

# #########################################################
# UTILITIES
# #########################################################

def to_2bytes(_inte):
    inte = bin(_inte)
    inte = inte[2:]
    while len(inte) < 16:
        inte = '0' + inte
    return inte

def to_4bytes(_inte):
    inte = bin(_inte)
    inte = inte[2:]
    while len(inte) < 32:
        inte = '0' + inte
    return inte

def make_header(t, did):
    global msg_count
    if   t == 1:
        type = "0000000000000001" 
    elif t == 2:
        type = "0000000000000010"
    elif t == 3:
        type = "0000000000000011"
    elif t == 4:
        type = "0000000000000100"
    else:
        type = "0000000000000101"
    return type + id + to_2bytes(int(did)) + to_2bytes(msg_count)

def send_OK(did, sock, numseq):
    global id
    str_msg = "0000000000000001" + id + did + numseq + "OK"
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
        ready_msg = make_header(5, d_id) + to_4bytes(len(msg)) + msg
        sent   = sock.send(ready_msg.encode())
        while True:
            ack = sock.recv(1024)
            ack = ack.decode()
            if ack[0:16] == "0000000000000001":
                break
            else:
                print("[ERROR] servidor mandou uma msg que não é um ACK")
        msg_count += 1
    elif in_str[0] == "S":
        global sel
        end_msg = make_header(4, "1111111111111111") + "END"
        sent    = sock.send(end_msg.encode())
        while True:
            ack = sock.recv(1024)
            ack = ack.decode()
            if ack[0:16] == "0000000000000001":
                break
            else:
                print("[ERROR] servidor mandou uma msg que não é um ACK")
        sel.unregister(sock)
        sel.unregister(sys.stdin.fileno())
        sock.close()
        sys.exit("[END] encerrando cliente")
    else:
        print(f"[ERROR] {in_str[0]} não é um comando válido")

# #########################################################
# SERVER COMUNICATION FUNCTION
# #########################################################

def read_server(sock):
    data = sock.recv(1024)
    if data:
        data = data.decode()
        msg_type  = data[0:16]
        origin_id = data[16:32]
        destin_id = data[32:48]
        seq_num   = data[48:64]
        _message   = data[64:]
        if msg_type == "0000000000000101": # MSG
            msg_tam = _message[0:32]
            message = _message[32:]
            print(f"Mensagem de {origin_id}: {message}")
            send_OK("1111111111111111", sock, seq_num)
        elif msg_type == "0000000000000010": # ERRO
            print("[ERROR] servidor reportou um erro")
        else:
            print("[ERROR] servidor mandou uma mensagem de tipo indefinido")
    else:
        pass

# #########################################################
# INITIAL SET UP
# #########################################################

sel = selectors.DefaultSelector()
msg_count = 0

id        = to_2bytes(int(sys.argv[1]))
serv_ip   = sys.argv[2]
serv_port = int(sys.argv[3])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#sock.setblocking(False) #!!!!!!!!!!!!!!
sock.connect_ex((serv_ip,serv_port))
print("[SYNC] achei o servidor")
hello_msg = make_header(3, "1111111111111111") + "oi"
_ = sock.send(hello_msg.encode())
while True:
    _ack = sock.recv(1024)
    _ack = _ack.decode()
    if _ack[0:16] == "0000000000000001":
        print("[CONN] conexão com o servidor estabelecida")
        break
    else:
        print("[ERROR] servidor mandou uma msg que não é um ACK")
sel.register(sock, selectors.EVENT_READ, data="rede")
#sel.register(sys.stdin.fileno(), selectors.EVENT_READ, data="input")

# #########################################################
# MAIN LOOP
# #########################################################

try:
    while True:
        print("in loop")
        events = sel.select(timeout=None)
        if events:
            print("there is a event")
            for key, mask in events:
                if key.data == "rede":
                    print("rede")
                    read_input(sock)
                elif key.data == "input":
                    print("input")
                    read_server(sock)
except:
    print("[ERROR] algo não funcionou bem..")