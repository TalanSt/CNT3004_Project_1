from os import path
from os.path import isfile
import socket
import threading

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes

IP = "localhost"
PORT = 4045
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = "./server_data"

def handle_client(conn: socket.socket, addr, PRIV_KEY: PrivateKeyTypes):
    print(f"New connection: {addr}")

    pub_key = PRIV_KEY.public_key().public_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PublicFormat.SubjectPublicKeyInfo
    )

    conn.send(pub_key)

    while True:

        data =  conn.recv(SIZE).decode(FORMAT)
        data = data.split("@")
        cmd = data[0] 

def main():
    PRIVATE_KEY = None

    if not isfile("private.pem"):
        print("A private key has not been made yet, and/or it is in the wrong location `private.pem`. Exiting.")
        return

    server = socket.socket()
    server.bind(ADDR)


    with open("private.pem", "rb") as f:
        key_data = f.read()
        PRIVATE_KEY = serialization.load_pem_private_key(
            key_data,
            password=None
        )


    server.listen()

    while True:
        conn, addr = server.accept()

        thread = threading.Thread(target = handle_client, args = (conn, addr, PRIVATE_KEY))
        thread.start()




if __name__ == "__main__":
    main()
