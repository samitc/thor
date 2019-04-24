NUM_OF_BYTES_TO_CODE_INT = 8
NUM_OF_BYTES_TO_CODE_BOOL = 1
NUM_OF_BYTES_TO_CODE_STRING_INT = 4


def __codedInt__(val: int, numOfBytesToCoded: int):
    return val.to_bytes(numOfBytesToCoded, 'big')


def __decodeInt__(val):
    return int.from_bytes(val, 'big')


def sendInt(conn, val: int):
    conn.send(__codedInt__(val, NUM_OF_BYTES_TO_CODE_INT))


def sendBool(conn, val):
    conn.send(__codedInt__(1 if val else 0, NUM_OF_BYTES_TO_CODE_BOOL))


def sendString(conn, val: str):
    encodeString = val.encode()
    lVal = __codedInt__(len(encodeString), NUM_OF_BYTES_TO_CODE_STRING_INT)
    conn.send(lVal + encodeString)


def sendHash(conn, hash, hashLen):
    if len(hash) != hashLen:
        raise Exception()
    conn.send(hash)


def recvInt(conn):
    return __decodeInt__(conn.recv(NUM_OF_BYTES_TO_CODE_INT))


def recvBool(conn):
    return __decodeInt__(conn.recv(NUM_OF_BYTES_TO_CODE_BOOL)) == 1


def recvString(conn):
    length = __decodeInt__(conn.recv(NUM_OF_BYTES_TO_CODE_STRING_INT))
    return conn.recv(length).decode()


def recvHash(conn, hashLen):
    return conn.recv(hashLen)
