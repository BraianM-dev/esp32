# Chat Ollama: Wi-Fi y USB en EspWebStudio v3.7.0

Este ejemplo conserva la web del ESP32 y añade acceso por el **mismo cable USB que usa EspWebStudio**. No requiere instalar un puente Python en la PC. En modo USB, la PC puede estar en el Wi-Fi del celular, en otra red o sin conexión Wi-Fi: los modelos instalados en Ollama siguen funcionando localmente. Abrir el IDE por primera vez y cargar sus bibliotecas puede requerir Internet.

## Preparar la placa una vez

1. Abre EspWebStudio en Chrome o Edge de escritorio y pulsa **Conectar**. Selecciona la ESP32-C3 con MicroPython. Cierra Thonny si tiene abierto ese puerto.
2. Pulsa **Web por USB → Crear archivos del chat**. Se crean dos pestañas locales, sin modificar automáticamente los archivos de la placa.
3. Revisa `main.py`. Configura `WIFI_SSID` y `WIFI_PASSWORD` si también quieres acceso por Wi-Fi. La contraseña vacía significa red abierta; USB no requiere que esa conexión funcione.
4. Selecciona la pestaña `index.html` y pulsa **Guardar**, conservando el nombre `index.html` en la raíz de la placa.
5. Selecciona `main.py` y pulsa **Guardar**, conservando ese nombre en la raíz. Guarda previamente tus archivos anteriores si deseas conservarlos: este paso puede reemplazarlos.
6. Con `main.py` seleccionado, pulsa **Ejecutar**. La consola muestra el inicio USB y la conexión Wi-Fi o el AP de respaldo. El marcador `# EspWebStudio: servicio` evita el límite de 120 segundos del Raw REPL.
7. Pulsa **Web por USB**. El IDE lee `index.html` desde la memoria de la placa por USB y muestra la página dentro de un panel.

También puedes descargar los archivos de esta carpeta y subirlos con el explorador del IDE. En la placa se guardan juntos en la raíz; no dentro de `ejemplos/chat_ollama/`.

## Ollama en la misma PC: preparación inicial

En el selector superior deja **Ollama desde: Esta PC**. En el chat usa `http://localhost:11434`, pulsa **Conectar y cargar modelos** y selecciona uno de los modelos instalados.

El navegador del IDE hace estas consultas desde su origen HTTPS. Debes permitir ese origen en Ollama y aceptar el permiso de acceso local si el navegador lo solicita. Para GitHub Pages de este proyecto, el origen es `https://braianm-dev.github.io` (sin `/esp32`). No es necesario exponer Ollama a toda la LAN para el modo PC.

### Windows: ejecución manual

1. Sal completamente de Ollama desde el icono de la bandeja, para no iniciar dos servidores en el mismo puerto.
2. Abre PowerShell y ejecuta:

```powershell
$env:OLLAMA_ORIGINS="https://braianm-dev.github.io"
ollama serve
```

3. Deja esa ventana abierta y vuelve al IDE. La variable anterior solo afecta a los programas lanzados desde esa sesión de PowerShell.
4. Para hacerlo persistente: busca **Editar las variables de entorno de esta cuenta**, crea `OLLAMA_ORIGINS` con el valor anterior y reinicia la aplicación Ollama. Si abres el IDE desde otro dominio, autoriza su origen exacto en lugar del anterior.

### Linux

Si lo ejecutas manualmente y no hay otro servidor ocupando el puerto:

```bash
OLLAMA_ORIGINS=https://braianm-dev.github.io ollama serve
```

Si se ejecuta como servicio:

```bash
sudo systemctl edit ollama.service
```

Añade:

```ini
[Service]
Environment="OLLAMA_ORIGINS=https://braianm-dev.github.io"
```

Después:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama.service
```

No uses `OLLAMA_ORIGINS=*` como configuración general. Las instrucciones oficiales están en [FAQ de Ollama](https://docs.ollama.com/faq).

## Acceso por Wi-Fi conservado

Abre `http://IP_DEL_ESP32:8080/` y escribe la IP de la PC con Ollama. En este modo el ESP32 consulta al modelo por su propia red, como en la versión anterior.

