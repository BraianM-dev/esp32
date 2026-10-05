# EspWebStudio v2.0.0

IDE web para programar ESP32 con MicroPython. Se publica como un único **index.html** en GitHub Pages: no requiere instalar un editor, Python ni un servidor en la PC.

## Qué incluye

- Editor Python, terminal REPL, ejecución en RAM, explorador y transferencia de archivos.
- Instalación de firmware MicroPython desde la web mediante Web Serial y **esptool-js 0.7.0**.
- Perfiles de flasheo: **ESP32-C3 / C3 Super Mini**, **ESP32 clásico** y **ESP32-S3**. El instalador detecta el chip, comprueba el perfil y la capacidad de la flash antes de escribir.
- Opción separada para borrar por completo la flash durante la instalación inicial. La opción comienza desmarcada.
- Biblioteca integrada con ejemplos editables: modo AP, modo STA, escaneo Wi-Fi y RSSI, monitor RSSI, diagnóstico, LED GPIO8 y UART GPIO4/GPIO5.
- Raw-paste REPL con control de flujo para transferir programas largos; alternativa Raw REPL por bloques para firmwares antiguos.

## Publicar en GitHub Pages

1. Sube el contenido de esta carpeta al directorio raíz del repositorio. El único archivo imprescindible para la aplicación es **index.html**.
2. En **Settings → Pages**, publica **main** y **/(root)**.
3. Abre la URL HTTPS de Pages en **Chrome o Edge de escritorio**, conecta la placa por USB y autoriza el puerto cuando el navegador lo solicite.

La interfaz se sirve como archivo estático. Las bibliotecas del editor y del flasheador se cargan desde CDN, por lo que se necesita Internet para abrirlas por primera vez. El firmware .bin se selecciona desde el disco del usuario; la aplicación no lo incluye ni lo envía a un servidor.

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

El botón **Ejemplos** abre cada programa en una pestaña local: ejecuta con **F5** o guarda en la placa con **Ctrl+S**. Si quieres que arranque automáticamente, guárdalo como **main.py**. Cambia TU_RED_WIFI, TU_CLAVE y la clave del ejemplo AP. Los GPIO del LED y UART son referencias para algunas variantes C3 Super Mini; comprueba el pinout de tu placa antes de conectarla.

El RSSI de escaneo y el RSSI de la conexión STA se miden en **dBm por la placa**. El navegador no obtiene la potencia Wi-Fi de la PC por medio de Web Serial.

## Compatibilidad y límites

- Web Serial requiere un navegador compatible y contexto seguro; GitHub Pages ofrece HTTPS. Firefox no expone esta API para este flujo.
- El cable USB debe transportar datos. Algunos adaptadores USB-UART pueden necesitar el controlador correspondiente del sistema operativo.
- Cierra Thonny o cualquier otro monitor que esté usando el puerto. Solo una aplicación puede abrirlo a la vez.
- Los chips con menos de 4 MiB de flash, firmware propio o variantes de hardware especiales pueden requerir otra imagen. La aplicación no compila MicroPython ni genera binarios a partir de código C/ELF.
- **Sin prueba física en una placa:** se verificaron sintaxis, navegación y flujo simulado; el flasheo definitivo debe comprobarse con una ESP32-C3 Super Mini real.

## Tecnología y licencias

EspWebStudio se distribuye bajo licencia **MIT** (archivo LICENSE). Usa bibliotecas de terceros con sus propias licencias: esptool-js de Espressif (**Apache-2.0**), CodeMirror, xterm.js y Lucide. El flasheador se carga bajo una versión fija; el resto de dependencias del editor se sirven por CDN.

Documentación técnica: [esptool-js](https://github.com/espressif/esptool-js), [Web Serial](https://developer.chrome.com/docs/capabilities/serial) y [Raw REPL de MicroPython](https://docs.micropython.org/en/latest/reference/repl.html).
