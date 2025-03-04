import socket
import re

class SMTPClient:
    def __init__(self, server: str, port: int):
        self.server = server
        self.port = port
        self.socket = None
        self.response = b''

    def connect(self):
        """Establece conexión con el servidor SMTP."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server, self.port))
        self._get_response()  # Leer respuesta inicial del servidor (220) segun RFC 5321

    def _send_command(self, command: str):
        """Envía un comando al servidor y guarda la respuesta."""
        self.socket.sendall(f"{command}\r\n".encode())
        self._get_response() 

    def _get_response(self):
        """Lee la respuesta del servidor."""
        self.response = b''
        while True:
            data = self.socket.recv(1024)
            self.response += data
            if data.endswith(b'\r\n'):  # Fin de respuesta 
                break

    def send_email(self, from_addr: str, to_addrs: list, subject: str, body: str):
        """Envía un correo siguiendo el flujo SMTP."""
        self._send_command(f"HELO {socket.gethostname()}")
        self._send_command(f"MAIL FROM:<{from_addr}>")
        for addr in to_addrs:
            self._send_command(f"RCPT TO:<{addr}>")
        self._send_command("DATA")
        # Construir mensaje según RFC 5322
        # Dentro de send_email()
        message = (
                f"From: {from_addr}\r\n"
                f"To: {', '.join(to_addrs)}\r\n"
                f"Subject: {subject}\r\n\r\n"
                f"{body}\r\n"  # Línea del cuerpo
                ".\r\n"         # Línea de terminación (CRLF + . + CRLF)
            )
        self.socket.sendall(message.encode())
        self._get_response()
        self._send_command("QUIT")
        
    def _send_command(self, command: str):
        print(f"[CLIENTE] Enviando: {command}")  # <-- Log de consola 
        self.socket.sendall(f"{command}\r\n".encode())
        self._get_response()
        print(f"[CLIENTE] Respuesta: {self.response.decode()}")  # <-- Log de consola

    def close(self):
        """Cierra la conexión."""
        if self.socket:
            self.socket.close()