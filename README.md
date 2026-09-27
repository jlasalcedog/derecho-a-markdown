# Derecho a Markdown

> Todo archivo tiene derecho a ser Markdown. Solo necesita un **click derecho**.

Click derecho sobre un archivo → **Convertir a Markdown** → eliges dónde guardar el `.md`.

Integra [microsoft/markitdown](https://github.com/microsoft/markitdown) (la librería original de Microsoft) en el Explorador de Windows, sin abrir terminal ni escribir comandos. Ideal para pasar PDFs, Word, Excel o PowerPoint a texto que puedes pegar en un LLM, en Obsidian o en tu repo.

[![CI](https://github.com/jlasalcedog/derecho-a-markdown/actions/workflows/ci.yml/badge.svg)](https://github.com/jlasalcedog/derecho-a-markdown/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/jlasalcedog/derecho-a-markdown)](https://github.com/jlasalcedog/derecho-a-markdown/releases/latest)
![Windows 10 | 11](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6)
![Python 3.10–3.14](https://img.shields.io/badge/Python-3.10%E2%80%933.14-3776AB)
![Licencia MIT](https://img.shields.io/badge/licencia-MIT-green)

---

## Características

- **Diálogo "Guardar como"**: se abre en la carpeta del archivo con el mismo nombre `.md`; puedes cambiar ruta y nombre.
- **Usa la librería oficial** `markitdown[all]`, instalada en un entorno Python propio (no ensucia tu Python global).
- **Sin administrador**: todo queda en tu usuario (`HKCU` y `%LOCALAPPDATA%`).
- **Funciona con el PowerShell que trae Windows** (5.1); no requiere PowerShell 7.
- **Solo aparece en formatos compatibles**: no llena el menú de archivos que MarkItDown no entiende.
- **Windows 11**: opción de activar el menú clásico para que la entrada salga directo al hacer click derecho.
- Barra de progreso, aviso si el resultado sale vacío (PDF escaneado) y opción de abrir el `.md` al terminar.
- Desinstalador que deja todo como estaba.

## Instalación

1. Descarga el `.zip` desde [**Releases**](https://github.com/jlasalcedog/derecho-a-markdown/releases/latest) (o *Code → Download ZIP*).
2. Click derecho sobre el `.zip` → **Extraer todo…**
3. Doble click en **`instalar.bat`**.
4. Responde las dos preguntas:
   - *¿Incluir imágenes y audio?* → recomendado **N** (ver [Formatos](#formatos)).
   - *¿Activar el menú clásico?* (solo Windows 11) → **S** si quieres la opción directo en el click derecho.

Si no tienes Python 3.10–3.14, el instalador ofrece instalar Python 3.12 con `winget`.

<details>
<summary>Instalación sin preguntas (PowerShell)</summary>

```powershell
powershell -ExecutionPolicy Bypass -File .\instalar.ps1 -SinPreguntas            # solo documentos
powershell -ExecutionPolicy Bypass -File .\instalar.ps1 -SinPreguntas -MenuClasico -IncluirMultimedia
```

| Parámetro | Efecto |
|---|---|
| `-SinPreguntas` | No pregunta nada; usa solo los parámetros |
| `-MenuClasico` | Activa el menú contextual clásico en Windows 11 |
| `-IncluirMultimedia` | Agrega `.jpg .jpeg .png .mp3 .wav .m4a` |
</details>

## Uso

1. Click derecho sobre un PDF, Word, Excel, PowerPoint…
2. **Convertir a Markdown**.
   En Windows 11 sin menú clásico: **Mostrar más opciones** (o **Shift + click derecho**).
3. Elige dónde guardar → espera la barra de progreso → ¿abrir el archivo?

Si seleccionas varios archivos, aparece un diálogo por cada uno.

## Formatos

| Tipo | Extensiones |
|---|---|
| Documentos | `.pdf` `.docx` `.pptx` `.xlsx` `.xls` `.epub` |
| Web y datos | `.html` `.htm` `.csv` `.json` `.xml` `.rss` `.atom` `.ipynb` |
| Otros | `.msg` (Outlook) `.zip` (convierte cada archivo interno) |
| Opcionales | `.jpg` `.jpeg` `.png` `.mp3` `.wav` `.m4a` |

> - **Imágenes**: sin un LLM configurado, MarkItDown solo extrae metadatos EXIF (requiere `exiftool`).
> - **Audio**: se transcribe con el servicio de voz de Google (requiere internet).
> - **No soportados** por MarkItDown: `.doc`, `.ppt` antiguos → guárdalos como `.docx` / `.pptx`.
> - **PDF escaneado** (solo imagen): el resultado sale vacío; MarkItDown no hace OCR por defecto.

## Desinstalar

Doble click en **`desinstalar.bat`** (o ejecuta `%LOCALAPPDATA%\DerechoAMarkdown\desinstalar.ps1`).
Quita la opción del menú, borra la carpeta de instalación y pregunta si quieres volver al menú de Windows 11.

## Actualizar

Vuelve a ejecutar `instalar.bat` (o el de una versión nueva): actualiza `markitdown` a la última versión y reescribe las entradas del menú.

## Cómo funciona

```
Click derecho ─► HKCU\Software\Classes\SystemFileAssociations\<.ext>\shell\DerechoAMarkdown
                   └─ command: "<venv>\Scripts\pythonw.exe" "<app>\convertir_markitdown.pyw" "%1"
                                 │
                                 ├─ tkinter: diálogo "Guardar como"
                                 ├─ MarkItDown().convert(archivo)   (en un hilo, con barra de progreso)
                                 └─ escribe el .md en UTF-8
```

| Qué | Dónde |
|---|---|
| Entorno Python + markitdown | `%LOCALAPPDATA%\DerechoAMarkdown\venv` |
| Script e ícono | `%LOCALAPPDATA%\DerechoAMarkdown\app` |
| Entradas del menú | `HKCU\Software\Classes\SystemFileAssociations\<ext>\shell\DerechoAMarkdown` |
| Menú clásico (opcional) | `HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}` |

Se usa `SystemFileAssociations` para que la opción aparezca sin importar qué programa abre cada tipo de archivo.

## Solución de problemas

| Síntoma | Qué hacer |
|---|---|
| "No encuentro la carpeta app" | Extrae el `.zip` completo antes de ejecutar `instalar.bat`. |
| No encuentra Python | Instala Python 3.12 desde [python.org](https://www.python.org/downloads/) marcando *Add python.exe to PATH*. El paso 1 muestra qué versiones detectó. |
| Falla `pip install` | Revisa internet o el proxy de tu red. |
| La opción no aparece | En Windows 11 está en *Mostrar más opciones*; o reinstala con `-MenuClasico`. |
| Error al convertir | El detalle queda en `%LOCALAPPDATA%\DerechoAMarkdown\app\errores.log`. |
| Log del instalador | `%TEMP%\derecho-a-markdown_instalar.log` |

¿Otro problema? Abre un [issue](https://github.com/jlasalcedog/derecho-a-markdown/issues) con el log.

## Desarrollo

```
app/convertir_markitdown.pyw   conversor + interfaz (tkinter)
app/markitdown.ico             ícono
instalar.ps1 / .bat            instalador
desinstalar.ps1 / .bat         desinstalador
tests/                         prueba de conversión con archivos de muestra
.github/workflows/ci.yml       instala, convierte y desinstala en Windows real
.github/workflows/release.yml  publica el .zip al crear un tag vX.Y.Z
```

Probar la conversión localmente:

```powershell
py -3.12 -m venv .venv; .venv\Scripts\pip install "markitdown[all]"
.venv\Scripts\python tests\test_conversion.py
```

Publicar una versión: `git tag v1.0.0 && git push --tags` → la Action crea el Release con el `.zip`.

## Alternativas

- [corgan2222/markitdown_context_menu](https://github.com/corgan2222/markitdown_context_menu): guarda junto al original o copia al portapapeles; requiere PowerShell 7.
- [andrekuros/MarkItDown_Windows_Right_Click](https://github.com/andrekuros/MarkItDown_Windows_Right_Click): convierte carpetas completas.

## Licencia

[MIT](LICENSE). MarkItDown es un proyecto de Microsoft bajo licencia MIT; este repositorio no está afiliado a Microsoft.

---

### English

**Derecho a Markdown** ("right to Markdown", a pun on *right-click*): Windows Explorer right-click entry that converts files to Markdown with [microsoft/markitdown](https://github.com/microsoft/markitdown) and asks where to save the `.md`. Per-user install (no admin), isolated Python venv, works with built-in Windows PowerShell 5.1. Extract the zip and run `instalar.bat`; run `desinstalar.bat` to remove. UI is in Spanish.
