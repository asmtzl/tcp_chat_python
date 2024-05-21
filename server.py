import socket
import threading
import json
from datetime import datetime
import os

class Server:
    def __init__(self, host='127.0.0.1', port=12345, base_dir='chat/logs'):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        self.clients = {}
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        print(f"Server started on {host}:{port}")
        print(f"Messages will be saved to {base_dir}")

    def handle_client(self, client, username):
        user_file = os.path.join(self.base_dir, f"{username}.json")
        while True:
            try:
                msg = client.recv(1024)
                if not msg:
                    break

                
                if msg.decode() == "/users":
                    self.send_connected_clients(client, username)
                elif msg.decode() == "/history":
                    self.send_history(client, user_file)
                elif msg.decode().startswith("/list"):
                    self.create_user_group(username, msg.decode())
                elif msg.decode().startswith("/search"):
                    keyword = msg.decode().split(" ", 1)[1]
                    self.search_messages(client, user_file, keyword)
                elif msg.decode().startswith("@"):
                    target_username, message = msg.decode().split(" ", 1)
                    target_username = target_username[1:]  
                    self.send_private_message(target_username, username, message)
                    self.save_message(user_file, username, f"(Private to {target_username}): {message}")
                    self.save_message(os.path.join(self.base_dir, f"{target_username}.json"), target_username,
                                      f"(Private from {username}): {message}")
                else:
                    self.broadcast(msg, client)
                    self.save_message(user_file, username, msg.decode())
            except Exception as e:
                print(f"Error: {e}")
                break
        client.close()
        del self.clients[username]
        self.show_connected_clients()

    def save_message(self, user_file, username, msg):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message_data = {
            "user": username,
            "message": msg,
            "timestamp": timestamp
        }
        with open(user_file, "a") as f:
            f.write(json.dumps(message_data) + "\n")

    def broadcast(self, msg, _client):
        sender_username = self.get_username(_client)
        formatted_msg = f"{sender_username}: {msg.decode()}"
        for client in self.clients.values():
            if client != _client:
                client.send(formatted_msg.encode())

    def send_private_message(self, target_username, sender_username, msg):
        if target_username in self.clients:
            self.clients[target_username].send(f"Private from {sender_username}: {msg}".encode())
        else:
            self.clients[sender_username].send(f"User {target_username} not found.".encode())

    def show_connected_clients(self):
        print("Connected Clients:")
        for username in self.clients:
            print(username)

    def get_username(self, client):
        for username, c in self.clients.items():
            if c == client:
                return username
        return "Unknown"

    def send_connected_clients(self, client, requesting_user):
        connected_clients = "Connected Clients:\n" + "\n".join(self.clients.keys())
        client.send(connected_clients.encode())

    def send_history(self, client, user_file):
        if os.path.exists(user_file):
            with open(user_file, "r") as f:
                history = f.read()
                client.send(history.encode())
        else:
            client.send("No message history found.".encode())

    def create_user_group(self, username, msg):
        # /list komutu ile gelen mesajı işle
        parts = msg.split(" ")
        group_name = parts[1]
        members = parts[2].split(",")
        
        if username not in self.user_groups:
            self.user_groups[username] = {}
        self.user_groups[username][group_name] = members

    def search_messages(self, client, user_file, keyword):
        if os.path.exists(user_file):
            matched_messages = []
            with open(user_file, "r") as f:
                for line_number, line in enumerate(f, 1):
                    try:
                        message_data = json.loads(line.strip())
                        if keyword.lower() in message_data['message'].lower():
                            matched_messages.append(message_data)
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON at line {line_number}: {line.strip()}")
                        print("Error:", e)
            if matched_messages:
                response = json.dumps(matched_messages) 
                client.send(response.encode())
            else:
                client.send("No matching messages found.".encode())
        else:
            client.send("No message history found.".encode())


    def start(self):
        while True:
            client, addr = self.server.accept()
            username = client.recv(1024).decode()
            if username not in self.clients:
                self.clients[username] = client
                print(f"{username} connected from {addr}")
                thread = threading.Thread(target=self.handle_client, args=(client, username))
                thread.start()
                self.show_connected_clients()
            else:
                client.send("Username already taken.".encode())
                client.close()




if __name__ == "__main__":
    server = Server()
    server.start()