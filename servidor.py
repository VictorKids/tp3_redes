import sys
import socket
import selectors

# #########################################################
# UTILITIES
# #########################################################

sel = selectors.DefaultSelector()
ID   = "65535"
class Clients:
    def __init__(self, id, socket, info):
        self.id = id
        self.socket = socket
        self.info = info
clients = []

# #########################################################
# ACCEPT FUNCTION
# #########################################################

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"[SYNC] recebendo conexão de {addr}.")
    data = "oi_dorgival"
    sel.register(conn, selectors.EVENT_READ, data=data)

# #########################################################
# READ FUNCTION
# #########################################################

def msg_read(client):
    data = client.recv(1024)
    if data:
        data = data.decode()
        msg_type  = data[0:2]
        origin_id = data[2:7]
        destin_id = data[7:12]
        seq_num   = data[12:17]
        message   = data[17:]

        if msg_type == "03": # OI
            print(f"[CONN] mensagem do tipo OI recebida de {origin_id}.")
            new_id_flag = True
            for c in clients:
                if c.id == origin_id:
                    new_id_flag = False
                    break
            if new_id_flag:
                clients.append(Clients(origin_id, client, client.getsockname()))
                send_OK(origin_id, client, seq_num)
            else:
                send_ERRO(origin_id, client, seq_num)

        else:
            security_check = False
            for c in clients:
                if c.id == origin_id and c.info == client.getsockname():
                    security_check = True
                    break
            if security_check == True:
                if   msg_type == "02": # ERRO
                    print(f"[ERROR] cliente {origin_id} não deveria mandar msgs do tipo ERRO ao servidor.")
                elif msg_type == "01": # OK 
                    print(f"[ACK] confirmação recebida de {origin_id}.")
                elif msg_type == "04": # FLW
                    print(f"[DCONN] desconectando cliente {origin_id}.")
                    send_OK(origin_id, client, seq_num)
                    for c in clients:
                        if c.id == origin_id:
                            sel.unregister(c.socket)
                            clients.remove(c)
                            client.close()
                            break
                elif msg_type == "05": # MSG
                    print(f"[MSG] mensagem recebida de {origin_id} para {destin_id}.")
                    if destin_id == "00000":
                        send_broadcast(origin_id, destin_id, message, client, seq_num)
                    else:
                        destin_flag = False
                        for c in clients:
                            if c.id == destin_id:
                                tmp = c
                                destin_flag = True
                                break
                        if destin_flag:
                            send_OK(origin_id, client, seq_num)
                            send_unicast(origin_id, destin_id, message, tmp, seq_num)
                        else:
                            send_ERRO(origin_id, client, seq_num)
                            send_back(origin_id, seq_num, message, client)                        
            else:
                send_ERRO(origin_id, client, seq_num) 
                print(f"[ERROR] {origin_id} não existe ou alguém tentou se passar por {origin_id}.")
    else:
        pass  

# #########################################################
# SEND FUNCTIONS
# #########################################################

def send_OK(id, cli, numseq):
    str_msg = "01" + ID + id + numseq + "OK"
    sent = cli.send(str_msg.encode())

def send_ERRO(id, cli, numseq):
    str_msg = "02" + ID + id + numseq + "ERRO"
    sent = cli.send(str_msg.encode())

def send_unicast(oid, did, msg, d_cli, numseq):
    str_msg = "05" + oid + did + numseq + msg
    sent = d_cli.socket.send(str_msg.encode())
    while(True):
        ack  = d_cli.socket.recv(1024)
        ack  = ack.decode()
        if ack[0:2] == "01":
            print(f"[OK] Confirmação recebida de {oid}.")
            break
        else:
            print(f"[ERROR] {d_cli.id} mandou uma msg que não é um ACK.")

def send_broadcast(oid, did, msg, cli, numseq):
    try:
        for c in clients:
            if c.id != ID and c.id != oid:
                send_unicast(oid, did, msg, c, numseq)
        send_OK(oid, cli, numseq)
    except:
        send_ERRO(oid, cli, numseq)

def send_back(oid, num, msg, cli):
    print("[ERROR] destinatário não reconhecido.")
    for c in clients:
        if c.id == oid:
            send_unicast(ID, oid, msg, c, num)
            break

# #########################################################
# SERVER SET UP
# #########################################################

PORT = int(sys.argv[1])
HOST = socket.gethostbyname(socket.gethostname())
print("\n")
print(f"IP do servidor: {HOST}")
print("\n")
serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv.bind((HOST,PORT))
serv.listen()
sel.register(serv, selectors.EVENT_READ, data=None)
clients.append(Clients(ID, serv, serv.getsockname())) 

# #########################################################
# MAIN LOOP
# #########################################################

while True:
    events = sel.select(timeout=None)
    for key, mask in events:
        if key.data is None:
            accept_wrapper(key.fileobj) # key.fileobj == socket
        else:                           
            msg_read(key.fileobj)

