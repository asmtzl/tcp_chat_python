import socket
import threading
import json
class Client:
    def __init__(self, host='127.0.0.1', port=12345):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))
        print('/users: list users \n/history: show massage history\n/list groupname user1,user2,... : create user list \n/search keyword : search for a keyword \n@username massage : send special message \n')
        self.username = input("Enter your username: ")
        self.client.send(self.username.encode())


    def receive_messages(self):
        while True:
            try:
                msg = self.client.recv(1024)
                if msg.decode().startswith("{"):  # JSON formatında mesaj
                    message_data = json.loads(msg.decode())
                    print(f"{message_data['timestamp']} {message_data['user']}: {message_data['message']}")
                else:
                    print(msg.decode())
            except Exception as e:
                print(f"Error: {e}")
                self.client.close()
                break

    def send_message(self):
        while True:
            msg = input()
            self.client.send(msg.encode())

    def start(self):
        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.start()
        send_thread = threading.Thread(target=self.send_message)
        send_thread.start()

if __name__ == "__main__":
    client = Client()
    client.start()
