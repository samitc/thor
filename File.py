import math
import os
import pickle

import Util
from Hash import Hash


class FileData:
    def __init__(self, fileHash, fileSize, partNumber, accessTimeInNanoSec, modificationTimeInNanoSec,
                 metaOrCreateTimeInNanoSec):
        self.fileHash = fileHash
        self.fileSize = fileSize
        self.partNumber = partNumber
        self.accessTimeInNanoSec = accessTimeInNanoSec
        self.modificationTimeInNanoSec = modificationTimeInNanoSec
        self.metaOrCreateTimeInNanoSec = metaOrCreateTimeInNanoSec


class File:
    def __init__(self, fileName, PACK_SIZE):
        self.fileName = fileName
        self.isFinished = False
        self.PACK_SIZE = PACK_SIZE
        self.fileData = FileData(None, None, None, None, None, None)

    def calcHashAndSize(self):
        if os.path.isfile(self.fileName + ".fileDat"):
            with open(self.fileName + ".fileDat", 'rb') as f:
                fd = pickle.load(f)
                h, fileSize = fd.fileHash, fd.fileSize
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
            h = h.calculateHash()
        return h, fileSize

    def load(self):
        if not self.loadFileData():
            self.fileHash, self.fileSize = self.calcHashAndSize()
            fileStat = os.stat(self.fileName)
            fd = FileData(self.fileHash, self.fileSize, -1, fileStat.st_atime_ns, fileStat.st_mtime_ns,
                          fileStat.st_ctime_ns)
            self.fileData = fd
            with open(self.fileName + ".fileDat", 'wb') as f:
                pickle.dump(fd, f, pickle.HIGHEST_PROTOCOL)
            self.isFinished = True
            self.partNumber = math.ceil(self.fileSize / self.PACK_SIZE)

    def checkIfFileCurrect(self):
        fileHash, fs = self.calcHashAndSize()
        return self.fileHash == fileHash

    def create(self, fileSize, fileHash, accessTimeInNanoSec, modificationTimeInNanoSec, metaOrCreateTimeInNanoSec):
        dirName = os.path.dirname(self.fileName)
        if dirName != "":
            os.makedirs(dirName, exist_ok=True)
        if not self.loadFileData():
            self.fileHash = fileHash
            self.fileSize = fileSize
            self.partNumber = 0
            self.fileData = FileData(fileHash, fileSize, self.partNumber, accessTimeInNanoSec,
                                     modificationTimeInNanoSec,
                                     metaOrCreateTimeInNanoSec)
            with open(self.fileName + ".fileDat", 'wb') as f:
                pickle.dump(self.fileData, f, pickle.HIGHEST_PROTOCOL)

    def save(self):
        if not self.isFinished:
            with open(self.fileName + ".fileDat", 'wb') as f:
                pickle.dump(FileData(self.fileHash, self.fileSize, self.partNumber, self.fileData.accessTimeInNanoSec,
                                     self.fileData.modificationTimeInNanoSec, self.fileData.metaOrCreateTimeInNanoSec),
                            f, pickle.HIGHEST_PROTOCOL)

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
                os.utime(self.fileName, ns=(self.fileData.accessTimeInNanoSec, self.fileData.modificationTimeInNanoSec))
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
            self.fileData = pickle.load(f)
            self.fileSize = self.fileData.fileSize
            self.fileHash = self.fileData.fileHash
            self.partNumber = self.fileData.partNumber
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
