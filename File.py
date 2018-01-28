import os
from Hash import Hash
import pickle


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

    def load(self):
        if not self.loadFileData():
            h = Hash()
            BUF_SIZE = 65536
            self.fileSize = 0
            with open(self.fileName, 'rb') as f:
                data = f.read(BUF_SIZE)
                h.update(data)
                self.fileSize += len(data)
            self.fileHash = h.calculateHash()
            self.isFinished = True
            self.partNumber = self.fileSize / self.PACK_SIZE + 1

    def checkIfFileCurrect(self):
        h = Hash()
        BUF_SIZE = 65536
        with open(self.fileName, 'rb') as f:
            data = f.read(BUF_SIZE)
            h.update(data)
        fileHash = h.calculateHash()
        return self.fileHash == fileHash

    def create(self, fileSize, fileHash):
        if not self.loadFileData():
            self.fileHash = fileHash
            self.fileSize = fileSize
            self.fileData = open(self.fileName + ".fileDat", 'w+b')
            self.partNumber = 0
            self.fileData.seek(0)
            pickle.dump(FileData(fileHash, fileSize, 0), self.fileData, pickle.HIGHEST_PROTOCOL)

    def save(self):
        if not self.isFinished:
            pickle.dump(FileData(self.fileHash, self.fileSize, self.partNumber), self.fileData, pickle.HIGHEST_PROTOCOL)

    def sendState(self, conn):
        conn.send(self.partNumber)

    def reciveFile(self, conn):
        with open(self.fileName, 'ab') as file:
            for _ in range(self.fileSize / self.PACK_SIZE + 1):
                data = conn.recv(self.PACK_SIZE)
                file.write(data)
                self.partNumber += 1

    def finishRecive(self):
        self.save()
        if self.checkIfFileCurrect():
            os.remove(self.fileName + ".fileDat")
        else:
            self.partNumber = 0
            self.save()

    def loadFileData(self):
        try:
            with open(self.fileName + ".fileDat", 'r+b') as f:
                pass
        except FileNotFoundError:
            return False
        else:
            self.fileData = f
            fileData = pickle.load(f, pickle.HIGHEST_PROTOCOL)
            self.fileSize = fileData.hashSize
            self.fileHash = fileData.fileHash
            self.partNumber = fileData.partNumber
            return True

    def isFileComplete(self):
        return self.isFinished
