import File
import os
import socket
import threading

from Hash import Hash

PACK_SIZE = 1024

ZERO_HASH = Hash().calculateHash()
from ArgsParser import ArgsParser


class ClientHandle:
    def __init__(self, conn: socket.socket, args: ArgsParser):
        self.conn = conn
        self.args = args
        self.files = dict()
        self.initFiles()

    def runClient(self):
        self.isSendClient = self.conn.recv(PACK_SIZE)
        self.isRecvClient = self.conn.recv(PACK_SIZE)
        self.conn.send(self.args.getIsSend())
        self.conn.send(self.args.getIsRecv())
        if self.isSendClient and self.args.getIsRecv():
            try:
                self.recvFiles()
            except:
                self.panic()
        if self.isRecvClient and self.args.getIsSend():
            self.sendFiles()

    def recvFiles(self):
        fileHash = self.conn.recv(PACK_SIZE)
        while fileHash is not ZERO_HASH:
            fileName = self.conn.recv(PACK_SIZE)
            fileSize = self.conn.recv(PACK_SIZE)
            file = self.checkFileExists(fileName, fileSize, fileHash)
            if file is None:
                file = File.File(fileName, PACK_SIZE)
                file.create(fileSize, fileHash)
                self.files[file.fileHash] = file
            file.sendState(self.conn)
            if not file.isFileComplete():
                file.reciveFile(self.conn)
                file.finishRecive()

    def sendFiles(self):
        for f in self.args.getFiles():
            file = File.File(f,PACK_SIZE)
            self.conn.send(file.fileHash)
            self.conn.send(file.fileName)
            self.conn.send()

    def checkFileExists(self, fileName, fileSize, fileHash):
        return self.files[fileHash]

    def initFiles(self):
        files = [File.File(f,PACK_SIZE) for f in os.listdir('.') if os.path.isfile(f)]
        for f in files:
            f.load()
            self.files[f.fileHash] = f

    def panic(self):
        for f in self.files.values():
            f.save()


def clientCon(conn, args):
    ch = ClientHandle(conn, args)
    threading.Thread(target=ch.runClient).start()


args = ArgsParser()
if not args.validate():
    exit(1)
tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpServer.bind((args.getUrl(), args.getPort()))
tcpServer.listen(0)
while True:
    conn, addr = tcpServer.accept()
    clientCon(conn, args)
