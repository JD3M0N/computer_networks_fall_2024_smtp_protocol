#!/bin/bash

# Iniciar el servidor
echo "Iniciando el servidor..."
# ./tests/smtp/server &
python src/smtp_server.py &
SERVER_PID=$!

# Esperar un poco para asegurarnos de que el servidor esté completamente iniciado
sleep 2

# Ejecutar las pruebas
echo "Ejecutando las pruebas..."
python ./tests/smtp/tests.py

if [[ $? -ne 0 ]]; then
  echo "SMTP test failed"
  exit 1
fi