import json
from socket import *
from _thread import *

server = socket(AF_INET, SOCK_STREAM)
server.connect(('localhost', 8080))

msg = str(json.dumps({
    "t": 0
}))
server.send((f"[{len(msg.encode())}]\n" + msg).encode())


def recv():
    new_message = True
    msg_size = 0
    recv_data = None
    while True:
        if new_message:
            data = server.recv(128)
            header_len = len((data.decode().split("\n")[0] + "\n").encode())
            msg_size = int(data.decode().split("\n")[0][1:-1]) - 128 + header_len
            # print(msg_size)
            recv_data = data
            new_message = False
        elif msg_size > 128:
            data = server.recv(128)
            msg_size -= 128
            recv_data += data
        else:
            if msg_size > 0:
                data = server.recv(msg_size)
                recv_data += data
            new_message = True
            print('\n'.join(recv_data.decode().split('\n')[1:]).strip())


start_new_thread(recv, ())

while True:
    room = input("Enter room: ")
    room = room if room else "test room"
    sender = input("Enter sender: ")
    sender = sender if sender else "tester"
    msg = input("Enter message: ")
    msg = str(json.dumps({
        "r": room,
        "m": msg,
        "s": sender,
        "G": False
    }))
    server.send((f"[{len(msg.encode())}]\n" + msg).encode())