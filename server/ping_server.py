import socket
from threading import Thread
from select import select

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip = socket.gethostbyname(socket.gethostname())
port = 6998

sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((ip, port))
sock.listen()
print("ping server started!")

connected = []

def accept():
    global connected
    while True:
        conn, addr = sock.accept()
        connected.append(conn)
Thread(target=accept, daemon=True).start()

try:
    while True:
        r = select(connected, [], [], 0.1)[0]
        if r:
            # print("network: 🟩", end="\r")
            try:
                x = r[0].recv(8)
                if not x:
                    del connected[connected.index(r[0])]
                else:
                    r[0].send(b"ping")
            except ConnectionResetError:
                del connected[connected.index(r[0])]
        else:
            # print("network: 🔴", end="\r")
            pass

except KeyboardInterrupt:
    sock.close()