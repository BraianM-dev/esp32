# EspWebStudio: servicio
# Lámpara Wi-Fi para ESP32-C3 Super Mini con MicroPython.
# Uso: guarda como main.py para que arranque sola. «Ejecutar» la mantiene
# activa hasta pulsar Detener. Requiere una placa real y una red propia.
# AP local -> escaneo y formulario -> STA -> AP apagado -> panel en la LAN.
# HTTP no cifra las credenciales ni el token: usa solo una red propia confiable.
import network
import socket
import select
import time
import json
import os
from machine import Pin

AP_SSID = "C3-Lampara"
AP_KEY = "Configura123"        # Cambia esta clave WPA2 (mínimo 8 caracteres).
LED_PIN = 8                  # Muchas C3 Super Mini usan LED activo en bajo.
ACTIVE_LEVEL = 0             # Invierte a 1 si tu LED es activo en alto.
CONFIG_FILE = "iot_lampara.json"
GPIO_SEGUROS = (0, 1, 3, 4, 5, 6, 7, 8, 10)


def escape(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))


def decode_part(value):
    value = value.replace(b"+", b" ")
    out = bytearray()
    i = 0
    while i < len(value):
        if value[i] == 37 and i + 2 < len(value):
            try:
                out.append(int(value[i + 1:i + 3], 16))
                i += 3
                continue
            except ValueError:
                pass
        out.append(value[i])
        i += 1
    return out.decode("utf-8", "replace")


def form_data(body):
    result = {}
    for part in body.split(b"&"):
        if b"=" in part:
            key, value = part.split(b"=", 1)
            result[decode_part(key)] = decode_part(value)
    return result


def defaults():
    return {"wifi_ssid": "", "wifi_key": "", "token": "", "salidas": [
        {"nombre": "LED integrado", "pin": LED_PIN, "activo": ACTIVE_LEVEL},
        {"nombre": "Salida auxiliar", "pin": 5 if LED_PIN == 4 else 4, "activo": 1}]}


def load_config():
    cfg = defaults()
    try:
        with open(CONFIG_FILE) as file:
            saved = json.load(file)
        if isinstance(saved, dict):
            cfg["wifi_ssid"] = str(saved.get("wifi_ssid", ""))[:32]
            cfg["wifi_key"] = str(saved.get("wifi_key", ""))[:63]
            token = str(saved.get("token", ""))
            if len(token) == 32 and all(c in "0123456789abcdef" for c in token):
                cfg["token"] = token
            outputs = saved.get("salidas")
            if isinstance(outputs, list) and len(outputs) == 2:
                pins = [int(item["pin"]) for item in outputs]
                if (len(set(pins)) == 2 and all(p in GPIO_SEGUROS for p in pins)
                        and all(int(item["activo"]) in (0, 1) for item in outputs)):
                    cfg["salidas"] = [{"nombre": str(item["nombre"])[:24],
                        "pin": pins[i], "activo": int(item["activo"])}
                        for i, item in enumerate(outputs)]
    except (OSError, ValueError, TypeError, KeyError):
        pass
    return cfg


def save_config(cfg):
    # Solo se escribe al configurar; nunca en cada clic de encendido.
    with open(CONFIG_FILE, "w") as file:
        json.dump(cfg, file)


def access_token(cfg):
    # Se conserva al reiniciar. Trátalo como una contraseña: HTTP no lo cifra.
    if not cfg["token"]:
        cfg["token"] = "".join("%02x" % b for b in os.urandom(16))
        save_config(cfg)
    return cfg["token"]


def authorized(headers, token):
    # API para otra placa: cabecera; navegador: cookie HttpOnly/SameSite.
    cookies = headers.get("cookie", "").split(";")
    return (headers.get("x-control-token", "") == token or
            "auth=" + token in [part.strip() for part in cookies])


def login_page(error=""):
    return layout("Acceso a lámpara", ("<p role='alert'>" + escape(error) + "</p>" if error else "") +
                  "<form method='post' action='/login'><label>Token de control "
                  "<input name='token' type='password' maxlength='32' required></label>"
                  "<button>Entrar</button></form><small>El token aparece en el "
                  "terminal USB y en la confirmación inicial del AP. HTTP local "
                  "no cifra el token. No abras este servicio a Internet.</small>")


