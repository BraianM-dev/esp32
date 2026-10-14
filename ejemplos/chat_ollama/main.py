# ============================================================================
# EspWebStudio: servicio
# EspWebStudio: web-usb
# Estos marcadores permiten ejecutar el servidor sin limite Raw REPL en el IDE.
# CHAT OLLAMA - ESP32-C3 SUPER MINI - MicroPython
# Copiar este archivo y index.html a la raiz de la placa con Thonny.
# El modelo se ejecuta en la PC; el ESP32 sirve la web y comunica con Ollama.
# ============================================================================

# 1. CONFIGURACION: una cadena vacia significa red Wi-Fi abierta.
WIFI_SSID = "Ceibal-2.4GHz"
WIFI_PASSWORD = ""
WIFI_TIMEOUT_SECONDS = 30
AP_SSID = "ESP32-Ollama"
AP_PASSWORD = "ESP32Chat1234"
WEB_PORT = 8080
OLLAMA_DEFAULT_URL = "http://192.168.1.50:11434"

# 2. PERSONALIZACION DEL ASISTENTE: valores iniciales para la pagina.
# Tambien se pueden cambiar desde el navegador, sin editar este archivo.
SYSTEM_PROMPT = "Eres un asistente educativo. Responde en espanol con claridad, explica paso a paso y reconoce cuando no sabes algo."
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
DEFAULT_NUM_CTX = 2048
DEFAULT_MAX_TOKENS = 300
DEFAULT_HISTORY_MESSAGES = 8

# 3. LIMITES: proteger la memoria y evitar conexiones esperando indefinidamente.
MAX_REQUEST_BYTES = 16000
MAX_RESPONSE_BYTES = 32000
HTTP_TIMEOUT_SECONDS = 12
OLLAMA_TIMEOUT_SECONDS = 180
MODELS_TIMEOUT_SECONDS = 20
MAX_CLIENTS = 4

import network
import time
import gc
import sys
try:
    import uselect as select
except ImportError:
    import select
try:
    import ubinascii as binascii
except ImportError:
    import binascii
try:
    import ujson as json
except ImportError:
    import json
try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

# Estado compartido: la web puede responder mientras Ollama esta trabajando.
ESTACION = None
MODO_RED = ""
OLLAMA_OCUPADO = False
CLIENTES = 0
ULTIMO_ERROR = ""
USB_ACTIVO = False
USB_OCUPADO = False
USB_PREFIX = "@EWSUSB:"


def url_web(ip):
    """Incluir el puerto real en todas las direcciones impresas."""
    return "http://%s:%d/" % (ip, WEB_PORT)


async def conectar_wifi_o_iniciar_ap():
    """Intentar la red existente y crear un AP solo si no se obtiene IP."""
    global ESTACION, MODO_RED
    ap = network.WLAN(network.AP_IF)
    ap.active(False)
    ESTACION = network.WLAN(network.STA_IF)
    ESTACION.active(False)
    await asyncio.sleep_ms(300)
    ESTACION.active(True)
    await asyncio.sleep_ms(500)

    # El escaneo permite comprobar nombre, cobertura y seguridad de la red.
    # Seguridad 0 indica una red abierta. El escaneo es una llamada sincrona.
    try:
        print("Redes visibles:")
        for red in ESTACION.scan():
            print(red[0].decode("utf-8", "ignore"),
                  "| senal:", red[3], "| seguridad:", red[4])
    except Exception as error:
        print("No se pudo escanear:", error)

    if WIFI_SSID and WIFI_SSID != "NOMBRE_DE_TU_WIFI":
        try:
            print("Conectando a:", WIFI_SSID)
            if WIFI_PASSWORD:
                ESTACION.connect(WIFI_SSID, WIFI_PASSWORD)
            else:
                # Red abierta: no pasar una contrasena.
                ESTACION.connect(WIFI_SSID)
            comienzo = time.ticks_ms()
            ultimo_estado = None
            while not ESTACION.isconnected():
                estado = ESTACION.status()
                if estado != ultimo_estado:
                    print("Estado Wi-Fi:", estado)
                    ultimo_estado = estado
                if time.ticks_diff(time.ticks_ms(), comienzo) >= WIFI_TIMEOUT_SECONDS * 1000:
                    break
                await asyncio.sleep_ms(300)
        except Exception as error:
            print("Error Wi-Fi:", error)

    if ESTACION.isconnected():
        MODO_RED = "Wi-Fi"
        print("Conectado:", ESTACION.ifconfig())
        print("Abre:", url_web(ESTACION.ifconfig()[0]))
        return

    print("Sin conexion. Estado final:", ESTACION.status())
    ESTACION.active(False)
    ap.active(True)
    try:
        ap.config(essid=AP_SSID, password=AP_PASSWORD, authmode=3)
    except Exception:
        ap.config(essid=AP_SSID, password=AP_PASSWORD)
    MODO_RED = "AP de respaldo"
    print("Red:", AP_SSID, "| Clave:", AP_PASSWORD)
    print("Abre:", url_web(ap.ifconfig()[0]))
    print("El AP no da acceso automatico a la LAN de Ollama.")


