# Privacidad y datos locales — EspWebStudio v3.6.1

EspWebStudio se publica como una página estática. No tiene un servidor propio para almacenar proyectos ni una función de telemetría integrada. Esta descripción se refiere al código de la aplicación entregada; los programas que escriba o ejecute cada persona pueden conectarse a servicios externos por su cuenta.

| Dato o acción | Dónde ocurre |
| --- | --- |
| Tema, idioma, accesibilidad, preferencias, perfil de placa, estado del explorador y altura de terminal | `localStorage` del navegador. |
| Proyecto de bloques | `localStorage`, **incluidos los campos de SSID y claves Wi-Fi que escribas en bloques**. |
| Documentos abiertos en Código | `localStorage` si está activada la recuperación de borradores (activada inicialmente): contenido, nombres, vista de Bloques vinculada y cambios. Puede incluir claves Wi-Fi del código. Descarga el `.py` para una copia independiente. Límite de 2 MB en la copia de recuperación. |
| Ejecución sin placa | Pyodide en un Web Worker del navegador; su sistema de archivos temporal no se sincroniza con la ESP32. Las respuestas escritas en el cuadro de `input()` se envían solo a ese Worker, permanecen en memoria durante la ejecución y no forman parte del borrador guardado. |
| Conexión, REPL y flasheo | Web Serial entre navegador y placa, después de autorizar el puerto. El navegador administra ese permiso. |
| Lámpara Wi-Fi | `iot_lampara.json` guarda un token aleatorio de acceso. Con **Recordar en esta placa**, también guarda SSID y clave en texto legible. `/status` exige cookie o token y no expone la clave. |
| Bibliotecas y fuente opcional | Se descargan desde CDN; esos servicios pueden recibir las solicitudes de red habituales del navegador. |

La elección **Mostrar/Ocultar explorador** y la de **Ocultar/Mostrar vista previa de Bloques** se conserva en una clave de EspWebStudio de `localStorage`. El estado anterior se usa una sola vez para respetar un panel que ya estaba cerrado; si no había una elección, se abre en escritorio y comienza cerrado en móvil. **Ajustes → Borrar datos guardados** elimina ambas preferencias junto con las otras claves de la aplicación.

En una computadora compartida, descarga primero el `.py` o exporta el proyecto de Bloques como `.json` y usa **Ajustes → Borrar datos guardados**. Esa acción elimina solo las claves de EspWebStudio en este origen y recarga la página. **No borra archivos ni firmware de la placa**, no elimina descargas previas y no revoca el permiso Web Serial que conserva el navegador. Para revocarlo, usa la configuración de permisos del sitio en el navegador.

El botón **Borrar datos guardados** avisa antes de actuar y elimina las copias recuperables de Código. Si desactivas **Recuperar pestañas de Código** en Ajustes, se borra esa copia inmediatamente; las pestañas abiertas siguen en memoria hasta cerrar o recargar. La recuperación trata todos los documentos como borradores locales y nunca asume que se conectó la misma placa. El borrado no se permite durante una instalación de firmware o ejecución activa. Para mover un proyecto visual a otra PC, exporta su JSON antes de limpiar el almacenamiento. **Este botón no borra `iot_lampara.json` de la placa**: usa Olvidar Wi-Fi guardada en su panel o elimina el archivo desde el explorador del IDE.

El formulario del portal AP y los paneles IoT usan **HTTP sin cifrado** dentro de la red local. La contraseña del Wi-Fi se transmite por ese AP al configurar la lámpara y puede quedar almacenada en la placa si marcas Recordar. El panel de la lámpara requiere un token aleatorio, pero **HTTP tampoco cifra ese token**; otros paneles de ejemplo (LED web y telemetría) no autentican. No expongas sus puertos a Internet y usa únicamente una red propia de confianza. Consulta [GUIA-IOT.md](GUIA-IOT.md).

La página necesita Internet la primera vez que carga sus bibliotecas externas. Ejecutar Python puro sin placa carga Pyodide bajo demanda; activar la tipografía para dislexia carga OpenDyslexic. Si necesitas un entorno sin dependencias de CDN, hace falta empaquetar y alojar esas bibliotecas por separado; el `index.html` entregado no incluye sus binarios.
