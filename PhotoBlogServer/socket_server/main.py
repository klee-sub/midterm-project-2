import os
import socket
from datetime import datetime

class SocketServer:
    def __init__(self):
        self.bufsize = 1024
        with open('./response.bin', 'rb') as file:
            self.RESPONSE = file.read()

        self.DIR_PATH = './request'
        self.createDir(self.DIR_PATH)

    def createDir(self, path):
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except OSError:
            print("Error: Failed to create the directory.")

    def run(self, ip, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen(10)
        print("Start the socket server...")
        print("'ctrl+c' for stopping the server.!\r\n")

        try:
            while True:
                clnt_sock, rem_addr = self.sock.accept()
                clnt_sock.settimeout(5.0)
                print("Request message...\r\n")

                request = b""
                while True:
                    try:
                        chunk = clnt_sock.recv(self.bufsize)
                    except socket.timeout:
                        break
                    if not chunk:
                        break
                    request += chunk

                filename = datetime.now().strftime('%Y-%m-%d-%H-%M-%S.bin')
                with open(os.path.join(self.DIR_PATH, filename), 'wb') as file:
                    file.write(request)

                clnt_sock.sendall(self.RESPONSE)

                clnt_sock.close()
        except KeyboardInterrupt:
            print("\r\nStop the server...")

        self.sock.close()

if __name__ == '__main__':
    server = SocketServer()
    server.run("127.0.0.1", 8000)
