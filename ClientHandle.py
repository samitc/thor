import ntpath
import os
import socket
from threading import Lock
import File
import Util
from ArgsParser import ArgsParser
from Hash import Hash

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
        self.conn.send(Util.sendBool(self.args.getIsSend()))
        Util.send(self.conn)
        self.conn.send(Util.sendBool(self.args.getIsRecv()))
        Util.send(self.conn)
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
                sfs.write(bfs.read(numOfParts*PACK_SIZE))
                sf.partNumber += numOfParts
    @staticmethod
    def doHandshake(conn):
        packOne=conn.recv(1)
        Util.recv(conn)
        packTwo = conn.recv(1)
        Util.recv(conn)
        if packOne==b'' or packTwo==b'':
            return False,False,False
        bOne=Util.recvBool(packOne)
        bTwo=Util.recvBool(packTwo)
        return bOne|bTwo,bOne,bTwo
