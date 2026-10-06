# Declaración de uso de inteligencia artificial — EspWebStudio v3.6.1

**Fecha:** 6 de octubre de 2026  
**Dirección y crédito del proyecto:** Braian M.  
**Herramienta empleada en esta etapa:** OpenAI Codex, asistente de IA para desarrollo de software.

## Alcance

Esta declaración describe la asistencia de IA en **EspWebStudio**, el IDE web de un solo `index.html` para ESP32 y MicroPython. No atribuye a este proyecto las herramientas ni la autoría declaradas por otros repositorios enlazados. En particular, el [Portal Cautivo Educativo](https://github.com/BraianM-dev/portal-cautivo) tiene su propia declaración y licencia; EspWebStudio incluye una adaptación educativa limitada, con atribución en el ejemplo y en el README.

| Componente | Participación documentada |
| --- | --- |
| Objetivo, requisitos, funciones solicitadas, disposición de la interfaz y crédito visible | Definidos mediante las indicaciones de Braian M. |
| Implementación y revisión del IDE, editor por bloques, panel Explorador adaptable, ejemplos, ejecución local interactiva, recuperación de borradores y proyectos IoT | Desarrollados y modificados con asistencia de OpenAI Codex a partir de esas indicaciones. |
| Ayuda, README, fichas de ejemplos, avisos y esta declaración | Redactados y revisados con asistencia de OpenAI Codex. |
| Pruebas efectuadas en esta etapa | Comprobaciones automáticas de sintaxis y estructura; simulaciones de AP → STA → panel HTTP con acceso por token, salida incremental del puerto, borradores, destino de guardado y pruebas de chatbot/Dungeon Master con entradas y tiradas controladas; análisis de sintaxis de los ejemplos y del JavaScript, y comprobaciones del editor visual. |
| Bibliotecas externas y firmware | Son proyectos de sus respectivos autores. La asistencia de IA no cambia sus licencias ni convierte su código en una creación de EspWebStudio. |

La selección de objetivos, la revisión final antes de publicar y la validación en dispositivos reales corresponden a quien mantiene el proyecto. Esta declaración **no afirma** que el portal de aprovisionamiento, el Wi-Fi real, los pines, las funciones de radio y el flasheo hayan sido probados en una placa física. El README y la [guía IoT](GUIA-IOT.md) distinguen las pruebas realizadas de las pendientes.

## Uso de IA al ejecutar EspWebStudio

La aplicación entregada **no incorpora un asistente de IA ni envía intencionalmente el código del editor a un modelo de IA**. El Python local se ejecuta con Pyodide en el navegador; los programas de MicroPython se envían a la placa por Web Serial. La página obtiene bibliotecas y, si se activa, la fuente OpenDyslexic desde servicios externos. El código que escriba el usuario puede realizar sus propias conexiones de red. Consulta [PRIVACIDAD.md](PRIVACIDAD.md) para los datos locales, las dependencias y las opciones de borrado.

## Comprobación y actualización

El código generado o sugerido por IA puede contener errores. Antes de usar la placa, confirma el modelo, los pines, el firmware y el comportamiento del programa. Revisa especialmente las operaciones que escriben flash, crean redes o reinician el dispositivo. Actualiza esta declaración si cambian sustancialmente las herramientas, las aportaciones o la forma en que la aplicación procesa datos.

**Licencia de EspWebStudio:** MIT, según [LICENSE](LICENSE). Esta declaración informa sobre el proceso de creación y no sustituye los avisos de licencia de las dependencias.