def direccion_actual():
    """Consultar la IP actual, incluso despues de una reconexion."""
    interfaz = ESTACION if MODO_RED == "Wi-Fi" else network.WLAN(network.AP_IF)
    return interfaz.ifconfig()[0]


async def cerrar(writer):
    """Cerrar sockets tambien en errores y cancelaciones por tiempo agotado."""
    if writer is not None:
        try:
            writer.close()
            await asyncio.wait_for(writer.wait_closed(), 2)
        except Exception:
            pass


async def leer_linea(reader, limite=2048):
    """Leer una linea HTTP con limite para no llenar la RAM."""
    datos = bytearray()
    while True:
        parte = await reader.read(1)
        if not parte:
            if not datos:
                raise ValueError("Conexion cerrada antes de completar HTTP")
            raise ValueError("Linea HTTP incompleta")
        datos.extend(parte)
        if len(datos) > limite:
            raise ValueError("Linea HTTP demasiado larga")
        if parte == b"\n":
            return bytes(datos)


async def leer_exactos(reader, cantidad):
    """No asumir que una lectura TCP devuelve todos los bytes solicitados."""
    datos = bytearray()
    while len(datos) < cantidad:
        parte = await reader.read(min(1024, cantidad - len(datos)))
        if not parte:
            raise ValueError("Cuerpo HTTP incompleto")
        datos.extend(parte)
    return datos


async def leer_cabeceras(reader):
    primera = (await leer_linea(reader)).decode().strip()
    cabeceras = {}
    total = len(primera)
    while True:
        linea = await leer_linea(reader)
        total += len(linea)
        if total > 4096:
            raise ValueError("Encabezados HTTP demasiado grandes")
        if linea in (b"\r\n", b"\n"):
            return primera, cabeceras
        nombre, valor = linea.decode().split(":", 1)
        cabeceras[nombre.lower().strip()] = valor.strip()


async def leer_solicitud(reader):
    primera, cabeceras = await leer_cabeceras(reader)
    partes = primera.split()
    if len(partes) != 3:
        raise ValueError("Solicitud HTTP invalida")
    largo = int(cabeceras.get("content-length", "0"))
    if largo < 0 or largo > MAX_REQUEST_BYTES:
        raise OverflowError("Mensaje demasiado grande: reduce el historial")
    if "transfer-encoding" in cabeceras:
        raise ValueError("La solicitud debe usar Content-Length")
    cuerpo = await leer_exactos(reader, largo)
    return partes[0], partes[1].split("?", 1)[0], cuerpo


async def responder(writer, codigo, datos):
    """Enviar un JSON al navegador, con estado HTTP y longitud correctos."""
    cuerpo = json.dumps(datos).encode()
    motivos = {200: "OK", 400: "Bad Request", 404: "Not Found",
               413: "Payload Too Large", 502: "Bad Gateway",
               503: "Service Unavailable", 504: "Gateway Timeout"}
    writer.write(("HTTP/1.1 %d %s\r\nContent-Type: application/json; charset=utf-8\r\n"
                  "Content-Length: %d\r\nConnection: close\r\nCache-Control: no-store\r\n\r\n"
                  % (codigo, motivos.get(codigo, "Error"), len(cuerpo))).encode())
    await writer.drain()
    writer.write(cuerpo)
    await writer.drain()