def setup_pins(cfg, previous=()):
    for output in previous:
        output["io"].value(1 - output["activo"])
    outputs = []
    for item in cfg["salidas"]:
        level = item["activo"]
        io = Pin(item["pin"], Pin.OUT, value=1 - level)
        outputs.append({"io": io, "nombre": item["nombre"], "pin": item["pin"],
                        "activo": level, "encendido": False})
    return outputs


def connect_sta(sta, ssid, key):
    sta.active(True)
    if sta.isconnected():
        sta.disconnect()
    try:
        sta.connect(ssid, key)
    except OSError as exc:
        print("Conexión STA:", exc)
        return None
    deadline = time.ticks_add(time.ticks_ms(), 15000)
    while not sta.isconnected() and time.ticks_diff(deadline, time.ticks_ms()) > 0:
        if sta.status() in (-1, -2, -3):
            break  # fallo, AP no encontrado o contraseña incorrecta
        time.sleep_ms(250)
    if sta.isconnected():
        return sta.ifconfig()[0]
    sta.disconnect()
    return None


def layout(title, body):
    style = ("body{font:16px system-ui;max-width:680px;margin:24px auto;padding:18px;"
             "background:#eef3f8;color:#17263b}main{background:white;padding:22px;"
             "border-radius:14px}input,select,button{font:inherit;padding:9px;margin:4px}"
             "button{background:#205bb0;color:white;border:0;border-radius:6px}"
             "fieldset{margin:12px 0}small{color:#52627b}")
    return ("<!doctype html><html lang='es'><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>" + escape(title) + "</title><style>" + style + "</style>"
            "<main><h1>" + escape(title) + "</h1>" + body + "</main></html>")


def portal_page(sta, ap_ip, error=""):
    options = []
    try:
        seen = set()
        for ssid, _, channel, rssi, _, _ in sorted(sta.scan(), key=lambda row: -row[3]):
            name = ssid.decode("utf-8", "replace")
            if name and name not in seen:
                seen.add(name)
                options.append("<option value='" + escape(name) + "'>" +
                               escape(name) + " (" + str(rssi) + " dBm, canal " +
                               str(channel) + ")</option>")
    except OSError as exc:
        error = "No se pudo escanear: " + str(exc) + ". Escribe el SSID manualmente."
    body = ("<p>1. Conéctate al AP <b>" + escape(AP_SSID) + "</b> con la clave "
            "que configuraste en el programa. 2. Elige tu Wi-Fi de 2,4 GHz. "
            "3. Escribe la clave y pulsa Conectar. 4. Vuelve a tu red y abre "
            "la IP que aparecerá en la confirmación.</p>"
            + ("<p role='alert'>" + escape(error) + "</p>" if error else "") +
            "<form method='post' action='/wifi'><label>Red detectada "
            "<select name='ssid'><option value=''>Elegir...</option>" +
            "".join(options) + "</select></label><br>"
            "<label>SSID manual (si está oculta) <input name='ssid_manual' maxlength='32'></label><br>"
            "<label>Clave Wi-Fi <input name='key' type='password' maxlength='63'></label><br>"
            "<label><input type='checkbox' name='remember' value='1'>Recordar en esta placa</label><br>"
            "<button>Conectar a la red</button></form>"
            "<small>Si no aparece el portal, visita http://" + escape(ap_ip) +
            ". El formulario usa HTTP local: la clave guardada queda en texto "
            "legible en iot_lampara.json. No configures en una red ajena.</small>")
    return layout("Configurar lámpara Wi-Fi", body)


