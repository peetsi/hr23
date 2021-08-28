#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import multiprocessing as mp

qu = mp.Queue()
qu.put("hello Peter")
print(qu.get())

sys.exit(0)






import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 31415        # Port to listen on (non-privileged ports are > 1023)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)

