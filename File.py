import os
from Hash import Hash
import pickle


class FileData:
    def __init__(self, fileHash, fileSize,partNumber):
        self.fileHash = fileHash
        self.fileSize = fileSize
        self.partNumber=partNumber

class File:
    def __init__(self, fileName):
        self.fileName = fileName
        self.isFinished = False

    def load(self, PACK_SIZE):
        if not self.loadFileData(PACK_SIZE):
            h = Hash()
            BUF_SIZE = 65536
            self.fileSize = 0
            with open(self.fileName, 'r') as f:
                data = f.read(BUF_SIZE)
                h.update(data)
                self.fileSize += len(data)
            self.fileHash = h.calculateHash()
            self.isFinished = True

    def create(self, fileSize, fileHash, PACK_SIZE):
        self.fileHash = fileHash
        self.fileSize = fileSize
        if not self.loadFileData(PACK_SIZE):
            self.recData = [False for _ in range(self.fileSize / PACK_SIZE)]
            self.fileData = open(self.fileName + ".fileDat", 'w+b')
            self.fileData.write(self.recData)
            self.fileData.seek(0)
            with open(self.fileName + ".fileMetaDat", 'w') as fileMetaData:
                pickle.dump(FileData(fileHash, fileSize), fileMetaData, pickle.HIGHEST_PROTOCOL)

    def save(self):
        if  not self.isFinished:
            self.fileData.seek(0)
            self.fileData.write(self.recData)

    def sendState(self, conn):
        conn.send(self.recData)

    def reciveFile(self, conn):
        numOfParts=0
        for r in self.recData:
            if not r:
                numOfParts+=1
        for

    def finishRecive(self):
        os.remove(self.fileName + ".fileMetaDat")
        os.remove(self.fileName + ".fileDat")
        self.checkIfFileCurrect()

    def loadFileData(self, PACK_SIZE):
        try:
            with open(self.fileName + ".fileDat", 'r+b') as f:
                pass
        except FileNotFoundError:
            return False
        else:
            self.fileData = f
            self.recData = f.read(os.stat(f).st_size / PACK_SIZE + 1)
            with open(self.fileName + ".fileMetaDat", 'w') as fileMetaData:
                fileData = pickle.load(fileMetaData, pickle.HIGHEST_PROTOCOL)
                self.fileSize = fileData.hashSize
                self.fileHash = fileData.fileHash
            return True
    def isFileComplete(self):
        return self.isFinished
