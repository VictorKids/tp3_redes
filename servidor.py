import sys
import socket
import selectors
import time

# #########################################################
# UTILITIES
# #########################################################

sel = selectors.DefaultSelector()
ID   = "00065535"
class Clients:
    def __init__(self, id, socket):
        self.id = id
        self.socket = socket
        self.waiting = False
clients = []

# #########################################################
# ACCEPT FUNCTION
# #########################################################

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"[SYNC] recebendo conexão de {addr}")
    conn.setblocking(False)
    data = "oi_dorgival"
    sel.register(conn, selectors.EVENT_READ, data=data)

# #########################################################
# READ FUNCTION
# #########################################################

def msg_read(client):
    data = client.recv(1024)
    if data:
        data = data.decode()
        msg_type  = data[0:16]
        origin_id = data[16:32]
        destin_id = data[32:48]
        seq_num   = data[48:64]
        message   = data[64:]

        if msg_type == "00000011": # OI
            print("[CONN] mensagem do tipo OI recebida")
            new_id_flag = True
            for c in clients:
                if c.id == origin_id:
                    new_id_flag = False
                    break
            if new_id_flag:
                clients.append(Clients(origin_id, client))
                send_OK(origin_id, client, seq_num)
            else:
                send_ERRO(origin_id, client, seq_num)

        else:
            security_check = False
            for c in clients:
                if c.id == origin_id and c.socket == client:
                    security_check == True
                    break
            if security_check == True:
                if   msg_type == "00000010": # ERRO
                    print("[ERROR] cliente não deveria mandar msgs do tipo ERRO ao servidor")
                elif msg_type == "00000001": # OK
                    print("[ACK] confirmação recebida")
                    for c in clients:
                        if c.id == destin_id:
                            c.wating = False
                            break
                elif msg_type == "00000100": # FLW
                    print(f"[DCONN] desconectando cliente {origin_id}")
                    send_OK(origin_id, client, seq_num)
                    for c in clients:
                        if c.id == origin_id:
                            client.remove(c)
                            sel.unregister(c)
                            c.close()
                            break
                elif msg_type == "00000101": # MSG
                    print(f"[MSG] mensagem recebida de {origin_id} para {destin_id}")
                    if destin_id == "00000000":
                        send_broadcast(origin_id, destin_id, message, client, seq_num)
                    else:
                        destin_flag = False
                        for c in clients:
                            if c.id == destin_id:
                                destin_flag = True
                                break
                        if destin_flag:
                            send_OK(origin_id, client, seq_num)
                            send_unicast(origin_id, destin_id, message, client, seq_num)
                        else:
                            send_ERRO(origin_id, client, seq_num)
                            send_back(destin_id, seq_num, message, client)                        
            else:
                send_ERRO(origin_id, client, seq_num) 
                print(f"[ERROR] {origin_id} não existe ou alguém tentou se passar por {origin_id}")
    else:
        print("[ERROR] mensagem vazia") 

# #########################################################
# SEND FUNCTIONS
# #########################################################

def send_OK(id, cli, numseq):
    str_msg = "00000001" + ID + id + numseq + "OK"
    sent = cli.send(str_msg.encode())

def send_ERRO(id, cli, numseq):
    str_msg = "00000010" + ID + id + numseq + "ERRO"
    sent = cli.send(str_msg.encode())

def send_unicast(oid, did, msg, cli, numseq):
    str_msg = "00000101" + oid + did + numseq + msg
    for c in clients:
        if c.id == did:
            tmp = c
            c.waiting = True
            break
    sent = cli.send(str_msg.encode())
    while tmp.waiting:     # esperar pelo ack
        time.sleep(1)

def send_broadcast(oid, did, msg, cli, numseq):
    for c in clients:
        if c.id != ID:
            send_unicast(oid, did, msg, cli, numseq)
    send_OK(oid, cli, numseq)

def send_back(destin, num, msg, cli):
    #str_msg = "00000101" + ID + destin + num + msg
    #sent = cli.send(str_msg.encode())
    print("[ERROR] destinatário não reconhecido")
    send_unicast(ID, destin, msg, cli, num)

# #########################################################
# SERVER SET UP
# #########################################################

PORT = int(sys.argv[1])
HOST = socket.gethostbyname(socket.gethostname())

serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv.bind((HOST,PORT))
serv.listen()
serv.setblocking(False)
sel.register(serv, selectors.EVENT_READ, data=None)
clients.append(Clients(ID, serv)) #precisa?

# #########################################################
# MAIN LOOP
# #########################################################

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj) # key.fileobj == socket
            else:                           # mask = event flag
                msg_read(key.fileobj)
except KeyboardInterrupt:
    pass
finally:
    sel.close()