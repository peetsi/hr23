
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
from socket import error as SocketError
import errno

#HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
HOST = 'localhost'  # is often faster than 1.0.0.127
PORT = 31413        # Port to listen on (non-privileged ports are > 1023)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            print("data=",data)
            if not data:
                break
            #conn.sendall(b"ACK")
