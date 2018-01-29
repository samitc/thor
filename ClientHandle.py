import socket
import Util
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
        self.conn.send(Util.sendBool(self.args.getIsSend()))
        Util.send(self.conn)
        self.conn.send(Util.sendBool(self.args.getIsRecv()))
        Util.send(self.conn)
        self.isSendClient = Util.recvBool(self.conn.recv(1))
        Util.recv(self.conn)
        self.isRecvClient = Util.recvBool(self.conn.recv(1))
        Util.recv(self.conn)
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
                self.conn.close()
                raise
        self.conn.close()

    def runRecvSend(self):
        self.isSendClient = Util.recvBool(self.conn.recv(1))
        Util.recv(self.conn)
        self.isRecvClient = Util.recvBool(self.conn.recv(1))
        Util.recv(self.conn)
        self.conn.send(Util.sendBool(self.args.getIsSend()))
        Util.send(self.conn)
        self.conn.send(Util.sendBool(self.args.getIsRecv()))
        Util.send(self.conn)
        if self.isSendClient and self.args.getIsRecv():
            try:
                self.recvFiles()
            except:
                self.conn.close()
                raise
        if self.isRecvClient and self.args.getIsSend():
            try:
                self.sendFiles()
            except:
                self.conn.close()
                raise
        self.conn.close()

    def recvFiles(self):
        fileHash = self.conn.recv(PACK_SIZE)
        Util.recv(self.conn)
        while fileHash != ZERO_HASH:
            fileName = Util.recvString(self.conn.recv(PACK_SIZE))
            Util.recv(self.conn)
            fileSize = Util.recvInt(self.conn.recv(PACK_SIZE))
            Util.recv(self.conn)
            file = self.checkFileExists(fileName, fileSize, fileHash)
            if file is None:
                file = File.File(fileName, PACK_SIZE)
                file.create(fileSize, fileHash)
                self.files[file.fileHash] = file
            try:
                file.sendState(self.conn)
                if not file.isFileComplete():
                    file.reciveFile(self.conn)
                    file.finishRecive()
            except:
                file.panic()
                raise
            fileHash = self.conn.recv(PACK_SIZE)
            Util.recv(self.conn)

    def sendFiles(self):
        for f in self.args.getFiles():
            file = File.File(f, PACK_SIZE)
            file.load()
            self.conn.send(file.fileHash)
            Util.send(self.conn)
            self.conn.send(Util.sendString(file.fileName))
            Util.send(self.conn)
            self.conn.send(Util.sendInt(file.fileSize))
            Util.send(self.conn)
            file.sendFile(self.conn)
        self.conn.send(ZERO_HASH)
        Util.send(self.conn)

    def checkFileExists(self, fileName, fileSize, fileHash):
        try:
            return self.files[fileHash]
        except KeyError:
            return None

    def initFiles(self):
        files = [File.File(f, PACK_SIZE) for f in os.listdir('.') if os.path.isfile(f)]
        for f in files:
            f.load()
            self.files[f.fileHash] = f

    def panic(self):
        for f in self.files.values():
            f.panic()
