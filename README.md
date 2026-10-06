# EspWebStudio v3.4.0

IDE web para programar ESP32 con MicroPython. Se publica como un único **index.html** en GitHub Pages: no requiere instalar un editor, Python ni un servidor en la PC.

## Qué incluye

- Editor Python, terminal REPL, ejecución en RAM, explorador y transferencia de archivos.
- Instalación de firmware MicroPython desde la web mediante Web Serial y **esptool-js 0.7.0**.
- Perfiles de flasheo: **ESP32-C3 / C3 Super Mini**, **ESP32 clásico** y **ESP32-S3**. El instalador detecta el chip, comprueba el perfil y la capacidad de la flash antes de escribir.
- Opción separada para borrar por completo la flash durante la instalación inicial. La opción comienza desmarcada.
- Biblioteca integrada con 37 ejemplos editables en Código y Bloques: Python local, GPIO, sensores, energía, I²C, SPI, UART/USB, Wi-Fi/HTTP, BLE, ESP-NOW, NeoPixel, NVS, archivos y portal cautivo educativo.
- Estudio visual Blockly con **60 bloques propios** y categorías estándar de control, funciones, variables, lógica, matemáticas y texto. Genera MicroPython editable para ejecutarlo en RAM o guardarlo en la placa.
- **31 proyectos visuales editables**: LED, botón, PWM, ADC, I²C, SPI, UART, AP, STA/RSSI, escaneo Wi-Fi, HTTP, BLE, ESP-NOW, NeoPixel, NVS y archivos. Todos aparecen en el catálogo general con una guía de pasos; cada uno se abre en la vista actual y tiene una representación editable en Bloques.
- Tema oscuro y claro integrado en Blockly, perfil ESP32-C3 Super Mini que comprueba pines reservados y botón **Verificar placa** para detectar módulos del firmware.
- **Código ↔ Bloques como vistas del mismo editor:** el cambio se realiza mediante pestañas, sin ventana superpuesta. Los 37 ejemplos conservan una representación visual. Las ediciones sencillas de campos generados también se reconocen; Python arbitrario se conserva íntegro en un bloque personalizado editable.
- Menú de **Accesibilidad** en la esquina superior derecha, junto a la paleta de comandos, con tamaño de interfaz, contraste, reducción de movimiento y tipografía OpenDyslexic; acceso por Alt+A. Selector de idioma Español / English en Ajustes para la interfaz, el catálogo y los bloques propios.
- **Explorador plegable** y guía de conexiones cerrable para ganar espacio en Bloques. Perfil de placa y Ver ejemplos permanecen en la barra compartida de ambas vistas.
- **Ejecución local sin placa** mediante Pyodide en un Web Worker: `print("Hola mundo")`, cálculos y Python puro. F5 usa la placa si está conectada y el navegador si no lo está; el botón Ejecutar local siempre fuerza el navegador.
- **Descargar .py** en la barra compartida guarda el programa actual del editor o el Python generado por Bloques en la PC, sin conectar una placa.
- Pestañas **Uso de IA** y **Privacidad** dentro de la documentación; Ajustes incluye el borrado local de preferencias y proyectos visuales con confirmación.
- Raw-paste REPL con control de flujo para transferir programas largos; alternativa Raw REPL por bloques para firmwares antiguos.

## Declaración de IA y privacidad

La [declaración de uso de IA](DECLARACION-IA.md) identifica el papel de Braian M. y la asistencia de OpenAI Codex por componente, las pruebas automatizadas realizadas y las validaciones físicas pendientes. También está disponible desde **Documentación → Uso de IA** dentro del HTML. La aplicación no integra un modelo de IA durante la programación o ejecución.

La [guía de privacidad](PRIVACIDAD.md) explica qué se guarda en `localStorage`, el permiso Web Serial y las dependencias de CDN. **Los bloques pueden guardar claves Wi-Fi en este navegador**. Descarga el `.py` o exporta `.json` antes de usar **Ajustes → Borrar datos guardados**. El borrado recarga la página y no modifica la placa ni revoca el permiso serial del navegador. La reconexión automática está desactivada por defecto; puede activarse en Ajustes.

La interfaz se sirve como archivo estático. Las bibliotecas del editor y del flasheador se cargan desde CDN, por lo que se necesita Internet para abrirlas por primera vez. El firmware .bin se selecciona desde el disco del usuario; la aplicación no lo incluye ni lo envía a un servidor.

