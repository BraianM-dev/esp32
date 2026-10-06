# Control IoT entre dos ESP32 en una red Wi-Fi propia.
# Esta segunda placa envía un clic HTTP a la lámpara al pulsar GPIO4.
# Requiere la lámpara del ejemplo «Lámpara Wi-Fi» encendida en la misma LAN.
import network
import socket
import time
from machine import Pin

SSID = "TU_RED_WIFI"
CLAVE = "TU_CLAVE"
LAMP_IP = "192.168.1.50"    # Cambia por la IP mostrada en el portal.
TOKEN = "PEGA_AQUI_TOKEN"    # Copia el token mostrado por la lámpara en su USB/AP.
BUTTON_PIN = 4             # Botón entre GPIO4 y GND; pull-up interno.

sta = network.WLAN(network.WLAN.IF_STA)
sta.active(True)
if not sta.isconnected():
    sta.connect(SSID, CLAVE)
    limite = time.ticks_add(time.ticks_ms(), 15000)
    while not sta.isconnected() and time.ticks_diff(limite, time.ticks_ms()) > 0:
        time.sleep_ms(250)
if not sta.isconnected():
    raise OSError("No se conectó a la red local")
if len(TOKEN) != 32 or any(c not in "0123456789abcdef" for c in TOKEN):
    raise ValueError("Configura TOKEN con los 32 caracteres hexadecimales de la lámpara")

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
print("Pulsa el botón conectado a GPIO", BUTTON_PIN)
for intento in range(20):  # Prueba acotada; para servicio continuo cambia por while True.
    if button.value() == 0:
        time.sleep_ms(30)   # Antirrebote.
        if button.value() == 0:
            client = socket.socket()
            try:
                client.settimeout(3)
                client.connect((LAMP_IP, 80))
                body = b"id=0"
                request = (b"POST /toggle HTTP/1.1\r\nHost: " + LAMP_IP.encode() +
                           b"\r\nContent-Type: application/x-www-form-urlencoded\r\n"
                           b"X-Control-Token: " + TOKEN.encode() + b"\r\n"
                           b"Content-Length: 4\r\nConnection: close\r\n\r\n" + body)
                client.sendall(request)
                print("Respuesta lámpara:", client.recv(64).split(b"\r\n", 1)[0])
            except OSError as error:
                print("No se pudo contactar la lámpara:", error)
            finally:
                client.close()
            while button.value() == 0:
                time.sleep_ms(30)
    time.sleep_ms(200)
