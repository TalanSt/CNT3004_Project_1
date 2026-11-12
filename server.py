from os import path, system
from os.path import exists, isfile
from pathlib import Path
import socket
import threading
import subprocess
import time
import ssl

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes

IP = "172.19.168.48"
PORT = 4045
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
BASE_DIR = Path.cwd()
SERVER_DATA_PATH = BASE_DIR / "server_data"

def handle_client(conn: socket.socket, addr):
    print(f"New connection: {addr}")

    # Handshake
    conn.send("OK@Ready".encode(FORMAT))
    conf = conn.recv(SIZE).decode(FORMAT)

    if conf != "OK":
        return

    print(f"Handshake completed with {addr}")


    pub_key = PRIV_KEY.public_key().public_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PublicFormat.SubjectPublicKeyInfo
    )

    current_dir = SERVER_DATA_PATH

    # conn.send(f"PUB@{pub_key}".encode(FORMAT))

    signed_in = False
    username = ""
    password = ""

    create_or_sign = conn.recv(SIZE).decode(FORMAT)

    in_account_creation = False
    if create_or_sign.lower()[0] == "c":
        in_account_creation = True

    while in_account_creation:
        conn.send("READY@Ready for account creation".encode(FORMAT))

        username = conn.recv(SIZE).decode(FORMAT)
        conn.send("REC@Received username".encode(FORMAT))

        password = conn.recv(SIZE).decode(FORMAT)
        conn.send("REC@Received password".encode(FORMAT))

        if exists(SERVER_DATA_PATH / username):
            conn.send("USR_EXIST@User already exists.".encode(FORMAT))
            time.sleep(1.5)
            continue

        (current_dir / username).mkdir(exist_ok = False)

        with open(current_dir / username / ".pass", "w", encoding = "utf-8") as f:
            f.write(password)

        conn.send("USR_CREATE@Successfully created user.".encode(FORMAT))
        in_account_creation = False

    while not signed_in:
        conn.send("READY@Ready for sign in".encode(FORMAT))

        username = conn.recv(SIZE).decode(FORMAT)
        conn.send("REC@Received username".encode(FORMAT))

        password = conn.recv(SIZE).decode(FORMAT)
        conn.send("REC@Received password".encode(FORMAT))

        if exists(SERVER_DATA_PATH / username) and exists(SERVER_DATA_PATH / username / ".pass"):
            with open(SERVER_DATA_PATH / username / ".pass", "r") as f:
                password_check = f.read()

                if password == password_check:
                    current_dir = current_dir / username
                    conn.send(f"SIGNED@Successfully signed in to {username}.".encode(FORMAT))
                    signed_in = True
                    break

                conn.send("NO_SIGN@Username or password was incorrect.".encode(FORMAT))
                time.sleep(1.5)
                continue

            conn.send("NO_SIGN@Username or password is incorrect.".encode(FORMAT))
            time.sleep(1.5)
            continue

        conn.send("NO_SIGN@Username or password is incorrect.".encode(FORMAT))
        time.sleep(1.5)

def main():

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile = "cert.pem", keyfile = "key.pem")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)

    server.listen()

    print(f"Listening securely on {IP}:{PORT}")

    with context.wrap_socket(server, server_side = True) as s_socket:
        while True:
            conn, addr = s_socket.accept()

            thread = threading.Thread(target = handle_client, args = (conn, addr))
            thread.start()

if __name__ == "__main__":
    main()
