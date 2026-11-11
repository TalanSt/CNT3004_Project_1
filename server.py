from os import path
from os.path import exists, isfile
from pathlib import Path
import socket
import threading
import subprocess

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes

IP = "localhost"
PORT = 4045
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
BASE_DIR = Path.cwd()
SERVER_DATA_PATH = BASE_DIR / "server_data"

def handle_client(conn: socket.socket, addr, PRIV_KEY: PrivateKeyTypes):
    print(f"New connection: {addr}")

    pub_key = PRIV_KEY.public_key().public_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PublicFormat.SubjectPublicKeyInfo
    )

    current_dir = SERVER_DATA_PATH

    # conn.send(f"PUB@{pub_key}".encode(FORMAT))

    signed_in = False
    username = ""
    password = ""

    while True:

        create_or_sign = conn.recv(SIZE).decode(FORMAT)

        in_account_creation = False
        if create_or_sign.lower()[0] == "c":
            in_account_creation = True

        while in_account_creation:
            username = conn.recv(SIZE).decode(FORMAT)
            password = conn.recv(SIZE).decode(FORMAT)

            if exists(SERVER_DATA_PATH / username):
                conn.send("USR_EXIST@User already exists.".encode(FORMAT))
                continue

            (current_dir / username).mkdir(exist_ok = False)

            with open(current_dir / username / ".pass", "w", encoding = "utf-8") as f:
                f.write(password)

            conn.send("USR_CREATE@Successfully created user.".encode(FORMAT))
            in_account_creation = False



        while not signed_in:
            username = conn.recv(SIZE).decode(FORMAT)
            password = conn.recv(SIZE).decode(FORMAT)

            if exists(SERVER_DATA_PATH / username) and exists(SERVER_DATA_PATH / username / ".pass"):
                with open(SERVER_DATA_PATH / username / ".pass", "r") as f:
                    password_check = f.read()

                    if password == password_check:
                        current_dir = current_dir / username
                        conn.send(f"SIGNED@Successfully signed in to {username}.".encode(FORMAT))
                        signed_in = True
                        break

                    conn.send("NO_SIGN@Username or password was incorrect.".encode(FORMAT))
                    continue

                conn.send("NO_SIGN@Username or password is incorrect.".encode(FORMAT))
                continue

            conn.send("NO_SIGN@Username or password is incorrect.".encode(FORMAT))

        data =  conn.recv(SIZE).decode(FORMAT)

        data = data.split("@")
        cmd = data[0]

def main():
    PRIVATE_KEY = None

    if not SERVER_DATA_PATH.exists():
        subprocess.run(["mkdir", "server_data"], check = False)

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

    print(f"Listening on {IP}:{PORT}")

    while True:
        conn, addr = server.accept()

        thread = threading.Thread(target = handle_client, args = (conn, addr, PRIVATE_KEY))
        thread.start()

if __name__ == "__main__":
    main()