def panel_page(sta, outputs):
    ip = sta.ifconfig()[0]
    rows = []
    for index, output in enumerate(outputs):
        rows.append("<fieldset><legend>" + escape(output["nombre"]) + "</legend>"
                    "<p>GPIO" + str(output["pin"]) + " · " +
                    ("Encendido" if output["encendido"] else "Apagado") + "</p>"
                    "<form method='post' action='/toggle'><input type='hidden' "
                    "name='id' value='" + str(index) + "'><button>" +
                    ("Apagar" if output["encendido"] else "Encender") +
                    "</button></form></fieldset>")
    config = []
    for i, output in enumerate(outputs):
        config.append("<fieldset><legend>Botón " + str(i + 1) + "</legend>"
                      "<label>Nombre <input name='name" + str(i) + "' maxlength='24' value='" +
                      escape(output["nombre"]) + "'></label>"
                      "<label>GPIO <select name='pin" + str(i) + "'>" +
                      "".join("<option value='" + str(pin) + "'" +
                              (" selected" if pin == output["pin"] else "") +
                              ">GPIO" + str(pin) + "</option>" for pin in GPIO_SEGUROS) +
                      "</select></label>"
                      "<label>Activo en <select name='active" + str(i) + "'>" +
                      "".join("<option value='" + str(level) + "'" +
                              (" selected" if level == output["activo"] else "") +
                              ">" + str(level) + "</option>" for level in (0, 1)) +
                      "</select></label></fieldset>")
    body = ("<p>La placa está en tu red local. IP: <b>" + escape(ip) +
            "</b> · RSSI: " + str(sta.status("rssi")) + " dBm</p>" +
            "".join(rows) +
            "<h2>Pruebas rápidas</h2><form method='post' action='/blink'>"
            "<button>Parpadear LED 3 veces</button></form>"
            "<form method='post' action='/alloff'><button>Apagar todas</button></form>"
            "<details><summary>Editar botones y GPIO</summary>"
            "<form method='post' action='/config'>" + "".join(config) +
            "<button>Guardar configuración</button></form></details>"
            "<p>Ejemplos: controla el LED integrado; conecta un LED externo con "
            "resistencia a GPIO4; consulta <a href='/status'>/status</a> como JSON "
            "para un panel IoT local.</p>"
            "<form method='post' action='/forget'><button>Olvidar Wi-Fi guardada</button></form>"
            "<p><a href='/logout'>Salir del panel</a></p>"
            "<small>Panel HTTP solo para red local de confianza. No expongas "
            "el puerto 80 a Internet ni conectes cargas de red directamente al GPIO.</small>")
    return layout("Lámpara ESP32-C3", body)


def reply(client, status, body, mime="text/html; charset=utf-8", location=None, cookie=None):
    payload = body.encode("utf-8") if isinstance(body, str) else body
    headers = ("HTTP/1.1 " + status + "\r\nContent-Type: " + mime +
               "\r\nContent-Length: " + str(len(payload)) +
               "\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\n"
               "Connection: close\r\n")
    if location:
        headers += "Location: " + location + "\r\n"
    if cookie:
        headers += "Set-Cookie: " + cookie + "\r\n"
    client.sendall(headers.encode() + b"\r\n" + payload)


def read_request(client):
    raw = b""
    while b"\r\n\r\n" not in raw and len(raw) < 2048:
        chunk = client.recv(512)
        if not chunk:
            break
        raw += chunk
    if b"\r\n\r\n" not in raw:
        raise ValueError("Cabecera incompleta")
    head, body = raw.split(b"\r\n\r\n", 1)
    parts = head.split(b"\r\n", 1)[0].split(b" ")
    if len(parts) < 2:
        raise ValueError("Solicitud inválida")
    method, path = parts[:2]
    length = 0
    headers = {}
    for line in head.split(b"\r\n")[1:]:
        if b":" in line:
            key, value = line.split(b":", 1)
            key = key.decode("ascii", "ignore").strip().lower()
            headers[key] = value.decode("ascii", "ignore").strip()
    if "content-length" in headers:
        length = int(headers["content-length"])
    if length < 0 or length > 768:
        raise ValueError("Formulario demasiado grande")
    while len(body) < length:
        chunk = client.recv(min(512, length - len(body)))
        if not chunk:
            raise ValueError("Formulario incompleto")
        body += chunk
    return method, path.split(b"?", 1)[0], form_data(body[:length]), headers


def dns_answer(dns, ip):
    packet, address = dns.recvfrom(512)
    if len(packet) < 17:
        return
    position = 12
    while position < len(packet) and 0 < packet[position] < 64:
        position += packet[position] + 1
    if position + 5 > len(packet) or packet[position] != 0:
        return
    qtype = (packet[position + 1] << 8) | packet[position + 2]
    question = packet[12:position + 5]
    answer = (packet[:2] + b"\x81\x80\x00\x01" +
              (b"\x00\x01" if qtype == 1 else b"\x00\x00") +
              b"\x00\x00\x00\x00" + question)
    if qtype == 1:
        answer += (b"\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x1e\x00\x04" +
                   bytes([int(part) for part in ip.split(".")]))
    dns.sendto(answer, address)


