# Cambios

## [1.0.0] - 2026-09-27

### Agregado
- Nombre del proyecto: **Derecho a Markdown**. Limpia automáticamente instalaciones previas con el nombre antiguo (`MarkItDownMenu`).
- Opción "Convertir a Markdown" en el menú contextual para PDF, Office, HTML, CSV, JSON, XML, EPUB, Jupyter, Outlook y ZIP.
- Diálogo "Guardar como" con carpeta y nombre sugeridos, barra de progreso y opción de abrir el resultado.
- Instalador por usuario (sin admin) con entorno Python aislado y `markitdown[all]`.
- Opción de menú clásico en Windows 11 e inclusión opcional de imágenes y audio.
- Desinstalador.
- CI en Windows (instalación, conversión y desinstalación) y publicación automática de Releases.

### Corregido
- Detección de Python en Windows PowerShell 5.1 (comillas dobles mal pasadas a `python -c`).