Ollama debe escuchar en la LAN (`OLLAMA_HOST=0.0.0.0:11434`) y el firewall permitir ese puerto. El AP de respaldo se llama `ESP32-Ollama`, con la clave configurable al inicio de `main.py`. Su dirección suele ser `http://192.168.4.1:8080/`.

El panel USB también permite seleccionar **Ollama desde: ESP32**: la página se transporta por USB, pero los modelos y las respuestas se obtienen usando el Wi-Fi de la placa. En este caso usa la IP LAN de Ollama, no `localhost`.

## Uso diario

- Conecta el USB y abre el IDE. Su conexión inicial interrumpe el programa para consultar la placa y sus archivos; esto conserva el comportamiento previo de EspWebStudio.
- Pulsa **Web por USB → Iniciar main.py guardado**, espera el mensaje de servicio y pulsa **Cargar web**. No hace falta volver a transferir los archivos.
- Para usar solo Wi-Fi, reinicia físicamente la placa; `main.py` arranca automáticamente.
- **Cerrar** oculta la página y cancela consultas pendientes desde la PC; el programa del ESP32 continúa. **Detener** interrumpe el servicio de la placa y libera el acceso al REPL y a los archivos.
- Solo una aplicación puede abrir el puerto USB. No abras Thonny ni otro monitor mientras el IDE lo usa.

## Funciones conservadas

Selector de modelos instalados; IP o URL editable; system prompt; temperatura; top-p; contexto; máximo de tokens; mensajes anteriores; nueva conversación; estado y memoria libre de la placa; reconexión STA; AP de respaldo; límites de tamaño; tiempos de espera; cierre de sockets; envío de HTML por bloques. Los ajustes USB se guardan en el navegador del IDE; el historial de conversación permanece en la sesión de la página. El modo Wi-Fi sigue guardando sus ajustes en el navegador que abre la IP de la placa.

## Cómo funciona

El firmware usa un protocolo de líneas ASCII `@EWSUSB:` por la consola USB, con fragmentos hexadecimales de 48 bytes y confirmación por fragmento. Atiende las solicitudes con las mismas funciones HTTP de Wi-Fi. La página se transmite por bloques; no se convierte el USB en una tarjeta de red.

En modo PC, el ESP32 valida y prepara el prompt, el historial y los límites en `/api/prepare`; EspWebStudio consulta a Ollama desde el navegador y entrega la respuesta al chat. Así el ESP32 no necesita llegar a la red de la PC. En modo ESP32, `/api/models` y `/api/chat` utilizan la conexión Wi-Fi de la placa.

La página de la placa se ejecuta en un iframe con sandbox, sin acceso al editor, al almacenamiento del IDE ni a la red por su cuenta. Solo las rutas de estado, modelos y chat pasan por el puente. Sus tres claves de configuración se conservan mediante mensajes validados, sin copiar otros datos del IDE.

## Límites y diagnóstico

- Requiere este firmware cooperativo. Una web HTTP de otro programa no se transforma automáticamente en una web USB.
- No sustituye a un USB Ethernet, VPN o túnel general. `localhost` identifica a la PC del navegador, no a la placa.
- El firmware necesita `asyncio`/`uasyncio`, `select.poll` sobre `sys.stdin` y MicroPython para ESP32-C3. No añadas otro lector de `sys.stdin` sin coordinarlo con este protocolo.
- La transferencia USB tiene un límite de 128 KB por respuesta; las solicitudes del chat, 16 KB. Ollama tiene un límite de 32 KB de respuesta en este ejemplo.
- El chat espera hasta 180 s. La primera respuesta puede tardar mientras se carga el modelo. Cancelar la petición no garantiza que Ollama deje de generar inmediatamente en la PC.
- Si falla el acceso local: comprueba Ollama, el origen permitido, el permiso del navegador y su política de contenido mixto/red local. El código no puede eludir esas políticas.
- Si falla Raw REPL al ejecutar una versión anterior: utiliza la versión con el marcador de servicio. Si aparece un traceback, conserva el texto completo; ese sí identifica una falla del programa.
- Se realizaron pruebas automatizadas de fragmentación, ACK, secuencias, UTF-8, desconexión, rutas, preparación del chat, aislamiento del iframe y regresiones del IDE. Falta validación física en la placa del usuario.
