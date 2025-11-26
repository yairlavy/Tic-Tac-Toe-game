# protocol.py
def send(conn, msg):
    conn.sendall((msg + "\n").encode())

def recv_line(conn):
    buffer = ""
    while True:
        data = conn.recv(1).decode()
        if not data:
            return None
        if data == "\n":
            return buffer.strip()
        buffer += data