El botón **Bloques** carga Blockly 13.3.0 desde CDN cuando se abre la vista visual. Ejecutar local carga Pyodide v314.0.7 bajo demanda desde CDN; la fuente OpenDyslexic también se descarga bajo demanda. Todo el código de la aplicación y los ejemplos siguen dentro de **index.html**; no hace falta instalar programas en la PC. El MicroPython generado se ejecuta en el ESP32 conectado mediante el mismo botón **Conectar** del IDE.

## Instalar MicroPython en una ESP32-C3 Super Mini

1. Abre el botón **Firmware** y deja seleccionado **ESP32-C3 / C3 Super Mini**.
2. Desde el enlace de MicroPython descarga el **archivo .bin completo** del perfil ESP32_GENERIC_C3. No selecciones .app-bin.
3. Selecciona el archivo descargado. Para la primera instalación, marca **Borrar completamente la flash**; esto elimina los programas y datos anteriores de la placa.
4. Marca la confirmación y pulsa **Instalar MicroPython**. Selecciona el puerto USB de la placa. Si ya estaba abierta en el IDE, el instalador libera y reutiliza ese puerto.
5. Espera a que termine la escritura y pulsa **Conectar** en el IDE. Si la placa no se detecta en modo descarga, mantén **BOOT**, pulsa **RESET** y reintenta; el procedimiento físico puede variar entre fabricantes.

El perfil C3 usa dirección **0x0**. ESP32-S3 también usa **0x0**; ESP32 clásico usa **0x1000**, de acuerdo con las páginas oficiales de descarga de MicroPython. El instalador usa DIO/40 MHz y detecta la capacidad de flash; rechaza un chip que no coincida con el perfil elegido. El nombre de un archivo de firmware personalizado no siempre permite verificar su familia, de modo que debes seleccionar la imagen apropiada.

