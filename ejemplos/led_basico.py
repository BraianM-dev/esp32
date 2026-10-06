# LED integrado de muchas ESP32-C3 Super Mini: GPIO8, activo en bajo.
# Ajusta pin y polaridad según el esquema de tu placa.
from machine import Pin
import time

LED_PIN = 8
ACTIVO = 0
led = Pin(LED_PIN, Pin.OUT, value=1 - ACTIVO)
try:
    print("Encendiendo LED integrado durante 2 segundos...")
    led.value(ACTIVO)
    time.sleep(2)
finally:
    led.value(1 - ACTIVO)
    print("LED apagado")
