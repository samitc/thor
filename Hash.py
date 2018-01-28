import hashlib


class Hash:
    def __init__(self):
        self.h = hashlib.sha512()

    def calculateHash(self):
        return self.h.hexdigest()

    def update(self, data):
        self.h.update(data)
