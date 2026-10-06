# Privacidad y datos locales — EspWebStudio v3.4.0

EspWebStudio se publica como una página estática. No tiene un servidor propio para almacenar proyectos ni una función de telemetría integrada. Esta descripción se refiere al código de la aplicación entregada; los programas que escriba o ejecute cada persona pueden conectarse a servicios externos por su cuenta.

| Dato o acción | Dónde ocurre |
| --- | --- |
| Tema, idioma, accesibilidad, preferencias, perfil de placa, estado del explorador y altura de terminal | `localStorage` del navegador. |
| Proyecto de bloques | `localStorage`, **incluidos los campos de SSID y claves Wi-Fi que escribas en bloques**. |
| Documentos abiertos en Código | Memoria de la pestaña; descarga el `.py` para conservarlos. El proyecto de bloques sí se guarda localmente. |
| Ejecución sin placa | Pyodide en un Web Worker del navegador; su sistema de archivos temporal no se sincroniza con la ESP32. |
| Conexión, REPL y flasheo | Web Serial entre navegador y placa, después de autorizar el puerto. El navegador administra ese permiso. |
| Bibliotecas y fuente opcional | Se descargan desde CDN; esos servicios pueden recibir las solicitudes de red habituales del navegador. |

En una computadora compartida, descarga primero el `.py` o exporta el proyecto de Bloques como `.json` y usa **Ajustes → Borrar datos guardados**. Esa acción elimina solo las claves de EspWebStudio en este origen y recarga la página. **No borra archivos ni firmware de la placa**, no elimina descargas previas y no revoca el permiso Web Serial que conserva el navegador. Para revocarlo, usa la configuración de permisos del sitio en el navegador.

El botón **Borrar datos guardados** avisa antes de actuar. Las pestañas de Código que no hayas descargado se perderán al recargar. El borrado no se permite durante una instalación de firmware o ejecución activa. Para mover un proyecto visual a otra PC, exporta su JSON antes de limpiar el almacenamiento.

La página necesita Internet la primera vez que carga sus bibliotecas externas. Ejecutar local carga Pyodide bajo demanda; activar la tipografía para dislexia carga OpenDyslexic. Si necesitas un entorno sin dependencias de CDN, hace falta empaquetar y alojar esas bibliotecas por separado; el `index.html` entregado no incluye sus binarios.
