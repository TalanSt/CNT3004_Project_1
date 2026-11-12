# Client Implementation

import os
import socket
import ssl

IP = "172.19.168.48"
PORT = 4045
ADDR = (IP,PORT)
SIZE = 1024 ## byte .. buffer size
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"

def main() -> int:
    context = ssl.create_default_context(cafile="cert.pem")
    context.check_hostname = False

    socket_t = socket.create_connection(ADDR)
    client = context.wrap_socket(socket_t)
    
    print("Connected to server")

    conf = client.recv(SIZE).decode(FORMAT)
    if conf != "OK@Ready":
        return

    client.send("OK".encode(FORMAT))
    print("Handshake completed")

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
        client.recv(SIZE)

        signInUser = input("Enter Username:")
        client.send(signInUser.encode(FORMAT))
        client.recv(SIZE)

        signInPass = input("Enter Password:")
        client.send(signInPass.encode(FORMAT))
        client.recv(SIZE)

        signInConfirm = client.recv(SIZE).decode(FORMAT).split("@")

        if signInConfirm[0] == "SIGNED":
            print(signInConfirm[1])
            break

        print("Server reported not success: ", signInConfirm[1])
        print("Retry.")

    while True:
        data = client.recv(SIZE).decode(FORMAT)
        command, message = data.split("@")

        if command == "OK":
            print("Good")
        elif command == "Disconnected from the sever":
            print("Disconnected")


if __name__ == "__main__":
    main()
