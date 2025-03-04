import os, sys
import json

import sys
sys.stdout.reconfigure(encoding='utf-8')

def send_email(from_address, to_addresses, subject, body, headers=None):
    print(f"🚀 Enviando email desde {from_address} a {to_addresses}...")
    headerstr = "-h {}" if headers is None else f" -h {headers}"
    
    command = f"sh run.sh -u localhost -p 2525 -f {from_address} -t {to_addresses} -s {subject} {headerstr} -b {body}"
    print(f"📌 Ejecutando: {command}")

    print("🔄 Ejecutando el comando...")
    response_string = os.popen(command).read()
    print("🔄 Comando ejecutado.")
    print(f"🔍 Respuesta del servidor: '{response_string}'")
    
    try:
        response = json.loads(response_string)
    except json.JSONDecodeError:
        print("❌ Error: La respuesta no es un JSON válido.")
        response = {}

    return response


# Almacena los resultados de las pruebas
results = []

def print_case(case, description):
    print(f"\n👉 \033[1mCase: {case}\033[0m")
    print(f"   📝 {description}")

def evaluate_response(case, expected_status, actual_status, expected_message=None, actual_message=None):
    success = f'{actual_status}' == f'{expected_status}' and (expected_message is None or expected_message in actual_message)
    results.append({
        "case": case,
        "status": "Success" if success else "Failed",
        "expected_status": expected_status,
        "actual_status": actual_status,
        "expected_message": expected_message,
        "actual_message": actual_message
    })
    if success:
        print(f"   ✅ \033[92mSuccess\033[0m")
    else:
        print(f"   ❌ \033[91mFailed\033[0m")

# Caso 1: Envío de correo simple
print_case("Send simple email", "Enviar un correo simple sin encabezados adicionales")
response = send_email(
    from_address="sender@example.com",
    to_addresses='[\\"recipient@example.com\\"]',
    subject="Simple Email",
    body="This is a simple email."
)
evaluate_response("Send simple email", 250, response["status_code"], "Message accepted for delivery", response["message"])

# Caso 2: Envío de correo con encabezados adicionales
print_case("Send email with CC", "Enviar un correo con encabezados adicionales (CC)")
response = send_email(
    from_address="sender@example.com",
    to_addresses='[\\"recipient@example.com\\"]',
    subject="Email with CC",
    body="This email includes a CC header.",
    headers='{\\"CC\\":\\ \\"cc@example.com\\"}'
)
evaluate_response("Send email with CC", 250, response["status_code"], "Message accepted for delivery", response["message"])

# Caso 3: Envío de correo con múltiples destinatarios
print_case("Send email to multiple recipients", "Enviar un correo a múltiples destinatarios")
response = send_email(
    from_address="sender@example.com",
    to_addresses='[\\"recipient1@example.com\\",\\ \\"recipient2@example.com\\"]',
    subject="Multiple Recipients",
    body="This email is sent to multiple recipients."
)
evaluate_response("Send email to multiple recipients", 250, response["status_code"], "Message accepted for delivery", response["message"])

# Caso 4: Envío de correo con mensaje mal formado
print_case("Malformed email body", "Enviar un correo con un cuerpo mal formado")
response = send_email(
    from_address="sender@example.com",
    to_addresses='[\\"recipient@example.com\\"]',
    subject="Malformed Body",
    body=None  # Este caso puede simular un cuerpo mal formado
)
evaluate_response("Malformed email body", 250, response["status_code"], "Message accepted for delivery", response["message"])

# Caso 5: Envío con encabezados vacíos
print_case("Send email with empty headers", "Enviar un correo con encabezados vacíos")
response = send_email(
    from_address="sender@example.com",
    to_addresses='[\\"recipient@example.com\\"]',
    subject="Empty Headers",
    body="This email has empty headers.",
    headers='{}'
)
evaluate_response("Send email with empty headers", 250, response["status_code"], "Message accepted for delivery", response["message"])

print_case("Send email without 'From' address", "Enviar un correo sin la dirección 'From'")
response = send_email(
    from_address=None,  # Sin dirección 'From'
    to_addresses='[\\"recipient@example.com\\"]',
    subject="No From Address",
    body="This email has no 'From' address."
)
evaluate_response("Send email without 'From' address", 501, response["status_code"], "Invalid sender address", response["message"])

print_case("Send email with invalid recipient address", "Enviar un correo con una dirección de destinatario inválida")
response = send_email(
    from_address="sender@example.com",
    to_addresses='[\\"invalidemail@com\\"]',  # Dirección inválida
    subject="Invalid Recipient",
    body="This email has an invalid recipient address."
)
evaluate_response("Send email with invalid recipient address", 550, response["status_code"], "Invalid recipient address", response["message"])

print_case("Send email with empty body", "Enviar un correo con un cuerpo vacío")
response = send_email(
    from_address="sender@example.com",
    to_addresses='[\\"recipient@example.com\\"]',
    subject="Empty Body",
    body=""  # Cuerpo vacío
)
evaluate_response("Send email with empty body", 250, response["status_code"], "Message accepted for delivery", response["message"])

print_case("Send email with empty subject", "Enviar un correo con un asunto vacío")
response = send_email(
    from_address="sender@example.com",
    to_addresses='[\\"recipient@example.com\\"]',
    subject="",  # Asunto vacío
    body="This email has no subject."
)
evaluate_response("Send email with empty subject", 250, response["status_code"], "Message accepted for delivery", response["message"])

# Resumen de los resultados
print("\n🎉 \033[1mTest Summary\033[0m 🎉")
total_cases = len(results)
success_cases = sum(1 for result in results if result["status"] == "Success")
failed_cases = total_cases - success_cases

print(f"   ✅ Successful cases: {success_cases}/{total_cases}")

if failed_cases > 0:
    print(f"   ❌ Failed cases: {failed_cases}/{total_cases}")
    print("\n📋 \033[1mFailed Cases Details:\033[0m")
    for result in results:
        if result["status"] == "Failed":
            print(f"   ❌ {result['case']}")
            print(f"      - Expected status: {result['expected_status']}, Actual status: {result['actual_status']}")
            if result['expected_message'] and result['actual_message']:
                print(f"      - Expected message: {result['expected_message']}")
                print(f"      - Actual message: {result['actual_message']}\n")
    sys.exit(1)