async def servir_html(writer):
    """Enviar la pagina por bloques; no cargar todo el HTML en RAM."""
    import os
    largo = os.stat("index.html")[6]
    writer.write(("HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n"
                  "Content-Length: %d\r\nConnection: close\r\nCache-Control: no-store\r\n\r\n"
                  % largo).encode())
    await writer.drain()
    with open("index.html", "rb") as archivo:
        while True:
            bloque = archivo.read(1024)
            if not bloque:
                break
            writer.write(bloque)
            await writer.drain()


def separar_direccion(direccion):
    """Aceptar IP o http://IP:11434. Usar la IP LAN de la PC, no localhost."""
    direccion = str(direccion or OLLAMA_DEFAULT_URL).strip()
    if "://" not in direccion:
        direccion = "http://" + direccion
    if not direccion.startswith("http://"):
        raise ValueError("Usa http://IP_DE_LA_PC:11434")
    servidor = direccion[7:].split("/", 1)[0]
    if ":" in servidor:
        host, puerto = servidor.rsplit(":", 1)
        puerto = int(puerto)
    else:
        host, puerto = servidor, 11434
    if not host or host in ("localhost", "127.0.0.1") or not 1 <= puerto <= 65535:
        raise ValueError("Introduce la IP LAN de la computadora y un puerto valido")
    return host, puerto


async def peticion_ollama(direccion, ruta, solicitud=None):
    """HTTP asincrono. Aceptar Content-Length, chunked y cierre de conexion."""
    host, puerto = separar_direccion(direccion)
    writer = None
    try:
        reader, writer = await asyncio.open_connection(host, puerto)
        cuerpo = b"" if solicitud is None else json.dumps(solicitud).encode()
        metodo = "GET" if solicitud is None else "POST"
        writer.write(("%s %s HTTP/1.1\r\nHost: %s:%d\r\n"
                      "Content-Type: application/json\r\nContent-Length: %d\r\n"
                      "Connection: close\r\n\r\n"
                      % (metodo, ruta, host, puerto, len(cuerpo))).encode())
        writer.write(cuerpo)
        await writer.drain()
        primera, cabeceras = await leer_cabeceras(reader)
        codigo = int(primera.split()[1])
        respuesta = bytearray()

        # Algunos servidores HTTP envian el JSON en bloques (chunked).
        if "chunked" in cabeceras.get("transfer-encoding", "").lower():
            while True:
                largo = int((await leer_linea(reader)).split(b";", 1)[0].strip(), 16)
                if largo == 0:
                    break
                if largo < 0 or len(respuesta) + largo > MAX_RESPONSE_BYTES:
                    raise ValueError("Respuesta muy grande; reduce los tokens")
                respuesta.extend(await leer_exactos(reader, largo))
                if bytes(await leer_exactos(reader, 2)) != b"\r\n":
                    raise ValueError("Bloque HTTP invalido")
        elif "content-length" in cabeceras:
            largo = int(cabeceras["content-length"])
            if largo < 0 or largo > MAX_RESPONSE_BYTES:
                raise ValueError("Respuesta muy grande; reduce los tokens")
            respuesta = await leer_exactos(reader, largo)
        else:
            while True:
                bloque = await reader.read(1024)
                if not bloque:
                    break
                if len(respuesta) + len(bloque) > MAX_RESPONSE_BYTES:
                    raise ValueError("Respuesta muy grande; reduce los tokens")
                respuesta.extend(bloque)
        if codigo != 200:
            raise RuntimeError("Ollama HTTP %d: %s" % (codigo, bytes(respuesta[:400]).decode("utf-8", "ignore")))
        return json.loads(bytes(respuesta).decode())
    finally:
        await cerrar(writer)


