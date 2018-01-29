import argparse
import os


class ArgsParser:
    def __init__(self):
        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('-u', action='store', dest='url', help='address of remote computer', default='127.0.0.1')
        parser.add_argument('-p', action='store', dest='port', type=int, help='port of remove computer',
                            default='10000')
        parser.add_argument('-s', action='store_true', dest='send', help='send file to remote computer', default=False)
        parser.add_argument('-r', action='store_true', dest='recv', help='recived file from remote computer',
                            default=False)
        parser.add_argument('-f', action='append', dest='files', help='add file to send', default=[])
        self.result = parser.parse_args()
        self.error = ""
        self.__validate__()

    def __validate__(self):
        if not self.result.send and not self.result.recv:
            self.error += "not recv and not send"
        if self.result.send and len(self.result.files) is 0:
            self.error += "no files were added to sending" + os.linesep
        elif not self.result.send and len(self.result.files) > 0:
            self.error += "files was chosen for send but no send flag" + os.linesep

    def validate(self):
        if self.error != "":
            print(self.error)
            return False
        return True

    def getUrl(self):
        if (self.validate()):
            return self.result.url

    def getPort(self):
        if (self.validate()):
            return self.result.port

    def getIsSend(self):
        if self.validate():
            return self.result.send

    def getIsRecv(self):
        if self.validate():
            return self.result.recv

    def getFiles(self):
        if self.validate():
            return self.result.files