| Familia | Página oficial de firmware | Dirección |
| --- | --- | --- |
| ESP32-C3 | [ESP32_GENERIC_C3](https://micropython.org/download/ESP32_GENERIC_C3/) | 0x0 |
| ESP32 clásico | [ESP32_GENERIC](https://micropython.org/download/ESP32_GENERIC/) | 0x1000 |
| ESP32-S3 | [ESP32_GENERIC_S3](https://micropython.org/download/ESP32_GENERIC_S3/) | 0x0 |

## Ejemplos y flujo de trabajo

El botón **Ver ejemplos** reúne 37 fichas organizadas por función. Cada una explica sus pasos, muestra advertencias cuando corresponde y se abre en **la vista que ya estés usando**: Código o Bloques. Cambia de pestaña para ver el mismo documento convertido sin ventana superpuesta. Ejecuta con **F5**, guarda en la placa con **Ctrl+S** o pulsa **Descargar .py** para conservar el archivo sin placa. Si quieres que arranque automáticamente, guárdalo como **main.py**. Cambia TU_RED_WIFI, TU_CLAVE y la clave del ejemplo AP. Los GPIO del LED y UART son referencias para algunas variantes C3 Super Mini; comprueba el pinout de tu placa antes de conectarla.

El RSSI de escaneo y el RSSI de la conexión STA se miden en **dBm por la placa**. El navegador no obtiene la potencia Wi-Fi de la PC por medio de Web Serial.

El ejemplo **Monitor de RSSI** ahora activa STA, conecta con SSID y clave propios, espera como máximo 15 segundos y mide diez muestras solo si hay conexión; muestra errores o pérdidas de señal. Sustituye TU_RED_WIFI y TU_CLAVE. El ejemplo visual **Conectar STA y medir RSSI** usa la misma secuencia y genera Python editable.

## Ejecutar Python sin placa

Abre **Hola mundo sin placa** y pulsa **Ejecutar local**: la pestaña Salida mostrará `Hola mundo`. También puedes pulsar **F5** o **Ejecutar** con la placa desconectada. Si hay una ESP32 conectada, **Ejecutar** y **F5** envían el programa a la placa; **Ejecutar local** mantiene la ejecución en el navegador. **Detener** termina el Web Worker local, incluso ante un bucle que no responde, y la siguiente prueba recarga ese intérprete. La primera carga necesita Internet y puede tardar por el tamaño de Pyodide. Las pestañas de Código viven en memoria hasta que descargues el archivo; el proyecto visual se conserva en el almacenamiento local del navegador.

Este modo usa Python en WebAssembly (Pyodide/CPython), por lo que sirve para `print`, variables, bucles, funciones, texto y cálculos. Incluye un puente mínimo para `time.sleep_ms`, `time.ticks_ms` y los alias `utime`, `ujson`, `ubinascii`. **No emula la ESP32 ni ejecuta MicroPython de hardware**: `machine`, `network`, `bluetooth`, `espnow`, `esp32`, `neopixel`, los pines y el puerto USB de la placa necesitan firmware MicroPython y una placa conectada. En Bloques también puedes ejecutar localmente los programas de Python puro, como **Matemáticas sin placa**; un bloque de hardware mostrará el error del módulo correspondiente. El sistema de archivos local del intérprete no se transfiere automáticamente a la ESP32.

## Programar por bloques

1. Pulsa **Ver ejemplos** en la fila superior del editor y abre cualquiera de los 37 programas. Si estás en Bloques, se abre allí; si estás en Código, se abre en Código. Elige el perfil **ESP32-C3 Super Mini** en esa misma fila.
2. Revisa el MicroPython generado en el panel derecho. Corrige las advertencias de GPIO y cambia el SSID y la clave en los bloques si usas Wi-Fi. **Verificar placa** muestra si tu firmware incluye BLE, ESP-NOW y NeoPixel.
3. Encaja las muescas de los bloques para definir el orden; coloca valores redondos dentro de huecos compatibles. La guía de conexiones se cierra con × y se recupera con **Ayuda de bloques**. **Ocultar explorador** agranda la zona de trabajo. Selecciona un bloque para ver su ayuda y usa comentarios en las plantillas. Pulsa **Ejecutar en la placa** para probarlo, **Ver Código del mismo proyecto** para editar Python, o **Guardar .py en la placa** para escribir el archivo.
4. Usa **Exportar .json** para conservar un proyecto visual editable y **Importar .json** para cargarlo más tarde. El navegador también lo guarda automáticamente en almacenamiento local, incluidos los campos con claves Wi-Fi; limpia el proyecto en una PC compartida.

Las representaciones de los nueve ejemplos Python cubren Hola mundo, AP, STA, escaneo, RSSI, diagnóstico, LED, UART y portal educativo. El archivo Python original se mantiene exactamente al alternar las vistas mientras los bloques no se modifiquen. Al editar los bloques, se genera el Python equivalente, que puede tener otra estructura interna. La conversión visual reconoce instrucciones sencillas como `print("texto")`, `time.sleep_ms(...)` y escritura de `Pin`, además de mantener la estructura de los proyectos generados. Cuando el código editado incluye instrucciones que no se pueden traducir de forma inequívoca, se agrupa en un **bloque Python personalizado**. Selecciónalo y pulsa **Python** para editarlo; el código original se conserva sin pérdida. En una plantilla generada, una edición aislada de un campo, como el SSID, se refleja de vuelta en su bloque si la regeneración coincide exactamente. En los ejemplos Python de AP, STA y RSSI también se reconocen cambios aislados del SSID o la clave.

Los bloques que usan periféricos requieren una placa conectada con MicroPython. El navegador genera el código y se lo envía a la placa. Los bloques de Python puro también pueden ejecutarse localmente con Pyodide, según la sección anterior. En algunas ESP32-C3 Super Mini el LED conectado a GPIO8 es activo en bajo; comprueba el pinout y ajusta el nivel del bloque Parpadear LED.

### Categorías avanzadas

| Categoría | Bloques incluidos |
| --- | --- |
| Placa y control | Memoria, identificación, tiempo, bucles continuos, reposo ligero y profundo. |
| GPIO, ADC y PWM | Entradas con pull-up/down, cambios de estado, lectura analógica, alarma ADC con LED, brillo PWM y NeoPixel externo. |
| Buses | Escaneo y registros I²C, transferencia SPI, UART1 y salida por consola USB/REPL. |
| Wi-Fi y HTTP | AP, STA, RSSI, escaneo, estado de red, consulta HTTP, servidor HTTP limitado y portal cautivo educativo acotado. |
| BLE | Anuncio, escaneo de dispositivos y servicio GATT que controla un LED. |
| ESP-NOW | Inicio, registro de MAC, envío, recepción y procesamiento de mensajes. |
| Datos | Archivos, almacenamiento NVS y watchdog. |

Los bloques de BLE, ESP-NOW y NeoPixel necesitan que el firmware incluya sus módulos. BLE GATT usa el servicio UUID **FFF0** y la característica escribible **FFF1**; escribe `1` o `ON` para encender el LED. Para comunicaciones ESP-NOW, introduce la MAC del par y asegúrate de que ambas placas operan en el mismo canal Wi-Fi. El ejemplo de envío usa difusión; para un par concreto reemplaza la MAC `FF:FF:FF:FF:FF:FF`.

El bloque **HTTP GET** usa HTTP sin TLS y está identificado como tal. El servidor HTTP atiende una cantidad limitada de solicitudes para que una ejecución de prueba pueda terminar. Para servicios continuos o BLE, guarda el programa como **main.py** en la placa y reiníciala.

### Pines y USB en ESP32-C3

El perfil C3 bloquea en la vista visual los GPIO12–17, normalmente usados por la flash, y GPIO18/19, utilizados por el USB Serial/JTAG. Advierte sobre GPIO2, 8 y 9 porque intervienen en el arranque. La lectura ADC se restringe a GPIO0–4. Los pines expuestos y el LED integrado pueden variar entre fabricantes de placas Super Mini; confirma el esquema de tu unidad.

ESP32-C3 tiene **Bluetooth Low Energy**, no Bluetooth Classic. Su USB integrado sirve para serial/JTAG; el bloque de salida USB utiliza `print()` y la terminal REPL. No genera dispositivos USB HID o un puerto USB personalizado.

En el centro del pie de página figura «</> Diseñado y Desarrollado por Braian M. | 2026».

## Portal cautivo educativo y uso responsable

**Portal cautivo educativo** se inspira en el flujo AP → DNS → HTTP de [Portal Cautivo Educativo de Braian Mosqueira](https://github.com/BraianM-dev/portal-cautivo), publicado bajo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Esta adaptación escrita para el IDE muestra una página informativa; **no solicita ni guarda credenciales, no imita instituciones y no incluye simulación de phishing o ransomware**. Su código y ficha incluyen atribución y aviso.

Configura SSID y clave de una red de prueba propia y conecta únicamente dispositivos de participantes informados. Al ejecutarlo, la placa responde DNS y HTTP para **clientes de ese AP** durante hasta 45 segundos o 20 solicitudes HTTP; después cierra los sockets y apaga el AP. Abre `http://192.168.4.1` si el sistema no muestra el portal automáticamente. Los navegadores y sistemas varían en sus pruebas de conectividad; **HTTPS no se redirige**. El operador es responsable de obtener autorización para cualquier demostración. Los ejemplos de reposo profundo advierten sobre reinicios y los que escriben flash deben usarse con moderación.

## Compatibilidad y límites

- Para conectar o flashear, Web Serial requiere un navegador compatible y contexto seguro; GitHub Pages ofrece HTTPS. Firefox no expone esta API para este flujo. Ejecutar Python local no necesita Web Serial.
- El cable USB debe transportar datos. Algunos adaptadores USB-UART pueden necesitar el controlador correspondiente del sistema operativo.
- Cierra Thonny o cualquier otro monitor que esté usando el puerto. Solo una aplicación puede abrirlo a la vez.
- Los chips con menos de 4 MiB de flash, firmware propio o variantes de hardware especiales pueden requerir otra imagen. La aplicación no compila MicroPython ni genera binarios a partir de código C/ELF.
- **Sin prueba física en una placa:** se verificaron sintaxis, generación, serialización y el flujo DNS/HTTP simulado; Bluetooth, ESP-NOW, pines, USB, apertura automática del portal y flasheo deben comprobarse con una ESP32-C3 Super Mini real.

## Tecnología y licencias

EspWebStudio se distribuye bajo licencia **MIT** (archivo LICENSE). La transparencia sobre asistencia de IA consta en [DECLARACION-IA.md](DECLARACION-IA.md). Usa bibliotecas de terceros con sus propias licencias: esptool-js de Espressif (**Apache-2.0**), Blockly (**Apache-2.0**), CodeMirror, xterm.js y Lucide. La ejecución local utiliza Pyodide y la fuente opcional OpenDyslexic se distribuye bajo SIL OFL 1.1. Blockly y el flasheador se cargan bajo versiones fijas; el resto de dependencias del editor se sirven por CDN.

Documentación técnica: [Blockly](https://developers.google.com/blockly/guides/create-custom-blocks/code-generation/overview), [ESP32-C3 GPIO](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-reference/peripherals/gpio.html), [MicroPython ESP-NOW](https://docs.micropython.org/en/latest/library/espnow.html), [MicroPython BLE](https://docs.micropython.org/en/latest/library/bluetooth.html), [esptool-js](https://github.com/espressif/esptool-js), [Web Serial](https://developer.chrome.com/docs/capabilities/serial), [Raw REPL](https://docs.micropython.org/en/latest/reference/repl.html), [Pyodide en Web Worker](https://pyodide.org/en/stable/usage/webworker.html) y [OpenDyslexic](https://github.com/antijingoist/opendyslexic).
