import socket
import time
TCP_IP="127.0.0.1"
TCP_PORT=10000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("13.68.88.215", TCP_PORT))
try:
    while True:
        data = sock.recv(4096)
        print (data, time.time())
except:
    pass
sock.close()
