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

def handle_client(conn: ssl.SSLSocket, addr):
    print(f"New connection: {addr}")

    # Handshake
    conn.send("OK@Ready".encode(FORMAT))
    conf = conn.recv(SIZE).decode(FORMAT)

    if conf != "OK":
        return

    print(f"Handshake completed with {addr}")

    current_dir = SERVER_DATA_PATH

    signed_in = False
    username = ""
    password = ""

    create_or_sign = conn.recv(SIZE).decode(FORMAT)

    in_account_creation = False
    if create_or_sign.lower()[0] == "c":
        in_account_creation = True

    # Account Creation
    while in_account_creation:
        print(f"Creating account on {addr}")

        conn.send("READY@Ready for account creation".encode(FORMAT))

        username = conn.recv(SIZE).decode(FORMAT)
        print(f"Received username creation on {addr}")
        conn.send("REC@Received username".encode(FORMAT))

        password = conn.recv(SIZE).decode(FORMAT)
        print(f"Received password creation on {addr}")
        conn.send("REC@Received password".encode(FORMAT))

        if exists(SERVER_DATA_PATH / username):
            print(f"{addr} tried to make an account that already exists.")
            conn.send("USR_EXIST@User already exists.".encode(FORMAT))
            time.sleep(1.5)
            continue

        (current_dir / username).mkdir(exist_ok = False)

        with open(current_dir / username / ".pass", "w", encoding = "utf-8") as f:
            f.write(password)

        conn.send("USR_CREATE@Successfully created user.".encode(FORMAT))
        print(f"{addr} created account named {username}")
        in_account_creation = False

    # Signing in
    while not signed_in:
        print(f"Signing in on {addr}")
        conn.send("READY@Ready for sign in".encode(FORMAT))

        username = conn.recv(SIZE).decode(FORMAT)
        print(f"Received username sign in on {addr}")
        conn.send("REC@Received username".encode(FORMAT))

        password = conn.recv(SIZE).decode(FORMAT)
        print(f"Received password sign on on {addr}")
        conn.send("REC@Received password".encode(FORMAT))

        time.sleep(0.5)

        if exists(SERVER_DATA_PATH / username) and exists(SERVER_DATA_PATH / username / ".pass"):
            with open(SERVER_DATA_PATH / username / ".pass", "r") as f:
                password_check = f.read()

                if password == password_check:
                    current_dir = current_dir / username
                    conn.send(f"SIGNED@Successfully signed in to {username}.".encode(FORMAT))
                    print(f"{addr} signed into {username}")
                    signed_in = True
                    break

                conn.send("NO_SIGN@Username or password was incorrect.".encode(FORMAT))
                print(f"{addr} gave the wrong username or password.")
                time.sleep(1.5)
                continue

            conn.send("NO_SIGN@Username or password is incorrect.".encode(FORMAT))
            print(f"{addr} gave the wrong username or password.")
            time.sleep(1.5)
            continue

        conn.send("NO_SIGN@Username or password is incorrect.".encode(FORMAT))
        print(f"{addr} gave the wrong username or password.")
        time.sleep(1.5)

    # Actual command interface
    while True:
        conn.send("AWAIT@Awaiting input".encode(FORMAT))
        cmd = conn.recv(SIZE).decode(FORMAT)

        cmd_split = cmd.split("@")

        if cmd_split[0] != "OK":
            break

        cmd_args = cmd_split[1].split(" ")
        cmd_name = cmd_args[0]

        if cmd_name == "dir" or cmd_name == "ls" or cmd_name == "directory":
            ls_res = subprocess.run(["ls", "-R", str(current_dir.absolute())], capture_output=True, text=True)

            output = ls_res.stdout

            conn.send(output.encode(FORMAT))

        if cmd_name == "logout":
            conn.close()
            print(f"Successfully closed connection from {addr}")
            break

        if cmd_name == "folder":
            cmd_sub = cmd_args[1]
            if cmd_sub == "add" or cmd_sub == "create":
                cmd_folder_name = cmd_args[2]
                if (current_dir / cmd_folder_name).exists():
                    conn.send("ERR@Folder already exists".encode(FORMAT))
                    continue

                (current_dir / cmd_folder_name).mkdir()
                conn.send("OK@Created subfolder".encode(FORMAT))



def main():

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile = "cert.pem", keyfile = "key.pem")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)

    server.listen()

    print(f"Listening securely on {IP}:{PORT}")

    try:
        with context.wrap_socket(server, server_side = True) as s_socket:
            while True:
                conn, addr = s_socket.accept()

                thread = threading.Thread(target = handle_client, args = (conn, addr))
                thread.start()

    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Stopping.")
        try:
            server.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        finally:
            server.close()

if __name__ == "__main__":
    main()