def preparar_chat(datos):
    """Validar mensaje, historial y opciones personalizables del modelo."""
    mensaje = str(datos.get("message", "")).strip()
    modelo = str(datos.get("model", "")).strip()
    if not mensaje or not modelo:
        raise ValueError("Escribe un mensaje y selecciona un modelo")
    if len(mensaje) > 1000:
        raise ValueError("El mensaje admite hasta 1000 caracteres")
    prompt = str(datos.get("system_prompt", SYSTEM_PROMPT))[:1600]
    mensajes = [{"role": "system", "content": prompt}]
    cantidad = max(0, min(12, int(datos.get("history_messages", DEFAULT_HISTORY_MESSAGES))))
    historial = datos.get("history", [])
    if isinstance(historial, list) and cantidad:
        for item in historial[-cantidad:]:
            if isinstance(item, dict) and item.get("role") in ("user", "assistant"):
                mensajes.append({"role": item["role"], "content": str(item.get("content", ""))[:1000]})
    mensajes.append({"role": "user", "content": mensaje})
    return {"model": modelo[:100], "messages": mensajes, "stream": False,
            "options": {
                "temperature": max(0.0, min(2.0, float(datos.get("temperature", DEFAULT_TEMPERATURE)))),
                "top_p": max(0.1, min(1.0, float(datos.get("top_p", DEFAULT_TOP_P)))),
                "num_ctx": max(512, min(8192, int(datos.get("num_ctx", DEFAULT_NUM_CTX)))),
                "num_predict": max(32, min(1024, int(datos.get("max_tokens", DEFAULT_MAX_TOKENS))))}}


async def atender(reader, writer):
    """Una tarea por navegador; permitir consultar estado durante una generacion."""
    global CLIENTES, OLLAMA_OCUPADO, ULTIMO_ERROR
    CLIENTES += 1
    posee_ollama = False
    try:
        if CLIENTES > MAX_CLIENTS:
            await responder(writer, 503, {"error": "Demasiadas conexiones; reintenta"})
            return
        metodo, ruta, cuerpo = await asyncio.wait_for(leer_solicitud(reader), HTTP_TIMEOUT_SECONDS)
        if metodo == "GET" and ruta in ("/", "/index.html"):
            await asyncio.wait_for(servir_html(writer), HTTP_TIMEOUT_SECONDS)
            return
        if metodo == "GET" and ruta == "/api/status":
            await responder(writer, 200, {
                "ip": direccion_actual(), "port": WEB_PORT, "mode": MODO_RED,
                "connected": ESTACION.isconnected() if MODO_RED == "Wi-Fi" else True,
                "busy": OLLAMA_OCUPADO, "free_memory": gc.mem_free(),
                "last_error": ULTIMO_ERROR, "ollama_default_url": OLLAMA_DEFAULT_URL,
                "usb_protocol": 1, "usb_active": USB_ACTIVO,
                "timeout": OLLAMA_TIMEOUT_SECONDS,
                "defaults": {"system_prompt": SYSTEM_PROMPT, "temperature": DEFAULT_TEMPERATURE,
                             "top_p": DEFAULT_TOP_P, "num_ctx": DEFAULT_NUM_CTX,
                             "max_tokens": DEFAULT_MAX_TOKENS, "history_messages": DEFAULT_HISTORY_MESSAGES}})
            return
        if metodo == "POST" and ruta == "/api/prepare":
            # El modo USB utiliza EXACTAMENTE los ajustes y validaciones de
            # esta placa, pero ejecuta Ollama desde la PC del navegador.
            # Esta ruta no conecta a Ollama ni modifica configuracion persistente.
            datos = json.loads(bytes(cuerpo).decode())
            if not isinstance(datos, dict):
                raise ValueError("La solicitud debe contener un objeto JSON")
            await responder(writer, 200, {"request": preparar_chat(datos)})
            return
        if metodo == "POST" and ruta in ("/api/models", "/api/chat"):
            datos = json.loads(bytes(cuerpo).decode())
            if not isinstance(datos, dict):
                raise ValueError("La solicitud debe contener un objeto JSON")
            if OLLAMA_OCUPADO:
                await responder(writer, 503, {"error": "Ollama esta trabajando. Espera a que termine."})
                return
            # Una sola consulta al modelo a la vez para proteger memoria.
            OLLAMA_OCUPADO = True
            posee_ollama = True
            direccion = datos.get("ollama_url", OLLAMA_DEFAULT_URL)
            if ruta == "/api/models":
                resultado = await asyncio.wait_for(peticion_ollama(direccion, "/api/tags"), MODELS_TIMEOUT_SECONDS)
                modelos = [m.get("name", m.get("model", "")) for m in resultado.get("models", [])]
                await responder(writer, 200, {"models": [m for m in modelos if m]})
            else:
                print("Generando con:", datos.get("model"))
                resultado = await asyncio.wait_for(peticion_ollama(direccion, "/api/chat", preparar_chat(datos)), OLLAMA_TIMEOUT_SECONDS)
                texto = resultado.get("message", {}).get("content", "")
                if not texto:
                    texto = "El modelo no devolvio texto. Prueba otro modelo o aumenta los tokens."
                await responder(writer, 200, {"reply": texto})
                print("Respuesta enviada.")
            ULTIMO_ERROR = ""
            return
        await responder(writer, 404, {"error": "Ruta inexistente"})
    except Exception as error:
        # No dejar que el error de una solicitud termine el servidor entero.
        ULTIMO_ERROR = str(error) or type(error).__name__
        codigo = 502
        if isinstance(error, asyncio.TimeoutError):
            codigo = 504
            ULTIMO_ERROR = "Tiempo agotado. Revisa IP, firewall, red y velocidad del modelo."
        elif isinstance(error, OverflowError):
            codigo = 413
        elif isinstance(error, ValueError):
            codigo = 400
        print("Error:", ULTIMO_ERROR)
        try:
            await asyncio.wait_for(responder(writer, codigo, {"error": ULTIMO_ERROR[:500]}), 3)
        except Exception:
            pass
    finally:
        if posee_ollama:
            OLLAMA_OCUPADO = False
        CLIENTES -= 1
        await cerrar(writer)
        gc.collect()


