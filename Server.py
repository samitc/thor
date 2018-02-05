import socket
import threading

from ArgsParser import ArgsParser
from ClientHandle import ClientHandle


def clientCon(conn, args):
    conn.settimeout(10)
    ch = ClientHandle(conn, args)
    threading.Thread(target=ch.runRecvSend).start()


args = ArgsParser()
if not args.validate():
    exit(1)
tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpServer.bind((args.getUrl(), args.getPort()))
tcpServer.listen(0)
try:
    while True:
        conn, addr = tcpServer.accept()
        clientCon(conn, args)
except:
    tcpServer.close()
    raise
