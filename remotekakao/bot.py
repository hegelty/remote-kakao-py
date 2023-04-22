import functools
from socket import *
import json
import typing as t
import logging
import base64


def decorator(f: t.Callable[..., t.Any]) -> t.Callable[..., t.Any]:
    def wrapper(self, *args, **kwargs):
        return f(self, *args, **kwargs)

    return t.cast(t.Callable[..., t.Any], functools.update_wrapper(wrapper, f))


class Bot:
    def __init__(self, prefix: str):
        if len(prefix) > 1:
            raise Exception("prefix should be a character")
        self.__prefix = prefix
        self.__token = None
        self.__port = None
        self.__host = None
        self.authorized = False
        self.client_socket = None
        self.server_socket = None
        self.router_dic = {}
        self.on_message_func = None

    def run(self, host: str = "localhost", port: int = 8001, token: t.Optional[str] = None):
        '''
        :param host: host ip
        :param port: port number
        :param token: not implemented
        '''
        self.__host = host
        self.__port = port
        self.__token = token

        print(f"{self.__host}:{self.__port} 소켓 실행")
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.bind((self.__host, self.__port))
        self.server_socket.listen(1)

        self.client_socket, addr = self.server_socket.accept()

        new_message = True
        msg_size = 0
        recv_data = None
        while True:
            try:
                if new_message:
                    data = self.client_socket.recv(128)
                    header_len = len((data.decode().split("\n")[0] + "\n").encode())
                    msg_size = int(data.decode().split("\n")[0][1:-1]) - 128 + header_len
                    recv_data = data
                    new_message = False
                elif msg_size > 128:
                    data = self.client_socket.recv(128)
                    msg_size -= 128
                    recv_data += data
                else:
                    if msg_size > 0:
                        data = self.client_socket.recv(msg_size)
                        recv_data += data
                    new_message = True

                    self.router('\n'.join(recv_data.decode().split('\n')[1:]).strip())
            except Exception as e:
                print("reconnecting...")
                self.server_socket = socket(AF_INET, SOCK_STREAM)
                self.server_socket.bind((self.__host, self.__port))
                self.server_socket.listen(1)

                self.client_socket, addr = self.server_socket.accept()
                print("reconnected!")
                self.replier("카카오톡 봇 커뮤니티", "testabcdefghijklmnopqrstuvwxyz_testabcdefghijklmnopqrstuvwxyz_testabcdefghijklmnopqrstuvwxyz_testabcdefghijklmnopqrstuvwxyz_testabcdefghijklmnopqrstuvwxyz_testabcdefghijklmnopqrstuvwxyz_testabcdefghijklmnopqrstuvwxyz_testabcdefghijklmnopqrstuvwxyz")

    def router(self, recv_data: str):
        '''
        {
            "t": special option: int,
            "r": room: str,
            "m": msg: str,
            "s": sender: str,
            "G": isGroupChat: bool,
            "i": imageDB(optional): str,
            "p": packageName(optional): str
        }
        '''
        data = json.loads(recv_data)
        if "t" in data:
            t = data["t"]
            if t == 0:
                print("connected")
            elif t == 1:
                print("reconnected")
            return

        room = data["r"]
        msg = data["m"]
        sender = data["s"]
        isGroupChat = data['G']
        imageDB = data['i'] if 'i' in data else None
        packageName = data['p'] if 'p' in data else None
        prefix = msg[0]
        cmd = msg.split()[0][1:]
        msg = msg[len(cmd) + 2:].lstrip()

        if prefix in self.router_dic:
            rd = self.router_dic[prefix]
            if cmd in rd:
                if not rd[cmd]["room"] or (rd[cmd]["room"] and room in rd[cmd]["room"]):
                    if type(rd[cmd]["is_group_chat"]) != bool or rd[cmd]["is_group_chat"] == isGroupChat:
                        output = rd[cmd]["func"](room, msg, sender, isGroupChat, imageDB, packageName)
                        print(output)
                        if output:
                            self.replier(room, output)
                            return
        if self.on_message_func:
            output = self.on_message_func(room, msg, sender, isGroupChat, imageDB, packageName)
            if output:
                self.replier(room, output)
                return

    def replier(self, room: str, msg):
        print(room)
        if type(msg) == str:
            msg_data = str(json.dumps({
                "r": room,
                "t": 0,
                "m": msg
            }))
            self.client_socket.send((f"[{len(msg_data.encode())}]\n" + msg_data).encode())
        else:
            raise TypeError

    @decorator
    def route(self,
              cmd: str,
              prefix: t.Optional[str] = None,
              room: t.Optional[t.Iterable[str]] = None,
              is_group_chat: t.Optional[bool] = None):
        '''
        :param func:
        :param cmd: 명령어
        :param prefix: 명렁어 접두사(default: 봇 접두사)
        :param room: 작동할 방 목록(방 이름)
        :param is_group_chat: 단체톡 여부
        '''

        def wrapper(f):
            pfx = self.__prefix
            if prefix:
                pfx = prefix
            if len(pfx) > 1:
                raise Exception("prefix should be a character")

            if pfx in self.router_dic:
                if cmd in self.router_dic[pfx]:
                    ori = self.router_dic[pfx][cmd]
                    if ori["is_group_chat"] == is_group_chat:  # 중복
                        raise Exception("router duplicated")
                self.router_dic[pfx][cmd] = {"func": f, "room": room, "is_group_chat": is_group_chat}
            else:
                self.router_dic[pfx] = {cmd: {"func": f, "room": room, "is_group_chat": is_group_chat}}
            return f

        return wrapper

    @decorator
    def on_msg(self):
        def wrapper(f):
            if self.on_message_func:
                raise Exception("router duplicated")
            self.on_message_func = f
            return f

        return wrapper
