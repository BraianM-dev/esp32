# EspWebStudio: servicio
# Página y API JSON de telemetría local (ADC GPIO0, RSSI y RAM).
# El sensor ADC debe entregar 0–3,3 V. No expongas este puerto a Internet.
import network
import socket
import time
import gc
import json
from machine import Pin, ADC

SSID = "TU_RED_WIFI"
CLAVE = "TU_CLAVE"
SENSOR_PIN = 0
PORT = 8080

sta = network.WLAN(network.WLAN.IF_STA)
sta.active(True)
if not sta.isconnected():
    sta.connect(SSID, CLAVE)
    limite = time.ticks_add(time.ticks_ms(), 15000)
    while not sta.isconnected() and time.ticks_diff(limite, time.ticks_ms()) > 0:
        time.sleep_ms(250)
if not sta.isconnected():
    raise OSError("No se pudo conectar al Wi-Fi")

sensor = ADC(Pin(SENSOR_PIN))
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen(2)
    print("Telemetría: http://%s:%d/" % (sta.ifconfig()[0], PORT))
    while True:
        client, _ = server.accept()
        try:
            client.settimeout(3)
            request = client.recv(512)
            path = request.split(b" ", 2)[1] if b" " in request else b"/"
            gc.collect()
            data = {"adc": sensor.read_u16(), "gpio": SENSOR_PIN,
                    "rssi_dbm": sta.status("rssi") if sta.isconnected() else None,
                    "ram_libre": gc.mem_free()}
            if path == b"/status":
                body = json.dumps(data).encode()
                mime = b"application/json"
            else:
                body = ("<!doctype html><html lang='es'><meta charset='utf-8'>"
                        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                        "<h1>Telemetría ESP32-C3</h1><p>ADC GPIO" + str(SENSOR_PIN) +
                        ": " + str(data["adc"]) + " / 65535</p><p>RSSI: " +
                        str(data["rssi_dbm"]) + " dBm</p><p>RAM libre: " +
                        str(data["ram_libre"]) + " bytes</p>"
                        "<a href='/status'>Ver JSON</a> · Actualiza la página para releer.</html>").encode()
                mime = b"text/html; charset=utf-8"
            header = (b"HTTP/1.1 200 OK\r\nContent-Type: " + mime +
                      b"\r\nCache-Control: no-store\r\nConnection: close\r\n"
                      b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n")
            client.sendall(header + body)
        except (OSError, IndexError) as error:
            print("Cliente HTTP:", error)
        finally:
            client.close()
finally:
    server.close()