def main():
    cfg = load_config()
    token = access_token(cfg)
    print("Token de control (guárdalo en privado):", token)
    outputs = setup_pins(cfg)
    sta = network.WLAN(network.WLAN.IF_STA)
    ap = network.WLAN(network.WLAN.IF_AP)
    ap.active(True)
    ap.config(ssid=AP_SSID, key=AP_KEY)
    ap_ip = "192.168.4.1"
    ap.ifconfig((ap_ip, "255.255.255.0", ap_ip, ap_ip))
    sta.active(True)
    print("AP:", AP_SSID, "| abre http://" + ap_ip)
    handoff = None
    if cfg["wifi_ssid"]:
        ip = connect_sta(sta, cfg["wifi_ssid"], cfg["wifi_key"])
        if ip:
            print("Red recordada conectada. Panel: http://" + ip)
            handoff = time.ticks_add(time.ticks_ms(), 1500)
        else:
            print("Red recordada no disponible: configura desde el AP.")

    web = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dns = None
    try:
        web.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        web.bind(("0.0.0.0", 80))
        web.listen(3)
        poll = select.poll()
        poll.register(web, select.POLLIN)
        try:
            dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            dns.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            dns.bind(("0.0.0.0", 53))
            poll.register(dns, select.POLLIN)
        except OSError as exc:
            if dns:
                dns.close()
            dns = None
            print("DNS opcional no disponible:", exc, "| usa http://" + ap_ip)

        while True:
            if ap.active() and sta.isconnected() and handoff is None:
                handoff = time.ticks_add(time.ticks_ms(), 1500)
            if handoff and time.ticks_diff(time.ticks_ms(), handoff) >= 0:
                if dns:
                    poll.unregister(dns)
                    dns.close()
                    dns = None
                ap.active(False)
                handoff = None
                print("AP apagado. Panel LAN: http://" + sta.ifconfig()[0])
            for channel, event in poll.poll(200):
                if channel == dns:
                    try:
                        dns_answer(dns, ap_ip)
                    except (OSError, ValueError):
                        pass
                    continue
                if channel != web:
                    continue
                client, _ = web.accept()
                try:
                    client.settimeout(3)
                    method, path, form, headers = read_request(client)
                    if ap.active() and not sta.isconnected():
                        if method == b"POST" and path == b"/wifi":
                            ssid = form.get("ssid_manual", "").strip() or form.get("ssid", "")
                            key = form.get("key", "")
                            if not 1 <= len(ssid.encode()) <= 32 or (key and not 8 <= len(key) <= 63):
                                page = portal_page(sta, ap_ip, "SSID o clave inválidos.")
                                reply(client, "400 Bad Request", page)
                            else:
                                ip = connect_sta(sta, ssid, key)
                                if not ip:
                                    reply(client, "200 OK", portal_page(sta, ap_ip,
                                          "No se pudo conectar. Comprueba la clave y la red de 2,4 GHz."))
                                else:
                                    cfg["wifi_ssid"] = ssid if form.get("remember") == "1" else ""
                                    cfg["wifi_key"] = key if cfg["wifi_ssid"] else ""
                                    try:
                                        save_config(cfg)
                                    except OSError as exc:
                                        print("No se pudo guardar la preferencia:", exc)
                                    page = layout("Conectado", "<p>IP en tu red: <b>" + escape(ip) +
                                        "</b>. Reconecta tu teléfono/PC a esa red y abre "
                                        "<a href='http://" + escape(ip) + "'>http://" + escape(ip) +
                                        "</a>. El AP se apagará en unos segundos.</p>"
                                        "<p>Token de control: <code>" + token + "</code>. "
                                        "Anótalo para entrar al panel y configurar el control remoto.</p>")
                                    reply(client, "200 OK", page)
                                    print("Conectado a", ssid, "| panel http://" + ip)
                                    handoff = time.ticks_add(time.ticks_ms(), 1500)
                        else:
                            reply(client, "200 OK", portal_page(sta, ap_ip))
                    elif not sta.isconnected():
                        # Si cayó la red, vuelve a ofrecer la configuración AP.
                        ap.active(True)
                        reply(client, "200 OK", portal_page(sta, ap_ip))
                    elif method == b"GET" and path == b"/logout":
                        reply(client, "303 See Other", b"", location="/",
                              cookie="auth=; Max-Age=0; HttpOnly; SameSite=Strict; Path=/")
                    elif method == b"POST" and path == b"/login":
                        if form.get("token") == token:
                            reply(client, "303 See Other", b"", location="/",
                                  cookie="auth=" + token + "; HttpOnly; SameSite=Strict; Path=/")
                        else:
                            reply(client, "403 Forbidden", login_page("Token incorrecto."))
                    elif not authorized(headers, token):
                        if path == b"/status" or method == b"POST":
                            reply(client, "401 Unauthorized", json.dumps({"error": "token requerido"}),
                                  "application/json")
                        else:
                            reply(client, "200 OK", login_page())
                    elif method == b"GET" and path == b"/status":
                        status = {"ip": sta.ifconfig()[0], "rssi": sta.status("rssi"),
                                  "salidas": [{"nombre": o["nombre"], "pin": o["pin"],
                                              "encendido": o["encendido"]} for o in outputs]}
                        reply(client, "200 OK", json.dumps(status), "application/json")
                    elif method == b"POST" and path == b"/toggle":
                        try:
                            index = int(form.get("id", "-1"))
                            if index < 0 or index >= len(outputs):
                                raise ValueError("Índice inválido")
                            output = outputs[index]
                            output["encendido"] = not output["encendido"]
                            output["io"].value(output["activo"] if output["encendido"]
                                               else 1 - output["activo"])
                            reply(client, "303 See Other", b"", location="/")
                        except ValueError:
                            reply(client, "400 Bad Request", layout("Error", "Botón inválido"))
                    elif method == b"POST" and path == b"/blink":
                        output = outputs[0]
                        previous = output["encendido"]
                        for _ in range(3):
                            output["io"].value(output["activo"])
                            time.sleep_ms(180)
                            output["io"].value(1 - output["activo"])
                            time.sleep_ms(180)
                        output["io"].value(output["activo"] if previous
                                           else 1 - output["activo"])
                        reply(client, "303 See Other", b"", location="/")
                    elif method == b"POST" and path == b"/alloff":
                        for output in outputs:
                            output["encendido"] = False
                            output["io"].value(1 - output["activo"])
                        reply(client, "303 See Other", b"", location="/")
                    elif method == b"POST" and path == b"/config":
                        try:
                            new = []
                            for i in range(2):
                                name = form.get("name" + str(i), "").strip()[:24]
                                pin = int(form.get("pin" + str(i), "-1"))
                                level = int(form.get("active" + str(i), "-1"))
                                if not name or pin not in GPIO_SEGUROS or level not in (0, 1):
                                    raise ValueError("Nombre, GPIO o polaridad inválidos")
                                new.append({"nombre": name, "pin": pin, "activo": level})
                            if new[0]["pin"] == new[1]["pin"]:
                                raise ValueError("Cada botón necesita un GPIO diferente")
                            cfg["salidas"] = new
                            outputs = setup_pins(cfg, outputs)
                            save_config(cfg)
                            reply(client, "303 See Other", b"", location="/")
                        except (ValueError, OSError) as exc:
                            reply(client, "400 Bad Request", layout("Error", "<p>" +
                                  escape(exc) + "</p><a href='/'>Volver</a>"))
                    elif method == b"POST" and path == b"/forget":
                        cfg["wifi_ssid"] = cfg["wifi_key"] = ""
                        try:
                            save_config(cfg)
                        except OSError as exc:
                            print("No se pudo guardar:", exc)
                        reply(client, "303 See Other", b"", location="/")
                    else:
                        reply(client, "200 OK", panel_page(sta, outputs))
                except (OSError, ValueError) as exc:
                    print("Solicitud HTTP:", exc)
                    try:
                        reply(client, "400 Bad Request", layout("Error", "Solicitud inválida"))
                    except OSError:
                        pass
                finally:
                    client.close()
            if not sta.isconnected() and not ap.active():
                ap.active(True)
                ap.ifconfig((ap_ip, "255.255.255.0", ap_ip, ap_ip))
                try:
                    dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    dns.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    dns.bind(("0.0.0.0", 53))
                    poll.register(dns, select.POLLIN)
                except OSError as exc:
                    if dns:
                        dns.close()
                    dns = None
                    print("DNS opcional no disponible:", exc)
                print("Wi-Fi perdido. AP recuperado: http://" + ap_ip)
    finally:
        web.close()
        if dns:
            dns.close()
        ap.active(False)
        for output in outputs:
            output["io"].value(1 - output["activo"])


main()
