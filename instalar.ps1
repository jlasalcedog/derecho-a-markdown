<#
  Instalador: "Convertir a Markdown" en el menú contextual de Windows.
  https://github.com/microsoft/markitdown  (este proyecto no está afiliado a Microsoft)
  - Crea un entorno Python aislado en %LOCALAPPDATA%\DerechoAMarkdown
  - Instala microsoft/markitdown (pip install "markitdown[all]")
  - Registra la opción para las extensiones soportadas (solo para tu usuario, sin admin)

  Parámetros opcionales:
    -IncluirMultimedia   Agrega también imágenes (.jpg .jpeg .png) y audio (.mp3 .wav .m4a)
    -MenuClasico         Activa el menú clásico de Windows 10 (opción visible sin "Mostrar más opciones")
    -SinPreguntas        No hace preguntas (usa solo los parámetros)
#>
param(
    [switch]$IncluirMultimedia,
    [switch]$MenuClasico,
    [switch]$SinPreguntas
)

$Version    = '1.0.0'
$InstallDir = Join-Path $env:LOCALAPPDATA 'DerechoAMarkdown'
$VenvDir    = Join-Path $InstallDir 'venv'
$AppDir     = Join-Path $InstallDir 'app'
$VerbKey    = 'DerechoAMarkdown'
# Nombres de versiones previas (se limpian al instalar)
$LegacyVerbKeys = @('MarkItDown')
$LegacyDirs     = @((Join-Path $env:LOCALAPPDATA 'MarkItDownMenu'))
$VerbText   = 'Convertir a Markdown'
$ClassicClsidKey = 'HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32'

# Formatos que MarkItDown convierte bien sin configuración extra
$Extensiones = @(
    '.pdf', '.docx', '.pptx', '.xlsx', '.xls', '.csv',
    '.html', '.htm', '.epub', '.ipynb', '.msg', '.zip',
    '.json', '.xml', '.rss', '.atom'
)
# Imágenes: solo metadatos EXIF (necesita exiftool) salvo que configures un LLM.
# Audio: transcribe usando el servicio de voz de Google (requiere internet).
$ExtMultimedia = @('.jpg', '.jpeg', '.png', '.mp3', '.wav', '.m4a')

function Titulo($t) { Write-Host ""; Write-Host "== $t ==" -ForegroundColor Cyan }
function Ok($t)     { Write-Host "  [OK] $t" -ForegroundColor Green }
function Aviso($t)  { Write-Host "  [!]  $t" -ForegroundColor Yellow }
function Preguntar($t) {
    if ($SinPreguntas) { return $false }
    $r = Read-Host "$t (S/N)"
    return ($r -match '^(s|si|sí|y|yes)$')
}

function Find-Python {
    # Devuelve @{ Exe; Args; Version; Ruta } de un Python 3.10-3.14, o $null.
    # OJO: sin comillas dobles dentro del codigo Python. Windows PowerShell 5.1 no las
    # escapa al pasarlas a programas externos y Python recibe codigo roto (SyntaxError).
    $consulta = 'import sys;print(sys.version_info[0],sys.version_info[1],sys.executable,sep=chr(124))'
    $candidatos = @()
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($v in '3.12', '3.13', '3.11', '3.10', '3.14', '3') { $candidatos += ,@('py', "-$v") }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) { $candidatos += ,@('python') }
    if (Get-Command python3 -ErrorAction SilentlyContinue) { $candidatos += ,@('python3') }
    foreach ($ver in '312', '313', '311', '310', '314') {
        foreach ($raiz in @((Join-Path $env:LOCALAPPDATA 'Programs\Python'), $env:ProgramFiles, 'C:\')) {
            if (-not $raiz) { continue }
            $p = "$($raiz.TrimEnd('\'))\Python$ver\python.exe"
            if (Test-Path -LiteralPath $p -ErrorAction SilentlyContinue) { $candidatos += ,@($p) }
        }
    }
    foreach ($c in $candidatos) {
        $exe = $c[0]; $extra = @(); if ($c.Count -gt 1) { $extra = @($c[1..($c.Count - 1)]) }
        $txt = ($exe + ' ' + ($extra -join ' ')).Trim()
        try {
            $out = & $exe @extra -c $consulta 2>$null
            $code = $LASTEXITCODE
        } catch { $out = $null; $code = -1 }
        $linea = @($out | Where-Object { $_ -match '^\d+\|\d+\|' }) | Select-Object -Last 1
        if ($code -ne 0 -or -not $linea) {
            Write-Host "     - $txt : no responde" -ForegroundColor DarkGray
            continue
        }
        $maj, $min, $ruta = $linea.Trim() -split '\|', 3
        $maj = [int]$maj; $min = [int]$min
        Write-Host "     - $txt : Python $maj.$min" -ForegroundColor DarkGray
        if ($maj -eq 3 -and $min -ge 10 -and $min -le 14) {
            return @{ Exe = $exe; Args = $extra; Version = "$maj.$min"; Ruta = $ruta }
        }
    }
    return $null
}

