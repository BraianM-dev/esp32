# Conversión sencilla de temperatura (No necesita placa).
# Pulsa Ejecutar: funciona con Python del navegador o en la ESP32.
for celsius in (0, 10, 20, 25, 30):
    fahrenheit = celsius * 9 / 5 + 32
    print(celsius, "°C =", fahrenheit, "°F")
