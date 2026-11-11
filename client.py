# Client Implementation

import os
import socket

IP = "localhost"
PORT = 4045
ADDR = (IP,PORT)
SIZE = 1024 ## byte .. buffer size
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"

def main() -> int:
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(ADDR)
    
    print("Connected to server")

    conf = client.recv(SIZE).decode(FORMAT)
    if conf != "OK@Ready":
        return

    client.send("OK".encode(FORMAT))
    print("Handshake completed")

    while True:
        data = client.recv(SIZE).decode(FORMAT)
        command, message = data.split("@")

        if command == "OK":
            print("Good")
        elif command == "Disconnected from the sever":
            print("Disconnected")

        


    


        




      




if __name__ == "__main__":
    raise SystemExit(main())
