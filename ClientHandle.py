import socket
import File
import os

from ArgsParser import ArgsParser
from Hash import Hash

ZERO_HASH = Hash().calculateHash()
PACK_SIZE = 1024

class ClientHandle:
    def __init__(self, conn: socket.socket, args: ArgsParser):
        self.conn = conn
        self.args = args
        self.files = dict()
        self.initFiles()

    def runSendRecv(self):
        self.conn.send(self.args.getIsSend())
        self.conn.send(self.args.getIsRecv())
        self.isSendClient = self.conn.recv(PACK_SIZE)
        self.isRecvClient = self.conn.recv(PACK_SIZE)
        if self.isRecvClient and self.args.getIsSend():
            try:
                self.sendFiles()
            except:
                self.conn.close()
                raise
        if self.isSendClient and self.args.getIsRecv():
            try:
                self.recvFiles()
            except:
                self.panic()
                self.conn.close()
                raise

    def runRecvSend(self):
        self.isSendClient = self.conn.recv(PACK_SIZE)
        self.isRecvClient = self.conn.recv(PACK_SIZE)
        self.conn.send(self.args.getIsSend())
        self.conn.send(self.args.getIsRecv())
        if self.isSendClient and self.args.getIsRecv():
            try:
                self.recvFiles()
            except:
                self.panic()
                self.conn.close()
                raise
        if self.isRecvClient and self.args.getIsSend():
            try:
                self.sendFiles()
            except:
                self.conn.close()
                raise

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
            file = File.File(f, PACK_SIZE)
            self.conn.send(file.fileHash)
            self.conn.send(file.fileName)
            self.conn.send(file.fileSize)
            file.sendFile(self.conn)
        self.conn.send(ZERO_HASH)

    def checkFileExists(self, fileName, fileSize, fileHash):
        return self.files[fileHash]

    def initFiles(self):
        files = [File.File(f, PACK_SIZE) for f in os.listdir('.') if os.path.isfile(f)]
        for f in files:
            f.load()
            self.files[f.fileHash] = f

    def panic(self):
        for f in self.files.values():
            f.save()
