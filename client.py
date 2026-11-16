# Client Implementation

import os
import socket
import ssl
import sys
import threading
import time


from pathlib import Path

IP = "localhost"
PORT = 4045
ADDR = (IP,PORT)
SIZE = 8096 ## byte .. buffer size
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"
BASE_DIR = Path.cwd()

def main() -> int:
    start = time.perf_counter()

    context = ssl.create_default_context(cafile="cert.pem")
    context.check_hostname = False

    socket_t = socket.create_connection(ADDR)
    client = context.wrap_socket(socket_t)

    client.recv(SIZE)

    client.send("OK".encode(FORMAT))
    print("Handshake completed")

    end = time.perf_counter()

    print(f"Took {end - start:.4f} seconds to connect.")

    createOrSign = input("Choose c to create account or s to sign in > ")
    client.send(createOrSign.encode(FORMAT))

    if createOrSign.lower()[0] == "c":

        while True:
            startCreate = client.recv(SIZE)
            username = input("Create username > ")
            client.send(username.encode(FORMAT))
            client.recv(SIZE)

            password = input("Create password > ")
            client.send(password.encode(FORMAT))
            client.recv(SIZE)

            createConfirm = client.recv(SIZE).decode(FORMAT).split("@")

            if createConfirm[0] == "USR_CREATE":
                print(createConfirm[1])
                break

            print("Server reported not success: ", createConfirm[1])
            print("Retry.")

    while True:
        client.recv(SIZE).decode(FORMAT)

        signInUser = input("Enter Username: ")
        client.send(signInUser.encode(FORMAT))
        client.recv(SIZE).decode(FORMAT)

        signInPass = input("Enter Password: ")
        client.send(signInPass.encode(FORMAT))
        client.recv(SIZE).decode(FORMAT)

        signInConfirm = client.recv(SIZE).decode(FORMAT).split("@")

        if signInConfirm[0] == "SIGNED":
            print(signInConfirm[1])
            break

        print("Server reported not success: ", signInConfirm[1])
        print("Retry.")

    while True:
        client.recv(SIZE)

        command = input("Enter command: ")

        start = time.perf_counter()

        if command == "dir" or command == "ls" or command == "directory":
            client.send("OK@dir".encode(FORMAT))
            print(client.recv(SIZE).decode(FORMAT))

        if command == "logout":
            client.send("OK@logout".encode(FORMAT))
            sys.exit()

        command_arg = command.split(" ")
        command_name = command_arg[0]

        if command_name == "folder":

            client.send(f"OK@{command}".encode(FORMAT))

            folder_response = client.recv(SIZE).decode(FORMAT).split("@")

            if folder_response[0] == "OK":
                print(folder_response[1])

            if folder_response[0] == "ERR":
                print(folder_response[1])

        if command_name == "delete":

            client.send(f"OK@{command}".encode(FORMAT))

            folder_response = client.recv(SIZE).decode(FORMAT).split("@")

            if folder_response[0] == "OK":
                print(folder_response[1])

            if folder_response[0] == "ERR":
                print(folder_response[1])

        if command_name == "upload":

            source = command_arg[1]
            source_path = BASE_DIR / source

            client.send(f"OK@{command}".encode(FORMAT))

            folder_response = client.recv(SIZE).decode(FORMAT).split("@")

            if folder_response[0] == "ERR":
                print(folder_response[1])

            if folder_response[0] == "ASK":
                ask_response = input(folder_response[1])
                client.send(ask_response.encode(FORMAT))

                overwrite_response = client.recv(SIZE).decode(FORMAT).split("@")

                if overwrite_response[0] == "NOT":
                    print(overwrite_response[1])
                    continue

                if overwrite_response[0] == "PROC":
                    print(overwrite_response[1])

            start_upload = time.perf_counter()
            client.recv(SIZE)

            with open(source_path, "rb") as file:
                total_size = os.fstat(file.fileno()).st_size

                client.send(file.read(total_size))

                client.recv(SIZE)

                print("Done.")

            # The minus 2.5 is to take into account the server needing to timeout.
            end_upload = time.perf_counter() - 2.5

            time_took = end_upload - start_upload

            print(f"Upload took {time_took:.4f} seconds, with an average speed of {(total_size / (1024 * 1024)) / time_took:.4f} MB/s")

        if command_name == "download":

            client.send(f"OK@{command}".encode(FORMAT))

            destination = command_arg[2]
            destination_path = BASE_DIR / destination

            folder_response = client.recv(SIZE).decode(FORMAT).split("@")

            if folder_response[0] == "ERR":
                print(folder_response[0])
                continue

            orig = client.gettimeout()
            client.settimeout(2.5)
            client.send("OK".encode(FORMAT))

            start_download = time.perf_counter()

            total_bytes = 0

            with open(destination_path, "ab") as file:
                try:
                    while True:
                        byte = client.recv(SIZE)
                        file.write(byte)
                        total_bytes += len(byte)
                except TimeoutError:
                    pass

            client.settimeout(orig)

            client.send("Ok".encode(FORMAT))

            end_download = time.perf_counter() - 2.5

            elapsed = end_download - start_download

            print(f"Download Complete, took {elapsed:.4f} with a speed of {(total_bytes / (1024 * 1024)) / elapsed:.4f} MB/s")

        end = time.perf_counter()

        print(f"Operation took {end - start:.4f} seconds.")


if __name__ == "__main__":
    main()
