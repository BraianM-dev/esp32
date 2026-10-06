"""Regression checks for the single-file distribution; run with Python 3."""
import ast
import asyncio
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
EXAMPLES = dict(re.findall(
    r'<script type="text/x-micropython" id="example-([^"]+)">\n(.*?)\n</script>',
    HTML, re.S))


class ReleaseTests(unittest.TestCase):
    def test_javascript_and_embedded_python(self):
        scripts = re.findall(r"<script([^>]*)>(.*?)</script>", HTML, re.S)
        js = [body for attrs, body in scripts if not attrs.strip() and body.strip()]
        self.assertEqual(len(js), 1)
        with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as file:
            file.write(js[0])
            file.flush()
            subprocess.run(["node", "--check", file.name], check=True)
        self.assertEqual(len(EXAMPLES), 18)
        for name, code in EXAMPLES.items():
            with self.subTest(example=name):
                ast.parse(code, filename=name + ".py")

    def test_catalogue_and_exported_examples(self):
        catalogue = HTML.split("const EXAMPLES =", 1)[1].split("const ", 1)[0]
        ids = set(re.findall(r"\{ id:'([^']+)'", catalogue))
        self.assertEqual(len(ids), 18)
        guides = HTML.split("const EXAMPLE_GUIDES = {", 1)[1].split("\n};", 1)[0]
        visual_ids = set(re.findall(r"^  (?:'([^']+)'|([\w-]+)):\{", guides, re.M))
        self.assertEqual(len(ids) + len(visual_ids) - 3, 46)
        blocks = HTML.split("const definitions=[", 1)[1].split("definitions.forEach", 1)[0]
        self.assertEqual(len(re.findall(r"\b(?:statement|output|body)\('mp_", blocks)) +
                         int("B.Blocks.mp_python_raw" in HTML), 71)
        presets = HTML.split("const BLOCK_PRESETS = {", 1)[1].split("\n};", 1)[0]
        self.assertEqual(len(re.findall(r"^  (?:'[^']+'|[\w-]+):\[", presets, re.M)), 49)
        for path in (ROOT / "ejemplos").glob("*.py"):
            match = re.search(r"id:'([^']+)',name:'" + re.escape(path.name) + "'", HTML)
            self.assertIsNotNone(match, path.name)
            self.assertEqual(path.read_text(encoding="utf-8").strip(), EXAMPLES[match[1]].strip())

    def test_chatbot_and_dungeon_master_without_board(self):
        scripted = {
            "chatbot": (["clima", "nombre", "saludo", "edad", "chau"],
                        ["no es un pronóstico real", "ChatBot 9000", "¡Hola!", "no tengo edad", "Adiós"]),
            "dungeon-master": (["Ana", "1", "1", "2", "2"],
                               ["Ana el Mago", "dado d20: 15", "dado d20: 8", "dado d20: 1",
                                "Vida: 8 | Puntos: 7"]),
        }
        # Run the same top-level-await shape sent to Pyodide with a fake JS bridge.
        js_module = types.ModuleType("js")
        old_js = sys.modules.get("js")
        sys.modules["js"] = js_module
        try:
            for name, (answers, expected) in scripted.items():
                with self.subTest(example=name):
                    queued = iter(answers)
                    async def ask(_prompt):
                        return next(queued)
                    js_module.ewsAsk = ask
                    transform = r"""
const vm=require('node:vm'),fs=require('node:fs');
const html=fs.readFileSync(process.argv[1],'utf8');
function section(a,b) {return html.slice(html.indexOf(a),html.indexOf(b,html.indexOf(a)));}
const context=vm.createContext({});
vm.runInContext(section('function pythonWithoutLiterals(', 'const BOARD_MODULES')+
                section('function localInteractiveCode(', 'function runLocalPython('),context);
process.stdout.write(vm.runInContext('localInteractiveCode('+JSON.stringify(fs.readFileSync(0,'utf8'))+
                                     ').code',context));
"""
                    converted = subprocess.run(["node", "-e", transform, str(ROOT / "index.html")],
                                               input=EXAMPLES[name], text=True, capture_output=True,
                                               check=True).stdout
                    local_code = ("from js import ewsAsk\nasync def __ews_input(prompt=''):\n"
                                  "    return await ewsAsk(prompt)\n" + converted)
                    compiled = compile(local_code, name + "_local.py", "exec",
                                       flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
                    out = io.StringIO()
                    with patch("random.getrandbits", side_effect=[14, 7, 0]), \
                         contextlib.redirect_stdout(out):
                        asyncio.run(eval(compiled, {}))
                    for phrase in expected:
                        self.assertIn(phrase, out.getvalue())
        finally:
            if old_js is None:
                sys.modules.pop("js", None)
            else:
                sys.modules["js"] = old_js
        out = io.StringIO()
        with patch("builtins.input", side_effect=["NOMBRE", "Clima", "saludo", "edad", "chau"]), \
             contextlib.redirect_stdout(out):
            exec(compile(EXAMPLES["chatbot"], "mi_primer_chatbot.py", "exec"), {})
        for expected in ("ChatBot 9000", "no es un pronóstico real", "¡Hola!", "no tengo edad", "Adiós"):
            self.assertIn(expected, out.getvalue())

        out = io.StringIO()
        with patch("builtins.input", side_effect=["Ana", "1", "1", "2", "2"]), \
             patch("random.getrandbits", side_effect=[14, 7, 0]), \
             contextlib.redirect_stdout(out):
            exec(compile(EXAMPLES["dungeon-master"], "dungeon_master.py", "exec"), {})
        text = out.getvalue()
        for expected in ("Ana el Mago", "dado d20: 15", "dado d20: 8", "dado d20: 1",
                         "Vida: 8 | Puntos: 7"):
            self.assertIn(expected, text)

    def test_iot_token_helpers(self):
        source = EXAMPLES["iot-lamp"].rsplit("\nmain()", 1)[0]
        modules = {name: types.ModuleType(name) for name in ("network", "select", "machine")}
        modules["machine"].Pin = object
        prior = {name: sys.modules.get(name) for name in modules}
        sys.modules.update(modules)
        try:
            namespace = {}
            exec(compile(source, "lampara_wifi.py", "exec"), namespace)
            with tempfile.TemporaryDirectory() as tmp:
                cwd = os.getcwd()
                try:
                    os.chdir(tmp)
                    config = namespace["load_config"]()
                    token = namespace["access_token"](config)
                    self.assertRegex(token, r"^[0-9a-f]{32}$")
                    self.assertEqual(namespace["load_config"]()["token"], token)
                    self.assertFalse(namespace["authorized"]({}, token))
                    self.assertFalse(namespace["authorized"]({"x-control-token": "bad"}, token))
                    self.assertTrue(namespace["authorized"]({"x-control-token": token}, token))
                    self.assertTrue(namespace["authorized"]({"cookie": "x=1; auth=" + token}, token))
                    self.assertFalse(namespace["authorized"]({"cookie": "auth=" + token + "extra"}, token))
                    self.assertEqual(json.loads(Path("iot_lampara.json").read_text())["token"], token)
                finally:
                    os.chdir(cwd)
            self.assertIn('elif not authorized(headers, token):', source)
            self.assertLess(source.index('elif not authorized(headers, token):'),
                            source.index('elif method == b"GET" and path == b"/status":'))
            self.assertIn('b"X-Control-Token: " + TOKEN.encode()', EXAMPLES["iot-remote"])
        finally:
            for name, module in prior.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

    def test_lamp_ap_to_lan_and_token_routing(self):
        """Exercise the actual lamp main loop with fake radios, sockets and pins."""
        source = EXAMPLES["iot-lamp"].rsplit("\nmain()", 1)[0]
        modules = {name: types.ModuleType(name) for name in ("network", "select", "machine")}
        modules["machine"].Pin = object
        prior = {name: sys.modules.get(name) for name in modules}
        sys.modules.update(modules)
        try:
            env = {}
            exec(compile(source, "lampara_wifi.py", "exec"), env)
        finally:
            for name, module in prior.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

        class Radio:
            def __init__(self, ap=False):
                self.on = False
                self.ap = ap
                self.online = False
            def active(self, value=None):
                if value is not None:
                    self.on = value
                return self.on
            def config(self, **_):
                pass
            def ifconfig(self, value=None):
                return value if value else (("192.168.4.1" if self.ap else "192.168.1.42"),)
            def isconnected(self):
                return self.online
            def connect(self, ssid, key):
                self.online = ssid == "Casa" and key == "Password123"
            def disconnect(self):
                self.online = False
            def status(self, kind=None):
                return -48 if kind == "rssi" else 3
            def scan(self):
                return [(b"Casa", b"123456", 6, -48, 3, 0)]

        ap, sta = Radio(True), Radio()
        def wlan(kind):
            return sta if kind == 1 else ap
        wlan.IF_STA, wlan.IF_AP = 1, 2
        env["network"] = types.SimpleNamespace(WLAN=wlan)

        class Clock:
            tick = 0
            def ticks_ms(self):
                self.tick += 1600
                return self.tick
            def ticks_add(self, tick, delta):
                return tick + delta
            def ticks_diff(self, a, b):
                return a - b
            def sleep_ms(self, _):
                pass
            def sleep(self, _):
                pass
        env["time"] = Clock()
        class Pin:
            OUT = 1
            def __init__(self, _pin, _mode, value=1):
                self.level = value
            def value(self, level=None):
                if level is not None:
                    self.level = level
                return self.level
        env["Pin"] = Pin

        class Client:
            def __init__(self, packet):
                self.packet, self.response = packet, b""
            def settimeout(self, _):
                pass
            def recv(self, _):
                packet, self.packet = self.packet, b""
                return packet
            def sendall(self, data):
                self.response += data
            def close(self):
                pass

        def request(method, path, body=b"", headers=()):
            head = (method + " " + path + " HTTP/1.1\r\nHost: 192.168.1.42\r\n"
                    + "".join(headers) + "Content-Length: " + str(len(body)) +
                    "\r\n\r\n").encode()
            return Client(head + body)

        class Socket:
            def __init__(self, stream):
                self.stream = stream
            def setsockopt(self, *_):
                pass
            def bind(self, _):
                pass
            def listen(self, _):
                pass
            def accept(self):
                return clients.pop(0), None
            def close(self):
                pass
        web = Socket(True)
        env["socket"] = types.SimpleNamespace(AF_INET=2, SOCK_STREAM=1, SOCK_DGRAM=2,
            SOL_SOCKET=1, SO_REUSEADDR=2, socket=lambda _a, kind: web if kind == 1 else Socket(False))
        class Poll:
            def register(self, *_):
                pass
            def unregister(self, *_):
                pass
            def poll(self, _):
                if not clients:
                    raise KeyboardInterrupt("end simulated session")
                return [(web, 1)]
        env["select"] = types.SimpleNamespace(poll=Poll, POLLIN=1)

        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                token = env["access_token"](env["defaults"]())
                clients = [
                    request("GET", "/"),
                    request("POST", "/wifi", b"ssid=Casa&key=Password123&remember=1"),
                    request("GET", "/"),
                    request("GET", "/status"),
                    request("POST", "/login", ("token=" + token).encode()),
                    request("GET", "/status", headers=("Cookie: auth=" + token + "\r\n",)),
                    request("POST", "/toggle", b"id=0", ("X-Control-Token: " + token + "\r\n",)),
                    request("GET", "/status", headers=("X-Control-Token: " + token + "\r\n",)),
                ]
                sent = list(clients)
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
                    env["main"]()
                self.assertIn(b"Configurar l\xc3\xa1mpara", sent[0].response)
                self.assertIn(b"Conectado", sent[1].response)
                self.assertIn(token.encode(), sent[1].response)
                self.assertIn(b"Acceso a l\xc3\xa1mpara", sent[2].response)
                self.assertIn(b"401 Unauthorized", sent[3].response)
                self.assertIn(b"Set-Cookie: auth=", sent[4].response)
                self.assertIn(b'"rssi": -48', sent[5].response)
                self.assertIn(b"303 See Other", sent[6].response)
                self.assertIn(b'"encendido": true', sent[7].response)
                self.assertFalse(ap.active())
                self.assertEqual(env["load_config"]()["wifi_ssid"], "Casa")
            finally:
                os.chdir(cwd)

    def test_docs_and_static_publication(self):
        for name in ("README.md", "CHANGELOG.md", "GUIA-IOT.md", "PRIVACIDAD.md", "DECLARACION-IA.md"):
            contents = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("v3.6.1", contents, name)
        self.assertIn('lucide@1.18.0', HTML)
        self.assertNotIn('lucide@latest', HTML)
        self.assertIn('Recuperar pestañas de Código', HTML)


if __name__ == "__main__":
    unittest.main()
