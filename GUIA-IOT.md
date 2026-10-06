# Guía IoT — EspWebStudio v3.6.1

Para editar programas largos en Código o Bloques, usa **Ocultar explorador** en la fila de vistas. **Mostrar explorador** vuelve a abrir el panel de archivos cuando quieras guardar `main.py` o revisar `iot_lampara.json`. En móvil, el panel aparece sobre el editor y se cierra con su botón, el fondo o Esc; ocultarlo no cambia los archivos de la placa.

Los ejemplos están dentro de `index.html` y también como archivos `.py` opcionales en `ejemplos/`. Desde el catálogo se abren en **Código** o **Bloques**. En Bloques, los cuatro proyectos IoT ofrecen campos para editar los parámetros principales; cambia a Código para revisar o modificar cada función.

## Lámpara Wi-Fi con AP de configuración

1. Instala MicroPython para tu ESP32-C3 Super Mini, conecta el IDE y abre **Lámpara Wi-Fi: AP → red local**.
2. Revisa `LED_PIN = 8`, `ACTIVE_LEVEL = 0`, `AP_SSID` y `AP_KEY`. Algunas variantes de placa usan otro LED o una polaridad distinta. La clave del AP debe tener al menos ocho caracteres.
3. Pulsa **Ejecutar** para probar mientras la conexión serie está abierta, o guarda el programa como `main.py` y reinicia la placa para dejarlo disponible al arrancar. El marcador de servicio evita el límite de 120 segundos del ejecutor; **Detener** lo interrumpe. La pestaña **Salida** muestra `print()` en vivo durante el servicio, incluida la IP y el token.
4. Desde un teléfono o PC, conéctate al AP `C3-Lampara` (o el nombre que hayas elegido) y abre **http://192.168.4.1** si el portal no aparece automáticamente. Solo se redirigen consultas DNS/HTTP de los clientes de este AP; el comportamiento del aviso automático depende del sistema y HTTPS no se intercepta.
5. Selecciona un Wi-Fi de **2,4 GHz** de la lista o escribe el SSID oculto. Introduce la clave y pulsa **Conectar**. Si falla, el AP permanece disponible para intentarlo otra vez. Si se conecta, la página muestra la nueva IP y un **token de control de 32 caracteres**; anótalos en privado. El token también se imprime por USB. Vuelve a tu red doméstica y abre `http://IP`; introduce ese token para entrar.
6. En el panel local puedes encender y apagar dos salidas, probar **tres destellos**, apagar todas, cambiar sus etiquetas, GPIO y polaridad, y consultar `http://IP/status` como JSON después de iniciar sesión. Una petición de API desde otro cliente debe enviar la cabecera `X-Control-Token` con el mismo token. El primer control es el LED integrado; el segundo empieza en GPIO4. Cada botón debe tener un GPIO distinto.

La casilla **Recordar en esta placa** es opcional. Si la marcas, el programa guarda SSID y clave en `iot_lampara.json` y en el siguiente arranque inicia el AP, intenta reconectar y lo apaga al obtener IP. Si la red recordada falla, ofrece el AP de configuración. **Olvidar Wi-Fi guardada** borra esas credenciales del archivo, pero conserva el token; la conexión actual continúa hasta el próximo reinicio. El botón de borrar datos del navegador del IDE **no** borra este archivo de la placa. Al restaurar un borrador de Código, el IDE lo trata como local y no presupone cuál es la placa conectada.

## Otros ejemplos IoT

| Ejemplo | Qué hace | Preparación |
| --- | --- | --- |
| LED por página web local | Botones Encender y Apagar sobre HTTP en el puerto 80. | Cambia `SSID`, `CLAVE`, `LED_PIN` y `ACTIVO`; abre `http://IP`. |
| Telemetría IoT | Página HTML y `GET /status` JSON con ADC GPIO0, RSSI y RAM. | Sensor de 0–3,3 V en GPIO0, Wi-Fi y puerto 8080. |
| Botón remoto entre dos ESP32 | Una segunda placa envía `POST /toggle` a la lámpara al pulsar GPIO4. | Ambas en la misma LAN; botón entre GPIO4 y GND; ajusta `LAMP_IP` y `TOKEN` (copiado de la lámpara). |
| LED integrado básico | Enciende dos segundos y apaga GPIO8 sin red. | Verifica LED y polaridad de tu placa. |

Los servicios HTTP del panel LED y la telemetría también pueden guardarse como `main.py`. El ejemplo remoto realiza **20 ciclos de prueba** y termina; para operación continua puedes modificar ese bucle tras validar el cableado. Cuando un servicio corre mediante **Ejecutar**, el IDE muestra la salida USB en directo hasta pulsar **Detener**. Las IP del LED web y la telemetría se imprimen en **Salida**; también puedes consultarlas en el router. El historial visible de una ejecución larga está limitado para no agotar la memoria del navegador.

## Seguridad y límites

- El aprovisionamiento y el panel usan **HTTP sin TLS**. El formulario envía la clave a través del AP privado y la opción Recordar la guarda como texto legible en la flash. Usa una clave de AP propia, configura desde un dispositivo de confianza y elimina `iot_lampara.json` si compartes la placa.
- La lámpara genera un token aleatorio que queda en `iot_lampara.json`; su panel requiere el token y usa una cookie `HttpOnly; SameSite=Strict` después del ingreso. El control remoto lo envía en la cabecera `X-Control-Token`. **HTTP no cifra el token**: alguien que pueda observar el tráfico de la LAN podría copiarlo. Los otros paneles de demostración (LED web y telemetría) no tienen autenticación. No redirijas los puertos 80/8080 desde Internet.
- Un GPIO no puede alimentar una lámpara de 110/220 V. Para cargas reales se requiere electrónica de potencia, aislamiento y protección adecuados. Los ejemplos controlan directamente el LED de la placa o una salida lógica de baja tensión.
- Las redes de 5 GHz no son aptas para la radio Wi-Fi del ESP32-C3. Algunas variantes de C3 Super Mini no tienen LED en GPIO8 o cambian su polaridad; consulta su esquema.
- El portal automático depende de cómo cada sistema prueba la conectividad. Siempre puedes abrir la IP del AP de forma manual. No se realizó una prueba física con la placa del usuario; valida flasheo, Wi-Fi, GPIO y estabilidad del servicio en tu firmware y tu red antes de usarlo de forma continua.

## Qué hace Ejecutar

Hay un solo botón. Si el IDE tiene una ESP32 conectada, envía el programa a MicroPython. Si no hay placa, inspecciona imports y operaciones de hardware: el Python puro se ejecuta con Pyodide en el navegador y el código que necesita ESP32 muestra un aviso para conectar. Esta clasificación es una ayuda estática y no puede interpretar todas las importaciones dinámicas; ante un caso especial conecta la placa y ejecuta allí.

Fuentes técnicas: [WLAN de MicroPython](https://docs.micropython.org/en/latest/library/network.WLAN.html), [referencia ESP32](https://docs.micropython.org/en/latest/esp32/quickref.html) y [socket de MicroPython](https://docs.micropython.org/en/latest/library/socket.html).
