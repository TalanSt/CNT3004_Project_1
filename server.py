from os import path, system
import os
from os.path import exists, isfile
from pathlib import Path
import socket
import threading
import subprocess
import time
import ssl

IP = "172.19.168.48"
PORT = 4045
ADDR = (IP, PORT)
SIZE = 8096
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
            if len(cmd_args) != 3:
                print(f"{addr} gave invalid arguments on folder cmd")
                conn.send("ERR@Incorrect arguments: folder [add|remove] [name]".encode(FORMAT))
                continue

            cmd_sub = cmd_args[1]
            if cmd_sub == "add" or cmd_sub == "create":
                cmd_folder_name = cmd_args[2]
                if (current_dir / cmd_folder_name).exists():
                    conn.send("ERR@Folder already exists".encode(FORMAT))
                    print(f"{addr} tried to make a folder that already exists.")
                    continue

                (current_dir / cmd_folder_name).mkdir()
                conn.send("OK@Created subfolder".encode(FORMAT))
                print(f"{addr} created a new folder")
                continue

            if cmd_sub == "del" or cmd_sub == "delete" or cmd_sub == "remove":
                cmd_folder_name = cmd_args[2]
                if not (current_dir / cmd_folder_name).exists():
                    conn.send("ERR@Folder does not exist.".encode(FORMAT))
                    print(f"{addr} tried to remove a folder that doesn't exist.")
                    continue
                if not (current_dir / cmd_folder_name).is_dir():
                    conn.send("ERR@Given a file, not a folder.".encode(FORMAT))
                    print(f"{addr} tried to remove a file with the folder command.")
                    continue

                (current_dir / cmd_folder_name).rmdir()
                conn.send("OK@Deleted folder and its contents.".encode(FORMAT))
                print(f"{addr} removed a folder.")
                continue

            conn.send("ERR@Incorrect arguments: folder [add|remove] [name]".encode(FORMAT))
            print(f"{addr} gave invalid arguments on folder cmd.")
            continue

        if cmd_name == "delete":
            if len(cmd_args) != 2:
                conn.send("ERR@Incorrect arguments: delete [name]".encode(FORMAT))
                print(f"{addr} gave invalid arguments on delete cmd.")
                continue

            delete_file = current_dir / cmd_args[1]
            if not delete_file.exists():
                conn.send("ERR@File does not exist.".encode(FORMAT))
                print(f"{addr} tried to delete a file that does not exist.")
                continue

            if not delete_file.is_file():
                conn.send("ERR@Given path is not a file.".encode(FORMAT))
                print(f"{addr} tried to delete a folder with the delete cmd.")
                continue

            delete_file.unlink()
            conn.send("OK@Deleted file.".encode(FORMAT))
            print(f"{addr} deleted a file.")
            continue

        if cmd_name == "upload" or cmd_name == "up":
            if len(cmd_args) != 3:
                conn.send("ERR@Invalid arguments. upload [source] [destination]".encode(FORMAT))
                print(f"{addr} gave invalid arguments on upload cmd")
                continue

            source = cmd_args[1]
            destination = cmd_args[2]

            destination_path = current_dir / destination

            if destination_path.exists():
                if destination_path.is_dir():
                    conn.send("ERR@Given path is a directory and cannot be overwritten.".encode(FORMAT))
                    print(f"{addr} attempted to upload a file when it exists as a directory.")
                    continue

                conn.send("ASK@File already exists. Overwrite [y/N]? ".encode(FORMAT))
                print(f"{addr} is attempting to upload a file that already exists. Asking to overwrite.")

                overwrite = conn.recv(SIZE).decode(FORMAT)[0]

                if overwrite.lower() == "n":
                    conn.send("NOT@Nothing happened.".encode(FORMAT))
                    print(f"{addr} decided to not overwrite.")
                    continue

                print(f"{addr} will overwrite the file.")
                conn.send("PROC@Proceed with file upload.".encode(FORMAT))
                destination_path.unlink()

            conn.send("READY@Ready to receive file.".encode(FORMAT))

            with open(destination_path, "ab") as file:
                i = 0

                orig = conn.gettimeout()
                conn.settimeout(2.5)

                try:
                    while True:
                        print(f"Received chunk. {i}")

                        bits = conn.recv(SIZE)

                        file.write(bits)

                        i = i + 1
                except TimeoutError:
                    pass

                print("Finished upload")

                conn.send("OK@Finished upload".encode(FORMAT))

                conn.settimeout(orig)

                """print(f"Receiving file from {addr}")
                while True:

                    finished = False
                    for i in range(8):

                        bits = conn.recv(SIZE)
                        print(f"Received chunk from {addr}")

                        if bits.decode(FORMAT) == "DONE":
                            print(f"Finished uploading file from {addr}.")
                            conn.send("OK@Done.".encode(FORMAT))
                            finished = True
                            break

                        file.write(bits)

                    conn.send("CONT@Continue sending bytes.".encode(FORMAT))

                    if finished:
                        break"""

        if cmd_name == "download" or cmd_name == "dl":
            if len(cmd_args) != 3:
                conn.send("ERR@Incorrect Arguments: download [server_source] [client_destination]".encode(FORMAT))
                continue

            source = cmd_args[1]
            destination = cmd_args[2]

            source_path = current_dir / source

            if not source_path.exists():
                conn.send("ERR@Source file does not exist".encode(FORMAT))
                continue

            if source_path.is_dir():
                conn.send("ERR@Source arg is a directory, not a file.".encode(FORMAT))
                continue

            print("Ready to send file.")

            conn.send("OK@Ready".encode(FORMAT))
            conn.recv(SIZE)

            with open(source_path, "rb") as file:
                print("Sending file.")
                file_size = source_path.stat().st_size

                conn.send(file.read(file_size))


            conn.recv(SIZE)
            print("Done.")


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