function Remove-MenuEntry {
    $base = 'HKCU:\Software\Classes\SystemFileAssociations'
    if (-not (Test-Path $base)) { return 0 }
    $n = 0
    Get-ChildItem $base -ErrorAction SilentlyContinue | ForEach-Object {
        foreach ($nombre in @($VerbKey) + $LegacyVerbKeys) {
            $k = Join-Path $_.PSPath "shell\$nombre"
            if (Test-Path -LiteralPath $k) { Remove-Item -LiteralPath $k -Recurse -Force; $n++ }
        }
    }
    return $n
}

# Con 'Stop', Windows PowerShell 5.1 aborta si un programa externo (pip, py) escribe
# una simple advertencia en stderr. Usamos 'Continue' y revisamos $LASTEXITCODE.
$ErrorActionPreference = 'Continue'
$Log = Join-Path $env:TEMP 'derecho-a-markdown_instalar.log'
try { Start-Transcript -Path $Log -Force | Out-Null } catch { }

try {
    Write-Host ""
    Write-Host "  Derecho a Markdown  v$Version" -NoNewline -ForegroundColor White; Write-Host "   (click derecho -> Markdown con microsoft/markitdown)" -ForegroundColor White
    Write-Host "  Repositorio: https://github.com/microsoft/markitdown" -ForegroundColor DarkGray

    if (-not (Test-Path (Join-Path $PSScriptRoot 'app\convertir_markitdown.pyw'))) {
        throw "No encuentro la carpeta 'app' junto al instalador. Descomprime el .zip completo (click derecho > Extraer todo) y ejecuta instalar.bat desde la carpeta extraida."
    }

    # ---------------------------------------------------------------- Python
    Titulo "1/4  Buscando Python 3.10 - 3.14"
    $py = Find-Python
    if (-not $py) {
        Aviso "No se encontró Python 3.10-3.14."
        if ((Get-Command winget -ErrorAction SilentlyContinue) -and (Preguntar "¿Instalar Python 3.12 con winget ahora?")) {
            winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
            $env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine')
            $py = Find-Python
        }
        if (-not $py) {
            throw "Instala Python 3.12 desde https://www.python.org/downloads/ (marca 'Add python.exe to PATH') y vuelve a ejecutar este instalador."
        }
    }
    Ok "Python $($py.Version) en $($py.Ruta)"

    # ---------------------------------------------------------------- venv + markitdown
    Titulo "2/4  Instalando MarkItDown (puede tardar 1-3 minutos)"
    New-Item -ItemType Directory -Force -Path $InstallDir -ErrorAction Stop | Out-Null
    $VenvPy  = Join-Path $VenvDir 'Scripts\python.exe'
    $VenvPyw = Join-Path $VenvDir 'Scripts\pythonw.exe'

    # Si quedó un entorno roto de un intento anterior, se recrea
    $venvOk = $false
    if (Test-Path $VenvPy) { & $VenvPy -c "import sys" 2>$null; $venvOk = ($LASTEXITCODE -eq 0) }
    if (-not $venvOk) {
        if (Test-Path $VenvDir) { Remove-Item -LiteralPath $VenvDir -Recurse -Force -ErrorAction SilentlyContinue }
        $pyArgs = @($py.Args)
        & $py.Exe @pyArgs -m venv $VenvDir
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPy)) { throw "No se pudo crear el entorno virtual con $($py.Exe) $($pyArgs -join ' ')." }
    }
    Ok "Entorno Python en $VenvDir"

    & $VenvPy -m pip install --upgrade pip --quiet --disable-pip-version-check
    & $VenvPy -m pip install --upgrade "markitdown[all]" --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) {
        Aviso "Falló 'markitdown[all]'. Probando solo con los formatos de oficina y PDF..."
        & $VenvPy -m pip install --upgrade "markitdown[pdf,docx,pptx,xlsx,xls,outlook]" --disable-pip-version-check
        if ($LASTEXITCODE -ne 0) { throw "Falló 'pip install markitdown'. Revisa tu conexión a internet (o el proxy de tu red)." }
    }
    $mdVer = & $VenvPy -c "import markitdown; print(markitdown.__version__)"
    if ($LASTEXITCODE -ne 0) { throw "MarkItDown se instaló pero no se puede importar." }
    Ok "markitdown $mdVer instalado"

    # ---------------------------------------------------------------- archivos de la app
    Titulo "3/4  Copiando la aplicación"
    New-Item -ItemType Directory -Force -Path $AppDir -ErrorAction Stop | Out-Null
    Copy-Item -Path (Join-Path $PSScriptRoot 'app\*') -Destination $AppDir -Recurse -Force -ErrorAction Stop
    Copy-Item -Path (Join-Path $PSScriptRoot 'desinstalar.ps1') -Destination $InstallDir -Force -ErrorAction Stop
    Ok "Archivos en $InstallDir"

    # ---------------------------------------------------------------- registro
    Titulo "4/4  Registrando la opción en el menú contextual"
    if (-not $IncluirMultimedia -and -not $SinPreguntas) {
        $IncluirMultimedia = Preguntar "¿Incluir también imágenes y audio (.jpg .png .mp3 .wav .m4a)? Recomendado: N"
    }
    $lista = $Extensiones
    if ($IncluirMultimedia) { $lista += $ExtMultimedia }

    [void](Remove-MenuEntry)   # limpia instalaciones anteriores (incluye nombres antiguos)
    foreach ($d in $LegacyDirs) {
        if (Test-Path -LiteralPath $d) {
            Remove-Item -LiteralPath $d -Recurse -Force -ErrorAction SilentlyContinue
            Ok "Eliminada instalación anterior en $d"
        }
    }
    $script = Join-Path $AppDir 'convertir_markitdown.pyw'
    $icono  = Join-Path $AppDir 'markitdown.ico'
    $cmd    = "`"$VenvPyw`" `"$script`" `"%1`""
    foreach ($ext in $lista) {
        $k = "HKCU:\Software\Classes\SystemFileAssociations\$ext\shell\$VerbKey"
        New-Item -Path $k -Force -ErrorAction Stop | Out-Null
        New-ItemProperty -Path $k -Name 'MUIVerb' -Value $VerbText -PropertyType String -Force -ErrorAction Stop | Out-Null
        New-ItemProperty -Path $k -Name 'Icon'    -Value $icono    -PropertyType String -Force -ErrorAction Stop | Out-Null
        New-Item -Path "$k\command" -Value $cmd -Force -ErrorAction Stop | Out-Null
    }
    Ok ("Opción agregada para: " + ($lista -join ' '))

    # ---------------------------------------------------------------- Windows 11
    $build = [int](Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').CurrentBuildNumber
    if ($build -ge 22000) {
        Write-Host ""
        Aviso "En Windows 11 el menú nuevo esconde las opciones de programas en 'Mostrar más opciones' (o Shift + click derecho)."
        if (-not $MenuClasico -and -not $SinPreguntas) {
            $MenuClasico = Preguntar "¿Activar el menú clásico para que la opción aparezca directo al hacer click derecho?"
        }
        if ($MenuClasico) {
            & reg.exe add $ClassicClsidKey /ve /f | Out-Null
            Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            if (-not (Get-Process explorer -ErrorAction SilentlyContinue)) { Start-Process explorer.exe }
            Ok "Menú clásico activado (se reinició el Explorador)."
        }
    }

    Write-Host ""
    Write-Host "  Instalación terminada." -ForegroundColor Green
    Write-Host "  Click derecho sobre un PDF, Word, Excel, PowerPoint... -> '$VerbText'"
    Write-Host "  Para desinstalar: desinstalar.bat (o $InstallDir\desinstalar.ps1)"
    try { Stop-Transcript | Out-Null } catch { }
    exit 0
}
catch {
    Write-Host ""
    Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Registro completo en: $Log" -ForegroundColor Yellow
    Write-Host "  (puedes pegarme ese archivo o una captura de esta ventana)" -ForegroundColor Yellow
    try { Stop-Transcript | Out-Null } catch { }
    exit 1
}