async def supervisar():
    """Mostrar actividad y reintentar Wi-Fi perdido sin reiniciar el servidor."""
    ultima_reconexion = time.ticks_ms()
    contador = 0
    while True:
        await asyncio.sleep(5)
        contador += 1
        if MODO_RED == "Wi-Fi" and not ESTACION.isconnected():
            if time.ticks_diff(time.ticks_ms(), ultima_reconexion) >= 15000:
                ultima_reconexion = time.ticks_ms()
                print("Wi-Fi desconectado. Reintentando...")
                try:
                    ESTACION.disconnect()
                    if WIFI_PASSWORD:
                        ESTACION.connect(WIFI_SSID, WIFI_PASSWORD)
                    else:
                        ESTACION.connect(WIFI_SSID)
                except Exception as error:
                    print("Reconexion:", error)
        if contador % 6 == 0:
            gc.collect()
            print("Servidor activo | Ollama ocupado:", OLLAMA_OCUPADO,
                  "| clientes:", CLIENTES, "| RAM libre:", gc.mem_free())


def usb_emitir(datos):
    """Tramas ASCII: el hexadecimal evita mezclar UTF-8 con el protocolo REPL."""
    print(USB_PREFIX + json.dumps(datos))


class LectorUSB:
    """Adaptar una solicitud USB al mismo lector de solicitudes HTTP."""
    def __init__(self, datos):
        self.datos = datos
        self.posicion = 0

    async def read(self, cantidad):
        parte = self.datos[self.posicion:self.posicion + cantidad]
        self.posicion += len(parte)
        return parte


class EscritorUSB:
    """Enviar la respuesta HTTP por USB en bloques pequenos, sin copiarla entera."""
    def __init__(self, identificador):
        self.identificador = identificador
        self.secuencia = 0

    def write(self, datos):
        # .write solo encola el bloque actual; .drain lo transmite cooperativamente.
        self.pendiente = datos

    async def drain(self):
        datos = getattr(self, "pendiente", b"")
        for posicion in range(0, len(datos), 128):
            usb_emitir({"kind": "data", "id": self.identificador, "seq": self.secuencia,
                        "hex": binascii.hexlify(datos[posicion:posicion + 128]).decode()})
            self.secuencia += 1
            await asyncio.sleep_ms(2)
        self.pendiente = b""

    def close(self):
        usb_emitir({"kind": "end", "id": self.identificador, "seq": self.secuencia})

    async def wait_closed(self):
        pass


async def procesar_usb(identificador, datos):
    global USB_OCUPADO
    try:
        await atender(LectorUSB(datos), EscritorUSB(identificador))
    finally:
        USB_OCUPADO = False
        gc.collect()


