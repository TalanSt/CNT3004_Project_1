# Client Implementation

import os
import socket
import ssl
import sys
import threading


from pathlib import Path

IP = "172.19.168.48"
PORT = 4045
ADDR = (IP,PORT)
SIZE = 8096 ## byte .. buffer size
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"
BASE_DIR = Path.cwd()

#def handle_client(conn, addr):
    

def main() -> int:
    context = ssl.create_default_context(cafile="cert.pem")
    context.check_hostname = False

    socket_t = socket.create_connection(ADDR)
    client = context.wrap_socket(socket_t)

    client.recv(SIZE)

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
        data = client.recv(SIZE).decode(FORMAT)

        command = input("Enter command: ")

        if command == "OK":
            print("Good")
        elif command == "Disconnected from the sever":
            print("Disconnected")


    
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


            print(client.recv(SIZE).decode(FORMAT))

            with open(source_path, "rb") as file:
                total_size = os.fstat(file.fileno()).st_size

                client.send(file.read(total_size))

                client.recv(SIZE)

                print("Done.")

                """
                while True:
                    for i in range(8):
                        new_file = file.read(SIZE)

                        if not new_file:
                            client.send("DONE".encode(FORMAT))

                            upload_conf = client.recv(SIZE).decode(FORMAT).split("@")
                            print(upload_conf[1])
                            
                            break

                        client.send(new_file)

                    print(f"Percent Completed {round((file.tell() / total_size) * 100, 2)}")

                    send_continue = client.recv(SIZE).decode(FORMAT).split("@")

                    if (send_continue[0] == "CONT"):
                        continue

                    else:
                        break
                """

            
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

            with open(destination_path, "ab") as file:
                try:
                    while True:
                        byte = client.recv(SIZE)
                        file.write(byte)
                except TimeoutError:
                    pass
                    
            client.settimeout(orig)

            client.send("Ok".encode(FORMAT))
            print("Download Complete")
                

        

            

       








            
                

                

                    
    
        # elif command == "DOWNLOAD"



if __name__ == "__main__":
    main()
