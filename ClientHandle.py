import ntpath
import os
import socket
from threading import Lock
import File
import Util
from ArgsParser import ArgsParser

ZERO_HASH = b"0000000000000000000000000000000000000000000000000000000000000000"
PACK_SIZE = 1024
gLock = Lock()
filesLock = dict()


class ClientHandle:
    def __init__(self, conn: socket.socket, args: ArgsParser):
        self.conn = conn
        self.args = args
        self.files = dict()

    def runSendRecv(self):
        Util.sendBool(self.conn, self.args.getIsSend())
        Util.sendBool(self.conn, self.args.getIsRecv())
        valid, self.isSendClient, self.isRecvClient = ClientHandle.doHandshake(
            self.conn)
        if valid:
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
        valid, self.isSendClient, self.isRecvClient = ClientHandle.doHandshake(
            self.conn)
        if valid:
            Util.sendBool(self.conn, self.args.getIsSend())
            Util.sendBool(self.conn, self.args.getIsRecv())
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
        fileHash = Util.recvHash(self.conn, len(ZERO_HASH))
        while fileHash != ZERO_HASH and fileHash != b'':
            fileName = Util.recvString(self.conn)
            fileSize = Util.recvInt(self.conn)
            accessTimeInNanoSec = Util.recvInt(self.conn)
            modificationTimeInNanoSec = Util.recvInt(self.conn)
            metaOrCreateTimeInNanoSec = Util.recvInt(self.conn)
            files = self.checkFileExists(fileHash)
            if files is None:
                file = File.File(fileName, PACK_SIZE)
                file.create(fileSize, fileHash, accessTimeInNanoSec, modificationTimeInNanoSec,
                            metaOrCreateTimeInNanoSec)
                self.files[file.fileHash] = [file]
            else:
                file = None
                for f in files:
                    if f.fileName == fileName:
                        file = f
                if file is None:
                    file = File.File(fileName, PACK_SIZE)
                    file.create(fileSize, fileHash, accessTimeInNanoSec, modificationTimeInNanoSec,
                                metaOrCreateTimeInNanoSec)
                    ClientHandle.migrate(files[0], file)
                    file.save()
                    self.files[file.fileHash].append(file)
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
            fileHash = Util.recvHash(self.conn, len(ZERO_HASH))

    def sendFiles(self):
        for f in self.args.getFiles():
            if ClientHandle.isFileForTransfer(f):
                self.sendFile(f, ntpath.basename(f))
            else:
                self.sendAllFiles(f)
        Util.sendHash(self.conn, ZERO_HASH, len(ZERO_HASH))

    def checkFileExists(self, fileHash):
        try:
            return self.files[fileHash]
        except KeyError:
            return None

    def panic(self):
        for files in self.files.values():
            for f in files:
                f.panic()

    def sendAllFiles(self, f):
        if os.path.isdir(f):
            self.sendDir(f)
        elif os.path.isfile(f):
            self.sendFile(f, f)
        else:
            print(f"File {f} does not exists.")

    def sendFile(self, filePath, sendFilePath):
        if ClientHandle.isFileForTransfer(filePath):
            file = File.File(filePath, PACK_SIZE)
            file.load()
            Util.sendHash(self.conn, file.fileHash, len(ZERO_HASH))
            Util.sendString(self.conn, sendFilePath)
            Util.sendInt(self.conn, file.fileSize)
            Util.sendInt(self.conn, file.fileData.accessTimeInNanoSec)
            Util.sendInt(self.conn, file.fileData.modificationTimeInNanoSec)
            Util.sendInt(self.conn, file.fileData.metaOrCreateTimeInNanoSec)
            file.sendFile(self.conn)

    def sendDir(self, f):
        for f1 in os.listdir(f):
            filePath = os.path.join(f, f1)
            self.sendAllFiles(filePath)

    @staticmethod
    def isFileForTransfer(filePath: str):
        return os.path.isfile(filePath) and "fileDat" not in filePath

    @staticmethod
    def migrate(f1: File, f2: File):
        if f1.partNumber == f2.partNumber:
            return
        if f1.partNumber > f2.partNumber:
            bf = f1
            sf = f2
        else:
            bf = f2
            sf = f1
        with open(sf.fileName, "ab") as sfs:
            with open(bf.fileName, "rb") as bfs:
                numOfParts = bf.partNumber - sf.partNumber
                bfs.seek(sf.partNumber * PACK_SIZE)
                sfs.write(bfs.read(numOfParts * PACK_SIZE))
                sf.partNumber += numOfParts

    @staticmethod
    def doHandshake(conn):
        bOne = Util.recvBool(conn)
        bTwo = Util.recvBool(conn)
        return bOne | bTwo, bOne, bTwo
