import os
from Hash import Hash
import pickle
import Util
import ntpath
import math


class FileData:
    def __init__(self, fileHash, fileSize, partNumber):
        self.fileHash = fileHash
        self.fileSize = fileSize
        self.partNumber = partNumber


class File:
    def __init__(self, fileName, PACK_SIZE):
        self.fileName = fileName
        self.isFinished = False
        self.PACK_SIZE = PACK_SIZE

    def calcHashAndSize(self):
        if os.path.isfile(self.fileName + ".fileDat.c"):
            with open(self.fileName + ".fileDat.c", 'rb') as f:
                fd = pickle.load(f)
        else:
            h = Hash()
            BUF_SIZE = 65536
            fileSize = 0
            with open(self.fileName, 'rb') as f:
                while True:
                    data = f.read(BUF_SIZE)
                    if not data:
                        break
                    h.update(data)
                    fileSize += len(data)
            fd = FileData(h.calculateHash(), fileSize, -1)
            with open(self.fileName + ".fileDat.c", 'wb') as f:
                pickle.dump(fd, f, pickle.HIGHEST_PROTOCOL)
        return fd.fileHash, fd.fileSize

    def load(self):
        if not self.loadFileData():
            self.fileHash, self.fileSize = self.calcHashAndSize()
            self.isFinished = True
            self.partNumber = math.ceil(self.fileSize / self.PACK_SIZE)

    def checkIfFileCurrect(self):
        fileHash, fs = self.calcHashAndSize()
        return self.fileHash == fileHash

    def create(self, fileSize, fileHash):
        self.fileName = ntpath.basename(self.fileName)
        if not self.loadFileData():
            self.fileHash = fileHash
            self.fileSize = fileSize
            self.partNumber = 0
            with open(self.fileName + ".fileDat", 'wb') as f:
                pickle.dump(FileData(fileHash, fileSize, self.partNumber), f, pickle.HIGHEST_PROTOCOL)

    def save(self):
        if not self.isFinished:
            with open(self.fileName + ".fileDat", 'wb') as f:
                pickle.dump(FileData(self.fileHash, self.fileSize, self.partNumber), f, pickle.HIGHEST_PROTOCOL)

    def panic(self):
        self.save()

    def sendState(self, conn):
        conn.send(Util.sendInt(self.partNumber))
        Util.send(conn)

    def reciveFile(self, conn):
        data = bytearray()
        maxPart = int(math.ceil(self.fileSize / self.PACK_SIZE))
        packSize = self.fileSize - self.PACK_SIZE * self.partNumber if self.partNumber + 1 == maxPart else self.PACK_SIZE
        with open(self.fileName, 'ab') as file:
            while self.partNumber < maxPart:
                dataT = conn.recv(packSize - len(data))
                if not dataT:
                    break
                data += dataT
                if len(data) == packSize:
                    file.write(data)
                    self.partNumber += 1
                    data = bytearray()
                    if self.partNumber + 1 == maxPart:
                        packSize = self.fileSize - self.PACK_SIZE * self.partNumber

    def finishRecive(self):
        self.save()
        if self.partNumber == math.ceil(self.fileSize / self.PACK_SIZE):
            if self.checkIfFileCurrect():
                os.remove(self.fileName + ".fileDat")
                self.isFinished = True
            else:
                os.rename(self.fileName, self.fileName + ".notGood")
                os.remove(self.fileName + ".fileDat")
                self.partNumber = 0
                self.save()

    def loadFileData(self):
        try:
            f = open(self.fileName + ".fileDat", 'r+b')
        except FileNotFoundError:
            return False
        else:
            fileData = pickle.load(f)
            self.fileSize = fileData.fileSize
            self.fileHash = fileData.fileHash
            self.partNumber = fileData.partNumber
            f.close()
            return True

    def isFileComplete(self):
        return self.isFinished

    def sendFile(self, conn):
        filePart = Util.recvInt(conn.recv(self.PACK_SIZE))
        Util.recv(conn)
        maxPart = math.ceil(self.fileSize / self.PACK_SIZE)
        if filePart < maxPart:
            with open(self.fileName, 'rb') as file:
                file.seek(filePart * self.PACK_SIZE)
                while True:
                    data = file.read(self.PACK_SIZE)
                    if not data:
                        break
                    filePart += 1
                    conn.send(data)
