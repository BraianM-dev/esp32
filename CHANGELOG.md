# Cambios de EspWebStudio

## v3.6.1 — 6 de octubre de 2026

- Dos ejemplos nuevos: **Mi primer ChatBot** y **Dungeon Master: Calabozos y Código**. Ambos se ejecutan sin placa y también son programas Python para el REPL de MicroPython; el segundo usa `random.getrandbits(5)` para un dado d20 compatible con más firmwares.
- El ejecutor local ofrece un cuadro de entrada asíncrono para cada `input()` en el flujo superior del programa, con contexto reciente, respuesta y botón Detener. Los ejemplos interactivos también aceptan respuestas por serie cuando se ejecutan en la placa.
- Dos bloques de plantilla en **Conversación y juegos**, con parámetros de nombre, palabra de salida o salas. Catálogo: **46 ejemplos**, **71 bloques propios** y **49 plantillas de Bloques**. La lógica completa se ve y edita en Código.
- README, declaración de IA, privacidad, ayuda integrada y copias `.py` actualizados; pruebas de ambas rutas de los ejemplos y del puente de entrada incluidas en CI.

## v3.6.0 — 6 de octubre de 2026

- Salida Raw REPL incremental de `print()` durante ejecuciones y servicios; los programas indefinidos ya muestran IP y mensajes sin esperar a Detener. La copia visible del historial se limita a 120 000 caracteres por ejecución.
- Recuperación de pestañas de Código tras recargar, activada inicialmente y configurable en Ajustes. Los documentos restaurados se tratan como borradores locales; la copia se borra al desactivar la opción o al elegir Borrar datos guardados. Puede contener claves escritas en el código.
- «Guardar como» espera el resultado de la escritura antes de cambiar nombre y estado de la pestaña. No se confunde el archivo anterior con el destino nuevo si la transferencia falla.
- La lámpara genera y persiste un token aleatorio de 128 bits. El panel LAN y `/status` piden token; los navegadores usan cookie `HttpOnly; SameSite=Strict`, el control remoto usa `X-Control-Token`. HTTP local sigue sin cifrado, así que la guía advierte cómo proteger la red.
- Se añaden cuatro bloques propios (69 en total): conversión a Fahrenheit, kWh y dos tablas locales editables. Los ejemplos de Conversor y Tabla dejan de depender de un bloque Python multilínea. La vista previa generada se puede plegar.
- Lucide queda fijado a 1.18.0; guía IoT, README, privacidad y declaración de IA revisadas. Se incluyen copias `.py` de los ejemplos y pruebas de regresión ejecutables en CI.

## v3.5.1 — 6 de octubre de 2026

- El Explorador se oculta y se recupera desde un botón con texto en la barra compartida de Código/Bloques. También puede cerrarse desde su cabecera.
- Al cerrarlo, el editor aprovecha la columna completa y CodeMirror, Blockly y la terminal recalculan su tamaño. El estado se conserva en el navegador y el botón actualiza su texto en Español o English.
- En pantallas pequeñas, el Explorador se abre como panel lateral sobre el editor, con cierre desde el fondo o Esc. El botón ya no desaparece en móvil; la barra superior admite desplazamiento horizontal si es necesario.
- README y documentación integrada actualizados con el uso del panel y la disposición móvil. Se mantienen los 44 ejemplos, 65 bloques propios, proyectos IoT y declaración de IA de la versión anterior.

Se verificó la estructura y el comportamiento de alternancia mediante pruebas automatizadas. La disposición visual y el hardware físico quedan para comprobación manual en los navegadores y placas de destino.

## v3.5.0 — 6 de octubre de 2026

- Un solo botón **Ejecutar** en Código y Bloques. Usa la ESP32 si está conectada; sin placa ejecuta Python compatible en el navegador y avisa cuando detecta módulos o llamadas de hardware.
- Los ejemplos de Python puro se identifican con **(No necesita placa)**.
- Se conservan las 37 fichas anteriores y se agregan siete: LED integrado básico; lámpara AP → STA → panel local; LED por web; telemetría ADC/RSSI/JSON; botón remoto entre dos C3; conversor de temperatura y tabla de consumo.
- Cuatro bloques IoT editables en la categoría **Proyectos IoT**. Total: **44 ejemplos**, **65 bloques propios** y **47 plantillas de Bloques** (31 proyectos visuales y 16 representaciones de ejemplos Python).
- La lámpara configura Wi-Fi en un AP local, admite SSID manual, informa la IP de LAN y apaga el AP al conectar. Su panel tiene dos salidas configurables, parpadeo, apagado general y `/status` JSON. Guardar credenciales es opcional y queda documentado.
- Los servicios marcados en los ejemplos pueden ejecutarse hasta pulsar **Detener**; también pueden guardarse como `main.py` para arrancar al reiniciar.
- Guía IoT integrada en el HTML y disponible como documento. README, privacidad y declaración de IA actualizados.

La lógica del portal y de ejecución se probó mediante simulaciones, además de revisar sintaxis y generación. **No hubo prueba física** de Wi-Fi, GPIO, portal automático, flasheo o Web Serial con una placa real.
