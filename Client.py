import socket
from ArgsParser import ArgsParser
import ClientHandle
args=ArgsParser()
if  not args.validate():
    exit(1)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((args.getUrl(),args.getPort()))
handle=ClientHandle.ClientHandle(sock)
handle.runSendRecv()
