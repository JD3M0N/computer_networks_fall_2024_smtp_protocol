import socket
import json

def handle_client(client_socket):
    client_socket.send(b"220 Welcome to Simple SMTP Server\r\n")
    while True:
        data = client_socket.recv(1024).decode()
        if not data:
            break
        print(f"Received: {data.strip()}")

        response = {"status_code": 250, "message": "Message accepted for delivery"}
        if data.startswith("HELO") or data.startswith("EHLO"):
            response["message"] = "Hello"
        elif data.startswith("MAIL FROM"):
            response["message"] = "Sender OK"
        elif data.startswith("RCPT TO"):
            response["message"] = "Recipient OK"
        elif data.startswith("DATA"):
            response["message"] = "Ready for data"
        elif data.startswith("QUIT"):
            response["message"] = "Goodbye"
        else:
            response = {"status_code": 502, "message": "Command not implemented"}

        client_socket.send(json.dumps(response).encode() + b"\r\n")

    client_socket.close()

def start_server(bind_address="0.0.0.0", port=2525):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((bind_address, port))
    server_socket.listen(5)
    print(f"SMTP server listening on {bind_address}:{port}")
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr}")
        handle_client(client_socket)

if __name__ == "__main__":
    start_server()
