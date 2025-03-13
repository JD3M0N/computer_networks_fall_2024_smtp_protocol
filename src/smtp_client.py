#!/usr/bin/env python3
import asyncio
import base64
from email.utils import formatdate
import logging
import re
import argparse
import json
import sys

# Configuración básica de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constantes y expresiones regulares
DEFAULT_SMTP_SERVER = "127.0.0.1"
DEFAULT_SMTP_PORT = 2525
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

class SMTPClientError(Exception):
    """Excepción personalizada para errores del cliente SMTP"""
    pass

def validate_email_address(email: str) -> bool:
    """Valida una dirección de email usando expresión regular"""
    return isinstance(email, str) and bool(EMAIL_REGEX.match(email))

async def send_email(
    sender_address: str,
    sender_password: str,
    recipient_addresses: list,
    email_subject: str,
    email_body: str,
    custom_headers: dict,
    smtp_server: str = DEFAULT_SMTP_SERVER,
    smtp_port: int = DEFAULT_SMTP_PORT
) -> tuple:
    """
    Función asíncrona que simula el envío de un correo.
    
    Retorna:
        tuple: (email_sent: bool, error_type: int)
            error_type: 0 => éxito, 1 => error en remitente, 2 => error en destinatario
    """
    # Validar dirección remitente
    if not sender_address or not validate_email_address(sender_address):
        return False, 1

    # Validar cada destinatario
    for recipient in recipient_addresses:
        if not recipient or not validate_email_address(recipient):
            return False, 2

    # Aquí se simula el envío (sin conexión real a un servidor SMTP)
    logging.info("Simulación de envío de correo (no se realiza conexión real).")
    return True, 0

def main():
    # Mapas de errores y códigos de estado
    error_messages = {
        0: "Unknown server error.",
        1: "Invalid sender address",
        2: "Invalid recipient address",
        3: "SMTP error."
    }
    status_codes = {
        0: 550,  # Error genérico
        1: 501,
        2: 550,
        3: 503
    }

    # Configuración de argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description="Cliente SMTP simulado con validación de entradas",
        add_help=False
    )
    parser.add_argument("-p", "--port", type=int, required=True, help="Puerto del servidor SMTP")
    parser.add_argument("-u", "--host", type=str, required=True, help="Dirección del servidor SMTP")
    parser.add_argument("-f", "--from_mail", type=str, required=True, help="Dirección del remitente")
    parser.add_argument("-t", "--to_mail", type=str, required=True,
                        help="Destinatarios en formato JSON array", nargs="+")
    parser.add_argument("-s", "--subject", type=str, help="Asunto del correo", nargs="*")
    parser.add_argument("-b", "--body", type=str, help="Cuerpo del mensaje", nargs="*")
    parser.add_argument("-h", "--header", type=str, default="{}",
                        help="Encabezados personalizados en formato JSON", nargs="*")
    parser.add_argument("-P", "--password", type=str, default="", help="Contraseña para autenticación")
    parser.add_argument("--help", action="help", default=argparse.SUPPRESS,
                        help="Mostrar este mensaje de ayuda")
    
    args = parser.parse_args()

    # Procesamiento de encabezados personalizados
    try:
        if args.header:
            custom_headers = json.loads(" ".join(args.header))
            # Validar que los encabezados sean ASCII
            for key, value in custom_headers.items():
                if not all(ord(c) < 128 for c in f"{key}: {value}"):
                    raise ValueError("Encabezados contienen caracteres no ASCII")
        else:
            custom_headers = {}
    except Exception as e:
        print(json.dumps({"status_code": 400, "message": f"Error en encabezados: {str(e)}"}))
        sys.exit(1)

    # Procesamiento de destinatarios (se espera un JSON array)
    try:
        recipients = json.loads(" ".join(args.to_mail))
    except Exception as e:
        print(json.dumps({"status_code": 400, "message": f"Error en destinatarios: {str(e)}"}))
        sys.exit(1)

    # Construcción del asunto y cuerpo del correo
    email_subject = " ".join(args.subject) if args.subject else " "
    email_body = " ".join(args.body) if args.body else " "

    try:
        # Ejecutar la función asíncrona que simula el envío
        result, error_type = asyncio.run(
            send_email(
                args.from_mail,
                args.password,
                recipients,
                email_subject,
                email_body,
                custom_headers,
                args.host,
                args.port
            )
        )

        if result:
            output = {"status_code": 250, "message": "Message accepted for delivery"}
        else:
            output = {
                "status_code": status_codes.get(error_type, 550),
                "message": error_messages.get(error_type, "Unknown error")
            }
    except Exception as e:
        output = {"status_code": 500, "message": f"Excepción: {e}"}

    print(json.dumps(output))

if __name__ == "__main__":
    main()
