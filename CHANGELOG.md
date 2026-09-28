# Cambios

## [1.1.0] - 2026-09-27

### Agregado
- **Selección múltiple en una sola ventana**: al convertir varios archivos se elige la carpeta de destino una vez (antes se abría un "Guardar como" por archivo).
- Barra "N de M", botón Cancelar y resumen final (convertidos, vacíos, con error) con opción de abrir la carpeta.
- Manejo de nombres repetidos (`informe (pdf).md`) y de archivos existentes (reemplazar o `nombre (1).md`).
- La opción aparece aunque se seleccionen más de 15 archivos (`MultiSelectModel=Player`).
- Prueba automática de la agrupación con procesos reales en Windows (named pipes).

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
