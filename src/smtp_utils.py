import asyncio
import base64
from email.utils import formatdate
import logging
import re
import argparse
import json

# Configuración básica de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constantes y expresiones regulares precompiladas
DEFAULT_SMTP_SERVER = "127.0.0.1"
DEFAULT_SMTP_PORT = 2525
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class SMTPClientError(Exception):
    """Excepción personalizada para errores del cliente SMTP"""
    pass


def validate_email_address(email: str) -> bool:
    """Valida una dirección de email usando expresión regular"""
    return bool(EMAIL_REGEX.match(email))


async def read_server_response(reader: asyncio.StreamReader) -> str:
    """Lee y procesa la respuesta del servidor SMTP"""
    response_data = await reader.read(1024)
    decoded_response = response_data.decode().strip()
    logging.debug(f"Respuesta del servidor: {decoded_response}")
    
    # Verificar código de estado SMTP (2xx o 3xx son exitosos)
    if not decoded_response[:1] in {'2', '3'}:
        raise SMTPClientError(f"Error del servidor: {decoded_response}")
    
    return decoded_response


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
    Envía un correo electrónico usando el protocolo SMTP
    
    Retorna:
        tuple: (envío_exitoso: bool, tipo_error: int)
    """
    email_sent = False
    error_type = 0  # 0: Sin error, 1: Error remitente, 2: Error destinatario
    
    # Validación de direcciones de correo
    if not validate_email_address(sender_address):
        return email_sent, 1
    
    for recipient in recipient_addresses:
        if not validate_email_address(recipient):
            return email_sent, 2

    # Construcción de encabezados del correo
    email_headers = [
        f"From: {sender_address}",
        f"To: {', '.join(recipient_addresses)}",
        f"Subject: {email_subject}",
        f"Date: {formatdate(localtime=True)}"
    ]
    
    # Agregar encabezados personalizados
    for header, value in custom_headers.items():
        email_headers.append(f"{header}: {value}")
    
    # Construir contenido completo del correo
    email_content = "\r\n".join(email_headers) + "\r\n\r\n" + email_body
    writer = None

    try:
        # Establecer conexión con el servidor SMTP
        reader, writer = await asyncio.open_connection(smtp_server, smtp_port)
        await read_server_response(reader)

        # Inicio de sesión SMTP
        writer.write(b"EHLO localhost\r\n")
        await writer.drain()
        await read_server_response(reader)

        # Autenticación PLAIN (si está soportada)
        try:
            writer.write(b"AUTH PLAIN\r\n")
            await writer.drain()
            auth_response = await read_server_response(reader)
            if auth_response.startswith('334'):
                auth_credentials = f"\0{sender_address}\0{sender_password}".encode()
                auth_b64 = base64.b64encode(auth_credentials)
                writer.write(auth_b64 + b"\r\n")
                await writer.drain()
                await read_server_response(reader)
        except SMTPClientError as e:
            if "502" in str(e):
                logging.warning("Autenticación no soportada, continuando sin autenticar")
            else:
                raise

        # Proceso de envío SMTP
        writer.write(f"MAIL FROM:{sender_address}\r\n".encode())
        await writer.drain()
        try:
            await read_server_response(reader)
        except SMTPClientError as e:
            error_type = 1  # Error de remitente
            raise

        for recipient in recipient_addresses:
            writer.write(f"RCPT TO:{recipient}\r\n".encode())
            await writer.drain()
            try:
                await read_server_response(reader)
            except SMTPClientError as e:
                error_type = 2  # Error de destinatario
                raise
            
        # Envío del contenido del correo
        writer.write(b"DATA\r\n")
        await writer.drain()
        await read_server_response(reader)

        writer.write(email_content.encode() + b"\r\n.\r\n")
        await writer.drain()
        await read_server_response(reader)

        # Finalizar conexión
        writer.write(b"QUIT\r\n")
        await writer.drain()
        await read_server_response(reader)

        email_sent = True
        logging.info("Correo electrónico enviado exitosamente")

    except SMTPClientError as e:
        logging.error(f"Error SMTP: {str(e)}")
        if error_type == 0:
            if "501" in str(e):
                error_type = 1
            elif "550" in str(e):
                error_type = 2
    except Exception as e:
        logging.error(f"Error general: {str(e)}")
        error_type = 3  # Nuevo tipo para errores genéricos

    return email_sent, error_type

def main():
    
    error_messages = {
        0: "Error desconocido del servidor",
        1: "Invalid sender address",
        2: "Invalid recipient address",
        3: "Error de protocolo SMTP"
    }

    status_codes = {
        0: 550,  # Error genérico
        1: 501,
        2: 550,
        3: 503
    }

    """Función principal para ejecución desde línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Cliente SMTP con soporte para autenticación PLAIN",
        add_help=False
    )
    
    # Configuración de argumentos de línea de comandos
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
    except Exception as e:
        print(json.dumps({"status_code": 400, "message": f"Error en encabezados: {str(e)}"}))
        exit(1)

    # Procesamiento de destinatarios (se espera un JSON array)
    try:
        recipients = json.loads(" ".join(args.to_mail))
    except Exception as e:
        print(json.dumps({"status_code": 400, "message": f"Error en destinatarios: {str(e)}"}))
        exit(1)

    # Construcción de componentes del correo
    email_subject = " ".join(args.subject) if args.subject else " "
    email_body = " ".join(args.body) if args.body else " "

    try:
        # Ejecutar el cliente SMTP
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

        # Generar respuesta basada en resultados
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