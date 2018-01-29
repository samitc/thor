def sendInt(val: int):
    bl = 1 if val == 0 else val.bit_length()
    return val.to_bytes(bl, 'big')


def sendBool(val):
    return sendInt(1 if val else 0)


def sendString(val: str):
    return val.encode()


def recvInt(val):
    return int.from_bytes(val, 'big')


def recvBool(val):
    return recvInt(val) == 1


def recvString(val):
    return val.decode()
def send(conn):
    conn.recv(1)
def recv(conn):
    conn.send(bytes(1))