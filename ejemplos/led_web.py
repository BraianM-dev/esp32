# EspWebStudio: servicio
# Panel HTTP pequeño para encender/apagar el LED de una C3 en tu red propia.
# Guarda como main.py para un servicio continuo; Detener interrumpe «Ejecutar».
# HTTP es local y no tiene autenticación: úsalo solo en una LAN de confianza.
import network
import socket
import time
from machine import Pin

SSID = "TU_RED_WIFI"
CLAVE = "TU_CLAVE"
LED_PIN = 8                 # Ajusta según la variante de tu C3 Super Mini.
ACTIVO = 0                 # LED interno frecuente: activo en bajo.

sta = network.WLAN(network.WLAN.IF_STA)
sta.active(True)
if not sta.isconnected():
    sta.connect(SSID, CLAVE)
    limite = time.ticks_add(time.ticks_ms(), 15000)
    while not sta.isconnected() and time.ticks_diff(limite, time.ticks_ms()) > 0:
        time.sleep_ms(250)
if not sta.isconnected():
    raise OSError("No se pudo conectar al Wi-Fi; revisa SSID y clave")

led = Pin(LED_PIN, Pin.OUT, value=1 - ACTIVO)
encendido = False
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 80))
    server.listen(2)
    print("Panel del LED: http://" + sta.ifconfig()[0])
    while True:
        client, _ = server.accept()
        try:
            client.settimeout(3)
            request = client.recv(512)
            first = request.split(b"\r\n", 1)[0].split(b" ")
            if len(first) > 1 and first[0] == b"POST":
                if first[1] == b"/on":
                    encendido = True
                elif first[1] == b"/off":
                    encendido = False
                led.value(ACTIVO if encendido else 1 - ACTIVO)
            html = ("<!doctype html><html lang='es'><meta charset='utf-8'>"
                    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                    "<title>LED ESP32</title><style>body{font:18px system-ui;"
                    "max-width:480px;margin:10vh auto;padding:20px}button{font:inherit;"
                    "padding:12px;margin:8px}</style><h1>LED integrado</h1><p>GPIO" +
                    str(LED_PIN) + " · " + ("Encendido" if encendido else "Apagado") +
                    "</p><form method='post' action='/on'><button>Encender</button></form>"
                    "<form method='post' action='/off'><button>Apagar</button></form></html>")
            body = html.encode()
            header = (b"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n"
                      b"Cache-Control: no-store\r\nConnection: close\r\nContent-Length: " +
                      str(len(body)).encode() + b"\r\n\r\n")
            client.sendall(header + body)
        except OSError as error:
            print("Cliente HTTP:", error)
        finally:
            client.close()
finally:
    server.close()
    led.value(1 - ACTIVO)
