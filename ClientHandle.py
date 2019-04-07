import ntpath
import os
import socket
from threading import Lock

import File
import Util
from ArgsParser import ArgsParser
from Hash import Hash

ZERO_HASH = Hash().calculateHash()
PACK_SIZE = 1024
gLock = Lock()
filesLock = dict()


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

    def recvInt(self):
        val = Util.recvInt(self.conn.recv(PACK_SIZE))
        Util.recv(self.conn)
        return val

    def recvFiles(self):
        fileHash = self.conn.recv(PACK_SIZE)
        Util.recv(self.conn)
        while fileHash != ZERO_HASH and fileHash != b'':
            fileName = Util.recvString(self.conn.recv(PACK_SIZE))
            Util.recv(self.conn)
            fileSize = self.recvInt()
            accessTimeInNanoSec = self.recvInt()
            modificationTimeInNanoSec = self.recvInt()
            metaOrCreateTimeInNanoSec = self.recvInt()
            file = self.checkFileExists(fileHash)
            if file is None:
                file = File.File(fileName, PACK_SIZE)
                file.create(fileSize, fileHash, accessTimeInNanoSec, modificationTimeInNanoSec,
                            metaOrCreateTimeInNanoSec)
                self.files[file.fileHash] = file
            gLock.acquire()
            try:
                lock = filesLock[fileName]
            except KeyError:
                lock = Lock()
                filesLock[fileName] = lock
            lock.acquire()
            gLock.release()
            try:
                file.load()
                file.sendState(self.conn)
                if not file.isFileComplete():
                    file.reciveFile(self.conn)
                    file.finishRecive()
            except:
                file.panic()
                raise
            finally:
                lock.release()
            fileHash = self.conn.recv(PACK_SIZE)
            Util.recv(self.conn)

    def sendFiles(self):
        for f in self.args.getFiles():
            if ClientHandle.isFileForTransfer(f):
                self.sendFile(f, ntpath.basename(f))
            else:
                self.sendAllFiles(f)
        self.conn.send(ZERO_HASH)
        Util.send(self.conn)

    def checkFileExists(self, fileHash):
        try:
            return self.files[fileHash]
        except KeyError:
            return None

    def initFiles(self):
        files = [File.File(f, PACK_SIZE) for f in os.listdir('.') if ClientHandle.isFileForTransfer(f)]
        for f in files:
            f.load()
            self.files[f.fileHash] = f

    def panic(self):
        for f in self.files.values():
            f.panic()

    def sendAllFiles(self, f):
        if os.path.isdir(f):
            self.sendDir(f)
        elif os.path.isfile(f):
            self.sendFile(f, f)
        else:
            print(f"File {f} does not exists.")

    def sendInt(self, val):
        self.conn.send(Util.sendInt(val))
        Util.send(self.conn)

    def sendFile(self, filePath, sendFilePath):
        if ClientHandle.isFileForTransfer(filePath):
            file = File.File(filePath, PACK_SIZE)
            file.load()
            self.conn.send(file.fileHash)
            Util.send(self.conn)
            self.conn.send(Util.sendString(sendFilePath))
            Util.send(self.conn)
            self.sendInt(file.fileSize)
            self.sendInt(file.fileData.accessTimeInNanoSec)
            self.sendInt(file.fileData.modificationTimeInNanoSec)
            self.sendInt(file.fileData.metaOrCreateTimeInNanoSec)
            file.sendFile(self.conn)

    def sendDir(self, f):
        for f1 in os.listdir(f):
            filePath = os.path.join(f, f1)
            self.sendAllFiles(filePath)

    @staticmethod
    def isFileForTransfer(filePath: str):
        return os.path.isfile(filePath) and "fileDat" not in filePath