async def escuchar_usb():
    """Leer consola sin bloquear Wi-Fi. Nunca abrir un segundo puerto USB.

    El IDE manda fragmentos de 48 bytes y espera un ACK por fragmento: asi no
    desborda el buffer de entrada. Se conserva Ctrl+C para detener el programa.
    Un programa que tambien lee sys.stdin debe integrar su lectura con esta.
    """
    global USB_ACTIVO, USB_OCUPADO
    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)
    USB_ACTIVO = True
    linea = ""
    solicitud = bytearray()
    identificador = None
    secuencia = 0
    ultimo = time.ticks_ms()
    print("Web por USB lista. Pulsa Web por USB en EspWebStudio.")
    while True:
        # Descartar transferencias incompletas sin afectar el servidor Wi-Fi.
        if identificador is not None and time.ticks_diff(time.ticks_ms(), ultimo) > 15000:
            solicitud = bytearray()
            identificador = None
            secuencia = 0
        if poll.poll(0):
            caracter = sys.stdin.read(1)
            if caracter == "\n":
                texto = linea.rstrip("\r")
                linea = ""
                if not texto.startswith(USB_PREFIX):
                    continue
                trama = {}
                try:
                    trama = json.loads(texto[len(USB_PREFIX):])
                    nuevo_id = str(trama.get("id", ""))
                    indice = int(trama.get("seq", -1))
                    if not nuevo_id or len(nuevo_id) > 40 or trama.get("kind") != "request":
                        raise ValueError("Trama USB invalida")
                    if USB_OCUPADO:
                        raise ValueError("USB ocupado; espera la respuesta")
                    if indice == 0:
                        identificador = nuevo_id
                        solicitud = bytearray()
                        secuencia = 0
                    if nuevo_id != identificador or indice != secuencia:
                        raise ValueError("Secuencia USB incorrecta")
                    bloque = binascii.unhexlify(trama.get("hex", ""))
                    if len(bloque) > 48 or len(solicitud) + len(bloque) > MAX_REQUEST_BYTES + 4096:
                        raise ValueError("Solicitud USB demasiado grande")
                    solicitud.extend(bloque)
                    secuencia += 1
                    ultimo = time.ticks_ms()
                    usb_emitir({"kind": "ack", "id": identificador, "seq": indice})
                    if trama.get("last"):
                        USB_OCUPADO = True
                        asyncio.create_task(procesar_usb(identificador, solicitud))
                        solicitud = bytearray()
                        identificador = None
                        secuencia = 0
                except Exception as error:
                    usb_emitir({"kind": "error", "id": str(trama.get("id", "")), "error": str(error)})
                    solicitud = bytearray()
                    identificador = None
                    secuencia = 0
            elif caracter:
                linea += caracter
                if len(linea) > 512:
                    linea = ""
            # Ceder el control sin dormir entre caracteres pendientes.
            await asyncio.sleep_ms(0)
        else:
            await asyncio.sleep_ms(10)


async def principal():
    # Iniciar USB ANTES de esperar Wi-Fi: el acceso USB no depende de su red.
    tarea_usb = asyncio.create_task(escuchar_usb())
    servidor = None
    try:
        try:
            await conectar_wifi_o_iniciar_ap()
            servidor = await asyncio.start_server(atender, "0.0.0.0", WEB_PORT, backlog=2)
            print("Servidor iniciado:", url_web(direccion_actual()))
        except Exception as error:
            print("Wi-Fi/HTTP no disponible; el USB sigue activo:", error)
        print("Esperar solicitudes es normal. Ctrl+C detiene el programa.")
        await supervisar()
    finally:
        tarea_usb.cancel()
        if servidor is not None:
            servidor.close()
            await servidor.wait_closed()


# 4. ARRANQUE: no reiniciar silenciosamente ante una falla real.
# Se imprime el traceback para poder identificar firmware/memoria/puerto.
try:
    asyncio.run(principal())
except KeyboardInterrupt:
    print("Programa detenido desde Thonny o con Ctrl+C.")
except Exception as error:
    sys.print_exception(error)
    print("Revisa el error anterior y reinicia la placa con RESET.")
finally:
    asyncio.new_event_loop()
    gc.collect()
